#!/usr/bin/env python3
"""
check_output_structure.py — Structural checks on output.csv

Checks:
- header is exactly case_id,deletion_status,steps_json
- exactly 518 data rows, unique case_ids, sorted ascending as strings
- every steps_json parses as a JSON array
- every INCOMPLETE row has at least one step; NOT_APPLICABLE rows have []
- count rows with any UNKNOWN_CLASSIFICATION text in steps_json
"""

import sys
import csv
import json
from pathlib import Path

def check_structure(filepath="output.csv", expected_count=518):
    p = Path(filepath)
    if not p.exists():
        print(f"FAIL: {filepath} does not exist.")
        sys.exit(1)

    with open(p, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        expected_header = ["case_id", "deletion_status", "steps_json"]
        if header != expected_header:
            print(f"FAIL: Header mismatch: expected {expected_header}, got {header}")
            sys.exit(1)
        else:
            print("PASS: Header is exactly case_id,deletion_status,steps_json")

        rows = list(reader)

    count = len(rows)
    print(f"Total data rows: {count}")
    if count != expected_count:
        print(f"FAIL: Expected {expected_count} rows, got {count}")
        sys.exit(1)
    else:
        print(f"PASS: Exactly {expected_count} data rows")

    case_ids = [r[0] for r in rows]
    unique_ids = set(case_ids)
    if len(unique_ids) != count:
        print(f"FAIL: Duplicate case_ids found ({len(unique_ids)} unique)")
        sys.exit(1)
    else:
        print("PASS: All case_ids are unique")

    sorted_case_ids = sorted(case_ids)
    if case_ids != sorted_case_ids:
        print("FAIL: Rows are not sorted ascending by case_id string")
        sys.exit(1)
    else:
        print("PASS: Rows are sorted ascending as strings")

    json_parse_errors = 0
    incomplete_no_steps = 0
    na_with_steps = 0
    unknown_classification_rows = []

    status_counts = {}

    for r in rows:
        cid, status, steps_str = r[0], r[1], r[2]
        status_counts[status] = status_counts.get(status, 0) + 1
        
        try:
            steps = json.loads(steps_str)
            if not isinstance(steps, list):
                json_parse_errors += 1
        except Exception:
            json_parse_errors += 1
            steps = None

        if status == "INCOMPLETE":
            if not steps or len(steps) == 0:
                incomplete_no_steps += 1
        elif status == "NOT_APPLICABLE":
            if steps is None or len(steps) != 0:
                na_with_steps += 1

        if "UNKNOWN_CLASSIFICATION" in steps_str:
            unknown_classification_rows.append(cid)

    if json_parse_errors == 0:
        print("PASS: Every steps_json parses as a valid JSON array")
    else:
        print(f"FAIL: {json_parse_errors} rows failed to parse as JSON array")

    if incomplete_no_steps == 0:
        print("PASS: Every INCOMPLETE row has at least one step")
    else:
        print(f"FAIL: {incomplete_no_steps} INCOMPLETE rows have empty steps")

    if na_with_steps == 0:
        print("PASS: Every NOT_APPLICABLE row has exactly []")
    else:
        print(f"FAIL: {na_with_steps} NOT_APPLICABLE rows have non-empty steps")

    print(f"Rows with UNKNOWN_CLASSIFICATION in steps_json: {len(unknown_classification_rows)}")
    if unknown_classification_rows:
        print("  Listed rows:", unknown_classification_rows[:10])

    print("\n--- Status Distribution ---")
    for st, c in sorted(status_counts.items()):
        print(f"  {st:<15}: {c}")

if __name__ == "__main__":
    check_structure()
