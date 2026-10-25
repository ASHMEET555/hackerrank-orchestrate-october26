"""phase2_digest.py - print a compact per-case digest of code/.cache/phase2/cases.json (review aid)."""
import json
from pathlib import Path

cs = json.loads(Path("code/.cache/phase2/cases.json").read_text(encoding="utf-8"))
lo, hi = int(__import__("sys").argv[1]), int(__import__("sys").argv[2])


def pr(h):
    if h["kind"] == "sql":
        return "sql %s tbl=%s row=%s" % (h["file_id"], h["table"], str(h["row"])[:230])
    if h["kind"] == "text":
        return "text %s:%s %s" % (h["file_id"], h["line"], h["text"][:190])
    if h["kind"] == "json":
        return "json %s %s = %s" % (h["file_id"], h["json_path"], str(h["value"])[:170])
    if h["kind"] == "pdf":
        return "pdf %s p%s %s" % (h["file_id"], h["page"], h["line"][:170])
    return str(h)[:180]


for c in cs[lo:hi]:
    print("=" * 8, c["case_id"], "|", c["email"], "->", c["subject_user_id"],
          "| via", c["resolved_via"], "| audit", c["audit_at"],
          "| claim", c["reported_status"], "| EXP", c["expected_status"])
    hist = [a for a in c["aliases"] if "history" in a["kind"]]
    if hist:
        print("  hist aliases:", [(a["kind"], a["value"], a["source"]) for a in hist])
    for s in c["expected_steps"]:
        print("  step %d %s %s %s/%s %s ev=%r" % (s["step_no"], s["phase"][:4], s["operation"],
              s["system_id"], s["resource_id"], s["state"], s["evidence_id"]))
    for r in c["resources"]:
        cited = [h for h in r["hits"] if h.get("file_id") in r["cited_evidence"]]
        show = cited[:4] if cited else r["hits"][:2]
        print("  -- %s/%s exp=%s cited=%s hits=%d" % (r["system_id"], r["resource_id"],
              r["expected_state"], r["cited_evidence"], len(r["hits"])))
        for h in show:
            print("     ", pr(h))
        if r["activity_leads"]:
            print("      leads", [(l["activity_id"], l["event_type"], l["reported_result"])
                                  for l in r["activity_leads"][:3]])
