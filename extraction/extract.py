#!/usr/bin/env python3
"""
Product Attribute Extraction CLI

Usage:
    # Extract from a single file
    python extract.py /path/to/product_datasheet.pdf

    # Extract from a folder of documents for one product
    python extract.py /path/to/product_docs/

    # Extract and print JSON to stdout (no file writes)
    python extract.py /path/to/product_datasheet.pdf --json-only

    # Use a specific Claude model
    python extract.py /path/to/product_docs/ --model claude-opus-4-20250514

Environment:
    ANTHROPIC_API_KEY: Required. Your Anthropic API key.
"""

from lib.extractor import main

if __name__ == "__main__":
    main()
