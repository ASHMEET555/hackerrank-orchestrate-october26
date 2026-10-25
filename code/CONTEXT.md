# Project context: Ghost Data Still Exists

## Contract

This is a deterministic deletion-audit task. Read requests from `dataset/deletion_requests.csv`; produce exactly one root `output.csv` row per request (518), sorted by `case_id`, with the exact header `case_id,deletion_status,steps_json`. Status is `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`. A non-deletion request is `NOT_APPLICABLE` with `[]`. Each step has exactly `step_no`, `phase`, `system_id`, `resource_id`, `operation`, `state`, and `evidence_id`; numbers are consecutive from 1. Phase order is FINDING, REMEDIATION, VERIFICATION. Only information available at or before `audit_at` may decide the state. Workflow statuses and activity results are claims, not proof.

For COMPLETE cases, emit only evidence-backed VERIFICATION steps. For INCOMPLETE cases, include every supported finding, the ordered complete remediation plan, and future verification for the relevant subject resources/processes. Findings cite a participant-facing file/activity/audit ID. Incomplete-case remediation and future verification have `evidence_id: ""`; complete verification cites evidence. Do not use organizer-only material.

Allowed operations/states and their required ordering within a phase are in `problem_statement.md` §6.4 (also summarized in `notes/inferred_rules.md`). Sort by operation order, then `system_id`, then `resource_id`. Dependencies require disabling data flows/blocking restores before changing dependent records, and downstream copies before sources when needed.

## Participant-facing CSVs and schemas

All paths below are under `dataset/`.

| CSV | Rows | Columns | Role |
|---|---:|---|---|
| `deletion_requests.csv` | 518 | `case_id,email,requested_at,reported_status,reported_at,audit_at,request_text` | Evaluation inputs. Reported status is untrusted; request text decides scope. |
| `sample_deletion_requests.csv` | 32 | same as evaluation requests | Public examples. |
| `sample_output.csv` | 32 | `case_id,deletion_status,steps_json` | Canonical public examples; 10 COMPLETE and 22 INCOMPLETE, no NOT_APPLICABLE example. |
| `user_identities.csv` | 850 | `user_id,name,email,phone,email_hash,updated_at` | Current identity snapshot. |
| `user_audit_log.csv` | 306 | `audit_id,user_id,event_time,field_name,old_value,new_value` | Historical values; fields include email (107), email_hash (107), phone (92). |
| `system_activity.csv` | 4,011 | `activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details` | Broad operational stream, with decoys; use as leads and respect time cutoff. |
| `deletion_rules.csv` | 15 | `rule_id,data_category,condition,required_action` | Policy map; full entries below and in `notes/inferred_rules.md`. |
| `evidence_files.csv` | 94 | `file_id,file_path,origin,captured_at` | Manifest mapping IDs to evidence paths/time. |
| `output.csv` | 0 data rows | blank template | Header/template only; final output belongs in repository root. |

Request reported-status counts: COMPLETE 254, PARTIALLY_COMPLETE 152, NOT_STARTED 112. Activity event counts: DELETE_RECORD 890, UPDATE_RECORD 672, SYNC_RECORD 447, INDEX_RECORD 400, SEND_EMAIL 368, REFRESH_CACHE 284, RETAIN_RECORD 206, ANONYMIZE_RECORD 204, REDACT_RECORD 173, CREATE_EXPORT 155, CHECK_DATA_FLOW 89, DISABLE_DATA_FLOW 36, BLOCK_RESTORE 36, CHECK_RESTORE_ACCESS 28, LINK_RESOURCE_IDENTITY 12, CLASSIFY_REQUEST 10, RESTORE_BACKUP 1. `reported_result` is SUCCESS 2914, FAILED 721, PARTIAL 376; these remain claims without corroborating state evidence.

## Policy rules (verbatim action and condition)

| rule | category | condition | action |
|---|---|---|---|
| rule_01 | USER_PROFILE | Always | DELETE |
| rule_02 | SECONDARY_IDENTIFIER | Always | DELETE |
| rule_03 | SEARCH_INDEX_ENTRY | Always | DELETE |
| rule_04 | CACHE_ENTRY | Always | DELETE |
| rule_05 | SUPPORT_MESSAGE | Conversation contains shared customer, agent, or order context that must be retained | REDACT |
| rule_06 | SUPPORT_ATTACHMENT | Attachment belongs only to the deletion subject | DELETE |
| rule_07 | ANALYTICS_PROFILE | Record is still attributable to a user | ANONYMIZE |
| rule_08 | PRODUCT_TELEMETRY | Record is still attributable to a user | ANONYMIZE |
| rule_09 | USER_EXPORT | Always | DELETE |
| rule_10 | MARKETING_PROFILE | Always | DELETE |
| rule_11 | EMAIL_DELIVERY_LOG | Log contains a user email address | REDACT |
| rule_12 | SECURITY_AUDIT_LOG | Record is within the supplied retention period | RETAIN |
| rule_13 | LEGAL_HOLD_RECORD | A supplied legal hold is active | RETAIN |
| rule_14 | BACKUP_ARCHIVE | Restore access can be blocked | RETAIN |
| rule_15 | ACCOUNT_TOMBSTONE | Account is deleted and only a stable internal user_id is needed to preserve references to retained records | REDACT |

Tombstone treatment preserves `user_id` only and removes direct identifiers. Retention is not a deletion failure when policy requires the record; still verify required retained records remain.

## Evidence inventory

The manifest maps every supplied file: 94/94 paths exist and there are no unmapped evidence files. Types: 28 JSON, 26 LOG, 24 SQL, 11 PNG, 4 PDF, 1 TXT. SQL files are SQLite-compatible and represent primary, read/regional/reporting/failover snapshots. Images/PDFs are business artifacts and may need OCR or text extraction. Evidence must be joined by actual contents/identity/resource/time, not by manifest metadata alone. Never use an artifact captured after a case's `audit_at`.

## Sample-derived rules and edge cases

See `code/notes/inferred_rules.md` for case-by-case evidence and step summaries. Notable patterns:

- `case_01` and `case_02`: account absence alone can support COMPLETE; a workflow claim can be wrong in either direction (`case_02` is complete despite PARTIALLY_COMPLETE).
- `case_05`: workflow COMPLETE does not override a current failover replica row; report it and remediate.
- `case_03`, `case_21`, `case_25`–`case_28`, `case_31`: a complete answer may include proof of account absence plus required retained, anonymized, redacted, disabled, or restore-blocked state.
- `case_11`, `case_18`, `case_29`, `case_30`: findings can mix record remaining, exposed PII, active data flow; remediation disables flow first, then handles downstream resources by policy.
- `case_09`, `case_14`, `case_17`: retained backup is acceptable if restore access is blocked; report restore risk and block it.
- `case_31`/`case_32`: compliant/incompliant tombstones are distinguished by direct identifiers while the stable subject reference remains.
- `case_12` demonstrates an analytics record may require deletion when evidence/category context establishes a different record treatment than a default category rule; determine exact category and policy condition from evidence.
- Global logs, identities, activities, snapshots and resources contain unrelated decoys; identity matching and cutoffs are required.
- The 32 public examples contain no non-deletion request, so intent classification must generalize from the contract rather than sample labels.

## Decisions and open risks

- Deterministic-first; no model calls are needed for the facts/policy that can be grounded in structured evidence. Consider a model only if needed for multilingual request intent or genuinely ambiguous unstructured evidence, with calls logged and cached.
- Evidence extraction must support JSON/text/log, SQLite SQL, PDF text plus OCR fallback, and image OCR/vision. Keep raw personal data out of persistent notes and reports.
- Data at audit time is reconstructed from dated artifact contents and corroborated event trails; later snapshots must not leak into earlier answers.
- Work session started on existing `main` checkout, then moved to `codex/phase1-2`. Existing untracked code modules were present before this phase and were not edited or staged.
- No build/evaluation failures have been run in this phase. Known open validation: understand all resource/evidence modalities and confirm policy condition handling before implementation; create >=3 custom tests later.

## Available tools and intended use

The environment exposes filesystem/terminal/patch tools, clock, image inspection/generation, web search, and Notion/document-control/pets/plugin-management/safety-settings MCPs. For this repository, use `exec_command` for read-only inventory, Git, and eventually local runs; `apply_patch` for reviewable markdown/source edits; `clock__curr_time` for accurate timestamps; `view_image` for local visual evidence inspection. `web__run` is reserved for explicitly useful public research, not evidence already in `dataset/`. No Playwright tool is exposed. Notion/document-control/pets/plugin-management/safety-settings tools are unrelated and will not be used. See `notes/tool_inventory.md` for the exact exposed function names.
