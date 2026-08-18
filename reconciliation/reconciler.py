"""
Reconciliation Module
Merges multiple per-document extraction JSONs into one authoritative product record.
"""

import json
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from .conflict_resolver import resolve_field_conflict
from .inference import infer_fields


def reconcile(
    extraction_jsons: list[dict],
    client: Anthropic | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """
    Reconcile multiple extraction JSONs (from different documents) into one merged record.

    Args:
        extraction_jsons: List of product extraction dicts, each following /shared/schema.json
        client: Anthropic client instance (created automatically if None)
        model: Claude model for conflict resolution
        
    Returns:
        Merged product record following /shared/schema.json exactly.
    """
    if not extraction_jsons:
        raise ValueError("At least one extraction JSON is required.")

    if len(extraction_jsons) == 1:
        # Single source, no conflicts possible — return as-is with structure validated
        record = extraction_jsons[0].copy()
        record["fields"] = record.get("fields", {})
        return record

    # Verify all documents are for the same product
    product_ids = [doc.get("product_id") for doc in extraction_jsons]
    if len(set(product_ids)) > 1:
        raise ValueError(f"Cannot reconcile different products: {product_ids}")
    
    product_id = product_ids[0]

    # Collect all field names across all documents
    all_field_names: set[str] = set()
    for doc in extraction_jsons:
        all_field_names.update(doc.get("fields", {}).keys())

    # Group field values by source document
    field_sources: dict[str, list[dict]] = {}
    for field_name in all_field_names:
        field_sources[field_name] = []
        for doc in extraction_jsons:
            fields = doc.get("fields", {})
            if field_name in fields:
                field_sources[field_name].append(fields[field_name])

    # Resolve each field
    merged_fields = {}
    resolution_log = []

    for field_name in sorted(field_sources.keys()):
        sources = field_sources[field_name]

        if len(sources) == 1:
            # Only one source has this field — use it directly
            entry = sources[0]
            merged_fields[field_name] = {
                "value": entry["value"],
                "source": "extracted",
                "source_doc": entry["source_doc"],
                "source_location": entry.get("source_location", ""),
                "confidence": entry.get("confidence", 0),
                "reasoning": entry.get("reasoning", ""),
                "conflicts": [],
            }
        else:
            # Multiple sources — check for conflicts
            unique_values = set(str(s["value"]) for s in sources)
            if len(unique_values) == 1:
                # All sources agree
                entry = sources[0]
                merged_fields[field_name] = {
                    "value": entry["value"],
                    "source": "extracted",
                    "source_doc": entry["source_doc"],
                    "source_location": entry.get("source_location", ""),
                    "confidence": entry.get("confidence", 0),
                    "reasoning": entry.get("reasoning", ""),
                    "conflicts": [],
                }
            else:
                # Conflict — resolve
                resolved = resolve_field_conflict(field_name, sources, client)
                merged_fields[field_name] = resolved
                resolution_log.append({
                    "field": field_name,
                    "conflicting_values": unique_values,
                    "chosen": str(resolved["value"]),
                })

    merged = {
        "product_id": product_id,
        "fields": merged_fields,
    }

    # Run inference to derive missing fields
    merged, inferred_fields = infer_fields(merged)

    # Print resolution summary
    print(f"\n{'='*60}")
    print(f"Reconciliation Summary for {product_id}")
    print(f"{'='*60}")
    print(f"Documents merged: {len(extraction_jsons)}")
    print(f"Total fields: {len(merged['fields'])}")
    print(f"Fields with conflicts resolved: {len(resolution_log)}")
    print(f"Fields inferred: {len(inferred_fields)}")
    if resolution_log:
        print(f"\nConflict resolutions:")
        for r in resolution_log:
            print(f"  • {r['field']}: chose '{r['chosen']}' from values {r['conflicting_values']}")
    if inferred_fields:
        print(f"\nInferred fields: {', '.join(inferred_fields)}")
    print(f"{'='*60}\n")

    return merged


def reconcile_from_files(
    file_paths: list[str | Path],
    client: Anthropic | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """
    Convenience function: load extraction JSONs from file paths and reconcile.
    
    Args:
        file_paths: List of paths to extraction JSON files
        client: Anthropic client instance (created automatically if None)
        model: Claude model for conflict resolution
        
    Returns:
        Merged product record.
    """
    extractions = []
    for fp in file_paths:
        with open(fp, "r", encoding="utf-8") as f:
            extractions.append(json.load(f))
    return reconcile(extractions, client, model)


def save_merged(merged: dict, output_path: str | Path) -> None:
    """Save merged product record to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"Merged record saved to: {output_path}")


if __name__ == "__main__":
    # Standalone execution: reconcile all mock inputs
    import sys
    from pathlib import Path

    mock_dir = Path(__file__).parent / "mock_inputs"
    output_dir = Path(__file__).parent / "output"

    if not mock_dir.exists():
        print(f"Mock inputs directory not found: {mock_dir}")
        sys.exit(1)

    output_dir.mkdir(exist_ok=True)

    # Gather all JSON files from mock_inputs
    json_files = sorted(mock_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {mock_dir}")
        sys.exit(1)

    print(f"Loading {len(json_files)} extraction files:")
    for f in json_files:
        print(f"  - {f.name}")

    merged = reconcile_from_files(json_files)

    # Save output
    product_id = merged.get("product_id", "unknown")
    output_path = output_dir / f"{product_id}_merged.json"
    save_merged(merged, output_path)
