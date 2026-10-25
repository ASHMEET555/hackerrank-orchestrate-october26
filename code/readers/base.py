"""Fact extraction data structures and base reader."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceFact:
    file_id: str
    system_id: str
    resource_id: str
    state: str
    captured_at: datetime
    data_category: str = "UNKNOWN"
    locator: str = ""  # table name, json path, line number, or page
    attributes: Dict[str, Any] = field(default_factory=dict)
    text_snippet: str = ""

    def is_usable_at(self, audit_at: Optional[datetime]) -> bool:
        if not audit_at:
            return False
        return self.captured_at <= audit_at
