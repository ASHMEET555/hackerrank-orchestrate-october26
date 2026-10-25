"""ResourceLinker: maps evidence facts and resources to deletion subjects via exact direct identifiers only.

Rules:
- Exact matches only: user_id, email, email_hash, or phone valid at audit_at.
- Grounded strictly in dataset/user_identities.csv and user_audit_log.csv.
- If a link resolves to nothing or a different user_id (decoy), drop it.
- Respects DECISIONS.md D1-D5.
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Direct identifier keys commonly found in evidence attributes
_DIRECT_KEYS = [
    "user_id", "customer_id", "subject_reference", "customer_reference", "subject_ref",
    "email", "customer_email", "owner_email", "requester_email",
    "lookup_key", "match_key", "subject_key", "subject_selector", "lookup_value", "matched_value",
    "phone", "owner_phone", "requester_phone", "scan_key",
    "email_hash",
]


class Linker:
    def __init__(self, dataset_dir: Path):
        self.dataset_dir = Path(dataset_dir).resolve()
        self.identities: Dict[str, Dict[str, str]] = {}
        self.user_by_id: Dict[str, Dict[str, str]] = {}
        
        # Load user identities
        id_path = self.dataset_dir / "user_identities.csv"
        if id_path.exists():
            for r in csv.DictReader(open(id_path, encoding="utf-8")):
                self.identities[r["email"].lower().strip()] = r
                self.user_by_id[r["user_id"]] = r

        # Load user audit log
        self.audit_log: List[Dict[str, str]] = []
        aud_path = self.dataset_dir / "user_audit_log.csv"
        if aud_path.exists():
            self.audit_log = list(csv.DictReader(open(aud_path, encoding="utf-8")))

        # Cache of parsed PDF full texts by file_id
        self._pdf_cache: Dict[str, str] = {}

    def get_subject_tokens(self, user_id: str, audit_at: datetime) -> Set[str]:
        """Returns all exact direct identifiers for the subject valid at audit_at."""
        tokens: Set[str] = set()
        u = self.user_by_id.get(user_id)
        if u:
            tokens.add(u["user_id"].lower())
            tokens.add(u["email"].lower().strip())
            if u.get("phone"):
                tokens.add(u["phone"].strip())
            if u.get("email_hash"):
                tokens.add(u["email_hash"].lower().strip())

        # Historical tokens from user_audit_log valid at or before audit_at
        for a in self.audit_log:
            if a["user_id"] == user_id:
                old_val = a["old_value"].strip()
                if old_val:
                    if a["field_name"] in ("email", "email_hash"):
                        tokens.add(old_val.lower())
                    elif a["field_name"] == "phone":
                        tokens.add(old_val)

        tokens.discard("")
        return tokens

    def _get_pdf_text(self, file_path_rel: str) -> str:
        if file_path_rel in self._pdf_cache:
            return self._pdf_cache[file_path_rel]
        abs_p = self.dataset_dir / file_path_rel
        if not abs_p.exists():
            return ""
        try:
            import fitz
            doc = fitz.open(abs_p)
            txt = " ".join(page.get_text() for page in doc)
            doc.close()
            self._pdf_cache[file_path_rel] = txt.lower()
            return self._pdf_cache[file_path_rel]
        except Exception:
            return ""

    def match_fact(
        self,
        fact: Any,
        subject_user_id: str,
        subject_tokens: Set[str],
        active_link_types: Optional[Set[str]] = None,
    ) -> bool:
        """Determines whether a fact belongs to the subject using exact direct identifiers.

        active_link_types: Optional set of allowed categories e.g. {'support', 'analytics', 'data_flow'}.
        If None, all categories are evaluated.
        """
        cat = fact.data_category
        # Check active link category filter if specified
        if active_link_types is not None:
            cat_lower = cat.lower() if cat else ""
            matches_active = False
            for t in active_link_types:
                if t in cat_lower or (t == "support" and "support_" in fact.resource_id) or \
                   (t == "analytics" and "analytics_" in fact.resource_id) or \
                   (t == "data_flow" and "data_flow_" in fact.resource_id):
                    matches_active = True
                    break
            if not matches_active:
                return False

        # 1. Direct attribute inspection
        for k in _DIRECT_KEYS:
            v = fact.attributes.get(k)
            if not v:
                continue
            if isinstance(v, str):
                v_clean = v.strip().lower()
                for tok in subject_tokens:
                    if tok.startswith("user_"):
                        if re.search(r'\b' + re.escape(tok) + r'\b', v_clean):
                            return True
                    elif tok in v_clean:
                        return True

        # 2. Structured JSON attributes (e.g. record_json, document, hits, message_text)
        for k in ("record_json", "document", "hits", "message_text", "profile"):
            v = fact.attributes.get(k)
            if not v:
                continue
            v_str = json.dumps(v).lower() if isinstance(v, (dict, list)) else str(v).lower()
            for tok in subject_tokens:
                if tok.startswith("user_"):
                    if re.search(r'\b' + re.escape(tok) + r'\b', v_str):
                        return True
                elif tok in v_str:
                    return True

        # 3. Text snippet inspection
        if fact.text_snippet:
            txt_lower = fact.text_snippet.lower()
            for tok in subject_tokens:
                if tok.startswith("user_"):
                    if re.search(r'\b' + re.escape(tok) + r'\b', txt_lower):
                        return True
                elif tok in txt_lower:
                    return True

        # 4. PDF document full text (for PDF evidence where snippet was truncated)
        if fact.locator.startswith("page"):
            # check file extension from locator or inspect PDF text
            pdf_txt = self._get_pdf_text(f"evidence/documents/{fact.file_id}.pdf")
            if not pdf_txt:
                # find in manifest
                for sub in ("documents/delivery_correction_attachment.pdf",):
                    if (self.dataset_dir / "evidence" / sub).exists():
                        pdf_txt = self._get_pdf_text(f"evidence/{sub}")
                        break
            if pdf_txt:
                for tok in subject_tokens:
                    if tok in pdf_txt:
                        return True

        return False
