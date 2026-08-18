"""
Conflict Resolution Module
Resolves conflicting field values using source priority and Claude API.
"""

import json
import os
import re
from anthropic import Anthropic


# Source priority table: lower number = higher priority
SOURCE_PRIORITY = {
    "datasheet": 1,        # Datasheets are the gold standard
    "manufacturer": 2,     # Manufacturer website is authoritative
    "distributor": 3,      # Distributor listings are secondary
    "review": 4,           # Blog/review sites are lowest priority
}


def classify_source(source_doc: str) -> str:
    """Classify a source document into a priority tier based on filename patterns."""
    doc_lower = source_doc.lower()
    if "datasheet" in doc_lower or doc_lower.endswith(".pdf"):
        return "datasheet"
    elif "manufacturer" in doc_lower or "mfr" in doc_lower:
        return "manufacturer"
    elif "distributor" in doc_lower or "mouser" in doc_lower or "digikey" in doc_lower or "listing" in doc_lower:
        return "distributor"
    elif "review" in doc_lower or "blog" in doc_lower or "forum" in doc_lower:
        return "review"
    else:
        return "distributor"  # default to mid-tier


def get_priority(source_doc: str) -> int:
    """Get numeric priority for a source document."""
    tier = classify_source(source_doc)
    return SOURCE_PRIORITY.get(tier, 3)


def resolve_conflicts_via_claude(
    field_name: str,
    candidates: list[dict],
    client: Anthropic | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """
    Use Claude API to pick the correct value from conflicting candidates.
    
    Args:
        field_name: Name of the field with conflicts
        candidates: List of {value, source_doc, confidence} dicts
        client: Anthropic client (created if None)
        model: Claude model to use
        
    Returns:
        {chosen_value: str, reasoning: str}
    """
    if client is None:
        client = Anthropic()

    candidates_text = json.dumps(candidates, indent=2)

    prompt = f"""You are resolving a conflict for a product data field in an electronics component database.

Field name: "{field_name}"
Here are the conflicting values from different sources (with their priority tier):

{candidates_text}

Source priority (highest to lowest):
1. Datasheet (authoritative PDF from component manufacturer)
2. Manufacturer site (official product page)
3. Distributor listing (Mouser, DigiKey, etc.)
4. Review/blog (third-party opinions)

TASK:
1. Pick the single most correct value.
2. Give a one-sentence explanation of WHY you chose it, referencing the priority table and any domain knowledge.
3. Be concise. Output ONLY valid JSON in this exact format:
{{"chosen_value": <the winning value>, "reasoning": "<one sentence explanation>"}}

Consider:
- Datasheet values are the gold standard for electrical specs.
- Distributor sites sometimes list ratings incorrectly or rounded.
- Blog/review values are least reliable.
- For ranges, prefer the specific value from the higher-priority source.
"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        result_text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{[^}]+\}", result_text)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[conflict_resolver] Claude API call failed: {e}")

    # Fallback: pick by priority (highest priority wins)
    best = min(candidates, key=lambda c: get_priority(c["source_doc"]))
    return {
        "chosen_value": best["value"],
        "reasoning": f"Fallback: selected value from highest-priority source '{best['source_doc']}' (priority {get_priority(best['source_doc'])}).",
    }


def resolve_field_conflict(
    field_name: str,
    all_values: list[dict],
    client: Anthropic | None = None,
) -> dict:
    """
    Given all extracted values for a field, resolve conflicts and return the best value.
    
    If all values agree, returns that value directly.
    If there are conflicts, calls Claude API to pick the best one.
    
    Returns:
        {
            "value": <resolved value>,
            "source": "extracted",
            "source_doc": <winning source>,
            "source_location": <location in winning source>,
            "confidence": <confidence from winning source>,
            "reasoning": <resolution reasoning>,
            "conflicts": [{value, source_doc, resolved: true/false}, ...]
        }
    """
    # Deduplicate by value
    unique_values = {}
    for v in all_values:
        val_key = str(v["value"])
        if val_key not in unique_values:
            unique_values[val_key] = v

    unique_list = list(unique_values.values())

    if len(unique_list) == 1:
        # No conflict
        winner = unique_list[0]
        return {
            "value": winner["value"],
            "source": "extracted",
            "source_doc": winner["source_doc"],
            "source_location": winner["source_location"],
            "confidence": winner["confidence"],
            "reasoning": winner["reasoning"],
            "conflicts": [],
        }

    # Multiple distinct values — resolve conflict
    candidates = [
        {"value": v["value"], "source_doc": v["source_doc"], "confidence": v["confidence"]}
        for v in unique_list
    ]

    resolution = resolve_conflicts_via_claude(field_name, candidates, client)

    chosen_value = str(resolution["chosen_value"])
    chosen_source = None
    for v in unique_list:
        if str(v["value"]) == chosen_value:
            chosen_source = v
            break

    # If exact match failed, fall back to highest-priority source
    if chosen_source is None:
        chosen_source = min(unique_list, key=lambda c: get_priority(c["source_doc"]))

    # Build conflicts array
    conflicts = []
    for v in all_values:
        if str(v["value"]) != chosen_value:
            conflicts.append({
                "value": v["value"],
                "source_doc": v["source_doc"],
                "resolved": True,
            })

    return {
        "value": chosen_source["value"],
        "source": "extracted",
        "source_doc": chosen_source["source_doc"],
        "source_location": chosen_source["source_location"],
        "confidence": chosen_source["confidence"],
        "reasoning": resolution["reasoning"],
        "conflicts": conflicts,
    }
