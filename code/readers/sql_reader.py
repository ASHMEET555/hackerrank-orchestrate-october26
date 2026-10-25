"""SQL snapshot reader with in-memory SQLite introspection."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

import sys
from pathlib import Path

readers_dir = Path(__file__).resolve().parent
if str(readers_dir) not in sys.path:
    sys.path.insert(0, str(readers_dir))

from base import EvidenceFact


class SqlSnapshotReader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self._load()

    def _load(self):
        sql = self.file_path.read_text(encoding="utf-8", errors="replace")
        self.conn.executescript(sql)

    def get_tables(self) -> List[str]:
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        return [r[0] for r in cur.fetchall()]

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        cur = self.conn.execute(f"PRAGMA table_info({table_name})")
        return [{"cid": r[0], "name": r[1], "type": r[2]} for r in cur.fetchall()]

    def extract_facts(self, file_id: str, captured_at: datetime) -> List[EvidenceFact]:
        facts: List[EvidenceFact] = []
        tables = self.get_tables()

        for t in tables:
            if t == "snapshot_scope":
                continue
            cur = self.conn.execute(f"SELECT * FROM {t}")
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                res_id = r.get("resource_id", "")
                if not res_id:
                    continue
                # Determine system and state
                sys_id = "unknown_service"
                state = "PRESENT"
                cat = "UNKNOWN"

                if "customer_profiles" in t:
                    sys_id = "account_service"
                    cat = "USER_PROFILE"
                    state = "PRESENT"
                elif "search_documents" in t or "customer_search" in t:
                    sys_id = "search_service"
                    cat = "SEARCH_INDEX_ENTRY"
                    state = "PRESENT"
                elif "analytics_profiles" in t:
                    sys_id = "analytics_platform"
                    cat = "ANALYTICS_PROFILE"
                    # Check if identifiable
                    if r.get("email") or r.get("phone") or r.get("customer_reference"):
                        state = "PRESENT"
                    else:
                        state = "ANONYMIZED"
                elif "support_records" in t:
                    sys_id = "support_platform"
                    cat = "SUPPORT_MESSAGE"
                    state = "PRESENT"
                elif "customer_exports" in t:
                    sys_id = "export_service"
                    cat = "USER_EXPORT"
                    state = "PRESENT"
                elif "connector_subscriptions" in t:
                    sys_id = "integration_service"
                    cat = "DATA_FLOW"
                    enabled = r.get("enabled", 0)
                    state = "ACTIVE" if enabled == 1 else "DISABLED"
                elif "backup_restore_entries" in t:
                    sys_id = "backup_service"
                    cat = "BACKUP_ARCHIVE"
                    allowed = r.get("restore_allowed", 0)
                    state = "ACTIVE" if allowed == 1 else "BLOCKED"
                elif "security_audit_records" in t:
                    sys_id = "security_service"
                    cat = "SECURITY_AUDIT_LOG"
                    state = "PRESENT"

                facts.append(EvidenceFact(
                    file_id=file_id,
                    system_id=sys_id,
                    resource_id=res_id,
                    state=state,
                    captured_at=captured_at,
                    data_category=cat,
                    locator=f"table {t}",
                    attributes=r,
                ))

        return facts
