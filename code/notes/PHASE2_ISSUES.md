# PHASE2_ISSUES.md — Edge Cases, Ambiguities, and Implementation Challenges

Documented edge cases identified during Phase 2 case derivations and sample analysis.

---

## 1. Temporal Cutoff (`audit_at`) Strict Enforcement
- **Issue**: Some evidence files (e.g. `evidence_06`) capture events dated after a case's `audit_at`.
- **Contract Rule**: Only evidence captured at or before `audit_at` can be cited or used.
- **Resolution**: Evidence indexer and query layer must strictly filter out any evidence file or log entry where `capture_time > audit_at`. When proving absence without pre-cutoff positive evidence, mark citation as empty string (`""`) for post-remediation verification.

## 2. Evidence Citation in Post-Remediation Steps
- **Issue**: Complete cases require citing evidence for verification, whereas incomplete cases prescribe future state post-remediation.
- **Contract Rule**: Complete cases cite participant-visible evidence (`file_id`, `activity_id`, `audit_id`). Incomplete cases use `evidence_id: ""` for proposed remediations and post-remediation verifications.
- **Resolution**: In step generation, set `evidence_id = ""` for all steps in `REMEDIATION` phase and for all `VERIFICATION` steps when `deletion_status == "INCOMPLETE"`.

## 3. Account Tombstone Handling (`rule_15`)
- **Issue**: When an account is deleted but retained records (e.g. audit logs, billing records) require a reference, an `ACCOUNT_TOMBSTONE` remains.
- **Contract Rule**: Prohibited direct identifiers (name, email, phone, email hash) must be removed, but the stable `user_id` is preserved.
- **Resolution**: Do not flag `account_tombstone` as `REPORT_REMAINING_RECORD` if only the stable reference remains. If direct identifiers are found in the tombstone, report `REPORT_EXPOSED_PII` -> `REDACT_RECORD`.

## 4. Multi-System Remediation Ordering
- **Issue**: Modifying a source before disabling sync can trigger automated replication or re-ingestion.
- **Contract Rule**: Disable data flows (`DISABLE_DATA_FLOW`) and block restore risks (`BLOCK_RESTORE`) before remediating records (`DELETE_RECORD`, `REDACT_RECORD`, `ANONYMIZE_RECORD`).
- **Resolution**: Implemented via deterministic phase and operation priority ranking in `step_rules.yaml`.

## 5. Non-English & Ambiguous Request Texts
- **Issue**: Request text in `deletion_requests.csv` can be in different languages (German, French, Spanish, Japanese, Korean, Arabic, etc.).
- **Contract Rule**: Identify whether request authorizes deletion. Access, export, or correction requests must yield `NOT_APPLICABLE`.
- **Resolution**: Multilingual keyword matching and strict non-deletion negative filters in `code/intent.py`.
