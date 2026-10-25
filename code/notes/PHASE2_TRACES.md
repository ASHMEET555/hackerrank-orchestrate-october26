# PHASE2_TRACES.md — Representative End-to-End Execution Traces

Detailed walkthrough of key archetype cases from `sample_output.csv` demonstrating the full audit lifecycle:
1. Intent & subject resolution
2. Multi-system evidence grounding
3. Finding detection
4. Remediation planning
5. Verification formulation

---

## 1. Archetype 1: Clean Deletion (COMPLETE) — `case_01`
- **Request**: `amina.elmasri@gmail.com`
- **Intent**: Deletion requested and authorized.
- **Subject Resolution**: Matches `user_01` in `user_identities.csv`. Resource `account_001`.
- **Evidence Consulted**: `evidence_54` (SQL snapshot). Lookups in `customer_profiles_primary` and `customer_profiles_failover_replica` return 0 rows for `account_001`.
- **Status Verdict**: `COMPLETE`.
- **Output Steps**:
  1. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_001` `ABSENT` `evidence_54`

---

## 2. Archetype 2: Remaining Un-deleted Primary Data (INCOMPLETE) — `case_05`
- **Request**: `leila.haddad@yahoo.com`
- **Intent**: Deletion requested and authorized.
- **Subject Resolution**: Matches `user_05` in `user_identities.csv`. Resource `account_005`.
- **Evidence Consulted**: `evidence_54` (SQL snapshot). Table `customer_profiles_failover_replica` has active record for `account_005`. Replication drift caused failover replica to retain user profile.
- **Status Verdict**: `INCOMPLETE`.
- **Output Steps**:
  1. `FINDING` `REPORT_REMAINING_RECORD` `account_service/account_005` `PRESENT` `evidence_54`
  2. `REMEDIATION` `DELETE_RECORD` `account_service/account_005` `ABSENT` `""`
  3. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_005` `ABSENT` `""`

---

## 3. Archetype 3: Complex Multi-System Drift with Active Sync & Unredacted PII — `case_11`
- **Request**: `novak.tomasz@icloud.com`
- **Intent**: Deletion requested.
- **Subject Resolution**: Matches `user_32`.
- **Evidence Consulted**: `evidence_03` (structured log).
  - `account_service/account_4248`: `NOT_FOUND` (deleted)
  - `search_service/search_052`: `FOUND` (search index remaining)
  - `support_platform/support_864`: `IDENTIFIABLE` (support message unredacted)
  - `analytics_platform/analytics_2034`: `IDENTIFIABLE` (analytics profile unanonymized)
  - `integration_service/data_flow_9522`: `ACTIVE` (active synchronization bridge)
  - `security_service/audit_record_9394`: `FOUND` (audit log within retention)
- **Status Verdict**: `INCOMPLETE`.
- **Output Steps**:
  - Findings: search index remaining, analytics & support exposed PII, active data flow.
  - Remediation order:
    1. `DISABLE_DATA_FLOW` `integration_service/data_flow_9522` (stop ingestion/recreation first)
    2. `DELETE_RECORD` `search_service/search_052`
    3. `REDACT_RECORD` `support_platform/support_864`
    4. `ANONYMIZE_RECORD` `analytics_platform/analytics_2034`
  - Post-remediation Verifications: confirm account absent, search absent, audit record retained, support redacted, analytics anonymized, data flow disabled.

---

## 4. Archetype 4: Restore Risk via Backup Archive — `case_14`
- **Request**: `y.tanaka32@gmail.com`
- **Intent**: Deletion requested.
- **Subject Resolution**: Matches `user_37`.
- **Evidence Consulted**: `evidence_03`.
  - `account_service/account_3677`: absent.
  - `backup_service/backup_3870`: `ACTIVE` (restore allowed, no deletion block).
  - `security_service/audit_record_987`: retained audit log.
- **Status Verdict**: `INCOMPLETE`.
- **Output Steps**:
  1. `FINDING` `REPORT_RESTORE_RISK` `backup_service/backup_3870` `ACTIVE` `evidence_03`
  2. `REMEDIATION` `BLOCK_RESTORE` `backup_service/backup_3870` `BLOCKED` `""`
  3. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_3677` `ABSENT` `""`
  4. `VERIFICATION` `VERIFY_RECORD_PRESENT` `security_service/audit_record_987` `PRESENT` `""`
  5. `VERIFICATION` `VERIFY_RESTORE_BLOCKED` `backup_service/backup_3870` `BLOCKED` `""`

---

## 5. Archetype 5: Non-Deletion Request (NOT_APPLICABLE) — `case_29`..`case_32`
- **Request**: Inquiries regarding data access, marketing preferences, or general account questions.
- **Intent**: Does NOT authorize deletion.
- **Status Verdict**: `NOT_APPLICABLE`.
- **Output Steps**: `[]` (empty JSON array).
