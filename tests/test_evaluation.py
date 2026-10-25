"""Tests for evaluation harness metric calculation functions using a 3-row toy input."""

import csv
import json
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("eval_main", Path("code/evaluation/main.py").resolve())
eval_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_main)
compare_outputs = eval_main.compare_outputs


@pytest.fixture
def toy_csvs(tmp_path):
    """Creates a 3-row toy truth and prediction set with hand-calculated expected metrics."""
    truth_file = tmp_path / "toy_truth.csv"
    pred_file = tmp_path / "toy_pred.csv"

    # Row 1: Exact match (status + 1 step)
    # Row 2: Status match, but step operation changed (sequence and row mismatch)
    # Row 3: Status mismatch (COMPLETE vs INCOMPLETE)
    step1 = {"step_no": 1, "phase": "VERIFICATION", "system_id": "acc", "resource_id": "r1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev1"}
    step2_truth = {"step_no": 1, "phase": "FINDING", "system_id": "sec", "resource_id": "r2", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "ev2"}
    step2_pred = {"step_no": 1, "phase": "FINDING", "system_id": "sec", "resource_id": "r2", "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": "ev2"}
    step3_truth = {"step_no": 1, "phase": "VERIFICATION", "system_id": "acc", "resource_id": "r3", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev3"}
    step3_pred = {"step_no": 1, "phase": "VERIFICATION", "system_id": "acc", "resource_id": "r3", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev3"}

    with open(truth_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "COMPLETE", json.dumps([step1])])
        writer.writerow(["case_02", "INCOMPLETE", json.dumps([step2_truth])])
        writer.writerow(["case_03", "COMPLETE", json.dumps([step3_truth])])

    with open(pred_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "COMPLETE", json.dumps([step1])])              # exact match
        writer.writerow(["case_02", "INCOMPLETE", json.dumps([step2_pred])])        # step op mismatch
        writer.writerow(["case_03", "INCOMPLETE", json.dumps([step3_pred])])        # status mismatch

    return truth_file, pred_file


def test_toy_metrics_calculation(toy_csvs):
    truth_file, pred_file = toy_csvs
    metrics, diffs = compare_outputs(pred_file, truth_file)

    # Hand-computed checks:
    # Total cases: 3
    assert metrics.total_cases == 3

    # Status matches: case_01 (COMPLETE==COMPLETE), case_02 (INCOMPLETE==INCOMPLETE), case_03 (COMPLETE!=INCOMPLETE)
    # status_accuracy = 2 / 3 = 0.666666...
    assert pytest.approx(metrics.status_accuracy, rel=1e-3) == 2 / 3

    # Row matches: only case_01 matches both status and all steps exactly
    # row_accuracy = 1 / 3 = 0.333333...
    assert pytest.approx(metrics.row_accuracy, rel=1e-3) == 1 / 3
    assert metrics.matched_cases == 1

    # Sequence matches:
    # case_01: seq match
    # case_02: REPORT_REMAINING_RECORD vs REPORT_EXPOSED_PII -> mismatch
    # case_03: seq match
    # sequence_accuracy = 2 / 3 = 0.666666...
    assert pytest.approx(metrics.sequence_accuracy, rel=1e-3) == 2 / 3

    # Field matches:
    # 3 cases * 1 step * 7 fields = 21 total fields.
    # case_01: 7 / 7 match
    # case_02: 6 / 7 match (only 'operation' differed)
    # case_03: 7 / 7 match
    # Total matched fields = 7 + 6 + 7 = 20 / 21 = 0.95238...
    assert pytest.approx(metrics.field_accuracy, rel=1e-3) == 20 / 21

    # Diffs should contain unified diffs for case_02 and case_03
    assert len(diffs) == 2
