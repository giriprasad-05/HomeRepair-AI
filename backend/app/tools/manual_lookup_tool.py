from typing import Dict, Any, List

# Static knowledge base of common error codes
ERROR_CODE_DB = [
    {
        "brand": "samsung",
        "category": "refrigerator",
        "error_code": "e1",
        "possible_meaning": "Defrost sensor error",
        "recommended_checks": [
            "Check defrost sensor wiring",
            "Verify sensor resistance",
            "Inspect control board connections"
        ]
    },
    {
        "brand": "samsung",
        "category": "refrigerator",
        "error_code": "e5",
        "possible_meaning": "Ice maker sensor error",
        "recommended_checks": [
            "Check ice maker sensor",
            "Ensure ice maker is seated properly"
        ]
    },
    {
        "brand": "lg",
        "category": "washing_machine",
        "error_code": "ue",
        "possible_meaning": "Unbalanced load error",
        "recommended_checks": [
            "Redistribute the laundry in the drum",
            "Ensure the washing machine is level",
            "Check suspension springs and shock absorbers"
        ]
    },
    {
        "brand": "whirlpool",
        "category": "dishwasher",
        "error_code": "f7e1",
        "possible_meaning": "Heating element fault",
        "recommended_checks": [
            "Check heating element continuity",
            "Inspect thermostat",
            "Look for burned wires near the heater"
        ]
    }
]

def lookup_error_code(brand: str, category: str, error_code: str) -> Dict[str, Any]:
    """
    Looks up an error code in the local static knowledge base.
    """
    b = brand.lower() if brand else ""
    c = category.lower() if category else ""
    e = error_code.lower() if error_code else ""
    
    matches = []
    for entry in ERROR_CODE_DB:
        # We try to find a match. If brand or category are provided, they must match.
        if b and entry["brand"] != b:
            continue
        if c and entry["category"] != c:
            continue
        if e and entry["error_code"] != e:
            continue
            
        matches.append(entry)
        
    if not matches:
        return {
            "found": False,
            "message": f"No exact match found for {brand} {category} error code '{error_code}'.",
            "query": {"brand": brand, "category": category, "error_code": error_code}
        }
        
    return {
        "found": True,
        "matches": matches,
        "query": {"brand": brand, "category": category, "error_code": error_code}
    }
