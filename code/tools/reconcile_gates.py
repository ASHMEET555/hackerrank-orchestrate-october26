"""reconcile_gates.py — Compares GHOST_DATA_MASTER_PLAN.md gates to PROGRESS.md rows."""

from pathlib import Path

# 15 master gates from GHOST_DATA_MASTER_PLAN.md Sections 6 and 7
PLAN_GATES = [
    ("G-P0", "Phase 0 Gate: Environment, tool inventory & repo hygiene"),
    ("G-P1", "Phase 1 Gate: Contract extraction & data profiling"),
    ("G-P2", "Phase 2 Gate: Spec-from-samples & step rules reproduction"),
    ("G-P3", "Phase 3 Gate: Test harness & validator"),
    ("G-P4", "Phase 4 Gate: Evidence readers & index"),
    ("G-P5", "Phase 5 Gate: Intent classification & identity resolution"),
    ("G-P6", "Phase 6 Gate: State reconstruction & policy engine"),
    ("G-P7", "Phase 7 Gate: Step builder & end-to-end sample evaluation"),
    ("G-P8", "Phase 8 Gate: Generalization & hardening"),
    ("G-P9", "Phase 9 Gate: Reports, packaging & interview prep"),
    ("G-S7.1", "Section 7.1: Unit tests per module"),
    ("G-S7.2", "Section 7.2: Mutation tests"),
    ("G-S7.3", "Section 7.3: Custom evaluation cases"),
    ("G-S7.4", "Section 7.4: Property checks across 518 outputs"),
    ("G-S7.5", "Section 7.5: Cross-check finding-remediation-verification"),
]

# Read PROGRESS.md rows
progress_path = Path("code/notes/PROGRESS.md")
with open(progress_path, "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.startswith("| G-")]

progress_gates = []
for l in lines:
    parts = [p.strip() for p in l.split("|")[1:-1]]
    progress_gates.append((parts[0], parts[1], parts[2], parts[3]))

print(f"Master Plan Gates Count: {len(PLAN_GATES)}")
for gid, name in PLAN_GATES:
    print(f"  {gid:8s} | {name}")

print(f"\nPROGRESS.md Gates Count: {len(progress_gates)}")
for gid, sec, name, status in progress_gates:
    print(f"  {gid:8s} | {sec:12s} | {status:8s} | {name}")

plan_ids = {g[0] for g in PLAN_GATES}
progress_ids = {g[0] for g in progress_gates}

diff_missing_in_progress = plan_ids - progress_ids
diff_extra_in_progress = progress_ids - plan_ids

print(f"\nDiff (Plan - Progress): {diff_missing_in_progress if diff_missing_in_progress else 'None (0 missing)'}")
print(f"Diff (Progress - Plan): {diff_extra_in_progress if diff_extra_in_progress else 'None (0 extra)'}")
print(f"Final Count Reconciled: {len(PLAN_GATES)} == {len(progress_gates)} -> {'PASS' if len(PLAN_GATES) == len(progress_gates) and not diff_missing_in_progress and not diff_extra_in_progress else 'FAIL'}")
