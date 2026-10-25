"""PDF document text extraction using PyMuPDF (fitz) or pdftotext."""

import re
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

import fitz  # PyMuPDF

import sys
from pathlib import Path

readers_dir = Path(__file__).resolve().parent
if str(readers_dir) not in sys.path:
    sys.path.insert(0, str(readers_dir))

from base import EvidenceFact


class PdfDocumentReader:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def extract_text(self) -> List[Tuple[int, str]]:
        """Extracts text per page as (page_number_1_based, page_text)."""
        pages: List[Tuple[int, str]] = []
        doc = fitz.open(self.file_path)
        for idx in range(len(doc)):
            page = doc[idx]
            text = page.get_text()
            pages.append((idx + 1, text))
        doc.close()
        return pages

    def total_char_count(self) -> int:
        pages = self.extract_text()
        return sum(len(text) for _, text in pages)

    def extract_facts(self, file_id: str, captured_at: datetime) -> List[EvidenceFact]:
        facts: List[EvidenceFact] = []
        pages = self.extract_text()

        for page_no, text in pages:
            # Look for resource_ids (e.g. support_001, account_007, etc.)
            res_matches = re.findall(r"\b([a-z0-9_]+_\d+)\b", text)
            for res_id in set(res_matches):
                sys_id = "unknown_service"
                cat = "UNKNOWN"
                state = "PRESENT"
                if res_id.startswith("support_"):
                    sys_id = "support_platform"
                    cat = "SUPPORT_ATTACHMENT"
                elif res_id.startswith("account_"):
                    sys_id = "account_service"
                    cat = "USER_PROFILE"

                facts.append(EvidenceFact(
                    file_id=file_id,
                    system_id=sys_id,
                    resource_id=res_id,
                    state=state,
                    captured_at=captured_at,
                    data_category=cat,
                    locator=f"page {page_no}",
                    text_snippet=text[:200],
                ))

        return facts
