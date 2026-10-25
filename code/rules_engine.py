"""Policy evaluation engine: applies deletion policy rules to resource states."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from state_reconstructor import ResourceState


@dataclass
class Verdict:
    resource_id: str
    system_id: str
    data_category: str
    rule_id: str
    required_action: str
    is_compliant: bool
    evidence_id: str
    state: str
    finding_operation: Optional[str] = None
    finding_state: Optional[str] = None
    remediation_operation: Optional[str] = None
    remediation_state: Optional[str] = None
    verification_operation: str = ""
    verification_state: str = ""


# Grounded rules map
RULE_DEFINITIONS = {
    "USER_PROFILE": {
        "rule_id": "rule_01",
        "action": "DELETE",
        "compliant_states": {"ABSENT"},
        "finding_op": "REPORT_REMAINING_RECORD",
        "finding_state": "PRESENT",
        "rem_op": "DELETE_RECORD",
        "rem_state": "ABSENT",
        "ver_op": "VERIFY_RECORD_ABSENT",
        "ver_state": "ABSENT",
    },
    "SEARCH_INDEX_ENTRY": {
        "rule_id": "rule_03",
        "action": "DELETE",
        "compliant_states": {"ABSENT"},
        "finding_op": "REPORT_REMAINING_RECORD",
        "finding_state": "PRESENT",
        "rem_op": "DELETE_RECORD",
        "rem_state": "ABSENT",
        "ver_op": "VERIFY_RECORD_ABSENT",
        "ver_state": "ABSENT",
    },
    "SUPPORT_ATTACHMENT": {
        "rule_id": "rule_06",
        "action": "DELETE",
        "compliant_states": {"ABSENT"},
        "finding_op": "REPORT_REMAINING_RECORD",
        "finding_state": "PRESENT",
        "rem_op": "DELETE_RECORD",
        "rem_state": "ABSENT",
        "ver_op": "VERIFY_RECORD_ABSENT",
        "ver_state": "ABSENT",
    },
    "USER_EXPORT": {
        "rule_id": "rule_09",
        "action": "DELETE",
        "compliant_states": {"ABSENT"},
        "finding_op": "REPORT_REMAINING_RECORD",
        "finding_state": "PRESENT",
        "rem_op": "DELETE_RECORD",
        "rem_state": "ABSENT",
        "ver_op": "VERIFY_RECORD_ABSENT",
        "ver_state": "ABSENT",
    },
    "MARKETING_PROFILE": {
        "rule_id": "rule_10",
        "action": "DELETE",
        "compliant_states": {"ABSENT"},
        "finding_op": "REPORT_REMAINING_RECORD",
        "finding_state": "PRESENT",
        "rem_op": "DELETE_RECORD",
        "rem_state": "ABSENT",
        "ver_op": "VERIFY_RECORD_ABSENT",
        "ver_state": "ABSENT",
    },
    "SUPPORT_MESSAGE": {
        "rule_id": "rule_05",
        "action": "REDACT",
        "compliant_states": {"REDACTED", "ABSENT"},
        "finding_op": "REPORT_EXPOSED_PII",
        "finding_state": "PRESENT",
        "rem_op": "REDACT_RECORD",
        "rem_state": "REDACTED",
        "ver_op": "VERIFY_RECORD_REDACTED",
        "ver_state": "REDACTED",
    },
    "ACCOUNT_TOMBSTONE": {
        "rule_id": "rule_15",
        "action": "REDACT",
        "compliant_states": {"REDACTED", "ABSENT"},
        "finding_op": "REPORT_EXPOSED_PII",
        "finding_state": "PRESENT",
        "rem_op": "REDACT_RECORD",
        "rem_state": "REDACTED",
        "ver_op": "VERIFY_RECORD_REDACTED",
        "ver_state": "REDACTED",
    },
    "ANALYTICS_PROFILE": {
        "rule_id": "rule_07",
        "action": "ANONYMIZE",
        "compliant_states": {"ANONYMIZED", "ABSENT"},
        "finding_op": "REPORT_EXPOSED_PII",
        "finding_state": "PRESENT",
        "rem_op": "ANONYMIZE_RECORD",
        "rem_state": "ANONYMIZED",
        "ver_op": "VERIFY_RECORD_ANONYMIZED",
        "ver_state": "ANONYMIZED",
    },
    "SECURITY_AUDIT_LOG": {
        "rule_id": "rule_12",
        "action": "RETAIN",
        "compliant_states": {"PRESENT"},
        "finding_op": None,
        "finding_state": None,
        "rem_op": None,
        "rem_state": None,
        "ver_op": "VERIFY_RECORD_PRESENT",
        "ver_state": "PRESENT",
    },
    "BACKUP_ARCHIVE": {
        "rule_id": "rule_14",
        "action": "RETAIN",
        "compliant_states": {"BLOCKED"},
        "finding_op": "REPORT_RESTORE_RISK",
        "finding_state": "ACTIVE",
        "rem_op": "BLOCK_RESTORE",
        "rem_state": "BLOCKED",
        "ver_op": "VERIFY_RESTORE_BLOCKED",
        "ver_state": "BLOCKED",
    },
    "DATA_FLOW": {
        "rule_id": "rule_flow",
        "action": "DISABLE_DATA_FLOW",
        "compliant_states": {"DISABLED"},
        "finding_op": "REPORT_ACTIVE_DATA_FLOW",
        "finding_state": "ACTIVE",
        "rem_op": "DISABLE_DATA_FLOW",
        "rem_state": "DISABLED",
        "ver_op": "VERIFY_DATA_FLOW_DISABLED",
        "ver_state": "DISABLED",
    },
}


from pathlib import Path


class ClassificationError(Exception):
    """Raised when resource category cannot be mapped to a grounded deletion rule."""
    pass


class PolicyEngine:
    def __init__(self):
        self.issues = set()  # deduplicated; main.py rewrites failures.md from this each run

    def evaluate_resource(self, res: ResourceState) -> Verdict:
        cat = res.data_category
        rule = RULE_DEFINITIONS.get(cat)
        if not rule:
            self.issues.add(f"[CLASSIFICATION_ERROR] '{res.resource_id}' (system '{res.system_id}', category '{cat}') unmapped; UNKNOWN_CLASSIFICATION")

            return Verdict(
                resource_id=res.resource_id,
                system_id=res.system_id,
                data_category=cat,
                rule_id="UNKNOWN_CLASSIFICATION",
                required_action="DELETE",
                is_compliant=(res.state == "ABSENT"),
                evidence_id=res.cited_evidence_id,
                state=res.state,
                finding_operation="REPORT_REMAINING_RECORD",
                finding_state="PRESENT",
                remediation_operation="DELETE_RECORD",
                remediation_state="ABSENT",
                verification_operation="VERIFY_RECORD_ABSENT",
                verification_state="ABSENT",
            )

        is_compliant = res.state in rule["compliant_states"]
        return Verdict(
            resource_id=res.resource_id,
            system_id=res.system_id,
            data_category=cat,
            rule_id=rule["rule_id"],
            required_action=rule["action"],
            is_compliant=is_compliant,
            evidence_id=res.cited_evidence_id,
            state=res.state,
            finding_operation=rule["finding_op"] if not is_compliant else None,
            finding_state=rule["finding_state"] if not is_compliant else None,
            remediation_operation=rule["rem_op"] if not is_compliant else None,
            remediation_state=rule["rem_state"] if not is_compliant else None,
            verification_operation=rule["ver_op"],
            verification_state=rule["ver_state"],
        )

    def evaluate_all(self, resources: List[ResourceState]) -> List[Verdict]:
        return [self.evaluate_resource(r) for r in resources]
