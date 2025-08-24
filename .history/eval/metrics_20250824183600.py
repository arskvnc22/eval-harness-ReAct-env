from typing import Dict, Any

def normalize_text(x: str) -> str:
    return " ".join((x or "").strip().lower().split())

def outcome_em(pred: str, gold: str) -> float:
    return 1.0 if normalize_text(pred) == normalize_text(gold) else 0.0

def numeric_close(pred: float, gold: float, tol: float = 1e-6) -> float:
    try:
        return 1.0 if abs(float(pred) - float(gold)) <= tol else 0.0
    except Exception:
        return 0.0
