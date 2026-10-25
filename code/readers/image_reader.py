"""PNG visual read loader and image metadata handler."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

import sys
from pathlib import Path

# Relative/local import to avoid shadowing stdlib 'code'
readers_dir = Path(__file__).resolve().parent
if str(readers_dir) not in sys.path:
    sys.path.insert(0, str(readers_dir))

from base import EvidenceFact


# Ground truth visual reads transcribed directly from manual visual inspection
# of the 11 PNG files under dataset/evidence/images/ (Decision B1/B2, recorded in EVIDENCE_CATALOG.md)
PNG_VISUAL_TRANSCRIPTIONS: Dict[str, Dict[str, Any]] = {
    "evidence_04": {
        "description": "Admin dashboard screenshot for customer lookup",
        "transcription": "Customer account lookup: status=ACTIVE, email=jonas.berg@outlook.com, system=account_service",
        "facts": [
            ("account_service", "account_006", "PRESENT", "USER_PROFILE")
        ]
    },
    "evidence_09": {
        "description": "Customer handover screenshot",
        "transcription": "Support attachment CS-4827 active in queue",
        "facts": [
            ("support_platform", "support_001", "PRESENT", "SUPPORT_ATTACHMENT")
        ]
    },
    "evidence_14": {
        "description": "Export service UI download screen",
        "transcription": "customer_export_001.zip available for download",
        "facts": [
            ("export_service", "export_001", "PRESENT", "USER_EXPORT")
        ]
    },
    "evidence_19": {
        "description": "Search index admin console",
        "transcription": "Index customer_directory_v3 shard 4: hit search_052",
        "facts": [
            ("search_service", "search_052", "PRESENT", "SEARCH_INDEX_ENTRY")
        ]
    },
    "evidence_23": {
        "description": "Connector bridge status dashboard",
        "transcription": "Integration connector data_flow_9522 status: ACTIVE",
        "facts": [
            ("integration_service", "data_flow_9522", "ACTIVE", "DATA_FLOW")
        ]
    },
    "evidence_28": {
        "description": "Backup archive console",
        "transcription": "Archive snapshot backup_3870 restore_eligible=true deletion_block=false",
        "facts": [
            ("backup_service", "backup_3870", "ACTIVE", "BACKUP_ARCHIVE")
        ]
    },
    "evidence_32": {
        "description": "Identity service tombstone inspection UI",
        "transcription": "tombstone_9178 name='Kofi Addo' email='addo.kofi@gmail.com' direct PII exposed",
        "facts": [
            ("identity_service", "tombstone_9178", "PRESENT", "ACCOUNT_TOMBSTONE")
        ]
    },
    "evidence_37": {
        "description": "Analytics audience segment explorer",
        "transcription": "audience_cohort=general_shopper customer_reference=null anonymized",
        "facts": [
            ("analytics_platform", "analytics_9406", "ANONYMIZED", "ANALYTICS_PROFILE")
        ]
    },
    "evidence_42": {
        "description": "Support ticket redaction verification screen",
        "transcription": "support_4715 ticket CS-8715 message=[REDACTED] requester_email=null",
        "facts": [
            ("support_platform", "support_4715", "REDACTED", "SUPPORT_MESSAGE")
        ]
    },
    "evidence_46": {
        "description": "Security audit log reader",
        "transcription": "audit_record_2016 retention_until=2034-09-30T23:59:59Z verified retained",
        "facts": [
            ("security_service", "audit_record_2016", "PRESENT", "SECURITY_AUDIT_LOG")
        ]
    },
    "evidence_60": {
        "description": "Database replica drift monitor",
        "transcription": "Failover replica out of sync: account_005 still active",
        "facts": [
            ("account_service", "account_005", "PRESENT", "USER_PROFILE")
        ]
    },
}


class PngImageReader:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def get_image_info(self) -> Dict[str, Any]:
        with Image.open(self.file_path) as img:
            return {"format": img.format, "size": img.size, "mode": img.mode}

    def extract_facts(self, file_id: str, captured_at: datetime) -> List[EvidenceFact]:
        info = PNG_VISUAL_TRANSCRIPTIONS.get(file_id)
        if not info:
            return []

        facts: List[EvidenceFact] = []
        for sys_id, res_id, state, cat in info["facts"]:
            facts.append(EvidenceFact(
                file_id=file_id,
                system_id=sys_id,
                resource_id=res_id,
                state=state,
                captured_at=captured_at,
                data_category=cat,
                locator="visual_inspection",
                text_snippet=info["transcription"],
            ))
        return facts
