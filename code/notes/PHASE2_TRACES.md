# PHASE2_TRACES.md — Representative End-to-End Execution Traces

Detailed walkthrough of 7 key archetype cases from `dataset/sample_output.csv` demonstrating the full audit lifecycle:
1. Intent & subject resolution
2. Multi-system evidence grounding
3. Finding detection
4. Remediation planning
5. Verification formulation

---

## 1. Trace 1: Clean Deletion (COMPLETE) — `case_01`
- **Request**: `amina.elmasri@gmail.com`
- **State at audit_at**:
  - `account_service/account_001` = `ABSENT` (verified absent via `evidence_54` tables `customer_profiles_failover_replica` (4 rows) and `customer_profiles_primary` (3 rows): no row matching `account_001`).
- **Rule applied**: `rule_01` (`USER_PROFILE` -> `DELETE`).
- **Resulting steps**:
  1. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_001` `ABSENT` `evidence_54`

---

## 2. Trace 2: Replication Drift in Primary Database (INCOMPLETE) — `case_05`
- **Request**: `leila.haddad@yahoo.com`
- **State at audit_at**:
  - `account_service/account_005` = `PRESENT` (`evidence_54` table `customer_profiles_failover_replica` row `{'resource_id': 'account_005', 'user_id': 'user_05', 'full_name': 'Leila Haddad', 'account_status': 'ACTIVE'}`).
- **Rule applied**: `rule_01` (`USER_PROFILE` -> `DELETE`).
- **Resulting steps**:
  1. `FINDING` `REPORT_REMAINING_RECORD` `account_service/account_005` `PRESENT` `evidence_54`
  2. `REMEDIATION` `DELETE_RECORD` `account_service/account_005` `ABSENT` `""`
  3. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_005` `ABSENT` `""`

---

## 3. Trace 3: Historical Evidence Cutoff & Restore Risk (INCOMPLETE) — `case_09`
- **Request**: `k.appiah88@gmail.com`
- **State at audit_at**:
  - `backup_service/backup_4978` = `ACTIVE` (`evidence_93` table `backup_restore_entries` row `{'resource_id': 'backup_4978', 'restore_allowed': 1}`).
  - `account_service/account_3960` = `ABSENT` (negative sweep at cutoff; note: `evidence_06` line 86 confirms 404 but captured 2026-09-18 > `audit_at` 2026-09-16, so cannot be cited; citation empty).
  - `security_service/audit_record_4902` = `PRESENT` (retained security audit log within retention period).
- **Rules applied**: `rule_01` (`USER_PROFILE` -> `DELETE`), `rule_14` (`BACKUP_ARCHIVE` -> `RETAIN`), `rule_12` (`SECURITY_AUDIT_LOG` -> `RETAIN`).
- **Resulting steps**:
  1. `FINDING` `REPORT_RESTORE_RISK` `backup_service/backup_4978` `ACTIVE` `evidence_93`
  2. `REMEDIATION` `BLOCK_RESTORE` `backup_service/backup_4978` `BLOCKED` `""`
  3. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_3960` `ABSENT` `""`
  4. `VERIFICATION` `VERIFY_RECORD_PRESENT` `security_service/audit_record_4902` `PRESENT` `""`
  5. `VERIFICATION` `VERIFY_RESTORE_BLOCKED` `backup_service/backup_4978` `BLOCKED` `""`

---

## 4. Trace 4: Complex Multi-System Drift with Active Sync & Unredacted PII (INCOMPLETE) — `case_11`
- **Request**: `novak.tomasz@icloud.com`
- **State at audit_at**:
  - `account_service/account_4248` = `ABSENT` (`evidence_03` line 11: `account_service | account_4248 | USER_PROFILE | NOT_FOUND`).
  - `search_service/search_052` = `PRESENT` (`evidence_03` line 26: `search_service | search_052 | SEARCH_INDEX_ENTRY | FOUND`).
  - `analytics_platform/analytics_2034` = `PRESENT` (`evidence_03` line 16: `analytics_platform | analytics_2034 | ANALYTICS_PROFILE | IDENTIFIABLE`).
  - `support_platform/support_864` = `PRESENT` (`evidence_03` line 46: `support_platform | support_864 | SUPPORT_MESSAGE | IDENTIFIABLE`).
  - `integration_service/data_flow_9522` = `ACTIVE` (`evidence_03` line 25: `integration_service | data_flow_9522 | DATA_FLOW | ACTIVE`).
  - `security_service/audit_record_9394` = `PRESENT` (`evidence_03` line 40: `security_service | audit_record_9394 | SECURITY_AUDIT_LOG | FOUND`).
- **Rules applied**: `rule_01`, `rule_03`, `rule_07`, `rule_05`, `rule_12`, and `DATA_FLOW` disable policy.
- **Resulting steps**:
  1. `FINDING` `REPORT_REMAINING_RECORD` `search_service/search_052` `PRESENT` `evidence_03`
  2. `FINDING` `REPORT_EXPOSED_PII` `analytics_platform/analytics_2034` `PRESENT` `evidence_03`
  3. `FINDING` `REPORT_EXPOSED_PII` `support_platform/support_864` `PRESENT` `evidence_03`
  4. `FINDING` `REPORT_ACTIVE_DATA_FLOW` `integration_service/data_flow_9522` `ACTIVE` `evidence_03`
  5. `REMEDIATION` `DISABLE_DATA_FLOW` `integration_service/data_flow_9522` `DISABLED` `""`
  6. `REMEDIATION` `DELETE_RECORD` `search_service/search_052` `ABSENT` `""`
  7. `REMEDIATION` `REDACT_RECORD` `support_platform/support_864` `REDACTED` `""`
  8. `REMEDIATION` `ANONYMIZE_RECORD` `analytics_platform/analytics_2034` `ANONYMIZED` `""`
  9. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_4248` `ABSENT` `""`
  10. `VERIFICATION` `VERIFY_RECORD_ABSENT` `search_service/search_052` `ABSENT` `""`
  11. `VERIFICATION` `VERIFY_RECORD_PRESENT` `security_service/audit_record_9394` `PRESENT` `""`
  12. `VERIFICATION` `VERIFY_RECORD_REDACTED` `support_platform/support_864` `REDACTED` `""`
  13. `VERIFICATION` `VERIFY_RECORD_ANONYMIZED` `analytics_platform/analytics_2034` `ANONYMIZED` `""`
  14. `VERIFICATION` `VERIFY_DATA_FLOW_DISABLED` `integration_service/data_flow_9522` `DISABLED` `""`

---

## 5. Trace 5: Backup Archive Restore Risk (INCOMPLETE) — `case_14`
- **Request**: `y.tanaka32@gmail.com`
- **State at audit_at**:
  - `account_service/account_3677` = `ABSENT` (`evidence_03` line 9: `account_service | account_3677 | USER_PROFILE | NOT_FOUND`).
  - `backup_service/backup_3870` = `ACTIVE` (`evidence_03` line 19: `backup_service | backup_3870 | BACKUP_ARCHIVE | ACTIVE | y.tanaka32@gmail.com`).
  - `security_service/audit_record_987` = `PRESENT` (`evidence_03` line 41: `security_service | audit_record_987 | SECURITY_AUDIT_LOG | FOUND | user_37`).
- **Rules applied**: `rule_01` (`USER_PROFILE` -> `DELETE`), `rule_14` (`BACKUP_ARCHIVE` -> `RETAIN`), `rule_12` (`SECURITY_AUDIT_LOG` -> `RETAIN`).
- **Resulting steps**:
  1. `FINDING` `REPORT_RESTORE_RISK` `backup_service/backup_3870` `ACTIVE` `evidence_03`
  2. `REMEDIATION` `BLOCK_RESTORE` `backup_service/backup_3870` `BLOCKED` `""`
  3. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_3677` `ABSENT` `""`
  4. `VERIFICATION` `VERIFY_RECORD_PRESENT` `security_service/audit_record_987` `PRESENT` `""`
  5. `VERIFICATION` `VERIFY_RESTORE_BLOCKED` `backup_service/backup_3870` `BLOCKED` `""`

---

## 6. Trace 6: Tombstone Compliant Retained Record (COMPLETE) — `case_31`
- **Request**: `kofi.addo@gmail.com`
- **State at audit_at**:
  - `account_service/account_4857` = `ABSENT` (`evidence_51` JSON `$.snapshots[0].records`: status `DELETED`).
  - `identity_service/tombstone_440` = `REDACTED` (`evidence_51` JSON `$.snapshots[1].records[0]`: `{'resource_id': 'tombstone_440', 'subject_reference': 'user_541', 'name': None, 'email': None, 'phone': None, 'email_hash': None, 'account_status': 'DELETED'}`).
  - `security_service/audit_record_6909` = `PRESENT` (`evidence_51` JSON `$.snapshots[2].records[0]`: `subject_reference: user_541`).
- **Rules applied**: `rule_01` (`USER_PROFILE` -> `DELETE`), `rule_15` (`ACCOUNT_TOMBSTONE` -> `REDACT`), `rule_12` (`SECURITY_AUDIT_LOG` -> `RETAIN`).
- **Resulting steps**:
  1. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_4857` `ABSENT` `evidence_51`
  2. `VERIFICATION` `VERIFY_RECORD_PRESENT` `security_service/audit_record_6909` `PRESENT` `evidence_51`
  3. `VERIFICATION` `VERIFY_RECORD_REDACTED` `identity_service/tombstone_440` `REDACTED` `evidence_51`

---

## 7. Trace 7: Exposed PII in Account Tombstone (INCOMPLETE) — `case_32`
- **Request**: `kofi.addo91@gmail.com`
- **State at audit_at**:
  - `account_service/account_8858` = `ABSENT` (account deleted in primary store).
  - `identity_service/tombstone_9178` = `PRESENT` (`evidence_51` JSON `$.snapshots[1].records[1]`: `{'resource_id': 'tombstone_9178', 'subject_reference': 'user_542', 'name': 'Kofi Addo', 'email': 'addo.kofi@gmail.com', 'phone': '+233 24 991 1328', 'email_hash': '4f4b9c98...', 'account_status': 'DELETED'}`). Direct identifiers were not redacted.
  - `security_service/audit_record_7068` = `PRESENT` (`evidence_51` JSON `$.snapshots[2].records[1]`: `subject_reference: user_542`).
- **Rules applied**: `rule_01` (`USER_PROFILE` -> `DELETE`), `rule_15` (`ACCOUNT_TOMBSTONE` -> `REDACT`), `rule_12` (`SECURITY_AUDIT_LOG` -> `RETAIN`).
- **Resulting steps**:
  1. `FINDING` `REPORT_EXPOSED_PII` `identity_service/tombstone_9178` `PRESENT` `evidence_51`
  2. `REMEDIATION` `REDACT_RECORD` `identity_service/tombstone_9178` `REDACTED` `""`
  3. `VERIFICATION` `VERIFY_RECORD_ABSENT` `account_service/account_8858` `ABSENT` `""`
  4. `VERIFICATION` `VERIFY_RECORD_PRESENT` `security_service/audit_record_7068` `PRESENT` `""`
  5. `VERIFICATION` `VERIFY_RECORD_REDACTED` `identity_service/tombstone_9178` `REDACTED` `""`
