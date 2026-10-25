# PHASE2_UNCOVERED.md — Policy Rules & Contract Operations Uncovered in 32 Samples

Analysis of `dataset/deletion_rules.csv` and CONTRACT_SPEC.md against `dataset/sample_output.csv` (32 cases).

---

## 1. Deletion Rules Coverage (rule_01 to rule_15)

| Rule ID | Data Category | Required Action | Status in 32 Samples | Expected Behavior when Uncovered |
|---|---|---|---|---|
| `rule_01` | `USER_PROFILE` | `DELETE` | COVERED | When undeleted, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_02` | `SECONDARY_IDENTIFIER` | `DELETE` | UNCOVERED | If secondary identifier table/entry remains, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_03` | `SEARCH_INDEX_ENTRY` | `DELETE` | COVERED | When index remains, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_04` | `CACHE_ENTRY` | `DELETE` | UNCOVERED | If cache entry remains, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_05` | `SUPPORT_MESSAGE` | `REDACT` | COVERED | If unredacted, report `REPORT_EXPOSED_PII` -> `REDACT_RECORD` -> `VERIFY_RECORD_REDACTED`. |
| `rule_06` | `SUPPORT_ATTACHMENT` | `DELETE` | COVERED | If attachment belongs only to subject, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_07` | `ANALYTICS_PROFILE` | `ANONYMIZE` | COVERED | If attributable to user, report `REPORT_EXPOSED_PII` -> `ANONYMIZE_RECORD` -> `VERIFY_RECORD_ANONYMIZED`. |
| `rule_08` | `PRODUCT_TELEMETRY` | `ANONYMIZE` | UNCOVERED | If user-attributable telemetry record found, report `REPORT_EXPOSED_PII` -> `ANONYMIZE_RECORD` -> `VERIFY_RECORD_ANONYMIZED`. |
| `rule_09` | `USER_EXPORT` | `DELETE` | COVERED | If export zip/object remains, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_10` | `MARKETING_PROFILE` | `DELETE` | COVERED | If contact/marketing profile remains, report `REPORT_REMAINING_RECORD` -> `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_11` | `EMAIL_DELIVERY_LOG` | `REDACT` | UNCOVERED | If email delivery log contains user email, report `REPORT_EXPOSED_PII` -> `REDACT_RECORD` -> `VERIFY_RECORD_REDACTED`. |
| `rule_12` | `SECURITY_AUDIT_LOG` | `RETAIN` | COVERED | Within retention period, verify record retained with `VERIFY_RECORD_PRESENT`. |
| `rule_13` | `LEGAL_HOLD_RECORD` | `RETAIN` | UNCOVERED | If active legal hold exists, verify retained record with `VERIFY_RECORD_PRESENT`. |
| `rule_14` | `BACKUP_ARCHIVE` | `RETAIN` | COVERED | If restorable without block, report `REPORT_RESTORE_RISK` -> `BLOCK_RESTORE` -> `VERIFY_RESTORE_BLOCKED`. |
| `rule_15` | `ACCOUNT_TOMBSTONE` | `REDACT` | COVERED | If tombstone contains direct PII, report `REPORT_EXPOSED_PII` -> `REDACT_RECORD` -> `VERIFY_RECORD_REDACTED`. |

---

## 2. Operations & States Coverage from CONTRACT_SPEC.md

### Findings
| Operation | State | Status in 32 Samples | Expected Behavior when Uncovered |
|---|---|---|---|
| `REPORT_REMAINING_RECORD` | `PRESENT` | COVERED | Discovered remaining data copy where action is `DELETE`. |
| `REPORT_EXPOSED_PII` | `PRESENT` | COVERED | Discovered unredacted or unanonymized identifiers. |
| `REPORT_ACTIVE_DATA_FLOW` | `ACTIVE` | COVERED | Discovered active synchronization process. |
| `REPORT_RESTORE_RISK` | `ACTIVE` | COVERED | Discovered unblocked backup restore path. |

### Remediation
| Operation | State | Status in 32 Samples | Expected Behavior when Uncovered |
|---|---|---|---|
| `DISABLE_DATA_FLOW` | `DISABLED` | COVERED | Proposed disabling of active sync bridge. |
| `BLOCK_RESTORE` | `BLOCKED` | COVERED | Proposed blocking of backup restore path. |
| `DELETE_RECORD` | `ABSENT` | COVERED | Proposed deletion of whole record. |
| `REDACT_RECORD` | `REDACTED` | COVERED | Proposed removal of direct identifiers. |
| `ANONYMIZE_RECORD` | `ANONYMIZED` | COVERED | Proposed irreversible unlinking of record. |

### Verification
| Operation | State | Status in 32 Samples | Expected Behavior when Uncovered |
|---|---|---|---|
| `VERIFY_RECORD_ABSENT` | `ABSENT` | COVERED | Verify record is absent. |
| `VERIFY_RECORD_PRESENT` | `PRESENT` | COVERED | Verify policy-required retained record remains present. |
| `VERIFY_RECORD_REDACTED` | `REDACTED` | COVERED | Verify required direct identifiers are removed. |
| `VERIFY_RECORD_ANONYMIZED` | `ANONYMIZED` | COVERED | Verify record is anonymized. |
| `VERIFY_DATA_FLOW_DISABLED` | `DISABLED` | COVERED | Verify sync data flow is disabled. |
| `VERIFY_RESTORE_BLOCKED` | `BLOCKED` | COVERED | Verify backup restore is blocked. |
