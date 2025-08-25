import json
from typing import Dict, Any, List, Tuple
from eval.ast_checks import parse_action_json, is_well_formed
from eval.metrics import outcome_em, numeric_close
from tools.registry import to_canonical_args, map_tool_to_capability
from simulators.price import PRICE_SIMULATOR

# Plug more simulators here
SIMULATORS = {
    "price_lookup": PRICE_SIMULATOR.call
}

def run_step_action(action_json: str) -> Dict[str, Any]:
    parsed, err = parse_action_json(action_json)
    step_log = {"ast_valid": 0, "err": None, "capability": None, "observation": None}
    if err:
        step_log["err"] = err
        return step_log
    form_err = is_well_formed(parsed)
    if form_err:
        step_log["err"] = form_err
        return step_log
    step_log["ast_valid"] = 1

    tool = parsed["tool"]
    canon, conv_err = to_canonical_args(tool, parsed["arguments"])
    if conv_err:
        step_log["err"] = f"schema/constraints: {conv_err}"
        return step_log

    cap = map_tool_to_capability(tool)
    step_log["capability"] = cap.name if cap else None

    # Execute via simulator
    obs = SIMULATORS[cap.name](canon) if cap and cap.name in SIMULATORS else {"error": "no simulator"}
    step_log["observation"] = obs
    return step_log

def score_final(final_text: str, gold: Dict[str, Any]) -> float:
    # Example: if gold is numeric price, compare close price EM (or tolerance)
    if "numeric" in gold:
        return numeric_close(final_text, gold["numeric"], tol=gold.get("tol", 0.01))
    if "text" in gold:
        return outcome_em(final_text, gold["text"])
    return 0.0

def replay_dialogue(dialogue: List[Dict[str, Any]], gold_final: Dict[str, Any], max_steps: int = 8) -> Dict[str, Any]:
    """
    dialogue: list of events;  inject the model's outputs when running live.
    Here we assume 'action' entries contain JSON strings; 'final' is the model's final answer string.
    """
    track2 = {"steps": [], "invalid_calls": 0, "constraint_violations": 0}
    track1 = {"success": 0.0}

    steps = 0
    for msg in dialogue:
        if steps >= max_steps:
            break
        if msg.get("type") == "action":
            log = run_step_action(msg["content"])
            track2["steps"].append(log)
            if log["ast_valid"] == 0:
                track2["invalid_calls"] += 1
                if log["err"] and "start must differ" in log["err"]:
                    track2["constraint_violations"] += 1
            steps += 1
        elif msg.get("type") == "final":
            track1["success"] = score_final(msg["content"], gold_final)
            break

    return {
        "track1": track1,
        "track2": {
            "ast_valid_rate": (sum(s["ast_valid"] for s in track2["steps"]) / max(1, len(track2["steps"]))),
            "invalid_call_rate": (track2["invalid_calls"] / max(1, len(track2["steps"]))),
            "constraint_violations": track2["constraint_violations"],
            "num_steps": len(track2["steps"])
        }
    }

if __name__ == "__main__":
    import argparse, pathlib
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="path to canonical JSONL")
    ap.add_argument("--out", required=True, help="metrics json path")
    ap.add_argument("--max_steps", type=int, default=8)
    args = ap.parse_args()

    results = []
    with open(args.data, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            gold = ex.get("gold_final", {"text": ""})
            # Here we assume ex["dialogue"] already contains model outputs.
            # For live eval, call your model to fill actions/final per turn.
            metrics = replay_dialogue(ex["dialogue"], gold, max_steps=args.max_steps)
            metrics["id"] = ex.get("id")
            metrics["source"] = ex.get("meta", {}).get("source")
            results.append(metrics)

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {args.out}")
