"""phase2_table.py - generate code/notes/PHASE2_CASE_TABLE.md from code/.cache/phase2/cases.json.

Analysis aid (Phase 2). Read-only on dataset/. Citations are auto-formatted from
phase2_extract.py provenance hits; manual overrides live in OVERRIDES below.
Usage (repo root): python code/tools/phase2_table.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "dataset"
CASES = json.loads((ROOT / "code/.cache/phase2/cases.json").read_text(encoding="utf-8"))

# ---- category -> rule (deletion_rules.csv) ----
RULE = {
    "USER_PROFILE": ("rule_01", "DELETE"),
    "SECONDARY_IDENTIFIER": ("rule_02", "DELETE"),
    "SEARCH_INDEX_ENTRY": ("rule_03", "DELETE"),
    "CACHE_ENTRY": ("rule_04", "DELETE"),
    "SUPPORT_MESSAGE": ("rule_05", "REDACT"),
    "SUPPORT_ATTACHMENT": ("rule_06", "DELETE"),
    "ANALYTICS_PROFILE": ("rule_07", "ANONYMIZE"),
    "PRODUCT_TELEMETRY": ("rule_08", "ANONYMIZE"),
    "USER_EXPORT": ("rule_09", "DELETE"),
    "MARKETING_PROFILE": ("rule_10", "DELETE"),
    "EMAIL_DELIVERY_LOG": ("rule_11", "REDACT"),
    "SECURITY_AUDIT_LOG": ("rule_12", "RETAIN"),
    "LEGAL_HOLD_RECORD": ("rule_13", "RETAIN"),
    "BACKUP_ARCHIVE": ("rule_14", "RETAIN"),
    "ACCOUNT_TOMBSTONE": ("rule_15", "REDACT"),
    "DATA_FLOW": ("(none)", "DISABLE_DATA_FLOW"),
}

# category overrides where the evidence file does not print the category
CAT_OVERRIDE = {
    ("case_07", "support_001"): "SUPPORT_ATTACHMENT",   # evidence_58 p1: subject-only attachment
    ("case_10", "support_002"): "SUPPORT_ATTACHMENT",   # evidence_61 gives no category; sample demands DELETE
    ("case_12", "analytics_9914"): "MARKETING_PROFILE", # evidence_01:92 email_opt_in=true; sample demands DELETE
    ("case_19", "support_9553"): "SUPPORT_MESSAGE",     # evidence_01:15 message_pii_scan
    ("case_08", "export_001"): "USER_EXPORT",
    ("case_23", "export_7364"): "USER_EXPORT",
    ("case_06", "search_001"): "SEARCH_INDEX_ENTRY",
    ("case_31", "tombstone_440"): "ACCOUNT_TOMBSTONE",
    ("case_32", "tombstone_9178"): "ACCOUNT_TOMBSTONE",
}

# full citation replacement where the auto sweep finds nothing (negative proof / UNKNOWN)
MANUAL_CITE = {
    ("case_01", "account_001"): "`evidence_54` tables `customer_profiles_failover_replica` (4 rows) and `customer_profiles_primary` (3 rows): no row `resource_id=account_001` - proof by absence, sample cites this file",
    ("case_02", "account_002"): "`evidence_54` tables `customer_profiles_failover_replica` (4 rows) and `customer_profiles_primary` (3 rows): no row `resource_id=account_002` - proof by absence, sample cites this file",
    ("case_04", "account_004"): "`evidence_54` tables `customer_profiles_failover_replica` (4 rows) and `customer_profiles_primary` (3 rows): no row `resource_id=account_004` - proof by absence, sample cites this file",
    ("case_06", "account_006"): "`evidence_57` table `search_documents_primary` row `search_001` field `source_resource_id=account_006` is the only link; no account row for `account_006` in any file - proof by absence, sample step carries `ev=''`",
    ("case_09", "account_3960"): "UNKNOWN - the only hit is `evidence_06` line 86 (`rows=0 http_status=404`) but that file was captured 2026-09-18, after `audit_at=2026-09-16T09:00:00Z`, so it cannot be cited; sample step carries `ev=''`",
    ("case_09", "audit_record_4902"): "UNKNOWN - the only hit is `evidence_06` line 28 (`rows=1`) but that file was captured 2026-09-18, after `audit_at=2026-09-16T09:00:00Z`, so it cannot be cited; sample step carries `ev=''`",
    ("case_23", "account_410"): "negative sweep: `account_410` occurs 0 times as a row key in any file (`evidence_53` line 268 is the substring decoy `account_41038`) - proof by absence, sample step carries `ev=''`",
}
NEG_DEFAULT = ("negative sweep: `%s` occurs 0 times in all 94 evidence files "
               "(SQL tables, LOG/TXT lines, JSON values, PDF pages) - proof by absence, "
               "sample step carries `ev=''`")

# citation notes appended to an auto citation
CITE_NOTE = {
    ("case_09", "account_3960"):
        " [POST-CUTOFF: evidence_06 captured 2026-09-18 > audit_at 2026-09-16, not citable]",
    ("case_09", "audit_record_4902"):
        " [POST-CUTOFF: evidence_06 captured 2026-09-18 > audit_at 2026-09-16, not citable]",
    ("case_23", "account_410"):
        " [evidence_53:268 is a substring decoy: resource_id=account_41038, not account_410]",
    ("case_11", "account_4248"): " (line 11 is exactly at audit_at 2026-10-01T12:00:00Z -> citable)",
}

# ---- evidence_03 pipe categories ----
EV3 = {}
for i, line in enumerate(
        (DS / "evidence/records/customer_account_handover_20261001.txt")
        .read_text(encoding="utf-8").splitlines(), 1):
    m = re.match(r"- (\S+) \| (\S+) \| (\S+) \| (\S+) \| (\S+) \| (.*)$", line)
    if m:
        EV3[m.group(3)] = {"line": i, "category": m.group(4), "status": m.group(5)}


def category(case_id, rid, hits, cited):
    if (case_id, rid) in CAT_OVERRIDE:
        return CAT_OVERRIDE[(case_id, rid)]
    if rid in EV3:
        return EV3[rid]["category"]
    for h in hits:
        if h["kind"] == "sql":
            t = h["table"]
            if "search" in t:
                return "SEARCH_INDEX_ENTRY"
            if "analytics" in t:
                return "ANALYTICS_PROFILE"
            if "security" in t:
                return "SECURITY_AUDIT_LOG"
            if "profile" in t:
                return "USER_PROFILE"
        if h["kind"] == "json":
            p = h["json_path"]
            if ".analytics_platform." in p:
                return "ANALYTICS_PROFILE"
            if ".security_service." in p:
                return "SECURITY_AUDIT_LOG"
            if ".support_platform." in p:
                return "SUPPORT_MESSAGE"
            if ".export_service." in p:
                return "USER_EXPORT"
            if ".search_service." in p:
                return "SEARCH_INDEX_ENTRY"
            if ".backup_service." in p:
                return "BACKUP_ARCHIVE"
            if ".integration_service." in p:
                return "DATA_FLOW"
            if ".account_service." in p:
                return "USER_PROFILE"
        if h["kind"] == "text" and "service=" in h.get("text", ""):
            m = re.search(r"service=(\w+)", h["text"])
            svc = m.group(1) if m else ""
            return {
                "account_service": "USER_PROFILE", "search_service": "SEARCH_INDEX_ENTRY",
                "analytics_platform": "ANALYTICS_PROFILE", "support_platform": "SUPPORT_MESSAGE",
                "security_service": "SECURITY_AUDIT_LOG", "backup_service": "BACKUP_ARCHIVE",
                "integration_service": "DATA_FLOW", "export_service": "USER_EXPORT",
            }.get(svc, "UNKNOWN")
    # prefix fallback
    if rid.startswith("account_"):
        return "USER_PROFILE"
    if rid.startswith("search_"):
        return "SEARCH_INDEX_ENTRY"
    if rid.startswith("analytics_"):
        return "ANALYTICS_PROFILE"
    if rid.startswith("support_"):
        return "SUPPORT_MESSAGE"
    if rid.startswith("audit_record_"):
        return "SECURITY_AUDIT_LOG"
    if rid.startswith("backup_"):
        return "BACKUP_ARCHIVE"
    if rid.startswith("data_flow_"):
        return "DATA_FLOW"
    if rid.startswith("export_"):
        return "USER_EXPORT"
    if rid.startswith("tombstone_"):
        return "ACCOUNT_TOMBSTONE"
    return "UNKNOWN"


def text_snip(line):
    m = re.search(r"resource_id=.*", line)
    if m:
        s = m.group(0)
    else:
        s = line
    s = s.replace("|", "\\|")
    return s[:150]


def cite(hits, cited, rid, case_id):
    if (case_id, rid) in MANUAL_CITE:
        return MANUAL_CITE[(case_id, rid)]
    sel = [h for h in hits if h.get("file_id") in cited] or hits
    parts = []
    for h in sel[:2]:
        if h["kind"] == "sql":
            row = h["row"]
            brief = {k: v for k, v in row.items()
                     if k in ("resource_id", "user_id", "account_status", "status", "email",
                              "full_name", "restore_allowed", "origin_system")}
            parts.append("`%s` table `%s` row %s" % (h["file_id"], h["table"], brief))
        elif h["kind"] == "text":
            parts.append("`%s` line %d: `%s`" % (h["file_id"], h["line"], text_snip(h["text"])))
        elif h["kind"] == "json":
            v = h["value"]
            if isinstance(v, dict):
                brief = {k: val for k, val in v.items() if k in (
                    "resource_id", "status_code", "profile", "enabled", "restore_allowed",
                    "requester_email", "customer_reference", "retention_until", "email",
                    "phone", "email_hash", "name", "account_status", "subject_reference",
                    "owner_email", "download_available", "last_delivery_status")}
                parts.append("`%s` JSON `%s` = %s" % (h["file_id"], h["json_path"], brief))
            else:
                parts.append("`%s` JSON `%s` = %r" % (h["file_id"], h["json_path"], v))
        elif h["kind"] == "pdf":
            parts.append("`%s` page %d: `%s`" % (h["file_id"], h["page"], h["line"][:120]))
    if not parts:
        if cited:
            parts.append("`%s` contains no row/line/entry for `%s`; global sweep over all 94 files "
                         "also finds 0 occurrences - proof by absence" % (cited[0], rid))
        else:
            parts.append(NEG_DEFAULT % rid)
    return "; ".join(parts) + CITE_NOTE.get((case_id, rid), "")


def alias_cell(c):
    bits = []
    ident = c.get("identity_row")
    hist = [a for a in c["aliases"] if "history" in a["kind"]]
    if c["resolved_via"][0] == "identity_current":
        bits.append("`user_identities.csv` row `user_id=%s` (email match, case-fold+trim)" % ident["user_id"])
    else:
        bits.append("no current-email match; `user_audit_log.csv` %s links old email -> `user_id=%s`"
                    % (", ".join("`%s`" % a for a in c["resolved_via"][1]), c["subject_user_id"]))
        if ident:
            bits.append("current row `user_id=%s` email=%s" % (ident["user_id"], ident["email"]))
    for a in hist:
        bits.append("%s [%s] via %s" % (a["kind"].replace("_history", ""), a["value"], a["source"]))
    return "<br>".join(bits)


def main():
    out = []
    out.append("# PHASE2_CASE_TABLE - per-case derivation (32 sample cases)")
    out.append("")
    out.append("Generated by `code/tools/phase2_table.py` from `code/.cache/phase2/cases.json` "
               "(phase2_extract.py sweep of all 94 evidence files) plus manual category/citation "
               "overrides in that script. State citations point at file + line/table/page/JSON path. "
               "`UNKNOWN` cells state why. Expected steps are copied verbatim from "
               "`dataset/sample_output.csv`.")
    out.append("")
    out.append("Legend: step column = `step_no PHASE operation system/resource state evidence_id`; "
               "an empty evidence id is shown as ev=''. Cells marked `negative sweep` prove ABSENT by "
               "finding no row in any file; cells marked `UNKNOWN` state why no citable source exists.")
    out.append("")
    header = ("| case_id | request email | subject user_id | aliases used (provenance) | "
              "evidence_ids consulted | per-resource state at audit_at (cited) | "
              "policy rule | expected status | expected steps (verbatim from sample_output.csv) |")
    out.append(header)
    out.append("|" + "---|" * 9)
    for c in CASES:
        cid = c["case_id"]
        consulted = set()
        state_bits, rule_bits = [], []
        for r in c["resources"]:
            rid = r["resource_id"]
            hits = r["hits"]
            for h in hits:
                if h.get("file_id"):
                    consulted.add(h["file_id"])
            consulted.update(e for e in r["cited_evidence"] if e)
            cat = category(cid, rid, hits, r["cited_evidence"])
            rule_id, action = RULE.get(cat, ("UNKNOWN", "UNKNOWN"))
            state_bits.append("**`%s/%s` = %s** - %s"
                              % (r["system_id"], rid, r["expected_state"], cite(hits, r["cited_evidence"], rid, cid)))
            rule_bits.append("`%s` %s -> %s" % (rule_id, cat, action))
        steps = "<br>".join(
            "%d %s %s %s/%s %s ev=`%s`" % (
                s["step_no"], s["phase"], s["operation"], s["system_id"], s["resource_id"],
                s["state"], s["evidence_id"]) for s in c["expected_steps"])
        out.append("| `%s` | %s | `%s` | %s | %s | %s | %s | **%s** | %s |" % (
            cid, c["email"], c["subject_user_id"], alias_cell(c),
            ", ".join("`%s`" % e for e in sorted(consulted)) or "none",
            "<br>".join(state_bits), "<br>".join(rule_bits), c["expected_status"], steps))
    out.append("")
    out.append("## Notes carried into step_rules.yaml")
    out.append("")
    out.append("- `FINDING` order observed: `REPORT_REMAINING_RECORD` < `REPORT_EXPOSED_PII` < "
               "`REPORT_ACTIVE_DATA_FLOW` < `REPORT_RESTORE_RISK`, then ASCII `system_id`,`resource_id` "
               "inside each operation (case_11, case_13, case_16, case_18, case_20, case_23, case_29).")
    out.append("- `REMEDIATION` order observed: `DISABLE_DATA_FLOW` / `BLOCK_RESTORE` first, then "
               "`DELETE_RECORD` < `REDACT_RECORD` < `ANONYMIZE_RECORD`, ASCII inside each "
               "(case_11, case_13, case_19, case_22, case_29).")
    out.append("- `VERIFICATION` order observed: `VERIFY_RECORD_ABSENT` < `VERIFY_RECORD_PRESENT` < "
               "`VERIFY_RECORD_REDACTED` < `VERIFY_RECORD_ANONYMIZED` < `VERIFY_DATA_FLOW_DISABLED` < "
               "`VERIFY_RESTORE_BLOCKED`, ASCII inside each (case_11, case_26, case_27, case_28).")
    out.append("- Every `INCOMPLETE` case carries `evidence_id=\"\"` on all remediation and "
               "verification steps; only `FINDING` steps cite (all 22 INCOMPLETE cases).")
    out.append("- Every `COMPLETE` case is verification-only and every step cites an evidence id "
               "(all 10 COMPLETE cases).")
    path = ROOT / "code/notes/PHASE2_CASE_TABLE.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("wrote", path, len(CASES), "cases")


if __name__ == "__main__":
    main()
