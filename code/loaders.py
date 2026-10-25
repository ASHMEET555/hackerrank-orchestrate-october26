"""Manifest and evidence file loader with strict path-traversal prevention."""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from timeutil import parse_iso


@dataclass(frozen=True)
class EvidenceFileEntry:
    file_id: str
    file_path: str
    origin: str
    captured_at: datetime
    absolute_path: Path


class ManifestSecurityError(Exception):
    """Raised when an evidence file entry fails security or directory traversal checks."""
    pass


class ManifestLoader:
    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir.resolve()
        self.evidence_dir = (self.dataset_dir / "evidence").resolve()
        self.manifest_path = (self.dataset_dir / "evidence_files.csv").resolve()
        self.entries: Dict[str, EvidenceFileEntry] = {}
        self._load()

    def _load(self):
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        with open(self.manifest_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row["file_id"]
                rel_path = row["file_path"].strip()
                origin = row.get("origin", "")
                cap_str = row.get("captured_at", "")
                cap_dt = parse_iso(cap_str)
                if not cap_dt:
                    raise ValueError(f"Invalid captured_at '{cap_str}' for file_id {fid}")

                # Path traversal check
                # Normalize relative path: remove leading slashes or 'evidence/' prefixes if present
                clean_rel = rel_path.replace("\\", "/").lstrip("/")
                if clean_rel.startswith("evidence/"):
                    clean_rel = clean_rel[len("evidence/"):]

                resolved_path = (self.evidence_dir / clean_rel).resolve()
                if not resolved_path.is_relative_to(self.evidence_dir):
                    raise ManifestSecurityError(f"Path traversal detected in manifest: {rel_path} -> {resolved_path}")

                self.entries[fid] = EvidenceFileEntry(
                    file_id=fid,
                    file_path=rel_path,
                    origin=origin,
                    captured_at=cap_dt,
                    absolute_path=resolved_path,
                )

    def get(self, file_id: str) -> Optional[EvidenceFileEntry]:
        return self.entries.get(file_id)

    def all_entries(self) -> List[EvidenceFileEntry]:
        return list(self.entries.values())


def resolve_safe_path(base_dir: Path, untrusted_rel_path: str) -> Path:
    """Safely resolves an untrusted relative path against base_dir.
    
    Raises ManifestSecurityError if path traverses outside base_dir.
    """
    base = base_dir.resolve()
    clean = untrusted_rel_path.replace("\\", "/").lstrip("/")
    target = (base / clean).resolve()
    if not target.is_relative_to(base):
        raise ManifestSecurityError(f"Path traversal rejected: {untrusted_rel_path}")
    return target
