"""status_decider.py — Determines deletion_status (COMPLETE, INCOMPLETE, NOT_APPLICABLE)."""

from typing import List, Tuple
from rules_engine import Verdict
from state_reconstructor import ResourceState


class StatusDecider:
    """Decides case deletion status and provides audit reason."""

    @staticmethod
    def decide_status(
        intent_label: str,
        verdicts: List[Verdict],
        resource_states: List[ResourceState],
    ) -> Tuple[str, str]:
        """
        Returns (deletion_status, reason).
        Statuses:
          - NOT_APPLICABLE: intent does not authorize deletion.
          - COMPLETE: all resources compliant at audit_at, no active flows or restore risks.
          - INCOMPLETE: one or more policy violations or active recreation risks present.
        """
        if intent_label != "ERASURE":
            return "NOT_APPLICABLE", f"Intent is {intent_label} (non-deletion)"

        violations = []
        for v in verdicts:
            if v.rule_id == "UNKNOWN_CLASSIFICATION":
                violations.append(f"{v.resource_id} (UNKNOWN_CLASSIFICATION: unmapped category {v.data_category})")
            elif not v.is_compliant:
                violations.append(f"{v.resource_id} ({v.data_category}: {v.state} != required)")

        # Check for any active data flows or restore risks in resource_states
        for res in resource_states:
            if res.data_category == "DATA_FLOW" and res.state == "ACTIVE":
                violations.append(f"{res.resource_id} (active data flow)")
            elif res.data_category == "BACKUP_ARCHIVE" and res.state == "ACTIVE":
                violations.append(f"{res.resource_id} (unblocked restore risk)")

        if not violations:
            return "COMPLETE", "All in-scope resources compliant at audit cutoff; no active recreation risks."

        return "INCOMPLETE", f"Remaining violations/risks: {'; '.join(violations[:3])}"
