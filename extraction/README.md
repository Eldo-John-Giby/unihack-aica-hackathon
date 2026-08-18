<<<<<<< HEAD
# Extraction Module - Product Intelligence Pipeline

This module extracts structured product attributes from source documents (PDFs, images, text files, HTML pages) using Claude's vision and text capabilities.

## Overview

The extraction module processes individual source documents and outputs JSON files following the shared schema (`/shared/schema.json`). Each source document produces one JSON output file with extracted product attributes including confidence scores and source tracking.

## Features

- **Multi-format support**: Process PDFs, images (JPG, PNG, etc.), text files, HTML, Markdown, and JSON
- **Claude-powered extraction**: Uses Claude's vision capabilities for images and PDFs
- **Confidence scoring**: Each extracted field includes a confidence score (0-100)
- **Source tracking**: All extractions are tracked back to source document and location
- **Conflict detection**: Identifies conflicting values across document sections
- **Batch processing**: Process entire folders of documents at once

## Directory Structure

```
extraction/
├── extract.py           # Main extraction script
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── sample_data/        # Sample product documents for testing
    ├── product_datasheet.txt
    ├── product_page.html
    ├── technical_specs.md
    ├── product_data.json
    └── product_description.txt
=======
# Extraction Module

**Owner:** Eldo

## Overview

This module extracts structured product attributes from source documents (PDFs, images, text/HTML files) using Claude's vision and text capabilities. It outputs per-document JSON files following the shared schema contract defined in `/shared/schema.json`.

## Structure

```
/extraction/
├── extract.py              # CLI entry point
├── lib/
│   └── extractor.py        # Core extraction logic (Claude API)
├── sample_data/            # Test documents (realistic product docs)
│   ├── industrial_motor_datasheet.txt
│   ├── power_tool_product_page.html
│   ├── sensor_datasheet.txt
│   ├── chemical_product_specs.txt
│   └── furniture_product_data.json
├── mock_data/              # Pre-structured mock outputs (no API needed)
│   └── example_extraction_output.json
├── requirements.txt        # Python dependencies
└── README.md               # This file
>>>>>>> f7768a8c919c9d413852c835d8d1607e8695051f
```

## Prerequisites

<<<<<<< HEAD
- Python 3.8 or higher
- Anthropic API key (Claude API access)
- Internet connection (for Claude API calls)

## Installation

1. **Clone or navigate to the extraction module directory:**
   ```bash
   cd extraction
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Anthropic API key:**
   
   **Option A: Environment Variable (Recommended)**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
   
   **Option B: Pass via command line**
   ```bash
   python extract.py --api-key "your-api-key-here" ...
   ```

## Usage

### Command Line Interface (CLI)

**Extract from a single file:**
```bash
python extract.py path/to/product_file.pdf --product-id PROD-001
```

**Extract from a folder of documents:**
```bash
python extract.py path/to/product_folder/ --product-id PROD-001 --output-dir ./output
```

**With custom output directory:**
```bash
python extract.py ./sample_data/ --product-id SAMPLE-001 --output-dir ./test_output
```

### Python API (for other modules)

```python
from extract import extract

# Extract from a single file
result = extract(
    file_path="path/to/document.pdf",
    product_id="PROD-001",
    output_dir="./output"
)

# Extract from a folder
results = extract(
    file_path="path/to/product_folder/",
    product_id="PROD-001",
    output_dir="./output"
)

# Access extracted data
for field_name, field_data in result.get("fields", {}).items():
    print(f"{field_name}: {field_data['value']} (confidence: {field_data['confidence']}%)")
```

### Programmatic Usage (Advanced)

```python
from extract import ProductExtractor

# Initialize extractor
extractor = ProductExtractor(api_key="your-api-key")

# Extract from text content
result = extractor.extract_from_text(
    content="Product specifications text...",
    filename="spec.txt",
    product_id="PROD-001"
)

# Extract from image
result = extractor.extract_from_image(
    image_path="product_image.jpg",
    filename="product.jpg",
    product_id="PROD-001"
)

# Extract from PDF
result = extractor.extract_from_pdf(
    pdf_path="datasheet.pdf",
    filename="datasheet.pdf",
    product_id="PROD-001"
)
=======
- Python 3.10+
- An Anthropic API key

## Setup

```bash
cd extraction
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

### Extract from a single file

```bash
python extract.py sample_data/industrial_motor_datasheet.txt
# -> Creates industrial_motor_datasheet_extracted.json in the same directory
```

### Extract from a folder (all documents for one product)

```bash
python extract.py sample_data/
# -> Creates *_extracted.json for each document in sample_data/
```

### Print JSON to stdout (no file writes)

```bash
python extract.py sample_data/sensor_datasheet.txt --json-only
```

### Use a different Claude model

```bash
python extract.py sample_data/ --model claude-opus-4-20250514
```

## As a Library

```python
from lib.extractor import extract_from_file, extract_from_folder

# Single file
record = extract_from_file("sample_data/power_tool_product_page.html")
print(record["product_id"])
print(record["fields"]["weight"])

# Entire folder
records = extract_from_folder("sample_data/")
for r in records:
    print(f"{r['source_doc']}: {len(r['fields'])} fields extracted")
>>>>>>> f7768a8c919c9d413852c835d8d1607e8695051f
```

## Output Format

<<<<<<< HEAD
Each extracted document produces a JSON file following the shared schema:

```json
{
  "product_id": "PROD-001",
  "fields": {
    "product_name": {
      "value": "Widget Pro 3000",
      "source": "extracted",
      "source_doc": "datasheet.pdf",
      "source_location": "page 1, header section",
      "confidence": 95,
      "reasoning": "Found in main title and product overview",
      "conflicts": []
    },
    "weight": {
      "value": "5.2 kg",
      "source": "extracted",
      "source_doc": "datasheet.pdf",
      "source_location": "page 2, physical specifications table",
      "confidence": 90,
      "reasoning": "Clearly listed in specifications table",
      "conflicts": [
        {
          "value": "5.4 kg",
          "source_doc": "product_page.html",
          "resolved": false
        }
      ]
=======
Each extracted JSON file follows the shared product record schema:

```json
{
  "product_id": "PROD-XXXX",
  "source_doc": "original_filename.pdf",
  "fields": {
    "field_name": {
      "value": "extracted value",
      "source": "extracted | inferred",
      "source_doc": "original_filename.pdf",
      "source_location": "page 2 / section: Specifications",
      "confidence": 95,
      "reasoning": "short explanation",
      "conflicts": []
>>>>>>> f7768a8c919c9d413852c835d8d1607e8695051f
    }
  }
}
```

<<<<<<< HEAD
## Sample Data

The `sample_data/` directory contains 5 sample product documents for testing:

1. **product_datasheet.txt** - Industrial motor technical datasheet
2. **product_page.html** - Consumer electronics product page (headphones)
3. **technical_specs.md** - Industrial robot arm specifications (Markdown)
4. **product_data.json** - Laptop product data in JSON format
5. **product_description.txt** - Workbench product description

### Running Tests with Sample Data

**Test with a single file:**
```bash
# Activate virtual environment (if using)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Run extraction
python extract.py sample_data/product_datasheet.txt --product-id SAMPLE-MOTOR-001
```

**Test with all sample data:**
```bash
python extract.py ./sample_data/ --product-id SAMPLE-TEST --output-dir ./test_output
```

## API Key Setup

### Getting an Anthropic API Key

1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and save securely

### Key Security Notes

- **Never commit API keys to version control**
- **Use environment variables** for production
- **Rotate keys regularly**
- **Set up usage limits** in your Anthropic dashboard

## Supported File Types

| Format | Extension | Method |
|--------|-----------|--------|
| Text files | .txt, .md, .csv | Text extraction |
| HTML | .html, .htm | Text extraction |
| JSON | .json | Text extraction |
| XML | .xml | Text extraction |
| PDF | .pdf | Vision (page-by-page) |
| Images | .jpg, .jpeg, .png, .gif, .bmp, .webp | Vision |

## Common Issues & Solutions

### API Key Errors
```
Error: anthropic package not installed
```
**Solution:** Install requirements: `pip install -r requirements.txt`

### Rate Limiting
```
Error: Rate limit exceeded
```
**Solution:** Wait 60 seconds or reduce batch size. Consider implementing retry logic.

### PDF Processing Issues
```
Warning: pdf2image not available
```
**Solution:** Install poppler-utils:
- **macOS:** `brew install poppler`
- **Ubuntu/Debian:** `sudo apt-get install poppler-utils`
- **Windows:** Download poppler binaries and add to PATH

### Large File Processing
For very large PDFs (>50 pages), consider:
- Splitting into smaller documents
- Processing specific pages only
- Implementing pagination in extraction

## Integration with Other Modules

This module is designed to work with the Product Intelligence Pipeline:

### Data Flow
```
Source Documents → [EXTRACTION MODULE] → Per-document JSON files
                                              ↓
                                    (RECONCILIATION MODULE merges data)
```

### Calling from Other Modules

```python
# In reconciliation module
import sys
sys.path.append('../extraction')
from extract import extract

# Extract and process
results = extract("./raw_documents/product_1/", "PROD-001")
```

## Development Notes

### Adding New File Types

To support additional file types, modify the `extract_file` method in `ProductExtractor`:

```python
def extract_file(self, file_path: str, product_id: str) -> Dict[str, Any]:
    # Add new file type handling
    if mime_type == "application/new-type":
        return self.extract_from_new_type(str(file_path), filename, product_id)
```

### Custom Extraction Prompts

Modify `_build_extraction_prompt` to customize what attributes are extracted for specific document types.

## Version History

- **v1.0.0** (Current) - Initial release with multi-format support
  - PDF, image, and text extraction
  - Claude-powered analysis
  - Batch processing
  - Confidence scoring

## License

Internal use only - Part of Product Intelligence Pipeline

## Support

For issues or questions:
- Check the troubleshooting section above
- Review sample data for expected input format
- Test with provided sample documents first

---

**Note:** This module is owned by Eldo (extraction team). Please do not modify files outside the `/extraction` directory. For shared schema changes, coordinate with the team.
=======
**Key rules:**
- One JSON file per source document — never merged across documents
- Each field includes confidence score (0-100) and reasoning
- `source` is "extracted" (direct from doc) or "inferred" (derived)
- Conflicts within a single document go in the `conflicts` array

## Testing Without API

The `mock_data/` folder contains pre-structured extraction outputs that match the schema. You can use these to test downstream modules without calling the Claude API.

## Supported File Types

| Extension | Method |
|-----------|--------|
| `.pdf`    | Claude Vision (document API) |
| `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | Claude Vision (image API) |
| `.txt`, `.html`, `.htm`, `.md`, `.csv`, `.xml` | Claude Text |

## Notes

- The module extracts per-document only. Cross-document reconciliation is handled by the `/reconciliation` module.
- All sample data files are fabricated for testing purposes.
- The Claude API call uses `claude-sonnet-4-20250514` by default for cost efficiency.
>>>>>>> f7768a8c919c9d413852c835d8d1607e8695051f
