# Design: Ghost Data Still Exists

## Scope for this phase

This is the pre-build architecture from the challenge contract and public samples. No implementation or prediction run has been started. The solution should remain deterministic and evidence-grounded; use a language model only if a required unstructured decision cannot be made reliably by explicit rules.

## Pipeline

1. **Load and validate inputs.** Read all CSVs under `dataset/` with explicit UTF-8 handling. Validate required columns, unique case IDs, evidence manifest paths, timestamps, and policy categories. Index the manifest by `file_id` and resolve only paths beneath `dataset/evidence/`.
2. **Request intent.** Classify request text before other processing. Non-erasure intents immediately yield `NOT_APPLICABLE` and `[]`. Use deterministic multilingual phrase/intent rules first; route only ambiguous requests to a small, cached classifier if available. Record provider/model, exact calls, token usage and estimated cost for any LLM use.
3. **Resolve identity.** Match supplied email to current `user_identities` and historical `user_audit_log` values. Build aliases valid over time (including email/hash/phone and any merge/link audit events), then connect evidence/activity by stable IDs and aliases. Avoid matching generic names or uncorroborated partial identifiers.
4. **Establish audit cutoff.** For each case, derive `audit_at`; discard any evidence/activity captured after that cutoff for state decisions. Preserve artifact capture timestamps separately from record timestamps. Later evidence may not rewrite earlier state.
5. **Extract evidence.** Parse JSON, text, logs and CSV-like fields natively; execute SQLite-compatible SQL snapshots in an isolated in-memory database and inspect primary/replica/reporting/failover tables; extract PDF text and fall back to OCR; OCR images (or use vision only if OCR is insufficient). Store normalized evidence facts with source ID, resource/system, identity keys, observed/captured time, state, category, and confidence/provenance. Activity records are investigative leads; status strings/results are not sufficient proof.
6. **Reconstruct resource state.** Combine direct snapshots/readbacks with dated events and identity matches into a point-in-time graph of user -> resource -> system, recording every supported PRESENT/ABSENT/REDACTED/ANONYMIZED/ACTIVE/DISABLED/BLOCKED/retained state and its evidence. Treat replica drift, old aliases, tombstones, active sync/import, and restore-capable backups as first-class cases. Resolve conflicting evidence conservatively and expose the conflict for deterministic handling.
7. **Apply policy.** Map each relevant resource to its data category and applicable condition in `deletion_rules.csv`. Translate DELETE/REDACT/ANONYMIZE/RETAIN into the exact required final state. Retained items are compliant only with permitted fields; tombstones retain the stable user reference but redact direct identifiers. Backup archives can remain only when restore access is blocked.
8. **Decide and plan.** If every relevant resource has compliant treatment, required retained records remain, and no recreation path is active, mark COMPLETE and emit verification-only steps with evidence IDs. Otherwise mark INCOMPLETE; emit all supported findings, then remediation actions, then future checks. Stop flows and block restores before modifying dependent records; remove downstream copies before source records where dependencies require it.
9. **Order and serialize.** Use contract operation order inside each phase, then stable ascending `(system_id, resource_id)` ordering, with explicit dependency constraints where prescribed. Emit exactly seven step fields and consecutive numbering. NOT_APPLICABLE produces `[]`.
10. **Validate output.** Require exact header, 518 unique sorted rows matching input case IDs, legal status/operation/state combinations, valid JSON arrays, exact step keys, consecutive numbers, phase/operation ordering, existing evidence IDs for findings/COMPLETE verification, and empty evidence IDs for incomplete remediation/future verification.

## Proposed module layout

`code/main.py` orchestrates; focused modules should cover `intent`, `identity`, `evidence` (format readers/OCR), `sql_audit`, `state_reconstructor`, `rules`, `steps`, and `validate`. Keep prompts in code/Markdown if a model is used. Keep `code/CONTEXT.md`, `code/notes/`, `DESIGN.md`, and evaluation reports up to date as phases progress. Cache expensive extraction/model results keyed by file hash and parameters so reruns are reproducible.

## Evaluation plan (later phase)

Build a sample evaluator that compares case/status accuracy, row-level exact match, field-level step accuracy, and sequence accuracy against `sample_output.csv`, with per-case diffs. Add at least three independent synthetic tests for: a historical alias with residual replica data; active restore that can recreate a deleted profile; and a non-deletion request. Run the full 518 rows only after sample behavior is understood; report label distribution, crashes, missing citations, ordering/serialization failures, and all model usage. The present phase has not run code or evaluation.

## Risks to verify before coding

- Public samples do not cover NOT_APPLICABLE intent and use a mix of evidence modalities; implement the contract, not just sample patterns.
- Evidence inventories include decoys, partial snapshots and timestamps after some audits; matching and cutoff enforcement must be explicit.
- Category identification may be distinct from a system name (for example, an analytics system can hold a non-analytics category); use record contents and evidence context.
- SQLite captures may contain multiple replicas and table layouts; query schema and snapshot scope instead of assuming one table name.
- OCR/vision may be needed, but inferred identities must be corroborated to avoid false joins.
- The preexisting untracked files under `code/` are not part of this phase's edits; inspect before integrating during implementation.
