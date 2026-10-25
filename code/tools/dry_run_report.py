import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "code"))
import main

out = root / "code/.cache/dry_run_518.csv"
fl = root / "code/notes/failures.md"
hs = []
for i in range(2):
    main.run_pipeline(root / "dataset/deletion_requests.csv", out, root / "dataset", 518, fl)
    hs.append(hashlib.sha256(fl.read_bytes()).hexdigest()[:16])
print("failures.md sha256 after run1/run2:", hs, "lines:", len(fl.read_text(encoding="utf-8").splitlines()))
rows = list(csv.DictReader(open(out, encoding="utf-8")))
print("status distribution:", dict(Counter(r["deletion_status"] for r in rows)))
n_zero = n_inc_nofind = 0
for r in rows:
    steps = json.loads(r["steps_json"])
    if r["deletion_status"] == "COMPLETE" and not steps:
        n_zero += 1
    if r["deletion_status"] == "INCOMPLETE" and not any(s["phase"] == "FINDING" for s in steps):
        n_inc_nofind += 1
print("COMPLETE rows with zero steps (no evidence found):", n_zero)
print("INCOMPLETE rows with no FINDING (only UNKNOWN/user_* violations):", n_inc_nofind)
print(fl.read_text(encoding="utf-8")[:1500])
