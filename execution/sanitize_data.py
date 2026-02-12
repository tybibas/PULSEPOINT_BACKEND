
import re

def sanitize_data(data):
    """
    Applies strict data normalization rules recursively.
    """
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k] = sanitize_value(k, v)
        return new_data
    elif isinstance(data, list):
        return [sanitize_value(None, i) for i in data]
    else:
        return sanitize_value(None, data)

def sanitize_value(key, value):
    # 3. Handle Nulls
    if value is None:
        # Fallback for strict strictness
        return "N/A (Sector Avg)"

    # Context-Aware Rules based on Key
    if key:
        # 4. Sentiment Scaling
        if "sentiment" in key.lower() or "score" in key.lower():
            if isinstance(value, (int, float)):
                # Clamp to -1.0 to +1.0
                return max(-1.0, min(1.0, float(value)))
        
        # 1. Truncate Narrative (Insight/Content)
        if key.lower() in ["insight", "content", "description", "summary"]:
            if isinstance(value, str):
                words = value.split()
                if len(words) > 45:
                    return " ".join(words[:45]) + "..."
    
    # 2. Format Numbers (Global Rule for Floats)
    if isinstance(value, float):
        return round(value, 2)
        
    # Recursive for nested structures if value is list/dict (handled by main calls usually, but valid here too)
    if isinstance(value, (dict, list)):
        return sanitize_data(value)

    return value
