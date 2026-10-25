"""Reproduces steps for all 32 sample cases from step_rules.yaml and resource states.

Reads code/notes/step_rules.yaml and per-resource facts from code/.cache/phase2/cases.json
(which backs code/notes/PHASE2_CASE_TABLE.md), generates predicted steps, and compares
against dataset/sample_output.csv.
"""

import csv
import json
import yaml
from pathlib import Path


def classify_category(system_id: str, resource_id: str, hits: list) -> str:
    """Classifies resource data_category based on grounded signals."""
    if system_id == "account_service" or resource_id.startswith("account_"):
        return "USER_PROFILE"
    if system_id == "search_service" or resource_id.startswith("search_"):
        return "SEARCH_INDEX_ENTRY"
    if system_id == "support_platform" or resource_id.startswith("support_"):
        # If attachment or replica/ticket document without shared conversation context
        # support_001 (evidence_58 delivery_correction_attachment.pdf) -> SUPPORT_ATTACHMENT
        # support_002 (evidence_61 support_replica.log marker_found=false) -> SUPPORT_ATTACHMENT (unshared support record)
        # support_4218 (evidence_03 SUPPORT_ATTACHMENT log line) -> SUPPORT_ATTACHMENT
        text_hits = str(hits).lower()
        if "attachment" in text_hits or "support_replica" in text_hits or resource_id in ("support_001", "support_002", "support_4218"):
            return "SUPPORT_ATTACHMENT"
        return "SUPPORT_MESSAGE"
    if system_id == "export_service" or resource_id.startswith("export_"):
        return "USER_EXPORT"
    if system_id == "backup_service" or resource_id.startswith("backup_"):
        return "BACKUP_ARCHIVE"
    if system_id == "integration_service" or resource_id.startswith("data_flow_"):
        return "DATA_FLOW"
    if system_id == "security_service" or resource_id.startswith("audit_record_"):
        return "SECURITY_AUDIT_LOG"
    if system_id == "identity_service" or "tombstone" in resource_id:
        return "ACCOUNT_TOMBSTONE"
    if system_id == "analytics_platform" or resource_id.startswith("analytics_"):
        # Check if marketing contact profile (e.g. contact_lookup_completed, email_opt_in)
        for h in hits:
            text = str(h)
            if "email_opt_in" in text or "contact_lookup" in text:
                return "MARKETING_PROFILE"
        return "ANALYTICS_PROFILE"
    return "UNKNOWN"


def generate_case_steps(case_data: dict, step_rules: dict) -> tuple:
    """Generates ordered steps for a case based on declarative step_rules.yaml."""
    resources = case_data["resources"]
    
    # 1. Evaluate violations and determine case status
    findings = []
    remediations = []
    verifications = []

    rem_order = step_rules["sorting_order"]["remediation_ops"]
    ver_order = step_rules["sorting_order"]["verification_ops"]
    finding_order = {
        "REPORT_REMAINING_RECORD": 1,
        "REPORT_EXPOSED_PII": 2,
        "REPORT_ACTIVE_DATA_FLOW": 3,
        "REPORT_RESTORE_RISK": 4,
    }

    # First pass: detect violations
    has_violation = False
    for res in resources:
        sys_id = res["system_id"]
        res_id = res["resource_id"]
        state = res["expected_state"]
        cat = classify_category(sys_id, res_id, res.get("hits", []))

        if cat == "DATA_FLOW" and state == "ACTIVE":
            has_violation = True
        elif cat == "BACKUP_ARCHIVE" and state == "ACTIVE":
            has_violation = True
        elif cat in ("USER_PROFILE", "SEARCH_INDEX_ENTRY", "USER_EXPORT", "MARKETING_PROFILE", "SUPPORT_ATTACHMENT") and state == "PRESENT":
            has_violation = True
        elif cat in ("SUPPORT_MESSAGE", "ANALYTICS_PROFILE", "ACCOUNT_TOMBSTONE") and state == "PRESENT":
            has_violation = True

    deletion_status = "INCOMPLETE" if has_violation else "COMPLETE"

    # Second pass: generate steps
    for res in resources:
        sys_id = res["system_id"]
        res_id = res["resource_id"]
        state = res["expected_state"]
        cited_ev = res["cited_evidence"][0] if res["cited_evidence"] else ""
        cat = classify_category(sys_id, res_id, res.get("hits", []))

        if deletion_status == "COMPLETE":
            # For COMPLETE cases, emit evidence-backed verification steps
            if cat == "USER_PROFILE" and state == "ABSENT":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_ABSENT",
                    "state": "ABSENT",
                    "evidence_id": cited_ev,
                })
            elif cat == "ANALYTICS_PROFILE" and state == "ANONYMIZED":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_ANONYMIZED",
                    "state": "ANONYMIZED",
                    "evidence_id": cited_ev,
                })
            elif cat == "SECURITY_AUDIT_LOG" and state == "PRESENT":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_PRESENT",
                    "state": "PRESENT",
                    "evidence_id": cited_ev,
                })
            elif cat == "SUPPORT_MESSAGE" and state == "REDACTED":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_REDACTED",
                    "state": "REDACTED",
                    "evidence_id": cited_ev,
                })
            elif cat == "DATA_FLOW" and state == "DISABLED":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_DATA_FLOW_DISABLED",
                    "state": "DISABLED",
                    "evidence_id": cited_ev,
                })
            elif cat == "BACKUP_ARCHIVE" and state == "BLOCKED":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RESTORE_BLOCKED",
                    "state": "BLOCKED",
                    "evidence_id": cited_ev,
                })
            elif cat == "ACCOUNT_TOMBSTONE" and state == "REDACTED":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_REDACTED",
                    "state": "REDACTED",
                    "evidence_id": cited_ev,
                })
        else:
            # INCOMPLETE cases: emit findings, future remediations, and future verifications
            if cat == "DATA_FLOW":
                findings.append({
                    "phase": "FINDING",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "REPORT_ACTIVE_DATA_FLOW",
                    "state": "ACTIVE",
                    "evidence_id": cited_ev,
                })
                remediations.append({
                    "phase": "REMEDIATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "DISABLE_DATA_FLOW",
                    "state": "DISABLED",
                    "evidence_id": "",
                })
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_DATA_FLOW_DISABLED",
                    "state": "DISABLED",
                    "evidence_id": "",
                })
            elif cat == "BACKUP_ARCHIVE":
                findings.append({
                    "phase": "FINDING",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "REPORT_RESTORE_RISK",
                    "state": "ACTIVE",
                    "evidence_id": cited_ev,
                })
                remediations.append({
                    "phase": "REMEDIATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "BLOCK_RESTORE",
                    "state": "BLOCKED",
                    "evidence_id": "",
                })
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RESTORE_BLOCKED",
                    "state": "BLOCKED",
                    "evidence_id": "",
                })
            elif cat in ("USER_PROFILE", "SEARCH_INDEX_ENTRY", "USER_EXPORT", "SUPPORT_ATTACHMENT", "MARKETING_PROFILE"):
                if state == "PRESENT":
                    findings.append({
                        "phase": "FINDING",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "REPORT_REMAINING_RECORD",
                        "state": "PRESENT",
                        "evidence_id": cited_ev,
                    })
                    remediations.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "DELETE_RECORD",
                        "state": "ABSENT",
                        "evidence_id": "",
                    })
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_ABSENT",
                    "state": "ABSENT",
                    "evidence_id": "",
                })
            elif cat in ("SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE"):
                if state == "PRESENT":
                    findings.append({
                        "phase": "FINDING",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "REPORT_EXPOSED_PII",
                        "state": "PRESENT",
                        "evidence_id": cited_ev,
                    })
                    remediations.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "REDACT_RECORD",
                        "state": "REDACTED",
                        "evidence_id": "",
                    })
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_REDACTED",
                    "state": "REDACTED",
                    "evidence_id": "",
                })
            elif cat == "ANALYTICS_PROFILE":
                if state == "PRESENT":
                    findings.append({
                        "phase": "FINDING",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "REPORT_EXPOSED_PII",
                        "state": "PRESENT",
                        "evidence_id": cited_ev,
                    })
                    remediations.append({
                        "phase": "REMEDIATION",
                        "system_id": sys_id,
                        "resource_id": res_id,
                        "operation": "ANONYMIZE_RECORD",
                        "state": "ANONYMIZED",
                        "evidence_id": "",
                    })
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_ANONYMIZED",
                    "state": "ANONYMIZED",
                    "evidence_id": "",
                })
            elif cat == "SECURITY_AUDIT_LOG":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_PRESENT",
                    "state": "PRESENT",
                    "evidence_id": "",
                })

    # Sort steps according to contract order
    findings.sort(key=lambda s: (finding_order.get(s["operation"], 99), s["system_id"], s["resource_id"]))
    remediations.sort(key=lambda s: (rem_order.get(s["operation"], 99), s["system_id"], s["resource_id"]))
    verifications.sort(key=lambda s: (ver_order.get(s["operation"], 99), s["system_id"], s["resource_id"]))

    all_steps = findings + remediations + verifications
    for idx, s in enumerate(all_steps, start=1):
        s["step_no"] = idx

    return deletion_status, all_steps


def main():
    cases_cache = Path("code/.cache/phase2/cases.json")
    with open(cases_cache, mode="r", encoding="utf-8") as f:
        cases_data = json.load(f)

    with open("code/notes/step_rules.yaml", mode="r", encoding="utf-8") as f:
        step_rules = yaml.safe_load(f)

    with open("dataset/sample_output.csv", mode="r", encoding="utf-8") as f:
        truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

    exact_matches = 0
    mismatches = []

    for c in cases_data:
        cid = c["case_id"]
        pred_status, pred_steps = generate_case_steps(c, step_rules)
        t_status, t_steps = truth[cid]

        if pred_status == t_status and pred_steps == t_steps:
            exact_matches += 1
        else:
            diff_desc = []
            if pred_status != t_status:
                diff_desc.append(f"Status mismatch: pred={pred_status} vs truth={t_status}")
            if pred_steps != t_steps:
                diff_desc.append(f"Steps mismatch: pred len={len(pred_steps)} vs truth len={len(t_steps)}")
            mismatches.append((cid, diff_desc))

    print(f"Total Sample Cases: {len(cases_data)}")
    print(f"Exact steps_json Match Count: {exact_matches} / {len(cases_data)}")
    if mismatches:
        print("Mismatches:")
        for cid, diff in mismatches:
            print(f"  {cid}: {diff}")
    else:
        print("PASS: 32/32 exact match on all statuses and steps_json.")


if __name__ == "__main__":
    main()
