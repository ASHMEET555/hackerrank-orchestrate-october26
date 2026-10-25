# DECISIONS.md - decision log

Format: decision ID, contract quote, verdict, date. Every entry below is **owner approved**,
2026-10-25, received in the Phase 0/1 gate-approval reply. `problem_statement.md` quotes unless
another source is named.

| ID | Decision | Contract quote (source) | Status | Date |
|---|---|---|---|---|
| A1 | Output rows sorted **lexicographically** on `case_id` via `sorted()` on the string. A dedicated test asserts this exact order so it cannot change silently (test owned by Phase 3 validator). | "sorted by `case_id`" (problem_statement.md:73) | owner approved | 2026-10-25 |
| A2 | `system_id` and `resource_id` tie-break = plain ASCII ascending `sorted()`. | "`system_id` and `resource_id` in ascending order" (problem_statement.md:126) | owner approved | 2026-10-25 |
| A3 | Dependency rules (disable flows / block restores first, downstream before source) **never override** the contract sort key (phase -> operation -> system -> resource). | "Process downstream copies before their source records when the dependency requires it" (AGENTS.md §6.5) | owner approved | 2026-10-25 |
| A4/V3 | Intent = deterministic keyword rules only. No AMBIGUOUS tier, no LLM call. Route unclear text to NOT_APPLICABLE **only if the contract allows it**; otherwise treat as deletion and log the case here as low-confidence. | "Determine whether it actually authorizes deletion" (AGENTS.md §6.2); "because the person did not request deletion" (problem_statement.md:19) | owner approved | 2026-10-25 |
| A4/V4 | Email normalization = case-fold + trim only. No dot/plus-tag stripping. Verify against `user_audit_log` in Phase 5. | "Resolve the user's current and historical identifiers." (problem_statement.md:123) | owner approved | 2026-10-25 |
| A5/V5 | rule_05 condition false (no shared context) => rule does not apply => **no violation** for that SUPPORT_MESSAGE record. | "Conversation contains shared customer, agent, or order context that must be retained" (deletion_rules.csv rule_05) | owner approved | 2026-10-25 |
| A6/V6 | Shared SUPPORT_ATTACHMENT => **REDACT**, never DELETE shared data. | "Attachment belongs only to the deletion subject" (deletion_rules.csv rule_06) | owner approved | 2026-10-25 |
| A7/V7 | SECURITY_AUDIT_LOG outside retention => RETAIN lapses => **DELETE**. | "Record is within the supplied retention period" (deletion_rules.csv rule_12) | owner approved | 2026-10-25 |
| B1/B2 | **No installs.** PNG OCR stays a deferred blocker. Phase 4 reads the 11 PNGs visually for the samples and records every visual read in `EVIDENCE_CATALOG.md` with its source file. | "Evidence may be stored as PDFs, images, logs, JSON" (problem_statement.md:47) | owner approved | 2026-10-25 |
| B6 | No commit until the gate reply was processed and recorded; commit Phase 0/1 artifacts, keep `log.txt` uncommitted (AGENTS.md artifact), keep the 7 pre-existing untracked modules unstaged. | "One commit per completed phase" (GHOST_DATA_MASTER_PLAN.md §9) | owner approved | 2026-10-25 |
| D1 | rule_13: `retained_until > audit_at` counts as active legal hold (`RETAIN` / `VERIFY_RECORD_PRESENT`). | "Record is within the supplied retention period" (deletion_rules.csv rule_13) | default chosen, owner override possible | 2026-10-25 |
| D2 | Support attachment via shared name only: not linked to subject without direct identifier (`email`/`phone`/`user_id`). | "Attachment belongs only to the deletion subject" (deletion_rules.csv rule_06) | default chosen, owner override possible | 2026-10-25 |
| D3 | Trace-correlated log lines: not cited as evidence (cannot cite ungrounded trace completion lines lacking direct subject link). | "Determine resource state from the available evidence" (AGENTS.md §6.1, §6.6) | default chosen, owner override possible | 2026-10-25 |
| D4 | Absence-by-omission: not used as proof of deletion (omission from replica/snapshot bundle alone does not prove verified absence). | "Verification must cover the required final state for each remediated record or process" (AGENTS.md §6.5) | default chosen, owner override possible | 2026-10-25 |
| D5 | `unknown_service` resources: no automated deletion verdict; logged to `code/notes/failures.md` as `UNKNOWN_CLASSIFICATION`. | "Any ungrounded category must not be used by the engine" (GHOST_DATA_MASTER_PLAN.md §6) | default chosen, owner override possible | 2026-10-25 |

## Low-confidence intent log (append during Phase 5+)

| case_id | why unclear | resolution | date |
|---|---|---|---|
| _(none yet)_ | | | |
