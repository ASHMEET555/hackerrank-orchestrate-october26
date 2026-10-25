"""Evaluation harness for HackerRank Orchestrate: Ghost Data Still Exists.

Metrics Computed:
1. Case-Level Deletion-Status Accuracy (status_accuracy):
   Fraction of cases where prediction deletion_status matches ground truth deletion_status exactly.
   Formula: count(pred_status == truth_status) / total_cases.

2. Row-Level Accuracy (row_accuracy):
   Fraction of cases where the entire row matches truth completely.
   A row is counted as matched if and only if case_id, deletion_status, AND steps_json
   (all steps, attributes, and order) match ground truth exactly.
   Formula: count(row_match) / total_cases.

3. Field-Level Accuracy (field_accuracy):
   Accuracy across all step attributes across all steps in the evaluation set.
   For each corresponding step, compares: step_no, phase, system_id, resource_id,
   operation, state, and evidence_id (7 fields per step).
   Formula: matched_step_fields / total_expected_and_predicted_step_fields.

4. Sequence Accuracy (sequence_accuracy):
   Fraction of cases where the sequence of operations (phase, operation, system_id, resource_id)
   matches ground truth exactly.
   Formula: count(pred_step_seq == truth_step_seq) / total_cases.
"""

import argparse
import csv
import difflib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EvalMetrics:
    total_cases: int
    matched_cases: int
    status_accuracy: float
    row_accuracy: float
    field_accuracy: float
    sequence_accuracy: float
    timestamp: str


def normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures consistent dictionary key ordering and types for comparison."""
    return {
        "step_no": step.get("step_no"),
        "phase": step.get("phase"),
        "system_id": step.get("system_id"),
        "resource_id": step.get("resource_id"),
        "operation": step.get("operation"),
        "state": step.get("state"),
        "evidence_id": step.get("evidence_id"),
    }


def compare_outputs(
    pred_path: Path,
    truth_path: Path,
    verbose: bool = False,
    history_path: Optional[Path] = None,
) -> Tuple[EvalMetrics, List[str]]:
    """Evaluates prediction CSV against ground truth CSV."""
    with open(truth_path, mode="r", encoding="utf-8") as f:
        truth_rows = {row["case_id"]: row for row in csv.DictReader(f)}

    with open(pred_path, mode="r", encoding="utf-8") as f:
        pred_rows = {row["case_id"]: row for row in csv.DictReader(f)}

    diffs: List[str] = []
    total_cases = len(truth_rows)
    status_matches = 0
    row_matches = 0
    seq_matches = 0

    total_fields = 0
    matched_fields = 0

    for cid in sorted(truth_rows.keys()):
        t_row = truth_rows[cid]
        p_row = pred_rows.get(cid)

        if not p_row:
            diffs.append(f"Case {cid}: MISSING in predictions")
            continue

        # Status match
        t_status = t_row["deletion_status"]
        p_status = p_row["deletion_status"]
        if t_status == p_status:
            status_matches += 1

        # Parse steps
        try:
            t_steps = [normalize_step(s) for s in json.loads(t_row["steps_json"])]
        except Exception:
            t_steps = []
        try:
            p_steps = [normalize_step(s) for s in json.loads(p_row["steps_json"])]
        except Exception:
            p_steps = []

        # Sequence match (matching tuple of (phase, operation, system_id, resource_id))
        t_seq = [(s["phase"], s["operation"], s["system_id"], s["resource_id"]) for s in t_steps]
        p_seq = [(s["phase"], s["operation"], s["system_id"], s["resource_id"]) for s in p_steps]
        is_seq_match = (t_seq == p_seq)
        if is_seq_match:
            seq_matches += 1

        # Field-level accuracy
        max_len = max(len(t_steps), len(p_steps))
        for i in range(max_len):
            if i < len(t_steps) and i < len(p_steps):
                ts = t_steps[i]
                ps = p_steps[i]
                for k in ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                    total_fields += 1
                    if ts[k] == ps[k]:
                        matched_fields += 1
            else:
                total_fields += 7

        # Exact row match (case_id, deletion_status, steps_json)
        is_row_match = (t_status == p_status and t_steps == p_steps)
        if is_row_match:
            row_matches += 1
        else:
            t_str = json.dumps({"deletion_status": t_status, "steps": t_steps}, indent=2).splitlines()
            p_str = json.dumps({"deletion_status": p_status, "steps": p_steps}, indent=2).splitlines()
            u_diff = list(difflib.unified_diff(t_str, p_str, fromfile=f"truth/{cid}", tofile=f"pred/{cid}", lineterm=""))
            diffs.append("\n".join(u_diff))

    field_acc = (matched_fields / total_fields) if total_fields > 0 else 1.0
    metrics = EvalMetrics(
        total_cases=total_cases,
        matched_cases=row_matches,
        status_accuracy=(status_matches / total_cases) if total_cases > 0 else 0.0,
        row_accuracy=(row_matches / total_cases) if total_cases > 0 else 0.0,
        field_accuracy=field_acc,
        sequence_accuracy=(seq_matches / total_cases) if total_cases > 0 else 0.0,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    if history_path:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics)) + "\n")

    return metrics, diffs


def main():
    parser = argparse.ArgumentParser(description="Evaluate deletion audit output against truth")
    parser.add_argument("--pred", type=str, default="output.csv", help="Prediction CSV path")
    parser.add_argument("--truth", type=str, default="dataset/sample_output.csv", help="Truth CSV path")
    parser.add_argument("--history", type=str, default="code/.cache/eval_history.jsonl", help="History log path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print diffs")
    args = parser.parse_args()

    metrics, diffs = compare_outputs(
        pred_path=Path(args.pred),
        truth_path=Path(args.truth),
        verbose=args.verbose,
        history_path=Path(args.history),
    )

    print(f"Total Cases:       {metrics.total_cases}")
    print(f"Status Accuracy:   {metrics.status_accuracy * 100:.2f}%")
    print(f"Row Accuracy:      {metrics.row_accuracy * 100:.2f}%")
    print(f"Field Accuracy:    {metrics.field_accuracy * 100:.2f}%")
    print(f"Sequence Accuracy: {metrics.sequence_accuracy * 100:.2f}%")

    if args.verbose and diffs:
        print("\nUnified Diffs:")
        for d in diffs:
            print(d)


if __name__ == "__main__":
    main()
