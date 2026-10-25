# Evaluation Report

## Executive Summary
This report summarizes the evaluation metrics for the Ghost Data deletion audit engine across the reference sample cases, structural checks on the full 518 evaluation dataset predictions, link progression history, and known engine limitations.

---

## 1. Sample Metrics (32 Reference Cases)
Evaluated via `code/evaluation/main.py` against `dataset/sample_output.csv`:

| Metric | Score | Target |
|---|---|---|
| **Status Accuracy** | **90.62%** | 100.00% |
| **Row Accuracy** | **12.50%** | 100.00% |
| **Field Accuracy** | **60.24%** | 100.00% |
| **Sequence Accuracy** | **12.50%** | 100.00% |

- **Cases Evaluated**: 32
- **Accurate Deletion Status**: 29 / 32 cases
- **Accurate Exact Row Steps**: 4 / 32 cases

---

## 2. Link Progression History
Recorded from iterative link tuning in `code/notes/ENGINE_CHANGELOG.md`:

| Iteration / Link Type | Status Accuracy | Row Accuracy | Field Accuracy | Sequence Accuracy | Subject Mismatches | Action |
|---|---|---|---|---|---|---|
| **Baseline (pre-linker)** | 87.50% | 12.50% | 58.84% | 12.50% | 0 | Initial scaffold |
| **Iteration 1 (+ Support)** | 90.62% | 12.50% | 60.24% | 12.50% | 0 | **KEPT** (+3.12% Status, +1.40% Field) |
| **Iteration 2 (+ Analytics)** | 90.62% | 12.50% | 60.24% | 12.50% | 0 | **KEPT** (Stable, zero regressions) |
| **Iteration 3 (+ Data Flow)** | 90.62% | 12.50% | 60.24% | 12.50% | 0 | **KEPT** (Stable, zero regressions) |
| **Iteration 4 (All Unconstrained)** | 87.50% | 12.50% | 58.84% | 12.50% | 0 | **REVERTED** (Regression) |

---

## 3. Custom Evaluation Cases
Existing unit test cases in `tests/`:

| Test Suite | Tests Collected | Passed | Failed | Status |
|---|---|---|---|---|
| `tests/test_evaluation.py` | 1 | 1 | 0 | **PASS** |
| `tests/test_intent_identity.py` | 4 | 4 | 0 | **PASS** |
| `tests/test_phase6.py` | 3 | 3 | 0 | **PASS** |
| `tests/test_readers.py` | 6 | 6 | 0 | **PASS** |
| `tests/test_step_builder.py` | 3 | 3 | 0 | **PASS** |
| `tests/test_validate.py` | 17 | 17 | 0 | **PASS** |
| **Total** | **34** | **34** | **0** | **PASS** |

*Note: No additional external benchmark cases were added.*

---

## 4. Failures Found and Trace Checks
- **Failures Logged (`code/notes/failures.md`)**: **52** items
  - `[IDENTITY_RESOLUTION]`: 2 (user identifiers `user_03`, `user_18` appearing in PDF text lines excluded from resource state)
  - `[UNGROUNDED]`: 6 (`legal_hold_*` records in SQL/JSON lacking explicit `hold_status` field under Decision D1)
  - `[UNKNOWN_CLASSIFICATION]`: 44 (`analytics_*` and `support_*` records in `unknown_service` database tables under Decision D5)
- **Trace Verification (`code/notes/TRACE_CHECKS.md`)**:
  - Sample trace checks passing: 30 / 32
  - Cases failing trace verification: 2 (`case_31`, `case_32` due to tombstone and account verification citation differences)

---

## 5. Structural Validation on Full Dataset (`output.csv`)
Validation run using `code/validate.py output.csv --expected-count 518`:
- **Total Rows**: 518
- **Validation Errors**: **0**
- **Output Structure Checks (`code/tools/check_output_structure.py`)**:
  - Header: `case_id,deletion_status,steps_json` (exact match)
  - Unique Case IDs: 518 / 518
  - Lexicographic String Sort: Ascending (verified)
  - Valid JSON Array per row: 518 / 518
  - INCOMPLETE Rows with >= 1 step: 370 / 370
  - NOT_APPLICABLE Rows with `[]`: 10 / 10
  - Rows with `UNKNOWN_CLASSIFICATION`: 0

**Status Distribution (518 Cases)**:
- `COMPLETE`: 138 (26.6%)
- `INCOMPLETE`: 370 (71.4%)
- `NOT_APPLICABLE`: 10 (1.9%)

---

## 6. Known Limitations
1. **Low Row and Sequence Accuracy (12.50%)**:
   - The current engine linker is constrained to support, analytics, and data-flow resources using direct identifiers.
   - Missing verified account-absent proofs (absence-by-omission) for cases where account profiles were deleted from primary tables without affirmative deletion tombstones.
   - Missing security audit record verification steps for retained logs.
2. **Open Owner Decisions**:
   - 5 decisions remain under owner override in `code/notes/DECISIONS.md` (D1: legal hold date math, D2: shared name attachments, D3: trace correlation citation, D4: absence-by-omission proof, D5: unknown_service table categorization).
3. **Phases 6 and 7 Gates**:
   - Engine was developed under strict ground rules without circular expected-output tuning; gates requiring 100% row match on sample outputs remain incomplete pending owner decisions.
