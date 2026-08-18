# Reconciliation Module

**Owner:** Steve  
**Purpose:** Merge multiple per-document extraction JSONs into one authoritative product record, resolving conflicts and inferring missing fields.

## Overview

This module takes multiple product extraction JSONs (from different sources like datasheets, manufacturer sites, distributor listings) for the **same product** and produces a single merged record following `/shared/schema.json`.

### What it does:
1. **Collects** field values from all input documents
2. **Resolves conflicts** using Claude API with a source-priority table (datasheet > manufacturer > distributor > review)
3. **Infers missing fields** (e.g., mounting_type from package_type, power dissipation from voltage × current)
4. **Outputs** one merged JSON per product following the shared schema

## Directory Structure

```
/reconciliation/
├── README.md              ← this file
├── __init__.py            ← package init
├── reconciler.py          ← main reconcile() function
├── conflict_resolver.py   ← conflict resolution logic + Claude API
├── inference.py           ← field inference rules
├── run.py                 ← CLI entry point
├── mock_inputs/           ← mock extraction data (for standalone testing)
│   ├── doc1_datasheet.json
│   ├── doc2_manufacturer_site.json
│   ├── doc3_distributor_listing.json
│   └── doc4_review_site.json
└── output/                ← merged output (created on run)
    └── IRFZ44N_merged.json
```

## Prerequisites

- Python 3.10+
- Anthropic Python SDK

```bash
pip install anthropic
```

## Standalone Testing

### Step 1: Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Step 2: Run reconciliation on mock inputs

```bash
# From the project root:
cd reconciliation
python -m reconciliation.run

# Or specify files explicitly:
python -m reconciliation.run mock_inputs/doc1_datasheet.json mock_inputs/doc2_manufacturer_site.json mock_inputs/doc3_distributor_listing.json mock_inputs/doc4_review_site.json
```

### Step 3: Check the output

The merged record will be saved to `reconciliation/output/IRFZ44N_merged.json`.

### Run without API key (fallback mode)

If no `ANTHROPIC_API_KEY` is set, the module falls back to priority-based resolution (highest-priority source wins without AI reasoning):

```bash
unset ANTHROPIC_API_KEY
python -m reconciliation.run
```

## API Usage

```python
from reconciliation import reconcile, reconcile_from_files

# Option 1: From dicts (e.g., loaded in memory)
docs = [doc1, doc2, doc3]  # extraction JSON dicts
merged = reconcile(docs)

# Option 2: From files
merged = reconcile_from_files([
    "mock_inputs/doc1_datasheet.json",
    "mock_inputs/doc2_manufacturer_site.json",
])

# Save result
from reconciliation import save_merged
save_merged(merged, "output/my_product.json")
```

## Source Priority Table

| Priority | Source Type     | Pattern in filename            |
|----------|----------------|-------------------------------|
| 1 (best) | Datasheet      | `datasheet`, `*.pdf`          |
| 2        | Manufacturer   | `manufacturer`, `mfr`         |
| 3        | Distributor    | `distributor`, `mouser`, `digikey`, `listing` |
| 4 (worst)| Review/Blog    | `review`, `blog`, `forum`     |

## Inference Rules

| Rule | Condition | Inferred Field | Logic |
|------|-----------|---------------|-------|
| 1 | package_type known, mounting_type missing | `mounting_type` | TO-220/TO-92 → Through-Hole; SOT-23/QFN → SMD |
| 2 | VDS + ID known, power_dissipation missing | `power_dissipation` | P = VDS × ID × 0.85 (thermal correction) |
| 3 | gate_threshold_voltage known, typical_gate_voltage missing | `typical_gate_voltage` | VGS(th) midpoint + 6V headroom |
| 4 | max_operating_temp ≥ 150°C, min_operating_temp missing | `min_operating_temp` | -55°C (standard semiconductor range) |

## Mock Input Data

The mock inputs simulate extraction from 4 different sources for an **IRFZ44N N-Channel MOSFET** with deliberate conflicts:

| Field | Datasheet | Manufacturer | Distributor | Blog |
|-------|-----------|-------------|-------------|------|
| voltage_rating_vds | 55V | 55V | **60V** | 55V |
| current_rating_id | 49A | 47A | **50A** | 48A |
| power_dissipation | 94W | — | **80W** | — |
| package_type | TO-220 | TO-220AB | TO-220 | TO220 |
| gate_threshold_voltage | 4V | 2V-4V | — | 3.5V |

## Schema Compliance

All output strictly follows `/shared/schema.json`. Each field includes:
- `value`: the resolved or inferred value
- `source`: "extracted" or "inferred"
- `source_doc`: origin document filename
- `source_location`: where in the document the value was found
- `confidence`: 0-100 confidence score
- `reasoning`: explanation of value selection
- `conflicts`: array of rejected/conflicting values with resolution status
