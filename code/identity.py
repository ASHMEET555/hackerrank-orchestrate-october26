"""Subject identity resolution and historical alias chain reconstruction."""

import csv
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from timeutil import parse_iso


def normalize_email(email: str) -> str:
    """Normalizes an email by case-folding and trimming per Decision A4/V4."""
    if not email:
        return ""
    return email.strip().casefold()


@dataclass
class AliasRecord:
    kind: str  # email, phone, email_hash, user_id
    value: str
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source_id: str = ""  # identity row or audit_id
    field_name: str = ""


@dataclass
class SubjectIdentity:
    user_id: str
    current_name: Optional[str]
    current_email: str
    current_phone: Optional[str]
    current_email_hash: Optional[str]
    aliases: List[AliasRecord] = field(default_factory=list)
    resolution_path: List[str] = field(default_factory=list)

    def get_active_aliases_at(self, audit_at: Optional[datetime]) -> List[AliasRecord]:
        """Returns aliases that were valid at or before audit_at."""
        if not audit_at:
            return self.aliases
        valid = []
        for a in self.aliases:
            # If alias was introduced after audit_at, it cannot be used
            if a.valid_from and a.valid_from > audit_at:
                continue
            valid.append(a)
        return valid


class IdentityResolver:
    def __init__(self, dataset_dir: Union[Path, str]):
        self.dataset_dir = Path(dataset_dir).resolve()
        self.identities_path = self.dataset_dir / "user_identities.csv"
        self.audit_log_path = self.dataset_dir / "user_audit_log.csv"

        # Lookups
        self.users: Dict[str, Dict[str, Any]] = {}
        self.email_to_user: Dict[str, str] = {}
        self.audit_entries: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.identities_path.exists():
            with open(self.identities_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    uid = r["user_id"]
                    email_norm = normalize_email(r.get("email", ""))
                    self.users[uid] = {
                        "user_id": uid,
                        "name": r.get("name"),
                        "email": email_norm,
                        "phone": r.get("phone"),
                        "email_hash": r.get("email_hash"),
                        "updated_at": parse_iso(r.get("updated_at")),
                    }
                    if email_norm:
                        self.email_to_user[email_norm] = uid

        if self.audit_log_path.exists():
            with open(self.audit_log_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.audit_entries.append({
                        "audit_id": r["audit_id"],
                        "user_id": r["user_id"],
                        "event_time": parse_iso(r.get("event_time")),
                        "field_name": r.get("field_name"),
                        "old_value": r.get("old_value"),
                        "new_value": r.get("new_value"),
                    })
            # Sort audit entries chronologically
            self.audit_entries.sort(key=lambda x: x["event_time"] or datetime.min)

    def resolve(self, request_email: str, audit_at: Optional[datetime] = None) -> Tuple[Optional[SubjectIdentity], str]:
        """Resolves request_email to a SubjectIdentity with full alias history."""
        req_norm = normalize_email(request_email)
        if not req_norm:
            return None, "Empty email"

        resolved_user_id: Optional[str] = None
        resolution_notes = []

        # 1. Direct match in current user_identities
        if req_norm in self.email_to_user:
            resolved_user_id = self.email_to_user[req_norm]
            resolution_notes.append(f"Direct match in user_identities for user_id={resolved_user_id}")

        # 2. Historical audit search if not found in current snapshot
        if not resolved_user_id:
            # Check audit log for matching old_value or new_value (filtered by audit_at if supplied)
            matching_events = []
            for ev in self.audit_entries:
                if audit_at and ev["event_time"] and ev["event_time"] > audit_at:
                    continue  # Cannot resolve using events that occur after audit cutoff
                if ev["field_name"] == "email":
                    old_norm = normalize_email(ev.get("old_value", ""))
                    new_norm = normalize_email(ev.get("new_value", ""))
                    if req_norm in (old_norm, new_norm):
                        matching_events.append(ev)

            if len(matching_events) == 1:
                resolved_user_id = matching_events[0]["user_id"]
                ev = matching_events[0]
                resolution_notes.append(f"Historical match via audit log {ev['audit_id']} @ {ev['event_time'].isoformat()} for user_id={resolved_user_id}")
            elif len(matching_events) > 1:
                # Check if all events belong to same user_id
                uids = set(e["user_id"] for e in matching_events)
                if len(uids) == 1:
                    resolved_user_id = list(uids)[0]
                    resolution_notes.append(f"Multiple audit log matches for single user_id={resolved_user_id}")
                else:
                    return None, f"Ambiguous: email '{req_norm}' matched multiple user_ids in audit log: {uids}"

        if not resolved_user_id:
            return None, f"Unresolved: email '{req_norm}' not found in current identities or historical audit log"

        # Build alias chain for resolved user
        user_info = self.users.get(resolved_user_id, {
            "user_id": resolved_user_id,
            "name": None,
            "email": "",
            "phone": None,
            "email_hash": None,
            "updated_at": None,
        })

        aliases: List[AliasRecord] = []

        # Current snapshot aliases
        if user_info["email"]:
            aliases.append(AliasRecord(kind="email", value=user_info["email"], valid_from=user_info["updated_at"], source_id="user_identities", field_name="email"))
        if user_info["phone"]:
            aliases.append(AliasRecord(kind="phone", value=user_info["phone"], valid_from=user_info["updated_at"], source_id="user_identities", field_name="phone"))
        if user_info["email_hash"]:
            aliases.append(AliasRecord(kind="email_hash", value=user_info["email_hash"], valid_from=user_info["updated_at"], source_id="user_identities", field_name="email_hash"))

        # User audit history aliases
        user_audits = [e for e in self.audit_entries if e["user_id"] == resolved_user_id]
        for a in user_audits:
            fn = a["field_name"]
            et = a["event_time"]
            aid = a["audit_id"]
            if fn in ("email", "phone", "email_hash"):
                if a["old_value"]:
                    val = normalize_email(a["old_value"]) if fn == "email" else a["old_value"]
                    aliases.append(AliasRecord(kind=fn, value=val, valid_to=et, source_id=aid, field_name=fn))
                if a["new_value"]:
                    val = normalize_email(a["new_value"]) if fn == "email" else a["new_value"]
                    aliases.append(AliasRecord(kind=fn, value=val, valid_from=et, source_id=aid, field_name=fn))

        # Deduplicate aliases by (kind, value)
        seen = set()
        dedup_aliases = []
        for al in aliases:
            key = (al.kind, al.value)
            if key not in seen:
                seen.add(key)
                dedup_aliases.append(al)

        subj = SubjectIdentity(
            user_id=resolved_user_id,
            current_name=user_info["name"],
            current_email=user_info["email"],
            current_phone=user_info["phone"],
            current_email_hash=user_info["email_hash"],
            aliases=dedup_aliases,
            resolution_path=resolution_notes,
        )
        return subj, "RESOLVED"
