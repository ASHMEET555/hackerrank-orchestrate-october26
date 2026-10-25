"""Verify step_rules.yaml ordering and structure against dataset/sample_output.csv."""

import csv
import json
import yaml
from pathlib import Path


def main():
    with open("code/notes/step_rules.yaml", mode="r", encoding="utf-8") as f:
        step_rules = yaml.safe_load(f)

    with open("dataset/sample_output.csv", mode="r", encoding="utf-8") as f:
        sample_rows = list(csv.DictReader(f))

    rem_order = step_rules["sorting_order"]["remediation_ops"]
    ver_order = step_rules["sorting_order"]["verification_ops"]

    exact_matches = 0
    mismatches = []

    for r in sample_rows:
        cid = r["case_id"]
        status = r["deletion_status"]
        steps = json.loads(r["steps_json"])

        case_errors = []

        # 1. Phase order: FINDING (1) -> REMEDIATION (2) -> VERIFICATION (3)
        phases = [s["phase"] for s in steps]
        phase_ranks = [{"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}[p] for p in phases]
        if phase_ranks != sorted(phase_ranks):
            case_errors.append("phase order mismatch")

        # 2. Operation order within REMEDIATION
        rem_steps = [s for s in steps if s["phase"] == "REMEDIATION"]
        rem_ranks = [rem_order.get(s["operation"], 99) for s in rem_steps]
        if rem_ranks != sorted(rem_ranks):
            case_errors.append("remediation op order mismatch")

        # 3. Operation order within VERIFICATION
        ver_steps = [s for s in steps if s["phase"] == "VERIFICATION"]
        ver_ranks = [ver_order.get(s["operation"], 99) for s in ver_steps]
        if ver_ranks != sorted(ver_ranks):
            case_errors.append("verification op order mismatch")

        # 4. Lexicographic (system_id, resource_id) tie-breaking within same phase + operation
        for op in set(s["operation"] for s in steps):
            same_op_steps = [s for s in steps if s["operation"] == op]
            ids = [(s["system_id"], s["resource_id"]) for s in same_op_steps]
            if ids != sorted(ids):
                case_errors.append(f"system/resource tie-break order for {op}")

        # 5. Evidence ID rules from step_rules.yaml
        for s in steps:
            p = s["phase"]
            ev = s["evidence_id"]
            if status == "COMPLETE":
                if p != "VERIFICATION" or not ev:
                    case_errors.append(f"COMPLETE verification step missing evidence_id: {s}")
            elif status == "INCOMPLETE":
                if p == "FINDING" and not ev:
                    case_errors.append(f"INCOMPLETE finding missing evidence_id: {s}")
                elif p in ("REMEDIATION", "VERIFICATION") and ev != "":
                    case_errors.append(f"INCOMPLETE {p} has non-empty evidence_id: {s}")

        if not case_errors:
            exact_matches += 1
        else:
            mismatches.append((cid, case_errors))

    print(f"Total Sample Cases: {len(sample_rows)}")
    print(f"Exact Matches to step_rules.yaml: {exact_matches} / {len(sample_rows)}")
    if mismatches:
        print("Mismatches:")
        for cid, errs in mismatches:
            print(f" - {cid}: {errs}")
    else:
        print("All 32 sample cases strictly obey step_rules.yaml rules and ordering.")


if __name__ == "__main__":
    main()
