"""Compact per-case diff of predicted vs truth steps (evaluation tooling; reads truth by design)."""
import csv, json, sys

pred = {r["case_id"]: r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
truth = {r["case_id"]: r for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))}


def key(s):
    return (s["phase"][:3], s["operation"].replace("VERIFY_", "V_").replace("REPORT_", "R_"), s["resource_id"], s["evidence_id"])


for cid in sorted(truth):
    t, p = truth[cid], pred[cid]
    ts = {key(s) for s in json.loads(t["steps_json"])}
    ps = {key(s) for s in json.loads(p["steps_json"])}
    if t["deletion_status"] == p["deletion_status"] and ts == ps and t["steps_json"] == p["steps_json"]:
        continue
    print(f"{cid} status {p['deletion_status']} vs {t['deletion_status']}")
    for k in sorted(ts - ps):
        print("   MISSING", k)
    for k in sorted(ps - ts):
        print("   EXTRA  ", k)
