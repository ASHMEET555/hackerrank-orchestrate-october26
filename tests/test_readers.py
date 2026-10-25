"""Unit tests for Phase 4 evidence readers and index."""

import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest

code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

readers_dir = code_dir / "readers"
if str(readers_dir) not in sys.path:
    sys.path.insert(0, str(readers_dir))

from loaders import ManifestLoader, ManifestSecurityError, resolve_safe_path
from base import EvidenceFact
from image_reader import PngImageReader
from pdf_reader import PdfDocumentReader
from sql_reader import SqlSnapshotReader
from text_reader import TextLogJsonReader
from evidence_index import EvidenceIndex


def test_manifest_path_traversal_protection(tmp_path):
    safe_base = tmp_path / "dataset"
    safe_base.mkdir()

    # Valid safe path
    resolved = resolve_safe_path(safe_base, "evidence/test.json")
    assert resolved == (safe_base / "evidence" / "test.json").resolve()

    # Traversal attempts must raise ManifestSecurityError
    with pytest.raises(ManifestSecurityError):
        resolve_safe_path(safe_base, "../../../etc/passwd")

    with pytest.raises(ManifestSecurityError):
        resolve_safe_path(safe_base, "..\\..\\windows\\system32")


def test_sql_reader_introspection():
    sql_path = Path("dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql")
    reader = SqlSnapshotReader(sql_path)
    tables = reader.get_tables()
    assert "customer_profiles_failover_replica" in tables
    assert "customer_profiles_primary" in tables

    facts = reader.extract_facts("evidence_54", datetime.now(timezone.utc))
    assert len(facts) > 0
    assert any(f.resource_id == "account_005" for f in facts)


def test_pdf_reader_text_and_facts():
    pdf_path = Path("dataset/evidence/documents/delivery_correction_attachment.pdf")
    reader = PdfDocumentReader(pdf_path)
    char_count = reader.total_char_count()
    assert char_count > 500

    facts = reader.extract_facts("evidence_58", datetime.now(timezone.utc))
    assert len(facts) > 0
    assert any("support_001" in f.resource_id for f in facts)


def test_text_and_json_reader():
    json_path = Path("dataset/evidence/records/service_resource_export_20260915_114455.json")
    reader = TextLogJsonReader(json_path)
    facts = reader.extract_facts("evidence_92", datetime.now(timezone.utc))
    assert len(facts) > 0
    assert any(f.resource_id == "account_6440" for f in facts)


def test_png_image_reader():
    png_path = Path("dataset/evidence/images/account_admin_console_20260926.png")
    reader = PngImageReader(png_path)
    info = reader.get_image_info()
    assert info["format"] == "PNG"

    facts = reader.extract_facts("evidence_04", datetime.now(timezone.utc))
    assert len(facts) > 0
    assert facts[0].resource_id == "account_006"


def test_evidence_index_caching(tmp_path):
    idx = EvidenceIndex(Path("dataset"), cache_dir=tmp_path / "cache")
    facts1, hits1 = idx.build()
    assert facts1 > 0
    assert hits1 == 0

    facts2, hits2 = idx.build()
    assert facts2 == facts1
    assert hits2 == 94
