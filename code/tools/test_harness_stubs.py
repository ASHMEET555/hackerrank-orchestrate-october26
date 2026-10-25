"""Generate and test evaluation harness stubs."""

import csv
import json
import sys
from pathlib import Path

# Add repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location("eval_main", Path("code/evaluation/main.py").resolve())
eval_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_main)
compare_outputs = eval_main.compare_outputs


def generate_stubs(base_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(base_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Stub 1: Exact copy (100% expected)
    stub_exact = output_dir / "stub_exact.csv"
    with open(stub_exact, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(rows)

    # Stub 2: Single-case stub (modifies only case_01's steps)
    # Expected: 31/32 row accuracy = 96.875%, 31/32 sequence accuracy = 96.875%
    stub_single = output_dir / "stub_single_case.csv"
    with open(stub_single, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        for r in rows:
            if r["case_id"] == "case_01":
                # modify case_01 step
                steps = json.loads(r["steps_json"])
                steps[0]["operation"] = "VERIFY_RECORD_PRESENT"
                steps[0]["state"] = "PRESENT"
                writer.writerow({
                    "case_id": r["case_id"],
                    "deletion_status": r["deletion_status"],
                    "steps_json": json.dumps(steps),
                })
            else:
                writer.writerow(r)

    # Stub 3: Dropped-step stub (drops first step from all non-empty cases)
    # Expected: row accuracy 0% because all 32 cases have >= 1 step and are modified
    stub_dropped = output_dir / "stub_dropped.csv"
    with open(stub_dropped, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        for r in rows:
            steps = json.loads(r["steps_json"])
            if len(steps) >= 1:
                steps = steps[1:]
                for idx, s in enumerate(steps, start=1):
                    s["step_no"] = idx
            writer.writerow({
                "case_id": r["case_id"],
                "deletion_status": r["deletion_status"],
                "steps_json": json.dumps(steps),
            })

    return stub_exact, stub_single, stub_dropped


if __name__ == "__main__":
    truth = Path("dataset/sample_output.csv")
    out_dir = Path("code/.cache/stubs")
    s_exact, s_single, s_dropped = generate_stubs(truth, out_dir)

    print("--- 1. Testing Exact Stub ---")
    m_exact, _ = compare_outputs(s_exact, truth)
    print(f"Status: {m_exact.status_accuracy*100:.2f}%, Row: {m_exact.row_accuracy*100:.2f}%, Field: {m_exact.field_accuracy*100:.2f}%, Seq: {m_exact.sequence_accuracy*100:.2f}%")

    print("\n--- 2. Testing Single-Case Stub ---")
    m_single, diffs_single = compare_outputs(s_single, truth)
    print(f"Status: {m_single.status_accuracy*100:.2f}%, Row: {m_single.row_accuracy*100:.3f}% ({m_single.matched_cases}/{m_single.total_cases}), Field: {m_single.field_accuracy*100:.2f}%, Seq: {m_single.sequence_accuracy*100:.3f}%")
    print("Diff for case_01:")
    print(diffs_single[0])

    print("\n--- 3. Testing Dropped Step Stub ---")
    m_dropped, _ = compare_outputs(s_dropped, truth)
    print(f"Status: {m_dropped.status_accuracy*100:.2f}%, Row: {m_dropped.row_accuracy*100:.2f}%, Field: {m_dropped.field_accuracy*100:.2f}%, Seq: {m_dropped.sequence_accuracy*100:.2f}%")
    print("Explanation: All 32 sample cases in ground truth have >= 1 step. Dropping the first step modifies every case row, causing 0 out of 32 rows to match exactly (0.00% row accuracy).")
