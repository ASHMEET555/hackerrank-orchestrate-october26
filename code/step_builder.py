"""step_builder.py — Generates ordered, validated steps for deletion cases."""

from typing import Any, Dict, List, Tuple
from rules_engine import Verdict
from state_reconstructor import ResourceState

# Phase ordering
PHASE_ORDER = {
    "FINDING": 1,
    "REMEDIATION": 2,
    "VERIFICATION": 3,
}

# Operation ordering within each phase (from CONTRACT_SPEC and step_rules.yaml)
FINDING_ORDER = {
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
}

REMEDIATION_ORDER = {
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
}

VERIFICATION_ORDER = {
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}


def step_sort_key(step: Dict[str, Any]) -> Tuple[int, int, str, str]:
    """Computes sort key: (phase_rank, op_rank, system_id, resource_id)."""
    phase_rank = PHASE_ORDER.get(step["phase"], 99)
    op = step["operation"]
    if step["phase"] == "FINDING":
        op_rank = FINDING_ORDER.get(op, 99)
    elif step["phase"] == "REMEDIATION":
        op_rank = REMEDIATION_ORDER.get(op, 99)
    elif step["phase"] == "VERIFICATION":
        op_rank = VERIFICATION_ORDER.get(op, 99)
    else:
        op_rank = 99
    return (phase_rank, op_rank, step["system_id"], step["resource_id"])


class StepBuilder:
    """Builds and sorts plan steps for a case."""

    @staticmethod
    def build_steps(
        deletion_status: str,
        verdicts: List[Verdict],
        resource_states: List[ResourceState],
    ) -> List[Dict[str, Any]]:
        """
        Builds ordered steps.
        - NOT_APPLICABLE -> []
        - COMPLETE -> VERIFICATION steps citing evidence
        - INCOMPLETE -> FINDING (citing evidence) + REMEDIATION (future, "") + VERIFICATION (future, "")
        """
        if deletion_status == "NOT_APPLICABLE":
            return []

        raw_steps: List[Dict[str, Any]] = []

        if deletion_status == "COMPLETE":
            for v in verdicts:
                if v.verification_operation:
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": v.system_id,
                        "resource_id": v.resource_id,
                        "operation": v.verification_operation,
                        "state": v.verification_state,
                        "evidence_id": v.evidence_id,
                    })
        else:
            # INCOMPLETE
            # 1. Findings and Remediations for violations
            for v in verdicts:
                if not v.is_compliant:
                    if v.finding_operation:
                        raw_steps.append({
                            "phase": "FINDING",
                            "system_id": v.system_id,
                            "resource_id": v.resource_id,
                            "operation": v.finding_operation,
                            "state": v.finding_state,
                            "evidence_id": v.evidence_id,
                        })
                    if v.remediation_operation:
                        raw_steps.append({
                            "phase": "REMEDIATION",
                            "system_id": v.system_id,
                            "resource_id": v.resource_id,
                            "operation": v.remediation_operation,
                            "state": v.remediation_state,
                            "evidence_id": "",
                        })

                # Verification in INCOMPLETE: all resources need future verification
                if v.verification_operation:
                    raw_steps.append({
                        "phase": "VERIFICATION",
                        "system_id": v.system_id,
                        "resource_id": v.resource_id,
                        "operation": v.verification_operation,
                        "state": v.verification_state,
                        "evidence_id": "",
                    })

        # Sort by contract sort key
        raw_steps.sort(key=step_sort_key)

        # Number steps consecutively from 1, ensuring exactly 7 keys
        final_steps: List[Dict[str, Any]] = []
        for idx, s in enumerate(raw_steps, start=1):
            final_steps.append({
                "step_no": idx,
                "phase": s["phase"],
                "system_id": s["system_id"],
                "resource_id": s["resource_id"],
                "operation": s["operation"],
                "state": s["state"],
                "evidence_id": s["evidence_id"],
            })

        return final_steps
