"""Text, JSON, and log evidence reader."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import sys
from pathlib import Path

readers_dir = Path(__file__).resolve().parent
if str(readers_dir) not in sys.path:
    sys.path.insert(0, str(readers_dir))

from base import EvidenceFact


class TextLogJsonReader:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def extract_facts(self, file_id: str, captured_at: datetime) -> List[EvidenceFact]:
        ext = self.file_path.suffix.lower()
        if ext == ".json":
            return self._extract_json(file_id, captured_at)
        else:
            return self._extract_text_or_log(file_id, captured_at)

    def _extract_text_or_log(self, file_id: str, captured_at: datetime) -> List[EvidenceFact]:
        facts: List[EvidenceFact] = []
        try:
            content = self.file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return facts

        lines = content.splitlines()
        for line_no, line in enumerate(lines, start=1):
            # Check structured line patterns
            # e.g.: - 2026-10-01T12:00:00Z | account_service | account_4248 | USER_PROFILE | NOT_FOUND | novak.tomasz@icloud.com
            pipe_parts = [p.strip() for p in line.split("|")]
            if len(pipe_parts) >= 5 and any(sys in pipe_parts[1] for sys in ("account_service", "search_service", "analytics_platform", "support_platform", "integration_service", "backup_service", "security_service")):
                sys_id = pipe_parts[1]
                res_id = pipe_parts[2]
                cat = pipe_parts[3]
                raw_state = pipe_parts[4]
                state = "PRESENT"
                if raw_state in ("NOT_FOUND", "ABSENT"):
                    state = "ABSENT"
                elif raw_state in ("ACTIVE", "FOUND", "IDENTIFIABLE"):
                    state = "ACTIVE" if cat in ("DATA_FLOW", "BACKUP_ARCHIVE") else "PRESENT"
                elif raw_state == "ANONYMIZED":
                    state = "ANONYMIZED"
                elif raw_state == "REDACTED":
                    state = "REDACTED"
                elif raw_state in ("DISABLED", "STOPPED"):
                    state = "DISABLED"
                elif raw_state == "BLOCKED":
                    state = "BLOCKED"

                facts.append(EvidenceFact(
                    file_id=file_id,
                    system_id=sys_id,
                    resource_id=res_id,
                    state=state,
                    captured_at=captured_at,
                    data_category=cat,
                    locator=f"line {line_no}",
                    text_snippet=line,
                ))
                continue

            # Standard log key-value lines
            # resource_id=xxx or resource_id="xxx"
            m_res = re.search(r'\bresource_id=["\']?([a-z0-9_]+)["\']?', line)
            if m_res:
                res_id = m_res.group(1)
                m_sys = re.search(r'\b(?:system|service)=["\']?([a-z0-9_]+)["\']?', line)
                sys_id = m_sys.group(1) if m_sys else "unknown_service"

                state = "PRESENT"
                m_res_state = re.search(r'\bresult=["\']?([a-z0-9_]+)["\']?', line, re.IGNORECASE)
                if m_res_state:
                    r_val = m_res_state.group(1).upper()
                    if r_val in ("NOT_FOUND", "ABSENT"):
                        state = "ABSENT"
                    elif r_val in ("FOUND", "PRESENT", "IDENTIFIABLE"):
                        state = "PRESENT"
                    elif r_val in ("ANONYMIZED", "REDACTED", "DISABLED", "BLOCKED", "ACTIVE"):
                        state = r_val

                if 'rows="0"' in line or "rows=0" in line or 'http_status="404"' in line or "http_status=404" in line:
                    state = "ABSENT"
                elif 'enabled="true"' in line or "enabled=true" in line:
                    state = "ACTIVE"
                elif 'enabled="false"' in line or "enabled=false" in line or "stopped" in line:
                    state = "DISABLED"
                elif 'restore_allowed="false"' in line or "restore_allowed=false" in line or 'deletion_block="true"' in line or "deletion_block=true" in line:
                    state = "BLOCKED"
                elif 'eligible="true"' in line and ('deletion_block="false"' in line or "deletion_block=false" in line):
                    state = "ACTIVE"

                cat = "UNKNOWN"
                m_cat = re.search(r'\brecord_type=["\']?([a-z0-9_]+)["\']?', line)
                if m_cat:
                    cat = m_cat.group(1)
                elif res_id.startswith("account_"):
                    sys_id = "account_service"
                    cat = "USER_PROFILE"
                elif res_id.startswith("search_"):
                    sys_id = "search_service"
                    cat = "SEARCH_INDEX_ENTRY"
                elif res_id.startswith("analytics_"):
                    sys_id = "analytics_platform"
                    cat = "MARKETING_PROFILE" if "email_opt_in" in line else "ANALYTICS_PROFILE"
                elif res_id.startswith("support_"):
                    sys_id = "support_platform"
                    cat = "SUPPORT_MESSAGE"
                elif res_id.startswith("data_flow_"):
                    sys_id = "integration_service"
                    cat = "DATA_FLOW"
                elif res_id.startswith("backup_"):
                    sys_id = "backup_service"
                    cat = "BACKUP_ARCHIVE"
                elif res_id.startswith("audit_record_"):
                    sys_id = "security_service"
                    cat = "SECURITY_AUDIT_LOG"

                facts.append(EvidenceFact(
                    file_id=file_id,
                    system_id=sys_id,
                    resource_id=res_id,
                    state=state,
                    captured_at=captured_at,
                    data_category=cat,
                    locator=f"line {line_no}",
                    text_snippet=line,
                ))

        return facts

    def _extract_json(self, file_id: str, captured_at: datetime) -> List[EvidenceFact]:
        facts: List[EvidenceFact] = []
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return facts

        # Walk JSON looking for resource_id
        def walk(obj, path=""):
            if isinstance(obj, dict):
                if "resource_id" in obj:
                    res_id = obj["resource_id"]
                    if res_id:
                        sys_id = "unknown_service"
                        cat = "UNKNOWN"
                        state = "PRESENT"
                        if res_id.startswith("account_"):
                            sys_id = "account_service"
                            cat = "USER_PROFILE"
                            if obj.get("status_code") == 404 or obj.get("profile") is None:
                                state = "ABSENT"
                        elif res_id.startswith("search_"):
                            sys_id = "search_service"
                            cat = "SEARCH_INDEX_ENTRY"
                        elif res_id.startswith("analytics_"):
                            sys_id = "analytics_platform"
                            cat = "ANALYTICS_PROFILE"
                            if not obj.get("email") and not obj.get("phone") and not obj.get("customer_reference"):
                                state = "ANONYMIZED"
                        elif res_id.startswith("support_"):
                            sys_id = "support_platform"
                            cat = "SUPPORT_MESSAGE"
                            if not obj.get("requester_email") and not obj.get("requester_phone"):
                                state = "REDACTED"
                        elif res_id.startswith("export_"):
                            sys_id = "export_service"
                            cat = "USER_EXPORT"
                        elif res_id.startswith("data_flow_"):
                            sys_id = "integration_service"
                            cat = "DATA_FLOW"
                            state = "ACTIVE" if obj.get("enabled") is True else "DISABLED"
                        elif res_id.startswith("backup_"):
                            sys_id = "backup_service"
                            cat = "BACKUP_ARCHIVE"
                            state = "ACTIVE" if obj.get("restore_allowed") is True else "BLOCKED"
                        elif res_id.startswith("audit_record_"):
                            sys_id = "security_service"
                            cat = "SECURITY_AUDIT_LOG"
                        elif res_id.startswith("tombstone_"):
                            sys_id = "identity_service"
                            cat = "ACCOUNT_TOMBSTONE"
                            if obj.get("email") or obj.get("phone") or obj.get("name"):
                                state = "PRESENT"
                            else:
                                state = "REDACTED"

                        facts.append(EvidenceFact(
                            file_id=file_id,
                            system_id=sys_id,
                            resource_id=res_id,
                            state=state,
                            captured_at=captured_at,
                            data_category=cat,
                            locator=path,
                            attributes=obj,
                        ))
                for k, v in obj.items():
                    walk(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")

        walk(data, "$")
        return facts
