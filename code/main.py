"""main.py — Main CLI entry point for Ghost Data Still Exists deletion audit."""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from identity import IdentityResolver, SubjectIdentity
from intent import classify_intent
from rules_engine import PolicyEngine, Verdict
from state_reconstructor import ResourceState, StateReconstructor
from status_decider import StatusDecider
from step_builder import StepBuilder
from timeutil import parse_iso
import validate

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("main")


def process_case(
    row: Dict[str, str],
    identity_resolver: IdentityResolver,
    reconstructor: StateReconstructor,
    policy_engine: PolicyEngine,
    failures: Optional[set] = None,
) -> Tuple[str, str, List[Dict[str, Any]]]:
    case_id = row["case_id"]
    email = row["email"]
    request_text = row["request_text"]
    audit_at_str = row["audit_at"]
    audit_at = parse_iso(audit_at_str)
    requested_at = parse_iso(row.get("requested_at", ""))
    reported_at = parse_iso(row.get("reported_at", ""))

    try:
        # 1. Intent classification
        intent_label, intent_reason = classify_intent(request_text)
        if intent_label != "ERASURE":
            return case_id, "NOT_APPLICABLE", []

        # 2. Identity resolution
        subject, reason = identity_resolver.resolve(email, audit_at)
        if not subject:
            # Conservative fallback on resolution failure
            return case_id, "INCOMPLETE", []

        # 3. State reconstruction
        resource_states = reconstructor.reconstruct_for_case(
            case_id=case_id,
            subject=subject,
            audit_at=audit_at,
            requested_at=requested_at,
            reported_at=reported_at,
        )

        # 4. Policy evaluation
        verdicts = policy_engine.evaluate_all(resource_states)

        # 5. Status decision
        deletion_status, dec_reason = StatusDecider.decide_status(
            intent_label=intent_label,
            verdicts=verdicts,
            resource_states=resource_states,
        )

        # 6. Step generation
        steps = StepBuilder.build_steps(
            deletion_status=deletion_status,
            verdicts=verdicts,
            resource_states=resource_states,
        )

        return case_id, deletion_status, steps

    except Exception as e:
        logger.error(f"Error processing {case_id}: {e}")
        if failures is not None:
            failures.add(f"[CASE_ERROR] {case_id}: {e}")
        # G6.5 Failure policy: conservative fallback
        return case_id, "INCOMPLETE", []


def run_pipeline(
    input_path: Path,
    output_path: Path,
    dataset_dir: Path,
    expected_count: Optional[int] = None,
    failures_log: Optional[Path] = None,
) -> int:
    """Executes deletion audit pipeline over input CSV."""
    logger.info(f"Loading datasets from {dataset_dir}...")
    identity_resolver = IdentityResolver(dataset_dir)
    reconstructor = StateReconstructor(dataset_dir, active_link_types={"support", "analytics", "data_flow"})
    policy_engine = PolicyEngine()

    logger.info(f"Reading input from {input_path}...")
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"Processing {len(rows)} cases...")
    output_rows = []
    failures: set = set()
    for r in rows:
        cid, status, steps = process_case(
            row=r,
            identity_resolver=identity_resolver,
            reconstructor=reconstructor,
            policy_engine=policy_engine,
            failures=failures,
        )
        output_rows.append({
            "case_id": cid,
            "deletion_status": status,
            "steps_json": json.dumps(steps, separators=(",", ":")),
        })

    failures |= reconstructor.issues | policy_engine.issues
    if failures_log:
        failures_log.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(f"- {x}\n" for x in sorted(failures))
        failures_log.write_text("# Failures (rewritten each run)\n\n" + body, encoding="utf-8")

    # Sort output rows by case_id
    output_rows.sort(key=lambda x: x["case_id"])

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing {len(output_rows)} rows to {output_path}...")
    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(output_rows)

    logger.info(f"Running validation on {output_path}...")
    errors = validate.validate_file(output_path, expected_count=expected_count, dataset_dir=dataset_dir)
    if errors:
        logger.error(f"Validation failed with {len(errors)} errors:")
        for err in errors[:10]:
            logger.error(f"  {err}")
        return 1

    logger.info(f"SUCCESS: Output validated with 0 errors.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="HackerRank Ghost Data Still Exists Deletion Audit")
    parser.add_argument("--input", type=str, default="dataset/deletion_requests.csv", help="Input deletion requests CSV")
    parser.add_argument("--output", type=str, default="output.csv", help="Output prediction CSV")
    parser.add_argument("--dataset-dir", type=str, default="dataset", help="Dataset directory")
    parser.add_argument("--expected-count", type=int, default=None, help="Expected row count")
    parser.add_argument("--failures-log", type=str, default="code/notes/failures.md", help="Path to failures markdown")

    args = parser.parse_args()
    ret = run_pipeline(
        input_path=Path(args.input),
        output_path=Path(args.output),
        dataset_dir=Path(args.dataset_dir),
        expected_count=args.expected_count,
        failures_log=Path(args.failures_log) if args.failures_log else None,
    )
    sys.exit(ret)


if __name__ == "__main__":
    main()

