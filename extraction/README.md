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
```

## Prerequisites

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
```

## Output Format

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
    }
  }
}
```

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
