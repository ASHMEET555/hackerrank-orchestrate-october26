"""phase2_extract.py - Phase 2 mechanical extraction (analysis only, not engine code).

Produces code/.cache/phase2/cases.json with, per sample case:
  - identity resolution (current row + historical audit rows that link the email)
  - expected steps parsed from sample_output.csv
  - provenance hits for every (system_id, resource_id) in ALL evidence files
    (SQL: table+row; LOG/TXT: line number; JSON: path; PDF: page; PNG: visual-read flag)
    plus system_activity lead rows (activity_id)
Usage (repo root): python code/tools/phase2_extract.py
Read-only on dataset/.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "dataset"
CACHE = ROOT / "code" / ".cache" / "phase2"


def rows(name):
    with open(DS / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(v):
    return (v or "").strip().lower()


# ---------- provenance search ----------
_SQL_CACHE = {}


def _sql_conn(fid: str, path: Path):
    if fid not in _SQL_CACHE:
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.executescript(path.read_text(encoding="utf-8", errors="replace"))
        _SQL_CACHE[fid] = db
    return _SQL_CACHE[fid]


def hits_for_resource(rid: str):
    """Return list of provenance hits across every evidence file."""
    out = []
    manifest = rows("evidence_files.csv")
    for m in manifest:
        path = DS / m["file_path"]
        fid, ext = m["file_id"], path.suffix.lower()
        try:
            if ext == ".sql":
                db = _sql_conn(fid, path)
                tables = [r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                for t in tables:
                    cols = [c[1] for c in db.execute(f'PRAGMA table_info("{t}")')]
                    if "resource_id" not in cols:
                        continue
                    for row in db.execute(f'SELECT * FROM "{t}" WHERE resource_id = ?', (rid,)):
                        out.append({"kind": "sql", "file_id": fid, "path": m["file_path"],
                                    "table": t, "row": dict(row)})
            elif ext in (".log", ".txt"):
                for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if rid in line:
                        out.append({"kind": "text", "file_id": fid, "path": m["file_path"],
                                    "line": i, "text": line.strip()})
            elif ext == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                stack = [("$", data)]
                while stack:
                    p, node = stack.pop()
                    if isinstance(node, dict):
                        if node.get("resource_id") == rid:
                            out.append({"kind": "json", "file_id": fid, "path": m["file_path"],
                                        "json_path": p, "value": node})
                        for k, v in node.items():
                            stack.append((f"{p}.{k}", v))
                    elif isinstance(node, list):
                        for i, v in enumerate(node):
                            stack.append((f"{p}[{i}]", v))
                    elif isinstance(node, str) and rid in node:
                        out.append({"kind": "json", "file_id": fid, "path": m["file_path"],
                                    "json_path": p, "value": node})
            elif ext == ".pdf":
                import fitz
                with fitz.open(path) as doc:
                    for pno, page in enumerate(doc, 1):
                        txt = page.get_text()
                        if rid in txt:
                            line = next((l.strip() for l in txt.splitlines() if rid in l), "")
                            out.append({"kind": "pdf", "file_id": fid, "path": m["file_path"],
                                        "page": pno, "line": line})
            elif ext == ".png":
                pass  # content unsearchable (OCR deferred B1/B2); recorded once at case level
        except Exception as exc:
            out.append({"kind": "error", "file_id": fid, "path": m["file_path"], "error": str(exc)})
    return out


def activity_leads(rid: str):
    return [{"activity_id": a["activity_id"], "event_time": a["event_time"],
             "event_type": a["event_type"], "source": a["source_system"],
             "target": a["target_system"], "reported_result": a["reported_result"],
             "details": a["details"]}
            for a in ACTIVITY if a["resource_id"] == rid]


# ---------- main ----------

IDENT = rows("user_identities.csv")
AUDIT = rows("user_audit_log.csv")
ACTIVITY = rows("system_activity.csv")
SREQ = rows("sample_deletion_requests.csv")
SOUT = {r["case_id"]: r for r in rows("sample_output.csv")}


def resolve(email):
    e = norm(email)
    current = [r for r in IDENT if norm(r["email"]) == e]
    if current:
        return current[0]["user_id"], ("identity_current", None), current[0], []
    hist = [r for r in AUDIT if norm(r["old_value"]) == e or norm(r["new_value"]) == e]
    if hist:
        uid = hist[0]["user_id"]
        cur = next((r for r in IDENT if r["user_id"] == uid), None)
        return uid, ("audit_history", [h["audit_id"] for h in hist]), cur, hist
    return None, (None, None), None, []


def aliases(uid, hist_rows):
    ident = next((r for r in IDENT if r["user_id"] == uid), {})
    al = []
    if ident:
        al.append({"kind": "email_current", "value": ident["email"],
                   "source": f"user_identities row user_id={uid}"})
        al.append({"kind": "phone_current", "value": ident["phone"],
                   "source": f"user_identities row user_id={uid}"})
        al.append({"kind": "email_hash_current", "value": ident["email_hash"],
                   "source": f"user_identities row user_id={uid}"})
    for h in AUDIT:
        if h["user_id"] == uid:
            al.append({"kind": h["field_name"] + "_history", "value": f"{h['old_value']} -> {h['new_value']}",
                       "source": f"user_audit_log {h['audit_id']} @{h['event_time']}"})
    return al


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    out = []
    for c in SREQ:
        cid = c["case_id"]
        uid, how, ident_row, hist = resolve(c["email"])
        steps = json.loads(SOUT[cid]["steps_json"])
        resources = sorted({(s["system_id"], s["resource_id"]) for s in steps})
        res_states = []
        for sysid, rid in resources:
            hits = hits_for_resource(rid)
            cited = [s for s in steps if s["resource_id"] == rid]
            cited_fids = {s["evidence_id"] for s in cited if s["evidence_id"]}
            res_states.append({
                "system_id": sysid, "resource_id": rid,
                "expected_state": cited[0]["state"],
                "cited_evidence": sorted(cited_fids),
                "hits": sorted(hits, key=lambda h: (0 if h.get("file_id") in cited_fids else 1,
                                                    h.get("file_id", ""))),
                "activity_leads": activity_leads(rid),
            })
        out.append({
            "case_id": cid, "email": c["email"],
            "requested_at": c["requested_at"], "reported_status": c["reported_status"],
            "reported_at": c["reported_at"], "audit_at": c["audit_at"],
            "subject_user_id": uid, "resolved_via": how,
            "identity_row": ident_row, "aliases": aliases(uid, hist) if uid else [],
            "expected_status": SOUT[cid]["deletion_status"],
            "expected_steps": steps,
            "png_unsearched": [m["file_id"] for m in rows("evidence_files.csv")
                               if m["file_path"].endswith(".png")],
            "resources": res_states,
        })
    (CACHE / "cases.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                      encoding="utf-8", newline="\n")
    print(f"wrote {CACHE/'cases.json'}: {len(out)} cases")


if __name__ == "__main__":
    sys.exit(main())
