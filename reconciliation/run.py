#!/usr/bin/env python3
"""
Reconciliation CLI Entry Point

Usage:
    # Reconcile all mock inputs (standalone test)
    python reconciliation/run.py

    # Reconcile specific files
    python reconciliation/run.py path/to/doc1.json path/to/doc2.json

    # Save to custom output path
    python reconciliation/run.py --output path/to/output.json path/to/doc1.json path/to/doc2.json
"""

import argparse
import json
import sys
from pathlib import Path

from .reconciler import reconcile_from_files, save_merged


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile multiple extraction JSONs into one merged product record."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Paths to extraction JSON files. If none provided, uses mock_inputs/.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output path for merged JSON. Default: output/<product_id>_merged.json",
    )
    parser.add_argument(
        "--model", "-m",
        default="claude-sonnet-4-20250514",
        help="Claude model to use for conflict resolution.",
    )

    args = parser.parse_args()

    # Determine input files
    if args.inputs:
        input_files = [Path(p) for p in args.inputs]
    else:
        # Use mock inputs directory
        mock_dir = Path(__file__).parent / "mock_inputs"
        if not mock_dir.exists():
            print(f"Error: mock_inputs directory not found at {mock_dir}")
            sys.exit(1)
        input_files = sorted(mock_dir.glob("*.json"))
        if not input_files:
            print(f"Error: No JSON files found in {mock_dir}")
            sys.exit(1)
        print(f"No input files specified, using mock inputs from {mock_dir}/")

    # Validate input files
    for f in input_files:
        if not f.exists():
            print(f"Error: File not found: {f}")
            sys.exit(1)

    print(f"\nReconciling {len(input_files)} extraction document(s)...")
    for f in input_files:
        print(f"  • {f}")

    # Run reconciliation
    try:
        merged = reconcile_from_files(input_files, model=args.model)
    except Exception as e:
        print(f"\nError during reconciliation: {e}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        product_id = merged.get("product_id", "unknown")
        output_path = output_dir / f"{product_id}_merged.json"

    # Save
    save_merged(merged, output_path)

    # Also print the merged JSON to stdout
    print("\nMerged product record:")
    print(json.dumps(merged, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
