"""
Shared utility functions used across agents.
"""

import json
from bson import ObjectId


def clean_objectids(obj):
    """Ensure object is JSON serializable by converting ObjectIds to strings."""
    return json.loads(json.dumps(obj, default=str))


def safe_get(data: dict, *keys, default=None):
    """
    Safely navigate nested dicts.
    Usage: safe_get(state, "product_understanding", "product_name", default="Unknown")
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current
