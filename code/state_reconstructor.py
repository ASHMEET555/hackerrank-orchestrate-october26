"""State reconstruction: derives resource states at audit_at from indexed evidence facts only.

Inputs: dataset/evidence_files.csv (via EvidenceIndex) and the resolved SubjectIdentity
(from dataset/user_identities.csv + user_audit_log.csv). No sample-derived data is read.
"""

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from evidence_index import EvidenceIndex
from identity import SubjectIdentity
from linker import Linker


@dataclass
class ResourceState:
    system_id: str
    resource_id: str
    state: str  # PRESENT, ABSENT, REDACTED, ANONYMIZED, ACTIVE, DISABLED, BLOCKED
    data_category: str
    cited_evidence_id: str = ""  # file_id of the fact that decided the state
    file_id: str = ""
    locator: str = ""  # line N | table T | page N | JSON path
    supporting_facts: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    resolution_rule: str = ""


_ID_KEYS = [
    "user_id", "customer_id", "subject_reference", "customer_reference",
    "email", "customer_email", "owner_email", "requester_email",
    "phone", "owner_phone", "requester_phone", "email_hash",
]
_TOKEN_RE = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|user_\d+|account_\d+|[a-z_]+_\d+|\+?\d{2,3}-\d{3,4}-\d{4}|[a-f0-9]{32,64}"
)
# Link attributes that point from one record to the resource it was derived from.
_LINK_KEYS = ["source_resource_id"]
# State preference when facts tie on captured_at: any residue counts (topology rule).
_STATE_PRIORITY = {"ACTIVE": 0, "PRESENT": 1}

# Category signals grounded in step_rules.yaml rule_grounding (system_id / resource_id prefix).
_PREFIX_CATEGORY = [
    ("account_", "USER_PROFILE"),
    ("search_", "SEARCH_INDEX_ENTRY"),
    ("export_", "USER_EXPORT"),
    ("backup_", "BACKUP_ARCHIVE"),
    ("data_flow_", "DATA_FLOW"),
    ("audit_record_", "SECURITY_AUDIT_LOG"),
    ("tombstone_", "ACCOUNT_TOMBSTONE"),
]


class StateReconstructor:
    def __init__(self, dataset_dir: Path, active_link_types: Optional[Set[str]] = None):
        self.dataset_dir = Path(dataset_dir).resolve()
        self.evidence_index = EvidenceIndex(self.dataset_dir)
        self.evidence_index.build()
        self.issues: Set[str] = set()  # deduplicated; written by main each run
        self.linker = Linker(self.dataset_dir)
        self.active_link_types = active_link_types

        self.fact_by_token: Dict[str, List[Any]] = {}
        for f in self.evidence_index.facts:
            txt = f"{f.resource_id} {f.text_snippet} {f.attributes} {f.locator}".lower()
            tokens = set(_TOKEN_RE.findall(txt))
            for k in _ID_KEYS + _LINK_KEYS:
                v = f.attributes.get(k)
                if v and isinstance(v, str):
                    tokens.add(v.strip().lower())
            for t in tokens:
                self.fact_by_token.setdefault(t, []).append(f)

    # ---- classification -------------------------------------------------
    @staticmethod
    def classify(resource_id: str, fact_categories: List[str]) -> str:
        for c in fact_categories:
            if c and c != "UNKNOWN":
                return c
        for prefix, cat in _PREFIX_CATEGORY:
            if resource_id.startswith(prefix):
                return cat
        if resource_id.startswith("legal_hold_"):
            return "UNGROUNDED_LEGAL_HOLD"
        return "UNKNOWN"

    # ---- main -----------------------------------------------------------
    def reconstruct_for_case(
        self,
        case_id: str,
        subject: SubjectIdentity,
        audit_at: datetime,
        requested_at: Optional[datetime] = None,
        reported_at: Optional[datetime] = None,
    ) -> List[ResourceState]:
        subject_tokens = self.linker.get_subject_tokens(subject.user_id, audit_at)
        tokens = {a.value.strip().lower() for a in subject.aliases if a.value}
        tokens.add(subject.user_id.lower())
        tokens.update(subject_tokens)

        def collect(toks: Set[str]) -> List[Any]:
            out = []
            for t in toks:
                for f in self.fact_by_token.get(t, []):
                    if f.is_usable_at(audit_at):
                        out.append(f)
            return out

        matched = collect(tokens)

        # Linker scan for active link types (support, analytics, data_flow, etc.)
        if self.active_link_types:
            for f in self.evidence_index.facts:
                if f.is_usable_at(audit_at):
                    if self.linker.match_fact(f, subject.user_id, tokens, active_link_types=self.active_link_types):
                        matched.append(f)

        # One-hop link expansion: resources a matched record was derived from.
        link_tokens: Set[str] = set()
        for f in matched:
            for k in _LINK_KEYS:
                v = f.attributes.get(k)
                if v and isinstance(v, str):
                    link_tokens.add(v.strip().lower())
        if link_tokens:
            matched = matched + collect(link_tokens - tokens)

        by_res: Dict[Tuple[str, str], List[Any]] = {}
        for f in matched:
            by_res.setdefault((f.system_id, f.resource_id), []).append(f)

        states: List[ResourceState] = []
        for (sys_id, rid), facts in sorted(by_res.items()):
            if rid.lower().startswith("user_"):
                self.issues.add(f"[IDENTITY_RESOLUTION] '{rid}' is a user identifier, not a resource; excluded ({facts[0].file_id} {facts[0].locator})")
                continue
            cat = self.classify(rid, [f.data_category for f in facts])
            if cat == "UNGROUNDED_LEGAL_HOLD":
                self.issues.add(f"[UNGROUNDED] '{rid}' legal_hold record has no hold-status signal (rule_13 UNGROUNDED); no verdict produced ({facts[0].file_id} {facts[0].locator})")
                continue
            if cat == "UNKNOWN":
                self.issues.add(f"[UNKNOWN_CLASSIFICATION] '{rid}' (system '{sys_id}') unmapped category; no verdict produced ({facts[0].file_id} {facts[0].locator})")
                continue

            latest = max(f.captured_at for f in facts)
            top = [f for f in facts if f.captured_at == latest]
            top.sort(key=lambda f: (_STATE_PRIORITY.get(f.state, 9), f.file_id, f.locator))
            win = top[0]
            conflicts = []
            if len({f.state for f in top}) > 1:
                conflicts = [{"source": f"{f.file_id}:{f.locator}", "state": f.state} for f in top]
            rule = "topology_residue_any_copy" if conflicts and win.state in ("PRESENT", "ACTIVE") else "latest_usable_fact"
            states.append(ResourceState(
                system_id=win.system_id if win.system_id != "unknown_service" else sys_id,
                resource_id=rid,
                state=win.state,
                data_category=cat,
                cited_evidence_id=win.file_id,
                file_id=win.file_id,
                locator=win.locator,
                supporting_facts=[{"file_id": f.file_id, "locator": f.locator, "state": f.state} for f in top],
                conflicts=conflicts,
                resolution_rule=rule,
            ))
        return states
