# Inferred rule spec from the 32 public sample pairs

## Contract-derived decisions

1. First classify intent from `request_text`. Only actual account/data erasure is in scope. Access, correction, export, marketing opt-out, and unrelated requests are NOT_APPLICABLE with `[]`. No public sample demonstrates NOT_APPLICABLE, so this rule comes from `problem_statement.md` rather than sample fitting.
2. Resolve the request email against current identity and historical audit changes; connect by stable `user_id`, aliases, hashes, resource references, and evidence. Do not limit search to the supplied email or current snapshot.
3. Apply the per-category/condition policy to every relevant copy. A tombstone may remain with only its stable reference; security/legal records may be retained; analytics/telemetry may be anonymized; shared support context may be redacted; prohibited user records must be deleted.
4. Reconstruct state at `audit_at`. Evidence after cutoff is unavailable to this case. Reported workflow status, activity `reported_result`, and system event claims do not establish actual resulting state on their own.
5. COMPLETE means every applicable record has required treatment, required retention is intact, and no active data flow or unsafe restore can recreate prohibited data. It emits only evidence-backed verification steps.
6. INCOMPLETE means emit supported findings, a complete remediation plan, and post-remediation checks. All remediation/future verification `evidence_id` values are empty. Preserve required retained records in verification even if no finding is needed for them.
7. NOT_APPLICABLE uses `steps_json=[]`.
8. Step objects have exactly seven fields and step numbers are consecutive. Phase order is FINDING -> REMEDIATION -> VERIFICATION. In each phase use the allowed operation ordering from the contract, then `system_id` and `resource_id` ascending. Dependency order may require disabling flows / blocking restores before record changes and downstream-before-source.

## Policy lookup (deletion_rules.csv)

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

## Evidence and state rules demonstrated by samples

- `case_01`: `evidence_54` failover SQL proves `account_001` is absent, supporting one COMPLETE verification step.
- `case_02`: same failover evidence proves `account_002` absent; reported PARTIALLY_COMPLETE does not prevent COMPLETE.
- `case_03`: `evidence_94` point-in-time lookup trace supports absent account, retained security record, and anonymized analytics record. COMPLETE includes each required treatment.
- `case_04`: `evidence_54` account absent and `evidence_56` analytics record with user reference/direct identifiers null; COMPLETE verifies both.
- `case_05`: `evidence_54` failover replica contains `account_005` despite primary absence; incomplete finding cites replica evidence and asks DELETE.
- `case_06`: `evidence_57` SQL primary search table contains `search_001`; account absence isn't included as a finding, but future verification covers account and search.
- `case_07`: `evidence_58` PDF attachment proves `support_001` is present and subject-only; policy requires DELETE. Future verification covers account and attachment.
- `case_08`: `evidence_59` export manifest/job has `export_001` downloadable before expiry; delete export, verify account and export.
- `case_09`: `evidence_93` SQL snapshot indicates `backup_4978` can restore; backup may be retained but restore must be blocked. Verification also checks account absence and security retention.
- `case_10`: `evidence_61` log finds old-email-linked `support_002` replica without deletion marker. This illustrates historical email alias matching.
- `case_11`: `evidence_03` handover documents an absent account alongside a present search record, identifiable analytics and shared support records, and active integration flow. Policy actions are delete search, redact support, anonymize analytics; disable flow first. Verify retained security record too.
- `case_12`: `evidence_01` log is used to find `analytics_9914`; sample asks DELETE, underscoring that category classification/context must be grounded rather than assuming every analytics-looking item maps to ANALYTICS_PROFILE.
- `case_13`: `evidence_03` supports search/support copies; both are deleted. Verify account, both copies, and retained security record.
- `case_14` and `case_17`: `evidence_03` / `evidence_01` support active restore paths; block restore and verify account absence, required security retention, restore block.
- `case_15`: `evidence_01` supports active integration `data_flow_9846`; disable it before verifying account, security, flow.
- `case_16`: `evidence_05` read-replica SQL shows both account and search copy present. Remediate both and verify plus retained security.
- `case_18`: `evidence_94` has the same mixed remaining/exposed/active-flow pattern as case_11, with policy-based delete/redact/anonymize and flow disable.
- `case_19`: `evidence_01` supports remaining search and exposed support data; delete search, redact support.
- `case_20`: `evidence_94` supports a remaining search record and active flow; disable flow, delete search.
- `case_21`: `evidence_92` supports absent account, retained security, anonymized analytics, hence COMPLETE despite only verification steps.
- `case_22`: `evidence_05` supports remaining search and attributable analytics record; delete search and anonymize analytics.
- `case_23`: `evidence_92` supports remaining export and search records; delete both.
- `case_24`: `evidence_92` shows account and search record still present; both require deletion.
- `case_25`: `evidence_92` proves compliant state despite NOT_STARTED workflow claim: account absent, security retained, analytics anonymized.
- `case_26`–`case_28`: `evidence_92` proves complete multi-system treatment: absent account, retained security, redacted support, anonymized analytics, disabled flow, blocked restore. Workflow labels vary; evidence controls.
- `case_29`–`case_30`: `evidence_92` supports search present, analytics/support PII exposed, active integration; disable first, then delete/redact/anonymize.
- `case_31`: `evidence_51` snapshot proves absent account, retained security record, tombstone with stable `user_id` and all direct identifiers null: COMPLETE.
- `case_32`: `evidence_51` snapshot shows tombstone retaining name/email/phone/hash; report exposed PII and redact while retaining stable reference.

## Sample-level summary and limitations

Sample statuses: 10 COMPLETE, 22 INCOMPLETE, 0 NOT_APPLICABLE. Findings: 21 REPORT_REMAINING_RECORD, 11 REPORT_EXPOSED_PII, 6 REPORT_ACTIVE_DATA_FLOW, 3 REPORT_RESTORE_RISK. Remediations: 21 DELETE_RECORD, 6 DISABLE_DATA_FLOW, 3 BLOCK_RESTORE, 6 REDACT_RECORD, 5 ANONYMIZE_RECORD. There are 50 absent, 24 retained-present, 12 anonymized, 10 redacted, 9 flow-disabled, and 6 restore-blocked verification steps across all samples. The examples are intentionally diverse, but their many sample case IDs share themes; do not hardcode case IDs or infer the hidden evaluation distribution from sample frequencies.

## Open questions to resolve during implementation

- How should identity histories be bounded at request time versus audit time, and how do merged IDs connect to audit/evidence?
- Which specific file types require OCR/vision extraction and how can extracted facts be linked without introducing unsupported matches?
- How should partial snapshots and activity events be combined when evidence conflicts or appears after `audit_at`?
- For custom tests, include at least alias/history plus replica residue, restore recreation risk, and non-deletion intent.
