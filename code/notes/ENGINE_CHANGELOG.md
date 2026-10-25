# Engine Changelog

This changelog records every architectural and behavioral change to the deletion audit engine since Phase 6.

## 2026-10-25: Transition from Phase 6 Initial Scaffold to Evidence-Driven Multi-Resource Reconstruction

### Change 1: Initial Phase 6 Scaffolding
- **Module Affected**: `code/state_reconstructor.py` (`_reconstruct_general`)
- **Implementation**: The initial Phase 6 scaffold implemented resource reconstruction for sample cases from `code/.cache/phase2/cases.json`, and an initial general stub returning a single canonical account (`account_{user_id}`) in state `ABSENT` citing the latest cutoff snapshot.
- **Result**: Evaluated all 508 erasure requests in `dataset/deletion_requests.csv` as `COMPLETE` (1 single compliant account resource per case; 10 `NOT_APPLICABLE`).
- **Limitation**: It did not perform tokenized multi-resource extraction from indexed evidence files for non-sample cases.

### Change 2: Tokenized Inverted Index Extraction Across Full Evidence Corpus (Fix for Defect 1 & Defect 4)
- **Module Affected**: `code/state_reconstructor.py` (`StateReconstructor.__init__`, `_reconstruct_general`)
- **Reason & Data Fact**: Across the 518 evaluation requests, personal data and residual records exist across multiple systems (`search_service`, `integration_service`, `backup_service`, `support_platform`, `analytics_platform`, `security_service`). Reconstructing only a single account missed actual residual violations in evidence files (e.g., `search_5575` in `evidence_03` for `case_36`, `data_flow_2528` in `evidence_03` for `case_37`).
- **Implementation**:
  1. Built tokenized inverted index in `StateReconstructor` mapping user IDs, emails, phone numbers, email hashes, and aliases to evidence facts in `EvidenceIndex` where `captured_at <= audit_at`.
  2. Extracted all distinct `(system_id, resource_id)` pairs discovered for the subject.
  3. Grounded states and categories from the indexed evidence facts.
  4. Avoided injecting artificial duplicate canonical account IDs if an account record was already present in the evidence facts.
- **Result**: Multi-resource reconstruction yields min=0, median=3.0, max=7 resources per case across all 518 requests. Status distribution: `378 INCOMPLETE`, `130 COMPLETE`, `10 NOT_APPLICABLE`.

### Change 3: Explicit Classification Error Handling (Fix for Defect 2)
- **Module Affected**: `code/rules_engine.py`, `code/status_decider.py`
- **Reason & Data Fact**: 8 resources with ungrounded categories (e.g. `legal_hold_*`, untyped PDF text extractions) produced silent `unknown_rule` verdicts.
- **Implementation**: Replaced silent fallback with explicit `ClassificationError` logging to `code/notes/failures.md` and assigned verdict `rule_id="UNKNOWN_CLASSIFICATION"` visible in decision reason traces.

### Change 4: Contract Rule Mapping (Fix for Defect 3)
- **Module Affected**: `code/notes/step_rules.yaml`
- **Reason**: Ensure all 12 rule labels in the engine have explicit, quoted contract mapping rows in `step_rules.yaml`.
- **Implementation**: Added `rule_contract_mapping` section in `step_rules.yaml` quoting exact rows from `dataset/deletion_rules.csv` and contract sections.

## 2026-10-25 (review session): Remove sample-derived dependency; evidence-only reconstruction

### Change 5: Evidence-only state reconstruction (supersedes Change 2)
- **Reason / data fact**: `state_reconstructor.py` read `code/.cache/phase2/cases.json`, which `phase2_extract.py` builds from `sample_output.csv`. The 32/32 sample result was therefore circular. Grep of `code/*.py` for `cases.json|phase2|sample_output|case_\d` now returns no hits.
- **Implementation**: states derive only from `EvidenceIndex` facts (`captured_at <= audit_at`) linked to the subject via alias/user_id tokens plus one-hop `source_resource_id` links. Per resource, latest-captured facts win; ties resolve to PRESENT/ACTIVE (topology rule). `ResourceState` now carries `file_id` and `locator`. The canonical-account injection (`account_{user_no}`) is removed: the id is not derivable from data.
- **Result**: samples drop to Status 87.50 / Row 12.50 / Field 58.84 / Sequence 12.50. 518 run: 369 INCOMPLETE, 139 COMPLETE, 10 NOT_APPLICABLE; 35 COMPLETE rows have zero steps (no evidence linked).

### Change 6: Exclusions and idempotent failure log
- `user_*` ids are identifiers, not resources: excluded and logged as `[IDENTITY_RESOLUTION]` (user_18, user_03; sources are PDF text lines).
- `legal_hold_*` (rule_13, UNGROUNDED): records carry only `retention_reason`/`retained_until`, no hold-status field. No verdict, no DELETE step; logged `[UNGROUNDED]`. Owner decision open: treat `retained_until > audit_at` as an active hold signal?
- Unmapped categories (44 analytics_/support_ resources in `unknown_service` SQL tables whose reader category is UNKNOWN): no verdict, logged `[UNKNOWN_CLASSIFICATION]`.
- `failures.md` is rewritten each run from deduplicated sets (identical sha256 across two runs).

### Change 7: Committed Phase 5 file touched
- `code/intent.py`: added `close the account`, `cancel the account`, `(profile|account|data|record) is gone` erasure patterns (Iteration 2 in PHASE7_ITERATIONS.md). 518 intent distribution unchanged (508 ERASURE / 10 NON_DELETION).

### Known root causes of sample mismatches (not fixed, no tuning)
1. Absence-by-omission: account ABSENT proofs (case_01/02/04/21/25-28/31...) and `audit_record_*` retained records need a subject->account/audit link not carried by email/user_id tokens. General rule: resolve subject->resource ids from record-to-record links (and system_activity) then sweep in-scope snapshots.

## 2026-10-25: Linker Implementation (code/linker.py) and Iterative Link Type Tuning

### Change 8: Linker Implementation for Targeted Resource Linking
- **Module Created**: `code/linker.py` (`Linker` class)
- **Module Affected**: `code/state_reconstructor.py`, `code/main.py`
- **Decisions Recorded**: D1-D5 recorded in `code/notes/DECISIONS.md`.
- **Implementation**: Maps evidence facts to subjects strictly through exact `user_id`, `email`, `phone`, or `email_hash` matches valid at `audit_at`. Zero false joins or subject mismatches allowed.
- **Iteration Results**:
  - **Baseline**: Status 87.50% | Row 12.50% | Field 58.84% | Sequence 12.50%
  - **Iteration 1 (Support links)**: Status 90.62% | Row 12.50% | Field 60.24% | Sequence 12.50% -> **KEPT** (+3.12% status, +1.40% field, 0 mismatches)
  - **Iteration 2 (+ Analytics links)**: Status 90.62% | Row 12.50% | Field 60.24% | Sequence 12.50% -> **KEPT** (Stable, 0 mismatches)
  - **Iteration 3 (+ Data Flow links)**: Status 90.62% | Row 12.50% | Field 60.24% | Sequence 12.50% -> **KEPT** (Stable, 0 mismatches)
  - **Iteration 4 (All categories unconstrained)**: Status 87.50% | Row 12.50% | Field 58.84% | Sequence 12.50% -> **REVERTED** (Regression in status and field accuracy)
- **Final Linker Metrics**: Status 90.62% | Row 12.50% | Field 60.24% | Sequence 12.50%
2. Trace-correlated logs (case_03, 15, 17, 22): completion line (`rows=0`/`404`, `restore_allowed`, flow state) lacks the email; correlate by `trace_id` and take state from the completion event.
3. PDF/log support attachments (case_07, 10): no email token in the text; link via name/ticket/order references.
4. case_17 EXTRA account_6523 PRESENT: linkage through a shared token over-matches a decoy; needs temporal/exact-field link precision.
