# Build Handoff: Ghost Data Still Exists

## Objective

Build a deterministic, evidence-grounded auditor for the 518 rows in `dataset/deletion_requests.csv`. The program must decide whether each request authorizes deletion, resolve current and historical identities, establish compliant data state at `audit_at`, and write root `output.csv` with the exact contract. This plan is intended for the implementation agent to follow. Read the root `AGENTS.md` and this file before changing code.

## Repository state at handoff

- Work is on branch `codex/phase1-2`; discovery/design commit: `4a7000e`.
- The repository was already initialized. Existing untracked files were present in `code/` before this plan was updated: `evidence_index.py`, `identity.py`, `intent.py`, `rules_engine.py`, `sql_audit.py`, `state_reconstructor.py`, `step_builder.py`, and root `log.txt`. Inspect each file and `git status` before editing. Preserve useful work and do not reset, overwrite, stage, or commit unrelated user changes.
- Phase 1 and dataset discovery are complete. No prediction run or tests have been performed yet.

## Non-negotiable contract

- Input: all requests from `dataset/deletion_requests.csv`; 518 unique case IDs.
- Root output: exact header `case_id,deletion_status,steps_json`; exactly one row per input, sorted by `case_id`.
- Status: `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`. A non-deletion request is `NOT_APPLICABLE` with `[]`.
- Every step object has exactly seven keys: `step_no`, `phase`, `system_id`, `resource_id`, `operation`, `state`, `evidence_id`. Number consecutively from 1. Use only allowed phases, operations and states from `problem_statement.md` §6.4.
- Phase order: FINDING, REMEDIATION, VERIFICATION. Within a phase, follow the contract's operation order, then ascending `system_id` and `resource_id`; honor the required dependency order (disable flows/block restores before modifying dependent data, and downstream copies before sources where applicable).
- Operation order: FINDING `REPORT_REMAINING_RECORD`, `REPORT_EXPOSED_PII`, `REPORT_ACTIVE_DATA_FLOW`, `REPORT_RESTORE_RISK`; REMEDIATION `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `DELETE_RECORD`, `REDACT_RECORD`, `ANONYMIZE_RECORD`; VERIFICATION `VERIFY_RECORD_ABSENT`, `VERIFY_RECORD_PRESENT`, `VERIFY_RECORD_REDACTED`, `VERIFY_RECORD_ANONYMIZED`, `VERIFY_DATA_FLOW_DISABLED`, `VERIFY_RESTORE_BLOCKED`.
- COMPLETE emits only evidence-backed verification. INCOMPLETE emits supported findings, a complete remediation plan, and future verification. Findings cite a participant-visible `file_id`, `activity_id`, or `audit_id`. Remediation and future verification in an INCOMPLETE case use `evidence_id: ""`; COMPLETE verification cites evidence. Never cite evidence captured after `audit_at`.
- Workflow statuses and activity `reported_result` values are claims, not proof. Use only participant-facing files under `dataset/`; organizer-only data is prohibited.
- Apply every applicable row/condition from `deletion_rules.csv`. Preserve required security/legal records. A tombstone retains the stable `user_id` reference but removes direct identifiers. A retained backup is acceptable only when restore access is blocked.

## Evidence-based implementation principles

1. Keep artifact capture time, record/event time, identity change time, and `audit_at` distinct. Enforce the cutoff for each source; don't let later data influence an earlier audit.
2. Don't use a blanket “earliest file wins” rule. Prefer direct, resource-specific state evidence whose record and capture times fit the audit; compare snapshot topology and timestamps. When evidence conflicts, retain provenance and resolve using explicit, documented rules. Activity rows can guide lookup, but a SUCCESS/FAILED claim alone doesn't establish resulting state.
3. Join evidence through supported aliases, stable user/resource references, hashes, and exact IDs. Avoid name-only, partial-string, or guessed matches. Treat unrelated global records as decoys until linked by evidence.
4. Determine the resource's data category and policy condition from its contents and context. A system name alone does not establish category (for example, not every analytics-platform resource is necessarily an ANALYTICS_PROFILE).
5. Prefer deterministic local parsers. Do not assume or call a paid vision API. Extract PDF text first and use local OCR for image/PDF scans where available; if a case cannot be grounded, record the gap and only consider an external model if the owner has configured and authorized it. Never put secrets in source, prompts, or logs.
6. A reported active flow or restore path is a risk only when linked to the subject and supported at the cutoff. Include every supported policy violation and recreation path; don't hardcode sample case IDs or a fixed sample “skeleton.”

## Proposed module boundaries

| Module | Responsibility |
|---|---|
| `code/main.py` | Load inputs, build/reuse indexes, process every request, validate and write root output. |
| `code/intent.py` | Deletion authorization; explicit non-deletion handling and multilingual cases. |
| `code/identity.py` | Resolve subject and time-valid aliases from request email, identities and audit history. |
| `code/evidence_index.py` | Manifest-safe file loading; normalized facts with evidence ID, system/resource, category, identity keys, capture/observation time, state and provenance. |
| `code/sql_audit.py` | Load SQLite-compatible snapshots in memory; inspect schema/snapshot scope and compare primary, regional, reporting, read and failover replicas. |
| `code/state_reconstructor.py` | Join supported facts and reconstruct point-in-time resource/process state. |
| `code/rules_engine.py` | Apply category/condition policy and classify compliant resources vs violations. |
| `code/step_builder.py` | Build phase-ordered findings, remediation and verification; set correct IDs and evidence rules. |
| `code/validate.py` | Enforce output schema, row coverage, legal operations/states, evidence validity, numbering and ordering. |
| `code/evaluation/main.py` | Compare public sample answers at case, row, field and sequence levels; print per-case diffs. |

Reuse the preexisting untracked modules where sound; adjust module names only if the repository structure calls for it. Keep prompts in source or Markdown. Cache deterministic extraction by file hash and model results (if any) by stable inputs. Log actual provider/model, call counts, input/output tokens and actual cost assumptions for the usage report.

## Implementation sequence and completion gates

### Phase A — Inspect and stabilize the starting tree

1. Read `AGENTS.md` in full and follow its root `log.txt` append-only requirements for every turn.
2. Inspect `git status`, the existing untracked modules, and available local dependencies before changing files. Do not discard the current branch or existing user work.
3. Confirm the already committed setup artifacts and the CSV/evidence counts recorded in `code/CONTEXT.md`.

**Gate:** agree on which existing modules to reuse and document dependencies/run command. Do not begin with an external model choice.

### Phase B — Evidence readers and point-in-time facts

1. Implement/repair manifest-safe readers for JSON, TXT, logs, SQL, PDFs and PNGs. Current manifest inventory is 94 files: 28 JSON, 26 LOG, 24 SQL, 11 PNG, 4 PDF, 1 TXT. Validate the paths rather than relying on guessed type counts.
2. Parse PDFs locally before OCR; attempt local OCR for screenshots/scans. Avoid transmitting dataset contents to an external model by default.
3. For each SQL file, inspect tables and capture metadata, then query all relevant topologies. Do not assume table names are identical across snapshots.
4. Normalize extracted facts while preserving original evidence ID, capture timestamp, record timestamp, exact resource/system, and identity match reason. Use `system_activity.csv` as leads, not proof of successful operation.

**Gate:** inspect representative evidence from every format and verify that capture-time cutoff and replica differences are represented in the index.

### Phase C — Intent and identity resolution

1. Implement intent rules from the contract. Include explicit access/correction/export/marketing opt-out cases as non-deletion. Public samples have 32/32 deletion-authorized requests, so sample accuracy cannot validate this branch.
2. Link request email to a stable subject through exact current or historical identifiers. Process only identity/audit facts available by `audit_at`; account for snapshot `updated_at` and audit `event_time`. Preserve aliases and their validity/provenance rather than flattening away time.
3. Follow resource links only when supported by stable user IDs, hashes, audit history or explicit evidence references.

**Gate:** manually inspect historical-email examples (including sample `case_10`) and a newly authored non-deletion case; show the resolved alias chain and cutoff.

### Phase D — State, policy and plans

1. Reconstruct state for each relevant resource at `audit_at`, including account profiles, second identifiers, search/cache, support messages/attachments, exports, marketing, analytics/telemetry, delivery logs, security/legal retention, tombstones, data flows and backups.
2. Apply the exact policy action and its condition. Examples: shared support context -> REDACT; subject-only attachment -> DELETE; attributable analytics/telemetry -> ANONYMIZE; retained security/legal record -> preserve; tombstone -> redact direct identifiers but keep stable reference; backup -> retain only with restore blocked.
3. Decide COMPLETE only if all relevant copies have required treatment, required retained records remain, and no active sync/import/restore can recreate prohibited data. Otherwise report all supported violations/risks.
4. Build steps using contract operation ordering and dependencies. For incomplete requests, include required subject/account and retained-record verification when supported/required, plus every remediated resource/process; don't copy a fixed sample list into every case.

**Gate:** manually trace several cases across independent formats, including a replica residue, an alias match, a tombstone, a shared support record, and a recreation path. For each generated finding, identify the participant-visible evidence that supports it.

### Phase E — Evaluation and correction

1. Implement `code/evaluation/main.py` to compare against `dataset/sample_output.csv`: case accuracy (status per case ID), row accuracy (all output columns match for a case), field accuracy (individual step fields/objects), and sequence accuracy (the ordered steps match exactly). Print detailed per-case diffs.
2. Run against all 32 samples, categorize every discrepancy, fix general rules, rerun, and record each iteration's metrics and changes. Do not set a loose target such as 90% as a stopping criterion; explain any remaining mismatch and seek exact public-sample agreement without case-ID shortcuts.
3. Add at least three independent custom cases with explicit expected outcomes and results: (a) historical alias + replica residue; (b) restore path that could recreate data; (c) non-deletion intent. Keep expected cases in human-readable Markdown/source, not only ignored raw data.
4. Add a validator and perform a full 518-row dry run only after sample-level behavior is understood. Check status distribution, row coverage, crashes, evidence IDs, cutoff violations, JSON, steps and ordering.

**Gate:** document measured evaluation definitions/results, custom cases, failures, and improvements. Sample metrics are not a guarantee of hidden-set accuracy.

### Phase F — Final run and packaging

1. Run `python3 code/main.py` from the repository root; write `output.csv` at root.
2. Validate exact header, 518 rows, sorted unique IDs, legal statuses, JSON arrays, exact step fields, consecutive numbering, phase/operation order, and evidence-ID rules. Check no finding is unsupported and no evidence postdates its case cutoff.
3. Write `code/evaluation/evaluation_report.md` and `code/evaluation/usage_report.md` (the repository README's required location). The usage report must describe the actual final full-dataset run; if no model is used, state zero calls/tokens and zero model cost rather than an estimate from a plan.
4. Update the runnable `README.md` with setup/run instructions. Build `code.zip` with README and code only; exclude dataset, virtual environments, caches, and nested archives. Keep root `output.csv` and `log.txt` as separate submission artifacts.
5. Run the repository's final checklist from `README.md` and record the result. Commit coherent implementation phases without accidentally adding the dataset or unrelated preexisting files.

**Gate:** the output validator passes every case; required reports exist at the exact path; archive contents are inspected; root log has the required format and contains no secrets.

## Sample-derived checks (examples, not case shortcuts)

- `case_02`: COMPLETE despite PARTIALLY_COMPLETE workflow claim; `case_05`: INCOMPLETE despite COMPLETE claim due to failover residue.
- `case_09`, `case_14`, `case_17`: backup may remain if restore access is blocked.
- `case_11`, `case_18`, `case_29`, `case_30`: mixed remaining record, PII exposure and active-flow findings; remediation follows policy.
- `case_31`/ `case_32`: tombstone is compliant only when direct identifiers are removed while stable reference remains.
- `case_12`: do not infer action from “analytics” system name alone; trace resource category and context to the policy.
- No sample covers NOT_APPLICABLE; custom intent tests are mandatory.

For all 32 detailed sample evidence and step patterns, see `code/notes/inferred_rules.md`. The exact contract remains `problem_statement.md` and `README.md`.
