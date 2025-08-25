from typing import Dict, Any, Optional, Tuple
from .schema import Capability, ToolSpec

# ---------- Canonical capability: price_lookup ----------
def _map_yahoo(args: Dict[str, Any]) -> Dict[str, Any]:
    # yahoo: {symbol, start, end} -> canonical: {ticker, date_range:{start,end}}
    return {
        "ticker": args.get("symbol"),
        "date_range": {"start": args.get("start"), "end": args.get("end")}
    }

def _map_alpha(args: Dict[str, Any]) -> Dict[str, Any]:
    # alpha: {ticker, from, to} -> canonical
    return {
        "ticker": args.get("ticker"),
        "date_range": {"start": args.get("from"), "end": args.get("to")}
    }

def _constraints_price(canon: Dict[str, Any]) -> Optional[str]:
    # Additional constraints specific to price lookup
    dr = canon.get("date_range", {})
    if not canon.get("ticker"):
        return "ticker is required"
    if not dr.get("start") or not dr.get("end"):
        return "date_range.start and end are required"
    if dr.get("start") == dr.get("end"):
        return "date_range.start must differ from date_range.end"
    return None

PRICE_LOOKUP = Capability(
    name="price_lookup",
    parameters={
        "type": "object",
        "required": ["ticker", "date_range"],
        "properties": {
            "ticker": {"type": "string"},
            "date_range": {
                "type": "object",
                "required": ["start", "end"],
                "properties": {"start": {"type": "string"}, "end": {"type": "string"}}
            }
        }
    },
    implementations={
        # tool alias -> (arg_mapping_fn, constraints_fn)
        "get_price_yahoo": (_map_yahoo, _constraints_price),
        "get_price_alpha": (_map_alpha, _constraints_price),
        # you can add "mirror_price_api": (...)
    }
)

# ---------- Registry ----------
CAPABILITIES = {
    "price_lookup": PRICE_LOOKUP
}

# Tool alias -> capability name
TOOL_TO_CAPABILITY = {
    "get_price_yahoo": "price_lookup",
    "get_price_alpha": "price_lookup",
}

def map_tool_to_capability(tool_name: str) -> Optional[Capability]:
    cap_name = TOOL_TO_CAPABILITY.get(tool_name)
    return CAPABILITIES.get(cap_name) if cap_name else None

def to_canonical_args(tool_name: str, raw_args: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    cap = map_tool_to_capability(tool_name)
    if not cap:
        return None, f"unknown tool '{tool_name}'"
    mapper, constraints = cap.implementations[tool_name]
    canon = mapper(raw_args or {})
    # base schema
    err = cap.validate_canonical_args(canon)
    if err:
        return None, err
    # capability constraints
    if constraints:
        err2 = constraints(canon)
        if err2:
            return None, err2
    return canon, None

def schema_from_inputs(tools_declared: Dict[str, ToolSpec]) -> Dict[str, ToolSpec]:
    # (Optional) build a spec registry per sample from provided tools
    return tools_declared
