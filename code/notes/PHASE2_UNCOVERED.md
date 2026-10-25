# PHASE2_UNCOVERED.md — Policy Rules & Contract Operations Uncovered in 32 Samples

Analysis of `dataset/deletion_rules.csv` and contract specification against `dataset/sample_output.csv` (32 cases).

---

## 1. Uncovered Deletion Rules

Out of 15 deletion rules in `dataset/deletion_rules.csv`, the 32 public sample cases exercise 10 rules.  
The remaining **5 rules** are not exercised in the 32 samples:

| Rule ID | Data Category | Condition | Required Action | Engine Handling Requirement |
|---|---|---|---|---|
| `rule_02` | `SECONDARY_IDENTIFIER` | Always | `DELETE` | If secondary identifiers (e.g. alternate emails, phone records) appear in dedicated secondary tables/resources, treat as `DELETE_RECORD` -> `VERIFY_RECORD_ABSENT`. |
| `rule_04` | `CACHE_ENTRY` | Always | `DELETE` | Cache entries (Redis/memcached/cache services) must be reported as remaining if unevicted/present, remediated with `DELETE_RECORD`, and verified with `VERIFY_RECORD_ABSENT`. |
| `rule_08` | `PRODUCT_TELEMETRY` | Record is still attributable to a user | `ANONYMIZE` | Like `rule_07` (analytics profile): if user-identifiable, report `REPORT_EXPOSED_PII`, remediate with `ANONYMIZE_RECORD`, and verify with `VERIFY_RECORD_ANONYMIZED`. |
| `rule_11` | `EMAIL_DELIVERY_LOG` | Log contains a user email address | `REDACT` | Like `rule_05` (support message): if email address is present in message log, report `REPORT_EXPOSED_PII`, remediate with `REDACT_RECORD`, verify with `VERIFY_RECORD_REDACTED`. |
| `rule_13` | `LEGAL_HOLD_RECORD` | A supplied legal hold is active | `RETAIN` | Similar to `rule_12` (security audit log): record must not be deleted while active hold exists; verify with `VERIFY_RECORD_PRESENT`. |

---

## 2. Operation Coverage

All 4 FINDING operations, 5 REMEDIATION operations, and 6 VERIFICATION operations defined in AGENTS.md §6.4 are exercised in the 32 sample cases.  
Every allowed phase and operation has at least one positive exemplar in `dataset/sample_output.csv`.
