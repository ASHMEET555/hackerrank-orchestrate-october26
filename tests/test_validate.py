"""Unit tests for code/validate.py.

Includes tests for clean contract-compliant outputs and deliberately broken
fixtures testing every rule in CONTRACT_SPEC.md.
"""

import csv
import json
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("validate", Path("code/validate.py").resolve())
val = importlib.util.module_from_spec(spec)
spec.loader.exec_module(val)
validate_file = val.validate_file


@pytest.fixture
def clean_sample_output():
    return Path("dataset/sample_output.csv")


@pytest.fixture
def clean_sample_requests():
    return Path("dataset/sample_deletion_requests.csv")


@pytest.fixture
def dataset_dir():
    return Path("dataset")


def test_clean_sample_output_passes(clean_sample_output, clean_sample_requests, dataset_dir):
    errors = validate_file(
        output_path=clean_sample_output,
        requests_path=clean_sample_requests,
        dataset_dir=dataset_dir,
        expected_count=32,
    )
    assert errors == []


def test_missing_file():
    errors = validate_file(Path("non_existent_file.csv"))
    assert len(errors) == 1
    assert "File does not exist" in errors[0]


def test_bad_header(tmp_path, clean_sample_requests, dataset_dir):
    bad_csv = tmp_path / "bad_header.csv"
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "status", "steps_json"])  # wrong header
        writer.writerow(["case_01", "NOT_APPLICABLE", "[]"])

    errors = validate_file(bad_csv, requests_path=clean_sample_requests, dataset_dir=dataset_dir, expected_count=1)
    assert any("Header mismatch" in e for e in errors)


def test_row_count_mismatch(tmp_path, clean_sample_requests, dataset_dir):
    bad_csv = tmp_path / "bad_count.csv"
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "NOT_APPLICABLE", "[]"])

    errors = validate_file(bad_csv, requests_path=clean_sample_requests, dataset_dir=dataset_dir, expected_count=32)
    assert any("Expected 32 data rows, got 1" in e for e in errors)


def test_duplicate_case_id(tmp_path, dataset_dir):
    bad_csv = tmp_path / "dup_case.csv"
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "NOT_APPLICABLE", "[]"])
        writer.writerow(["case_01", "NOT_APPLICABLE", "[]"])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=2)
    assert any("duplicate case_id 'case_01'" in e for e in errors)


def test_case_id_out_of_order(tmp_path, dataset_dir):
    bad_csv = tmp_path / "order_case.csv"
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_02", "NOT_APPLICABLE", "[]"])
        writer.writerow(["case_01", "NOT_APPLICABLE", "[]"])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=2)
    assert any("case_id out of order" in e for e in errors)


def test_illegal_status(tmp_path, dataset_dir):
    bad_csv = tmp_path / "bad_status.csv"
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "PARTIALLY_COMPLETE", "[]"])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("illegal deletion_status 'PARTIALLY_COMPLETE'" in e for e in errors)


def test_not_applicable_non_empty_steps(tmp_path, dataset_dir):
    bad_csv = tmp_path / "na_steps.csv"
    step = {
        "step_no": 1,
        "phase": "VERIFICATION",
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "evidence_54",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "NOT_APPLICABLE", json.dumps([step])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("NOT_APPLICABLE must have empty steps array []" in e for e in errors)


def test_step_missing_key(tmp_path, dataset_dir):
    bad_csv = tmp_path / "missing_key.csv"
    step = {
        "step_no": 1,
        "phase": "VERIFICATION",
        "system_id": "account_service",
        # missing resource_id
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "evidence_54",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "COMPLETE", json.dumps([step])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("keys mismatch" in e for e in errors)


def test_step_numbering_not_consecutive(tmp_path, dataset_dir):
    bad_csv = tmp_path / "bad_step_no.csv"
    step = {
        "step_no": 2,  # starts at 2
        "phase": "VERIFICATION",
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "evidence_54",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "COMPLETE", json.dumps([step])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("expected step_no 1, got 2" in e for e in errors)


def test_illegal_phase_operation_combination(tmp_path, dataset_dir):
    bad_csv = tmp_path / "bad_combo.csv"
    step = {
        "step_no": 1,
        "phase": "VERIFICATION",
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "DELETE_RECORD",  # illegal for VERIFICATION
        "state": "ABSENT",
        "evidence_id": "evidence_54",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "COMPLETE", json.dumps([step])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("illegal combination" in e for e in errors)


def test_phase_out_of_order(tmp_path, dataset_dir):
    bad_csv = tmp_path / "bad_phase_order.csv"
    step1 = {
        "step_no": 1,
        "phase": "VERIFICATION",
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "",
    }
    step2 = {
        "step_no": 2,
        "phase": "FINDING",
        "system_id": "search_service",
        "resource_id": "search_001",
        "operation": "REPORT_REMAINING_RECORD",
        "state": "PRESENT",
        "evidence_id": "evidence_54",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "INCOMPLETE", json.dumps([step1, step2])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("phase out of order" in e for e in errors)


def test_operation_out_of_order(tmp_path, dataset_dir):
    bad_csv = tmp_path / "bad_op_order.csv"
    # In remediation: DELETE_RECORD (rank 3) before DISABLE_DATA_FLOW (rank 1)
    step1 = {
        "step_no": 1,
        "phase": "REMEDIATION",
        "system_id": "search_service",
        "resource_id": "search_001",
        "operation": "DELETE_RECORD",
        "state": "ABSENT",
        "evidence_id": "",
    }
    step2 = {
        "step_no": 2,
        "phase": "REMEDIATION",
        "system_id": "integration_service",
        "resource_id": "data_flow_01",
        "operation": "DISABLE_DATA_FLOW",
        "state": "DISABLED",
        "evidence_id": "",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "INCOMPLETE", json.dumps([step1, step2])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("operation out of order" in e for e in errors)


def test_system_resource_out_of_order(tmp_path, dataset_dir):
    bad_csv = tmp_path / "bad_sys_order.csv"
    step1 = {
        "step_no": 1,
        "phase": "FINDING",
        "system_id": "support_platform",
        "resource_id": "support_01",
        "operation": "REPORT_REMAINING_RECORD",
        "state": "PRESENT",
        "evidence_id": "evidence_54",
    }
    step2 = {
        "step_no": 2,
        "phase": "FINDING",
        "system_id": "account_service",
        "resource_id": "account_01",
        "operation": "REPORT_REMAINING_RECORD",
        "state": "PRESENT",
        "evidence_id": "evidence_54",
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "INCOMPLETE", json.dumps([step1, step2])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("system/resource out of order" in e for e in errors)


def test_complete_empty_evidence_id(tmp_path, dataset_dir):
    bad_csv = tmp_path / "complete_no_ev.csv"
    step = {
        "step_no": 1,
        "phase": "VERIFICATION",
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "VERIFY_RECORD_ABSENT",
        "state": "ABSENT",
        "evidence_id": "",  # illegal for COMPLETE
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "COMPLETE", json.dumps([step])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("COMPLETE verification must cite non-empty evidence_id" in e for e in errors)


def test_incomplete_remediation_with_evidence_id(tmp_path, dataset_dir):
    bad_csv = tmp_path / "remed_with_ev.csv"
    step = {
        "step_no": 1,
        "phase": "REMEDIATION",
        "system_id": "account_service",
        "resource_id": "account_001",
        "operation": "DELETE_RECORD",
        "state": "ABSENT",
        "evidence_id": "evidence_54",  # illegal for REMEDIATION
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_01", "INCOMPLETE", json.dumps([step])])

    errors = validate_file(bad_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("INCOMPLETE REMEDIATION step must have evidence_id=''" in e for e in errors)


def test_post_cutoff_evidence(tmp_path, dataset_dir):
    bad_csv = tmp_path / "post_cutoff.csv"
    req_csv = tmp_path / "req.csv"
    # evidence_06 captured 2026-09-18. If case audit_at is 2026-09-16, this must fail.
    with open(req_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "email", "requested_at", "reported_status", "reported_at", "audit_at", "request_text"])
        writer.writerow(["case_09", "k.appiah88@gmail.com", "2026-09-15T10:00:00Z", "COMPLETE", "2026-09-15T12:00:00Z", "2026-09-16T09:00:00Z", "Delete data"])

    step = {
        "step_no": 1,
        "phase": "FINDING",
        "system_id": "account_service",
        "resource_id": "account_3960",
        "operation": "REPORT_REMAINING_RECORD",
        "state": "PRESENT",
        "evidence_id": "evidence_06",  # captured 2026-09-18 > audit_at 2026-09-16
    }
    with open(bad_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        writer.writerow(["case_09", "INCOMPLETE", json.dumps([step])])

    errors = validate_file(bad_csv, requests_path=req_csv, dataset_dir=dataset_dir, expected_count=1)
    assert any("is after case audit_at" in e for e in errors)
