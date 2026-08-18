"""
Inference Module
Derives missing field values from known fields using domain rules.
All inferred fields are tagged with source="inferred".
"""

from typing import Any


def infer_fields(merged: dict) -> dict:
    """
    Given a partially merged product record, attempt to infer missing fields.
    
    Inference rules for MOSFET / semiconductor components:
    1. If VDS (voltage_rating_vds) is known and current_rating_id is known,
       estimate power_dissipation as VDS * ID if PD is missing.
    2. If package_type is known, infer mounting_type (through-hole vs SMD).
    3. If gate_threshold_voltage range is known, infer typical_gate_voltage (midpoint).
    
    Returns the same merged dict with inferred fields added.
    """
    fields = merged.get("fields", {})

    inferred = []

    # --- Rule 1: Infer mounting_type from package_type ---
    if "package_type" in fields and "mounting_type" not in fields:
        pkg_val = str(fields["package_type"]["value"]).upper()
        # Through-hole packages
        th_packages = {"TO-220", "TO-220AB", "TO-220AC", "TO-126", "TO-92", "TO-252", "DPAK", "D2PAK", "SOT-223"}
        # SMD packages
        smd_packages = {"SOT-23", "SOT-323", "SOT-223", "SOIC", "MSOP", "TSSOP", "QFN", "BGA", "DFN"}
        
        if any(p in pkg_val for p in ["TO-220", "TO-126", "TO-92"]):
            mounting = "Through-Hole"
        elif any(p in pkg_val for p in ["SOT-23", "SOT-323", "SOIC", "MSOP", "QFN", "BGA", "DFN"]):
            mounting = "Surface Mount (SMD)"
        else:
            mounting = "Through-Hole"  # Default for TO- packages

        fields["mounting_type"] = {
            "value": mounting,
            "source": "inferred",
            "source_doc": "reconciliation_inference",
            "source_location": "inference rule: package_type -> mounting_type",
            "confidence": 85,
            "reasoning": f"Inferred from package_type '{fields['package_type']['value']}': {mounting}.",
            "conflicts": [],
        }
        inferred.append("mounting_type")

    # --- Rule 2: Infer max_power_dissipation from VDS and ID ---
    # Only if power_dissipation is missing and both voltage + current are known
    if "power_dissipation" not in fields:
        vds_field = fields.get("voltage_rating_vds")
        id_field = fields.get("current_rating_id")
        if vds_field and id_field:
            try:
                vds_val = float(str(vds_field["value"]).replace("V", "").strip())
                id_val = float(str(id_field["value"]).replace("A", "").strip())
                # Theoretical max P = VDS * ID (not the same as rated PD, but a valid estimate)
                # In practice, PD is limited by thermal resistance, so this is an upper bound estimate
                estimated_pd = round(vds_val * id_val, 1)
                # This is a rough estimate; actual PD for MOSFETs is lower due to thermal limits
                # Apply a correction factor of ~0.85 for TO-220 thermal limitations
                corrected_pd = round(estimated_pd * 0.85, 1)
                
                pkg = fields.get("package_type", {}).get("value", "unknown")
                fields["power_dissipation"] = {
                    "value": f"{corrected_pd}W",
                    "source": "inferred",
                    "source_doc": "reconciliation_inference",
                    "source_location": "inference rule: VDS * ID * thermal_factor",
                    "confidence": 65,
                    "reasoning": f"Estimated power dissipation from VDS ({vds_field['value']}) × ID ({id_field['value']}) × 0.85 thermal correction factor for {pkg} package.",
                    "conflicts": [],
                }
                inferred.append("power_dissipation")
            except (ValueError, TypeError):
                pass  # Can't parse numeric values, skip inference

    # --- Rule 3: Infer typical_gate_voltage from gate_threshold_voltage ---
    if "typical_gate_voltage" not in fields:
        vth_field = fields.get("gate_threshold_voltage")
        if vth_field:
            vth_val = str(vth_field["value"])
            # Handle range like "2V-4V"
            range_match = None
            if "-" in vth_val and "V" in vth_val:
                parts = vth_val.replace("V", "").split("-")
                try:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    range_match = (low, high)
                except (ValueError, IndexError):
                    pass

            if range_match:
                low, high = range_match
                typical_gate = round((low + high) / 2 + 6.0, 1)  # Typical VGS for full enhancement
                fields["typical_gate_voltage"] = {
                    "value": f"{typical_gate}V",
                    "source": "inferred",
                    "source_doc": "reconciliation_inference",
                    "source_location": "inference rule: gate_threshold -> typical_gate_voltage",
                    "confidence": 60,
                    "reasoning": f"Estimated typical gate drive voltage (VGS) from threshold range {vth_val}: midpoint threshold + ~6V headroom for full enhancement.",
                    "conflicts": [],
                }
                inferred.append("typical_gate_voltage")
            else:
                # Single value
                try:
                    vth_num = float(vth_val.replace("V", "").strip())
                    typical_gate = round(vth_num + 6.0, 1)
                    fields["typical_gate_voltage"] = {
                        "value": f"{typical_gate}V",
                        "source": "inferred",
                        "source_doc": "reconciliation_inference",
                        "source_location": "inference rule: gate_threshold -> typical_gate_voltage",
                        "confidence": 65,
                        "reasoning": f"Estimated typical gate drive voltage from threshold ({vth_val}) + 6V headroom for full enhancement.",
                        "conflicts": [],
                    }
                    inferred.append("typical_gate_voltage")
                except (ValueError, TypeError):
                    pass

    # --- Rule 4: Infer min_operating_temp if max is known ---
    if "min_operating_temp" not in fields and "max_operating_temp" in fields:
        max_temp_field = fields["max_operating_temp"]
        try:
            max_temp = float(str(max_temp_field["value"]).replace("°C", "").strip())
            if max_temp >= 150:  # Semiconductor
                fields["min_operating_temp"] = {
                    "value": "-55°C",
                    "source": "inferred",
                    "source_doc": "reconciliation_inference",
                    "source_location": "inference rule: standard semiconductor temp range",
                    "confidence": 80,
                    "reasoning": f"Standard industrial temperature range minimum (-55°C) inferred for semiconductor with max operating temp of {max_temp_field['value']}.",
                    "conflicts": [],
                }
                inferred.append("min_operating_temp")
        except (ValueError, TypeError):
            pass

    merged["fields"] = fields
    return merged, inferred
