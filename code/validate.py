"""Validation module for HackerRank Orchestrate: Ghost Data Still Exists.

Enforces every rule in CONTRACT_SPEC.md:
- Exact header: case_id,deletion_status,steps_json
- Exactly 518 unique sorted rows (or custom expected_cases, e.g. 32 for sample set)
- Legal deletion_status: COMPLETE, INCOMPLETE, NOT_APPLICABLE
- NOT_APPLICABLE => steps_json must be exactly []
- steps_json must parse as valid JSON array
- Each step has exactly 7 keys: step_no, phase, system_id, resource_id, operation, state, evidence_id
- Consecutive step_no starting at 1
- Legal (phase, operation, state) combinations from contract
- Phase ordering: FINDING -> REMEDIATION -> VERIFICATION
- Operation ordering within phase:
    REMEDIATION: DISABLE_DATA_FLOW (1), BLOCK_RESTORE (2), DELETE_RECORD (3), REDACT_RECORD (4), ANONYMIZE_RECORD (5)
    VERIFICATION: VERIFY_RECORD_ABSENT (1), VERIFY_RECORD_PRESENT (2), VERIFY_RECORD_REDACTED (3),
                  VERIFY_RECORD_ANONYMIZED (4), VERIFY_DATA_FLOW_DISABLED (5), VERIFY_RESTORE_BLOCKED (6)
- Sorting within operation: system_id ASCII ascending, then resource_id ASCII ascending
- Evidence ID rules:
    FINDING and COMPLETE-VERIFICATION cite a usable evidence_id (from evidence_files, system_activity, or user_audit)
    REMEDIATION and INCOMPLETE-VERIFICATION must use empty string ""
- Cutoff enforcement: cited evidence capture_time / event_time must not be > case audit_at
- No duplicate steps
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


LEGAL_STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}

LEGAL_STEP_KEYS = [
    "step_no",
    "phase",
    "system_id",
    "resource_id",
    "operation",
    "state",
    "evidence_id",
]

LEGAL_COMBINATIONS = {
    # FINDINGS
    ("FINDING", "REPORT_REMAINING_RECORD", "PRESENT"),
    ("FINDING", "REPORT_EXPOSED_PII", "PRESENT"),
    ("FINDING", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE"),
    ("FINDING", "REPORT_RESTORE_RISK", "ACTIVE"),
    # REMEDIATION
    ("REMEDIATION", "DISABLE_DATA_FLOW", "DISABLED"),
    ("REMEDIATION", "BLOCK_RESTORE", "BLOCKED"),
    ("REMEDIATION", "DELETE_RECORD", "ABSENT"),
    ("REMEDIATION", "REDACT_RECORD", "REDACTED"),
    ("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED"),
    # VERIFICATION
    ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT"),
    ("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT"),
    ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED"),
    ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"),
    ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED"),
    ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED"),
}

PHASE_ORDER = {
    "FINDING": 1,
    "REMEDIATION": 2,
    "VERIFICATION": 3,
}

FINDING_OP_ORDER = {
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
}

REMEDIATION_OP_ORDER = {
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
}

VERIFICATION_OP_ORDER = {
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}


def parse_iso(ts_str: str) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        s = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


class EvidenceRegistry:
    """Loads valid evidence IDs and their capture/event timestamps."""

    def __init__(self, dataset_dir: Path):
        self.evidence_times: Dict[str, datetime] = {}
        self._load(dataset_dir)

    def _load(self, dataset_dir: Path):
        ev_file = dataset_dir / "evidence_files.csv"
        if ev_file.exists():
            with open(ev_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fid = row.get("file_id")
                    t_str = row.get("captured_at")
                    dt = parse_iso(t_str)
                    if fid and dt:
                        self.evidence_times[fid] = dt

        act_file = dataset_dir / "system_activity.csv"
        if act_file.exists():
            with open(act_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aid = row.get("activity_id")
                    t_str = row.get("event_time")
                    dt = parse_iso(t_str)
                    if aid and dt:
                        self.evidence_times[aid] = dt

        aud_file = dataset_dir / "user_audit_log.csv"
        if aud_file.exists():
            with open(aud_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    aud_id = row.get("audit_id")
                    t_str = row.get("event_time")
                    dt = parse_iso(t_str)
                    if aud_id and dt:
                        self.evidence_times[aud_id] = dt

    def exists(self, eid: str) -> bool:
        return eid in self.evidence_times

    def get_time(self, eid: str) -> Optional[datetime]:
        return self.evidence_times.get(eid)


def validate_file(
    output_path: Path,
    requests_path: Optional[Path] = None,
    dataset_dir: Optional[Path] = None,
    expected_count: Optional[int] = 518,
) -> List[str]:
    """Validates an output.csv file against all contract rules."""
    errors: List[str] = []

    if not output_path.exists():
        return [f"File does not exist: {output_path}"]

    # Read cases/cutoffs from requests file if provided
    case_cutoffs: Dict[str, datetime] = {}
    expected_case_ids: List[str] = []
    if requests_path and requests_path.exists():
        with open(requests_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cid = r.get("case_id")
                if cid:
                    expected_case_ids.append(cid)
                    aat = r.get("audit_at")
                    dt = parse_iso(aat)
                    if dt:
                        case_cutoffs[cid] = dt
        if expected_count is None:
            expected_count = len(expected_case_ids)

    # Load registry if dataset_dir given
    registry = EvidenceRegistry(dataset_dir) if dataset_dir else None

    # Read output.csv
    try:
        with open(output_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception as e:
        return [f"CSV read error: {e}"]

    if not rows:
        return ["File is empty"]

    # Rule: Header exact
    header = rows[0]
    expected_header = ["case_id", "deletion_status", "steps_json"]
    if header != expected_header:
        errors.append(f"Header mismatch: expected {expected_header}, got {header}")

    data_rows = rows[1:]

    # Rule: Row count
    if expected_count is not None and len(data_rows) != expected_count:
        errors.append(f"Expected {expected_count} data rows, got {len(data_rows)}")

    # Rule: Sorted and unique case_ids
    seen_case_ids: Set[str] = set()
    prev_case_id: Optional[str] = None

    for row_idx, row in enumerate(data_rows, start=2):
        if len(row) != 3:
            errors.append(f"Line {row_idx}: expected 3 columns, got {len(row)}")
            continue

        case_id, deletion_status, steps_json_str = row[0], row[1], row[2]

        if not case_id:
            errors.append(f"Line {row_idx}: empty case_id")
            continue

        if case_id in seen_case_ids:
            errors.append(f"Line {row_idx}: duplicate case_id '{case_id}'")
        seen_case_ids.add(case_id)

        if prev_case_id is not None and case_id < prev_case_id:
            errors.append(f"Line {row_idx}: case_id out of order ('{case_id}' < '{prev_case_id}')")
        prev_case_id = case_id

        # Rule: deletion_status legal
        if deletion_status not in LEGAL_STATUSES:
            errors.append(f"Line {row_idx} ({case_id}): illegal deletion_status '{deletion_status}'")

        # Parse JSON
        try:
            steps = json.loads(steps_json_str)
        except Exception as e:
            errors.append(f"Line {row_idx} ({case_id}): invalid JSON in steps_json: {e}")
            continue

        if not isinstance(steps, list):
            errors.append(f"Line {row_idx} ({case_id}): steps_json must be a JSON array, got {type(steps).__name__}")
            continue

        # Rule: NOT_APPLICABLE => []
        if deletion_status == "NOT_APPLICABLE":
            if steps != []:
                errors.append(f"Line {row_idx} ({case_id}): NOT_APPLICABLE must have empty steps array [], got {len(steps)} steps")
            continue

        # Rule: COMPLETE / INCOMPLETE step checks
        case_audit_at = case_cutoffs.get(case_id)
        seen_steps: Set[Tuple[str, str, str, str]] = set()

        prev_phase_rank = 0
        prev_op_rank = 0
        prev_sys = ""
        prev_res = ""

        for step_idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: step is not a JSON object")
                continue

            # Rule: Exactly 7 keys
            keys = list(step.keys())
            if set(keys) != set(LEGAL_STEP_KEYS) or len(keys) != 7:
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: keys mismatch. Expected {LEGAL_STEP_KEYS}, got {keys}")

            step_no = step.get("step_no")
            phase = step.get("phase")
            system_id = step.get("system_id", "")
            resource_id = step.get("resource_id", "")
            operation = step.get("operation")
            state = step.get("state")
            evidence_id = step.get("evidence_id")

            # Rule: Consecutive step_no starting at 1
            if step_no != step_idx:
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: expected step_no {step_idx}, got {step_no}")

            # Rule: Legal combination
            combo = (phase, operation, state)
            if combo not in LEGAL_COMBINATIONS:
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: illegal combination {combo}")

            # Rule: Phase ordering (FINDING -> REMEDIATION -> VERIFICATION)
            current_phase_rank = PHASE_ORDER.get(phase, 99)
            if current_phase_rank < prev_phase_rank:
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: phase out of order ({phase} after rank {prev_phase_rank})")
            elif current_phase_rank > prev_phase_rank:
                prev_phase_rank = current_phase_rank
                prev_op_rank = 0
                prev_sys = ""
                prev_res = ""

            # Rule: Operation order within phase
            current_op_rank = 0
            if phase == "FINDING":
                current_op_rank = FINDING_OP_ORDER.get(operation, 99)
            elif phase == "REMEDIATION":
                current_op_rank = REMEDIATION_OP_ORDER.get(operation, 99)
            elif phase == "VERIFICATION":
                current_op_rank = VERIFICATION_OP_ORDER.get(operation, 99)

            if current_op_rank < prev_op_rank:
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: operation out of order ({operation} after op rank {prev_op_rank})")
            elif current_op_rank > prev_op_rank:
                prev_op_rank = current_op_rank
                prev_sys = ""
                prev_res = ""

            # Rule: system_id and resource_id sort order within same operation
            if (system_id, resource_id) < (prev_sys, prev_res):
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: system/resource out of order (('{system_id}', '{resource_id}') < ('{prev_sys}', '{prev_res}'))")
            prev_sys = system_id
            prev_res = resource_id

            # Rule: Duplicate step check
            step_identity = (phase, operation, system_id, resource_id)
            if step_identity in seen_steps:
                errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: duplicate step {step_identity}")
            seen_steps.add(step_identity)

            # Rule: Evidence ID rules
            # COMPLETE: only VERIFICATION steps, all must cite evidence
            # INCOMPLETE: FINDING must cite evidence; REMEDIATION and future VERIFICATION must use ""
            if deletion_status == "COMPLETE":
                if phase != "VERIFICATION":
                    errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: COMPLETE case cannot have phase {phase}")
                if not evidence_id:
                    errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: COMPLETE verification must cite non-empty evidence_id")
            elif deletion_status == "INCOMPLETE":
                if phase == "FINDING":
                    if not evidence_id:
                        errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: FINDING must cite non-empty evidence_id")
                elif phase in ("REMEDIATION", "VERIFICATION"):
                    if evidence_id != "":
                        errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: INCOMPLETE {phase} step must have evidence_id='', got '{evidence_id}'")

            # Cutoff and registry checks
            if evidence_id and registry:
                if not registry.exists(evidence_id):
                    errors.append(f"Line {row_idx} ({case_id}) step {step_idx}: evidence_id '{evidence_id}' not found in registry")
                else:
                    ev_time = registry.get_time(evidence_id)
                    if ev_time and case_audit_at and ev_time > case_audit_at:
                        errors.append(
                            f"Line {row_idx} ({case_id}) step {step_idx}: evidence_id '{evidence_id}' captured at {ev_time.isoformat()} is after case audit_at {case_audit_at.isoformat()}"
                        )

    return errors
