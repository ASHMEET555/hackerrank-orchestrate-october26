"""Unit tests for Phase 5 intent and identity modules."""

import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest

code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from intent import classify_intent
from identity import IdentityResolver, normalize_email, AliasRecord
from timeutil import parse_iso


def test_intent_multilingual_and_edge_phrasing_variants():
    """G5.1: tests at least 15 phrasing variants (multilingual, mixed, negated, access-only, marketing-only)."""
    # 1. Standard English deletion
    label, _ = classify_intent("Please delete my account and personal data.")
    assert label == "ERASURE"

    # 2. English erasure
    label, _ = classify_intent("I would like the account associated with this address to be erased.")
    assert label == "ERASURE"

    # 3. German deletion (löschen)
    label, _ = classify_intent("Bitte löschen Sie alle meine personenbezogenen Daten und mein Konto.")
    assert label == "ERASURE"

    # 4. French deletion (supprimer / suppression)
    label, _ = classify_intent("Je demande la suppression définitive de mon compte et de mes données personnelles.")
    assert label == "ERASURE"

    # 5. Spanish deletion (eliminar / eliminación)
    label, _ = classify_intent("Solicito la eliminación permanente de la cuenta asociada a este correo.")
    assert label == "ERASURE"

    # 6. Portuguese deletion (exclusão)
    label, _ = classify_intent("Solicito a exclusão permanente da conta associada a este e-mail.")
    assert label == "ERASURE"

    # 7. Japanese deletion (削除 / 消去)
    label, _ = classify_intent("私のアカウントと個人データを完全に削除してください。")
    assert label == "ERASURE"

    # 8. Korean deletion (삭제)
    label, _ = classify_intent("제 계정과 개인정보를 완전히 삭제해 주시기 바랍니다.")
    assert label == "ERASURE"

    # 9. RTBF / Right to be forgotten
    label, _ = classify_intent("I am exercising my right to be forgotten under GDPR.")
    assert label == "ERASURE"

    # 10. Account closure with wipe
    label, _ = classify_intent("Close my account and wipe all database records.")
    assert label == "ERASURE"

    # 11. Negated deletion / leave active (Non-deletion)
    label, _ = classify_intent("The mobile number on my profile is out of date. Please replace it with the new one and leave the account active.")
    assert label == "NON_DELETION"

    # 12. Marketing opt-out only (Non-deletion)
    label, _ = classify_intent("Please stop the promotional emails. I still need the account and my order history, so I am not asking for deletion.")
    assert label == "NON_DELETION"

    # 13. Data export / portability (Non-deletion)
    label, _ = classify_intent("I'd like to download my account information in a portable format. Please keep the account as it is.")
    assert label == "NON_DELETION"

    # 14. Access request / copy of invoices (Non-deletion)
    label, _ = classify_intent("I need a copy of last year's invoices for my records. Please leave my profile and purchase history in place.")
    assert label == "NON_DELETION"

    # 15. Correction / rectification only (Non-deletion)
    label, _ = classify_intent("My surname is misspelled on the account. Can you correct it without removing any of my records?")
    assert label == "NON_DELETION"

    # 16. Login help (Non-deletion)
    label, _ = classify_intent("I can't access my profile and need help resetting the login. Do not close the account.")
    assert label == "NON_DELETION"


def test_identity_resolution_sample_cases():
    resolver = IdentityResolver(Path("dataset"))

    # Case 10: historical email requiring audit log resolution
    subj_10, res_10 = resolver.resolve("nadia.ionescu@yahoo.com", parse_iso("2026-09-17T22:30:00Z"))
    assert res_10 == "RESOLVED"
    assert subj_10.user_id == "user_10"
    assert any(a.value == "n.petrescu@yahoo.com" for a in subj_10.aliases)
    assert any(a.value == "nadia.ionescu@yahoo.com" for a in subj_10.aliases)

    # Case 01: current email direct resolution
    subj_01, res_01 = resolver.resolve("amina.elmasri@gmail.com", parse_iso("2026-09-03T11:30:00Z"))
    assert res_01 == "RESOLVED"
    assert subj_01.user_id == "user_01"

    # Case 12: historical email with audit change
    subj_12, res_12 = resolver.resolve("minjun.kim@gmail.com", parse_iso("2026-09-17T14:15:00Z"))
    assert res_12 == "RESOLVED"
    assert subj_12.user_id == "user_12"


def test_identity_edge_cases():
    resolver = IdentityResolver(Path("dataset"))

    # Case-fold variant resolution
    subj, res = resolver.resolve("Amina.ElMasri@Gmail.COM")
    assert res == "RESOLVED"
    assert subj.user_id == "user_01"

    # Email that appears in audit log ONLY AFTER audit_at must not resolve
    # audit_121 occurred at 2025-12-13T08:17:43Z. If cutoff is 2025-01-01, it must not resolve via that event.
    subj_early, res_early = resolver.resolve("nadia.ionescu@yahoo.com", parse_iso("2025-01-01T00:00:00Z"))
    assert subj_early is None
    assert "Unresolved" in res_early

    # Non-existent email
    subj_none, res_none = resolver.resolve("does.not.exist@nowhere.com")
    assert subj_none is None
    assert "Unresolved" in res_none


def test_reassigned_email_with_overlapping_windows_returns_ambiguous():
    """Test fixture: email reassigned to second user with overlapping or conflicting claims returns AMBIGUOUS."""
    resolver = IdentityResolver(Path("dataset"))
    
    # Inject synthetic decoy: email 'shared.decoy@example.com' belonging to both user_991 and user_992 in audit entries
    conflict_time = parse_iso("2026-05-01T10:00:00Z")
    audit_at = parse_iso("2026-06-01T10:00:00Z")
    
    resolver.audit_entries.append({
        "audit_id": "audit_synthetic_1",
        "user_id": "user_991",
        "event_time": conflict_time,
        "field_name": "email",
        "old_value": "user991.original@example.com",
        "new_value": "shared.decoy@example.com",
    })
    resolver.audit_entries.append({
        "audit_id": "audit_synthetic_2",
        "user_id": "user_992",
        "event_time": conflict_time,
        "field_name": "email",
        "old_value": "shared.decoy@example.com",
        "new_value": "user992.updated@example.com",
    })
    
    subj, note = resolver.resolve("shared.decoy@example.com", audit_at=audit_at)
    assert subj is None
    assert "Ambiguous" in note
    assert "user_991" in note and "user_992" in note
