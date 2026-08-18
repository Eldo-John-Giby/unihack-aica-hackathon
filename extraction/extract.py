#!/usr/bin/env python3
"""
Product Intelligence - Extraction Module
Extracts structured product attributes from source documents using Claude's vision and text capabilities.
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    print("Warning: anthropic package not installed. Using mock extraction.")
    print("For full functionality, run: pip install -r requirements.txt")
    ANTHROPIC_AVAILABLE = False

# Schema reference (read-only)
SCHEMA_PATH = Path(__file__).parent.parent / "shared" / "schema.json"

class ProductExtractor:
    """Extracts product attributes from documents using Claude API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the extractor with optional API key."""
        if ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.client = None
            self.model = "mock"
        
    def extract_from_text(self, content: str, filename: str, product_id: str) -> Dict[str, Any]:
        """Extract product attributes from text content."""
        prompt = self._build_extraction_prompt(content, filename, "text")
        return self._call_claude_api(prompt, filename, product_id, content_type="text")
    
    def extract_from_image(self, image_path: str, filename: str, product_id: str) -> Dict[str, Any]:
        """Extract product attributes from an image."""
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Determine media type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg"
        
        prompt = self._build_extraction_prompt("", filename, "image")
        return self._call_claude_api_with_vision(
            prompt, image_data, mime_type, filename, product_id
        )
    
    def extract_from_pdf(self, pdf_path: str, filename: str, product_id: str) -> Dict[str, Any]:
        """Extract product attributes from a PDF (using vision on rendered pages)."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)
            
            all_fields = {}
            for i, img in enumerate(images):
                # Convert PIL Image to base64
                import io
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
                
                page_num = i + 1
                prompt = self._build_extraction_prompt(
                    "", f"{filename} (page {page_num})", "pdf_page"
                )
                
                result = self._call_claude_api_with_vision(
                    prompt, image_data, "image/jpeg", filename, product_id,
                    page_info=f"page {page_num}"
                )
                
                # Merge fields from this page
                for field_name, field_data in result.get("fields", {}).items():
                    if field_name not in all_fields:
                        all_fields[field_name] = field_data
                    else:
                        # Keep the one with higher confidence
                        if field_data.get("confidence", 0) > all_fields[field_name].get("confidence", 0):
                            all_fields[field_name] = field_data
            
            return {
                "product_id": product_id,
                "fields": all_fields
            }
            
        except ImportError:
            print("Warning: pdf2image not available, falling back to text extraction")
            with open(pdf_path, "rb") as f:
                # Simple fallback - try to extract text from PDF
                content = f.read().decode("utf-8", errors="ignore")
                return self.extract_from_text(content, filename, product_id)
    
    def _build_extraction_prompt(self, content: str, filename: str, content_type: str) -> str:
        """Build the extraction prompt for Claude."""
        base_prompt = f"""You are a product data extraction specialist. Extract ALL product attributes from this {content_type} document.

For EACH attribute you extract, provide:
- value: The actual value
- source_doc: "{filename}"
- source_location: Page number or section name (e.g., "page 1", "technical specs section")
- confidence: 0-100 (how confident you are in this extraction)
- reasoning: Brief explanation of why you extracted this value
- conflicts: Array of any conflicting values you see (empty array if none)

Focus on extracting these common product fields (and any others you find):
- product_name / name
- brand / manufacturer
- model_number / sku
- dimensions (length, width, height, depth)
- weight
- material(s)
- color(s)
- ratings (customer ratings, scores)
- price (if shown)
- features / specifications
- certifications
- warranty information
"""
        
        if content_type == 'text':
            content_section = f"Content to analyze:\n{content}"
        else:
            content_section = "Analyze the visual content of this image."
        
        json_structure = f"""
Return your extraction as JSON with this structure:
{{
  "product_id": "placeholder",
  "fields": {{
    "field_name": {{
      "value": "extracted value",
      "source": "extracted",
      "source_doc": "{filename}",
      "source_location": "page/section info",
      "confidence": 85,
      "reasoning": "Found in technical specifications table",
      "conflicts": []
    }}
  }}
}}

Be thorough but precise. Only extract values you're confident about. If something is ambiguous, note it in reasoning."""
        
        return base_prompt + content_section + json_structure
    
    def _call_claude_api(self, prompt: str, filename: str, product_id: str, 
                         content: str = "", content_type: str = "text") -> Dict[str, Any]:
        """Call Claude API for text extraction."""
        if not ANTHROPIC_AVAILABLE or not self.client:
            return self._mock_extraction(filename, product_id, "text")
            
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            response_text = message.content[0].text
            return self._parse_claude_response(response_text, filename, product_id)
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return self._create_error_result(filename, product_id, str(e))
    
    def _call_claude_api_with_vision(self, prompt: str, image_data: str, 
                                     media_type: str, filename: str, product_id: str,
                                     page_info: str = "") -> Dict[str, Any]:
        """Call Claude API with vision for images/PDFs."""
        if not ANTHROPIC_AVAILABLE or not self.client:
            return self._mock_extraction(filename, product_id, "vision")
            
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            response_text = message.content[0].text
            return self._parse_claude_response(response_text, filename, product_id)
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return self._create_error_result(filename, product_id, str(e))
    
    def _parse_claude_response(self, response_text: str, filename: str, product_id: str) -> Dict[str, Any]:
        """Parse Claude's response into our schema format."""
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                # Ensure proper structure
                if "product_id" not in result:
                    result["product_id"] = product_id
                if "fields" not in result:
                    result["fields"] = {}
                    
                return result
            else:
                # If no JSON found, create a basic result
                return self._create_error_result(filename, product_id, "Could not parse Claude response")
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return self._create_error_result(filename, product_id, f"JSON parse error: {e}")
    
    def _create_error_result(self, filename: str, product_id: str, error: str) -> Dict[str, Any]:
        """Create an error result in schema format."""
        return {
            "product_id": product_id,
            "fields": {
                "_error": {
                    "value": error,
                    "source": "inferred",
                    "source_doc": filename,
                    "source_location": "extraction_error",
                    "confidence": 0,
                    "reasoning": f"Extraction failed: {error}",
                    "conflicts": []
                }
            }
        }
    
    def _mock_extraction(self, filename: str, product_id: str, extraction_type: str) -> Dict[str, Any]:
        """Mock extraction for testing without API access."""
        print(f"  [MOCK] Simulating {extraction_type} extraction for {filename}")
        
        # Return realistic mock data based on filename patterns
        mock_fields = {}
        
        if "datasheet" in filename.lower() or "motor" in filename.lower():
            mock_fields = {
                "product_name": {
                    "value": "Industrial Precision Motor X200",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "header section",
                    "confidence": 95,
                    "reasoning": "Found in product title",
                    "conflicts": []
                },
                "model_number": {
                    "value": "X200-PRO-400",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "general information section",
                    "confidence": 98,
                    "reasoning": "Clearly stated in specifications",
                    "conflicts": []
                },
                "weight": {
                    "value": "8.2 kg",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "physical specifications",
                    "confidence": 90,
                    "reasoning": "Found in weight specification",
                    "conflicts": []
                },
                "dimensions": {
                    "value": "400mm x 150mm x 150mm",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "physical specifications",
                    "confidence": 92,
                    "reasoning": "Extracted from dimensions table",
                    "conflicts": []
                },
                "material": {
                    "value": "Anodized Aluminum Alloy (6061-T6)",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "physical specifications",
                    "confidence": 88,
                    "reasoning": "Found in housing material specification",
                    "conflicts": []
                }
            }
        elif "headphone" in filename.lower() or "audio" in filename.lower():
            mock_fields = {
                "product_name": {
                    "value": "ProGuard Wireless Noise-Canceling Headphones",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "page title",
                    "confidence": 96,
                    "reasoning": "Found in main heading",
                    "conflicts": []
                },
                "price": {
                    "value": "$349.99",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "pricing section",
                    "confidence": 99,
                    "reasoning": "Current price clearly displayed",
                    "conflicts": []
                },
                "weight": {
                    "value": "254g",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "specifications table",
                    "confidence": 95,
                    "reasoning": "Listed in technical specs",
                    "conflicts": []
                },
                "rating": {
                    "value": "4.7/5.0",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "customer reviews section",
                    "confidence": 98,
                    "reasoning": "Average rating displayed",
                    "conflicts": []
                },
                "color": {
                    "value": "Midnight Black, Arctic White, Navy Blue",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "materials section",
                    "confidence": 94,
                    "reasoning": "Available colors listed",
                    "conflicts": []
                }
            }
        elif "robot" in filename.lower() or "arm" in filename.lower():
            mock_fields = {
                "product_name": {
                    "value": "TechSpec RS-2000 Articulated Robot Arm",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "title",
                    "confidence": 97,
                    "reasoning": "Main product title",
                    "conflicts": []
                },
                "payload_capacity": {
                    "value": "20 kg",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "overview section",
                    "confidence": 99,
                    "reasoning": "Primary specification highlighted",
                    "conflicts": []
                },
                "reach": {
                    "value": "1800 mm",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "mechanical specifications",
                    "confidence": 96,
                    "reasoning": "Listed in specs table",
                    "conflicts": []
                },
                "weight": {
                    "value": "185 kg",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "mechanical specifications",
                    "confidence": 94,
                    "reasoning": "Robot weight specification",
                    "conflicts": []
                }
            }
        else:
            # Generic mock data
            mock_fields = {
                "product_name": {
                    "value": f"Extracted Product from {filename}",
                    "source": "extracted",
                    "source_doc": filename,
                    "source_location": "document",
                    "confidence": 85,
                    "reasoning": "Generic extraction from document",
                    "conflicts": []
                }
            }
        
        return {
            "product_id": product_id,
            "fields": mock_fields
        }
    
    def extract_file(self, file_path: str, product_id: str) -> Dict[str, Any]:
        """Extract product attributes from a single file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return self._create_error_result(file_path.name, product_id, "File not found")
        
        filename = file_path.name
        mime_type, _ = mimetypes.guess_type(filename)
        
        # Determine extraction method based on file type
        if mime_type and mime_type.startswith("image/"):
            return self.extract_from_image(str(file_path), filename, product_id)
        elif mime_type == "application/pdf":
            return self.extract_from_pdf(str(file_path), filename, product_id)
        elif mime_type and (mime_type.startswith("text/") or 
                          mime_type in ["application/json", "application/xml", 
                                       "application/javascript", "application/x-yaml"]):
            # Text-based file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.extract_from_text(content, filename, product_id)
        else:
            # Try to read as text
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return self.extract_from_text(content, filename, product_id)
            except:
                return self._create_error_result(filename, product_id, 
                                                 f"Unsupported file type: {mime_type}")
    
    def extract_folder(self, folder_path: str, product_id: str, 
                       output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract product attributes from all files in a folder."""
        folder_path = Path(folder_path)
        output_dir = Path(output_dir) if output_dir else folder_path
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not folder_path.exists():
            print(f"Error: Folder {folder_path} does not exist")
            return []
        
        results = []
        supported_extensions = {".txt", ".md", ".html", ".htm", ".xml", ".json",
                               ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        
        for file_path in sorted(folder_path.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                print(f"Extracting from: {file_path.name}")
                result = self.extract_file(str(file_path), product_id)
                
                # Save output JSON
                output_file = output_dir / f"{file_path.stem}_extracted.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"  Saved: {output_file.name}")
                results.append(result)
        
        return results


def extract(file_path: str, product_id: str = "product_001", 
            output_dir: Optional[str] = None) -> Dict[str, Any] or List[Dict[str, Any]]:
    """
    Main extraction function - can be called by other modules.
    
    Args:
        file_path: Path to a file or folder of files
        product_id: Unique product identifier
        output_dir: Directory to save JSON outputs (defaults to same as input)
    
    Returns:
        Extracted data in schema format
    """
    extractor = ProductExtractor()
    path = Path(file_path)
    
    if path.is_dir():
        return extractor.extract_folder(file_path, product_id, output_dir)
    else:
        result = extractor.extract_file(file_path, product_id)
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = path.parent
        
        output_file = output_dir / f"{path.stem}_extracted.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result


def main():
    """CLI interface for the extraction module."""
    parser = argparse.ArgumentParser(
        description="Extract product attributes from documents using Claude API"
    )
    parser.add_argument("path", help="File or folder to extract from")
    parser.add_argument("--product-id", "-p", default="product_001",
                       help="Product ID (default: product_001)")
    parser.add_argument("--output-dir", "-o", help="Output directory for JSON files")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.path):
        print(f"Error: Path {args.path} does not exist")
        sys.exit(1)
    
    # Run extraction
    results = extract(args.path, args.product_id, args.output_dir)
    
    # Print summary
    if isinstance(results, list):
        print(f"\nExtracted attributes from {len(results)} documents")
    else:
        print(f"\nExtraction complete for {args.path}")


if __name__ == "__main__":
    main()