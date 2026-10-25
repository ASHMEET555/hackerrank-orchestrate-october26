"""test_step_builder.py — Unit tests for step builder and sort key contract."""

import pytest
import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from rules_engine import Verdict
from state_reconstructor import ResourceState
from step_builder import StepBuilder, step_sort_key


def test_step_sort_key_order():
    """Validates (phase_rank, op_rank, system_id, resource_id) sort order."""
    step_finding_1 = {
        "phase": "FINDING",
        "operation": "REPORT_REMAINING_RECORD",
        "system_id": "account_service",
        "resource_id": "account_001",
    }
    step_finding_2 = {
        "phase": "FINDING",
        "operation": "REPORT_ACTIVE_DATA_FLOW",
        "system_id": "integration_service",
        "resource_id": "data_flow_001",
    }
    step_remediation_1 = {
        "phase": "REMEDIATION",
        "operation": "DISABLE_DATA_FLOW",
        "system_id": "integration_service",
        "resource_id": "data_flow_001",
    }
    step_remediation_2 = {
        "phase": "REMEDIATION",
        "operation": "DELETE_RECORD",
        "system_id": "account_service",
        "resource_id": "account_001",
    }
    step_verification_1 = {
        "phase": "VERIFICATION",
        "operation": "VERIFY_RECORD_ABSENT",
        "system_id": "account_service",
        "resource_id": "account_001",
    }

    steps = [
        step_verification_1,
        step_remediation_2,
        step_finding_2,
        step_remediation_1,
        step_finding_1,
    ]

    steps.sort(key=step_sort_key)

    # Expected order:
    # 1. FINDING REPORT_REMAINING_RECORD
    # 2. FINDING REPORT_ACTIVE_DATA_FLOW
    # 3. REMEDIATION DISABLE_DATA_FLOW
    # 4. REMEDIATION DELETE_RECORD
    # 5. VERIFICATION VERIFY_RECORD_ABSENT
    assert steps[0] == step_finding_1
    assert steps[1] == step_finding_2
    assert steps[2] == step_remediation_1
    assert steps[3] == step_remediation_2
    assert steps[4] == step_verification_1


def test_step_builder_exactly_seven_keys_and_consecutive_numbering():
    """Validates that build_steps emits exactly 7 keys and consecutive step numbers."""
    verdict = Verdict(
        resource_id="account_005",
        system_id="account_service",
        data_category="USER_PROFILE",
        rule_id="rule_01",
        required_action="DELETE",
        is_compliant=False,
        evidence_id="evidence_54",
        state="PRESENT",
        finding_operation="REPORT_REMAINING_RECORD",
        finding_state="PRESENT",
        remediation_operation="DELETE_RECORD",
        remediation_state="ABSENT",
        verification_operation="VERIFY_RECORD_ABSENT",
        verification_state="ABSENT",
    )
    res_state = ResourceState(
        system_id="account_service",
        resource_id="account_005",
        state="PRESENT",
        data_category="USER_PROFILE",
        cited_evidence_id="evidence_54",
    )

    steps = StepBuilder.build_steps("INCOMPLETE", [verdict], [res_state])
    assert len(steps) == 3  # 1 finding, 1 remediation, 1 verification

    expected_keys = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
    for idx, s in enumerate(steps, start=1):
        assert set(s.keys()) == expected_keys
        assert len(s.keys()) == 7
        assert s["step_no"] == idx

    # Finding cites evidence, remediation and future verification have empty evidence_id
    assert steps[0]["phase"] == "FINDING"
    assert steps[0]["evidence_id"] == "evidence_54"
    assert steps[1]["phase"] == "REMEDIATION"
    assert steps[1]["evidence_id"] == ""
    assert steps[2]["phase"] == "VERIFICATION"
    assert steps[2]["evidence_id"] == ""


def test_step_builder_complete_and_not_applicable():
    """Validates COMPLETE only has verification with evidence, and NOT_APPLICABLE has []."""
    verdict = Verdict(
        resource_id="account_001",
        system_id="account_service",
        data_category="USER_PROFILE",
        rule_id="rule_01",
        required_action="DELETE",
        is_compliant=True,
        evidence_id="evidence_21",
        state="ABSENT",
        verification_operation="VERIFY_RECORD_ABSENT",
        verification_state="ABSENT",
    )
    res_state = ResourceState(
        system_id="account_service",
        resource_id="account_001",
        state="ABSENT",
        data_category="USER_PROFILE",
        cited_evidence_id="evidence_21",
    )

    complete_steps = StepBuilder.build_steps("COMPLETE", [verdict], [res_state])
    assert len(complete_steps) == 1
    assert complete_steps[0]["phase"] == "VERIFICATION"
    assert complete_steps[0]["evidence_id"] == "evidence_21"

    na_steps = StepBuilder.build_steps("NOT_APPLICABLE", [verdict], [res_state])
    assert na_steps == []
