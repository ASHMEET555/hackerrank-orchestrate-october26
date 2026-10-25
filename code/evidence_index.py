"""Evidence index with SHA-256 caching and multi-reader dispatch."""

import hashlib
import json
import sqlite3
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

readers_dir = code_dir / "readers"
if str(readers_dir) not in sys.path:
    sys.path.insert(0, str(readers_dir))

from loaders import EvidenceFileEntry, ManifestLoader
from readers.base import EvidenceFact
from readers.image_reader import PngImageReader
from readers.pdf_reader import PdfDocumentReader
from readers.sql_reader import SqlSnapshotReader
from readers.text_reader import TextLogJsonReader
from timeutil import format_iso, parse_iso


def compute_file_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class EvidenceIndex:
    def __init__(self, dataset_dir: Union[Path, str], cache_dir: Optional[Union[Path, str]] = None):
        self.dataset_dir = Path(dataset_dir).resolve()
        default_cache = Path(dataset_dir).parent / "code" / ".cache" / "evidence_index"
        self.cache_dir = Path(cache_dir or default_cache).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_loader = ManifestLoader(self.dataset_dir)
        self.facts: List[EvidenceFact] = []
        self.file_stats: Dict[str, Dict[str, Any]] = {}
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    def build(self) -> Tuple[int, int]:
        """Builds index across all manifest files. Returns (total_facts, cache_hits)."""
        entries = self.manifest_loader.all_entries()
        self.facts = []
        self.cache_hits = 0
        self.cache_misses = 0

        for entry in entries:
            file_id = entry.file_id
            abs_path = entry.absolute_path
            sha = compute_file_sha256(abs_path)
            cache_file = self.cache_dir / f"{file_id}_{sha}.json"

            file_facts: List[EvidenceFact] = []
            no_content_reason = ""

            if cache_file.exists():
                self.cache_hits += 1
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                    for item in cached_data["facts"]:
                        file_facts.append(EvidenceFact(
                            file_id=item["file_id"],
                            system_id=item["system_id"],
                            resource_id=item["resource_id"],
                            state=item["state"],
                            captured_at=parse_iso(item["captured_at"]),
                            data_category=item.get("data_category", "UNKNOWN"),
                            locator=item.get("locator", ""),
                            attributes=item.get("attributes", {}),
                            text_snippet=item.get("text_snippet", ""),
                        ))
                    no_content_reason = cached_data.get("no_content_reason", "")
                except Exception:
                    file_facts = []

            if not file_facts and not cache_file.exists():
                self.cache_misses += 1
                ext = abs_path.suffix.lower()
                try:
                    if ext == ".sql":
                        reader = SqlSnapshotReader(abs_path)
                        file_facts = reader.extract_facts(file_id, entry.captured_at)
                    elif ext == ".pdf":
                        reader = PdfDocumentReader(abs_path)
                        file_facts = reader.extract_facts(file_id, entry.captured_at)
                    elif ext == ".png":
                        reader = PngImageReader(abs_path)
                        file_facts = reader.extract_facts(file_id, entry.captured_at)
                    elif ext in (".log", ".json", ".txt"):
                        reader = TextLogJsonReader(abs_path)
                        file_facts = reader.extract_facts(file_id, entry.captured_at)
                except Exception as e:
                    no_content_reason = f"Parse error: {e}"

                if not file_facts and not no_content_reason:
                    no_content_reason = "No extractable identifiers or resources found"

                # Save to cache
                cache_payload = {
                    "file_id": file_id,
                    "sha256": sha,
                    "no_content_reason": no_content_reason,
                    "facts": [
                        {
                            "file_id": f.file_id,
                            "system_id": f.system_id,
                            "resource_id": f.resource_id,
                            "state": f.state,
                            "captured_at": format_iso(f.captured_at),
                            "data_category": f.data_category,
                            "locator": f.locator,
                            "attributes": f.attributes,
                            "text_snippet": f.text_snippet,
                        }
                        for f in file_facts
                    ],
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_payload, f)

            self.file_stats[file_id] = {
                "format": abs_path.suffix.lower(),
                "facts_count": len(file_facts),
                "no_content_reason": no_content_reason,
            }
            self.facts.extend(file_facts)

        return len(self.facts), self.cache_hits

    def get_facts_for_case(self, resource_ids: List[str], audit_at: Optional[datetime]) -> Tuple[List[EvidenceFact], List[EvidenceFact]]:
        """Returns (usable_facts, excluded_facts) for the given resource_ids relative to audit_at."""
        res_set = set(resource_ids)
        usable = []
        excluded = []
        for f in self.facts:
            if f.resource_id in res_set:
                if f.is_usable_at(audit_at):
                    usable.append(f)
                else:
                    excluded.append(f)
        return usable, excluded
