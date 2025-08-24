import json
from typing import Dict, Any, Optional, Tuple

def parse_action_json(s: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        obj = json.loads(s)
        if not isinstance(obj, dict):
            return None, "action must be a JSON object"
        if "tool" not in obj or "arguments" not in obj:
            return None, "action requires 'tool' and 'arguments'"
        if not isinstance(obj["arguments"], dict):
            return None, "'arguments' must be an object"
        if not isinstance(obj["tool"], str):
            return None, "'tool' must be a string"
        return obj, None
    except Exception as e:
        return None, f"invalid JSON: {e}"

def is_well_formed(obj: Dict[str, Any]) -> Optional[str]:
    # Minimal structural checks (BFCL-style vibe)
    tool = obj.get("tool")
    args = obj.get("arguments")
    if not tool or not isinstance(tool, str):
        return "invalid tool name"
    if not isinstance(args, dict):
        return "arguments must be object"
    return None
