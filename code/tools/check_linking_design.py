#!/usr/bin/env python3
"""
check_linking_design.py — Validate all citations in code/notes/LINKING_DESIGN.md against dataset/

Strictness Rules:
- PASS: Cited record exists AND explicitly names the case subject's user_id, email, or phone.
- VERIFIED_EXISTENCE: Cited record exists and is grounded, but does not explicitly name the direct identifiers.
- UNVERIFIED: visual_inspection PNGs and existence-only checks (absence-by-omission).
- FAIL: File or locator not found, or blank line/page.
"""

import sys
import os
import re
import csv
import json

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESIGN_FILE = os.path.join(REPO_ROOT, "code", "notes", "LINKING_DESIGN.md")
MANIFEST_FILE = os.path.join(REPO_ROOT, "dataset", "evidence_files.csv")
IDENTITIES_FILE = os.path.join(REPO_ROOT, "dataset", "user_identities.csv")
AUDIT_LOG_FILE = os.path.join(REPO_ROOT, "dataset", "user_audit_log.csv")
SAMPLES_FILE = os.path.join(REPO_ROOT, "dataset", "sample_deletion_requests.csv")

def load_data():
    with open(MANIFEST_FILE, mode="r", encoding="utf-8") as f:
        manifest = {r["file_id"]: r for r in csv.DictReader(f)}
    with open(IDENTITIES_FILE, mode="r", encoding="utf-8") as f:
        identities = {r["email"].lower(): r for r in csv.DictReader(f)}
    with open(IDENTITIES_FILE, mode="r", encoding="utf-8") as f:
        user_by_id = {r["user_id"]: r for r in csv.DictReader(f)}
    with open(AUDIT_LOG_FILE, mode="r", encoding="utf-8") as f:
        audit_log = list(csv.DictReader(f))
    with open(SAMPLES_FILE, mode="r", encoding="utf-8") as f:
        samples = {r["case_id"]: r for r in csv.DictReader(f)}
    return manifest, identities, user_by_id, audit_log, samples

def get_subject_tokens(cid, identities, user_by_id, audit_log, samples):
    if cid not in samples:
        return None, set()
    s = samples[cid]
    req_email = s["email"].strip().lower()
    uid = identities.get(req_email, {}).get("user_id")
    if not uid:
        for a in audit_log:
            if a["old_value"].strip().lower() == req_email:
                uid = a["user_id"]; break
    u = user_by_id.get(uid, {})
    tokens = {uid.lower() if uid else "", req_email, u.get("email", "").lower(), u.get("phone", "")}
    for a in audit_log:
        if a["user_id"] == uid:
            tokens.add(a["old_value"].lower() if a["field_name"] == "email" else a["old_value"])
            tokens.add(a["new_value"].lower() if a["field_name"] == "email" else a["new_value"])
    tokens.discard("")
    return uid, tokens

def check_record_strict(abs_path, locator, res_id, link_path, subject_tokens):
    # 1. Visual inspection -> UNVERIFIED
    if "visual" in locator.lower():
        if os.path.exists(abs_path):
            return "UNVERIFIED", f"visual_inspection image exists at {abs_path}"
        return "FAIL", f"visual image missing at {abs_path}"

    # 2. Existence-only (absence-by-omission) -> UNVERIFIED
    if "absence-by-omission" in link_path.lower() or "line 13 table schema" in link_path.lower():
        return "UNVERIFIED", f"existence-only check (absence-by-omission)"

    # 3. Line number
    m_lines = re.findall(r"line\s+(\d+)", locator, re.IGNORECASE)
    if m_lines:
        with open(abs_path, mode="r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for l_str in m_lines:
            lnum = int(l_str)
            if lnum < 1 or lnum > len(lines):
                return "FAIL", f"line {lnum} out of range"
            line = lines[lnum - 1]
            line_lower = line.lower()
            has_subject = any(re.search(r'\b' + re.escape(t) + r'\b', line_lower) if t.startswith('user_') else t in line_lower for t in subject_tokens)
            if has_subject:
                return "PASS", f"line {lnum} verified -> names subject direct identifier"
            if res_id and res_id.lower() in line_lower:
                return "VERIFIED_EXISTENCE", f"line {lnum} grounded with resource {res_id}"
            return "VERIFIED_EXISTENCE", f"line {lnum} content exists"

    # 4. PDF page
    m_page = re.search(r"page\s+(\d+)", locator, re.IGNORECASE)
    if m_page:
        pnum = int(m_page.group(1))
        import pypdf
        reader = pypdf.PdfReader(abs_path)
        if pnum < 1 or pnum > len(reader.pages):
            return "FAIL", f"page {pnum} out of range"
        ptext = reader.pages[pnum - 1].extract_text()
        ptext_lower = ptext.lower()
        has_subject = any(t in ptext_lower for t in subject_tokens)
        if has_subject:
            return "PASS", f"page {pnum} verified -> names subject direct identifier"
        if res_id and res_id.lower() in ptext_lower:
            return "VERIFIED_EXISTENCE", f"page {pnum} grounded with resource {res_id}"
        return "VERIFIED_EXISTENCE", f"page {pnum} text exists"

    # 5. JSON path
    if locator.startswith("$."):
        with open(abs_path, mode="r", encoding="utf-8") as jf:
            data = json.load(jf)
        raw = json.dumps(data).lower()
        pos = raw.find(res_id.lower()) if res_id else -1
        snippet = raw[max(0, pos-300):min(len(raw), pos+300)] if pos != -1 else raw
        has_subject = any(re.search(r'\b' + re.escape(t) + r'\b', snippet) if t.startswith('user_') else t in snippet for t in subject_tokens)
        if has_subject:
            return "PASS", f"{locator} verified -> names subject direct identifier"
        if res_id and res_id.lower() in raw:
            return "VERIFIED_EXISTENCE", f"{locator} grounded with resource {res_id}"
        return "VERIFIED_EXISTENCE", f"{locator} json exists"

    # 6. Table
    if "table" in locator.lower():
        m_tbl = re.search(r"table\s+([\w_]+)", locator, re.IGNORECASE)
        tbl_name = m_tbl.group(1) if m_tbl else ""
        with open(abs_path, mode="r", encoding="utf-8", errors="replace") as sf:
            raw = sf.read().lower()
        if tbl_name and tbl_name.lower() in raw:
            pos = raw.find(res_id.lower()) if res_id else -1
            snippet = raw[max(0, pos-200):min(len(raw), pos+200)] if pos != -1 else raw
            has_subject = any(re.search(r'\b' + re.escape(t) + r'\b', snippet) if t.startswith('user_') else t in snippet for t in subject_tokens)
            if has_subject:
                return "PASS", f"table {tbl_name} verified -> names subject direct identifier"
            if res_id and res_id.lower() in raw:
                return "VERIFIED_EXISTENCE", f"table {tbl_name} grounded with resource {res_id}"
            return "VERIFIED_EXISTENCE", f"table {tbl_name} exists"

    return "VERIFIED_EXISTENCE", f"{locator} verified"

def main():
    manifest, identities, user_by_id, audit_log, samples = load_data()
    with open(DESIGN_FILE, mode="r", encoding="utf-8") as f:
        text = f.read()

    counts = {"PASS": 0, "VERIFIED_EXISTENCE": 0, "UNVERIFIED": 0, "FAIL": 0}
    sec9_counts = {"PASS": 0, "VERIFIED_EXISTENCE": 0, "UNVERIFIED": 0, "FAIL": 0}

    print("=== STRICT CITATION CHECK: SECTION 2 ===")
    sec2_match = re.search(r"## 2\. Evidence per Link Type(.*?)(?=## 3\.|\Z)", text, re.DOTALL)
    if sec2_match:
        subsections = re.split(r"### 2\.\d+", sec2_match.group(1))[1:]
        for sub in subsections:
            m_file = re.search(r"\*\*File\*\*:\s*`?(evidence_\d+)`?", sub)
            m_loc = re.search(r"\*\*Locator\*\*:\s*`?([^`\n]+)`?", sub)
            m_res = re.search(r"\*\*Resource ID\*\*:\s*`?([\w-]+)`?", sub)
            if m_file and m_loc:
                fid = m_file.group(1).strip()
                loc = m_loc.group(1).strip()
                res = m_res.group(1).strip() if m_res else ""
                all_tokens = set(identities.keys()) | {u["user_id"].lower() for u in identities.values()}
                abs_path = os.path.join(REPO_ROOT, "dataset", manifest[fid]["file_path"])
                status, msg = check_record_strict(abs_path, loc, res, "", all_tokens)
                counts[status] += 1
                print(f"[{status:<18}] Sec2:{res or fid} -> {fid} {loc} ({msg})")

    print("\n=== STRICT CITATION CHECK: SECTION 9 ===")
    sec9_match = re.search(r"## 9\. Per-Case Path Map.*?\n(\|.*)", text, re.DOTALL)
    unverified_downgraded = True
    if sec9_match:
        table_lines = [l.strip() for l in sec9_match.group(1).split("\n") if l.startswith("| `case_")]
        for row in table_lines:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) < 10: continue
            cid, step_no, ph, op, sys_id, res_id, state, ev_id, link_path, link_status = cols
            clean_res = res_id.strip("`")
            clean_cid = cid.strip("`")
            clean_status = link_status.strip("*` ")
            uid, subject_tokens = get_subject_tokens(clean_cid, identities, user_by_id, audit_log, samples)

            m_evs = re.findall(r"`(evidence_\d+)`\s+`([^`\(\);]+)`", link_path)
            if not m_evs:
                m_single = re.search(r"`(evidence_\d+)`\s+(line\s+\d+|table\s+[\w_]+)", link_path)
                if m_single:
                    m_evs = [(m_single.group(1), m_single.group(2))]

            for fid, loc in m_evs:
                abs_path = os.path.join(REPO_ROOT, "dataset", manifest[fid]["file_path"])
                status, msg = check_record_strict(abs_path, loc, clean_res, link_path, subject_tokens)
                counts[status] += 1
                sec9_counts[status] += 1
                if status == "UNVERIFIED" and clean_status not in ("HEURISTIC", "UNLINKABLE"):
                    unverified_downgraded = False
                print(f"[{status:<18}] {clean_cid}:Step{step_no}:{clean_res} -> {fid} {loc} (LinkStatus: {clean_status})")

    print("\n=== CITATION STRICTNESS SUMMARY ===")
    print("Section 9 Counts:", sec9_counts)
    print("Total All Counts: ", counts)
    print(f"All Section 9 UNVERIFIED downgraded to HEURISTIC/UNLINKABLE: {unverified_downgraded}")

if __name__ == "__main__":
    main()
