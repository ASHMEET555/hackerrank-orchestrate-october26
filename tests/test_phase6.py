"""Phase 6 tests: topology rule on evidence-derived state, and per-case failure isolation."""
import sys
from pathlib import Path
from datetime import datetime, timezone

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "code"))

from identity import IdentityResolver
from main import process_case
from rules_engine import PolicyEngine
from state_reconstructor import ResourceState, StateReconstructor
from timeutil import parse_iso


def test_topology_residue_in_any_copy_counts_present():
    """Same-timestamp facts: failover PRESENT + primary ABSENT => PRESENT (residue in any copy)."""
    from readers.base import EvidenceFact
    t = datetime(2026, 9, 2, 23, 0, tzinfo=timezone.utc)
    rec = StateReconstructor(root / "dataset")
    rec.fact_by_token = {}
    mk = lambda st, loc: EvidenceFact(file_id="evidence_x", system_id="account_service", resource_id="account_777",
                                      state=st, captured_at=t, data_category="USER_PROFILE", locator=loc,
                                      attributes={"user_id": "user_777"}, text_snippet="")
    rec.fact_by_token["user_777"] = [mk("ABSENT", "table customer_profiles_primary"), mk("PRESENT", "table customer_profiles_failover_replica")]
    subj = type("S", (), {"user_id": "user_777", "aliases": []})()
    states = rec.reconstruct_for_case("any", subj, parse_iso("2026-09-03T00:00:00Z"))
    s = states[0]
    assert s.state == "PRESENT" and s.resolution_rule == "topology_residue_any_copy"
    assert s.locator == "table customer_profiles_failover_replica" and s.file_id == "evidence_x"
    assert not PolicyEngine().evaluate_resource(s).is_compliant


def test_no_evidence_after_cutoff_is_used():
    from readers.base import EvidenceFact
    rec = StateReconstructor(root / "dataset")
    rec.fact_by_token = {"user_777": [EvidenceFact(file_id="e", system_id="account_service", resource_id="account_777", state="PRESENT",
                                                   captured_at=datetime(2026, 9, 5, tzinfo=timezone.utc), data_category="USER_PROFILE",
                                                   locator="line 1", attributes={}, text_snippet="")]}
    subj = type("S", (), {"user_id": "user_777", "aliases": []})()
    assert rec.reconstruct_for_case("any", subj, parse_iso("2026-09-03T00:00:00Z")) == []


def test_failure_isolation_and_idempotent_sink():
    class Boom:
        def resolve(self, email, audit_at):
            raise RuntimeError("injected")
    row = {"case_id": "c_fault", "email": "x@y.z", "requested_at": "2026-01-01T00:00:00Z", "reported_at": "2026-01-02T00:00:00Z",
           "audit_at": "2026-01-03T00:00:00Z", "request_text": "Please delete my account data."}
    sink = set()
    for _ in range(2):
        cid, status, steps = process_case(row, Boom(), None, PolicyEngine(), failures=sink)
    assert (cid, status, steps) == ("c_fault", "INCOMPLETE", [])
    assert sink == {"[CASE_ERROR] c_fault: injected"}  # deduplicated
