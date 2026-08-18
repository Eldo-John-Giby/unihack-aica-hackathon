"""
Product Attribute Extraction Module

Extracts structured product attributes from source documents using Claude's
vision and text capabilities. Outputs per-document JSON following the shared
schema contract.
"""

import base64
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

import anthropic


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """\
You are a precise product data extraction system. Your task is to extract ALL \
product attributes from the provided document.

Return a JSON object with this exact structure (no markdown fences, just raw JSON):
{
  "product_id": "<generate a short unique id like 'PROD-XXXX' based on the product name>",
  "source_doc": "<the filename of this document>",
  "fields": {
    "<field_name>": {
      "value": <the extracted value>,
      "source": "extracted" or "inferred",
      "source_doc": "<filename>",
      "source_location": "<page number or section, e.g. 'page 2', 'section: Specifications', 'header'>",
      "confidence": <number 0-100>,
      "reasoning": "<short explanation of how you extracted this value>",
      "conflicts": []
    }
  }
}

RULES:
1. Extract EVERY relevant product attribute: name, brand/manufacturer, model/SKU, \
dimensions, weight, material, color, price, ratings/reviews, certifications, \
features, description, power requirements, operating temperature, IP rating, \
country of origin, warranty, package contents — include whatever is relevant.
2. For multi-value fields (like dimensions), store as a string like "10 x 5 x 3 cm".
3. If a field appears in multiple places in the document with different values, \
put the primary value in "value" and add entries to the "conflicts" array.
4. Set source="inferred" when you're deriving a value rather than copying it \
directly (e.g., inferring material from a description).
5. Set confidence based on how certain you are: 90-100 = explicit, \
70-89 = clearly implied, 50-69 = inferred from context, below 50 = uncertain.
6. source_location should be as specific as possible: page number, section \
heading, or element description.
7. Return ONLY valid JSON, nothing else.
"""


# ---------------------------------------------------------------------------
# File reading helpers
# ---------------------------------------------------------------------------

def _read_file_as_base64(file_path: str) -> tuple[str, str]:
    """Read a file and return (base64_data, media_type)."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # Fallback based on extension
        ext = Path(file_path).suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".html": "text/html",
            ".htm": "text/html",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".csv": "text/csv",
            ".xml": "application/xml",
            ".json": "application/json",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

    with open(file_path, "rb") as f:
        data = f.read()

    b64 = base64.standard_b64encode(data).decode("utf-8")
    return b64, mime_type


def _read_text_file(file_path: str) -> str:
    """Read a text file and return its content."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _is_image(mime_type: str) -> bool:
    return mime_type.startswith("image/")


def _is_pdf(mime_type: str) -> bool:
    return mime_type == "application/pdf"


def _is_text(mime_type: str) -> bool:
    return mime_type.startswith("text/") or mime_type in (
        "application/xml",
        "application/json",
    )


# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

def _build_vision_content(file_path: str, b64_data: str, media_type: str) -> list[dict]:
    """Build Claude vision API content blocks for binary files (PDF, images)."""
    return [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64_data,
            },
        },
        {
            "type": "text",
            "text": EXTRACTION_PROMPT,
        },
    ]


def _build_text_content(file_path: str, text_data: str) -> list[dict]:
    """Build Claude API content blocks for text/HTML files."""
    prompt = EXTRACTION_PROMPT + f"\n\n--- DOCUMENT CONTENT ---\n\n{text_data}"
    return [{"type": "text", "text": prompt}]


def extract_from_file(
    file_path: str,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict[str, Any]:
    """
    Extract product attributes from a single source document.

    Args:
        file_path: Path to the source document (PDF, image, text, or HTML).
        client: Optional Anthropic client instance. If None, creates one
                using ANTHROPIC_API_KEY env var.
        model: Claude model to use for extraction.

    Returns:
        A dict matching the shared product record schema.
    """
    file_path = os.path.abspath(file_path)
    filename = os.path.basename(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source document not found: {file_path}")

    if client is None:
        client = anthropic.Anthropic()

    # Read the file and determine type
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    if _is_image(mime_type) or _is_pdf(mime_type):
        b64_data, media_type = _read_file_as_base64(file_path)
        content = _build_vision_content(file_path, b64_data, media_type)
    elif _is_text(mime_type):
        text_data = _read_text_file(file_path)
        content = _build_text_content(file_path, text_data)
    else:
        # Try reading as text, fall back to vision
        try:
            text_data = _read_text_file(file_path)
            content = _build_text_content(file_path, text_data)
        except Exception:
            b64_data, media_type = _read_file_as_base64(file_path)
            content = _build_vision_content(file_path, b64_data, media_type)

    # Call Claude API
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )

    # Parse response
    raw_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            raise ValueError(
                f"Failed to parse Claude response as JSON.\n"
                f"Response:\n{raw_text[:500]}"
            )

    # Ensure source_doc is set correctly
    result["source_doc"] = filename
    if "fields" in result:
        for field_name, field_data in result["fields"].items():
            if isinstance(field_data, dict):
                field_data["source_doc"] = filename

    return result


def extract_from_folder(
    folder_path: str,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-sonnet-4-20250514",
    output_dir: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Extract product attributes from all supported files in a folder.

    Args:
        folder_path: Path to folder containing source documents for one product.
        client: Optional Anthropic client instance.
        model: Claude model to use.
        output_dir: Where to write per-document JSON files. Defaults to the
                    input folder.

    Returns:
        List of extracted product records (one per document).
    """
    folder_path = os.path.abspath(folder_path)
    if output_dir is None:
        output_dir = folder_path
    os.makedirs(output_dir, exist_ok=True)

    supported_exts = {
        ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
        ".txt", ".html", ".htm", ".md", ".csv", ".xml", ".json",
    }

    results = []
    files = sorted(os.listdir(folder_path))

    for fname in files:
        fpath = os.path.join(folder_path, fname)
        if not os.path.isfile(fpath):
            continue
        ext = Path(fname).suffix.lower()
        if ext not in supported_exts:
            print(f"  Skipping unsupported file: {fname}")
            continue

        print(f"  Extracting from: {fname}")
        try:
            record = extract_from_file(fpath, client=client, model=model)
            results.append(record)

            # Write per-document JSON
            out_name = Path(fname).stem + "_extracted.json"
            out_path = os.path.join(output_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            print(f"    -> {out_name}")
        except Exception as e:
            print(f"    ERROR extracting {fname}: {e}", file=sys.stderr)

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """CLI interface for the extraction module."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract product attributes from source documents using Claude."
    )
    parser.add_argument(
        "path",
        help="Path to a single file or a folder of source documents.",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for extracted JSON files. Defaults to same as input.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print extracted JSON to stdout (no file writes).",
    )

    args = parser.parse_args()

    target = os.path.abspath(args.path)
    if not os.path.exists(target):
        print(f"Error: path not found: {target}", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()

    if os.path.isfile(target):
        # Single file extraction
        print(f"Extracting from: {target}")
        record = extract_from_file(target, client=client, model=args.model)

        if args.json_only:
            print(json.dumps(record, indent=2, ensure_ascii=False))
        else:
            out_dir = args.output_dir or os.path.dirname(target)
            out_name = Path(target).stem + "_extracted.json"
            out_path = os.path.join(out_dir, out_name)
            os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            print(f"Output: {out_path}")
    elif os.path.isdir(target):
        # Folder extraction
        print(f"Extracting from folder: {target}")
        results = extract_from_folder(
            target, client=client, model=args.model,
            output_dir=args.output_dir,
        )
        print(f"\nDone. Extracted {len(results)} document(s).")


if __name__ == "__main__":
    main()
