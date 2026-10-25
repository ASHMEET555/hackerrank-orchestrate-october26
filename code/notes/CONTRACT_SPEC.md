# CONTRACT_SPEC.md - extracted contract (Phase 1)

Source priority: **`problem_statement.md` wins**; `AGENTS.md` (§6) supplies rules the problem
statement states only implicitly; `GHOST_DATA_MASTER_PLAN.md` items marked **[VERIFY]** are
resolved in §10. Every rule below carries a short verbatim quote (≤15 words) plus a file/line
reference so it can be traced back. Line numbers refer to `problem_statement.md` unless the
source is named otherwise.

---

## 1. Output schema

| Rule | Value | Quote | Source |
|---|---|---|---|
| Location | `output.csv` at repository root | "Produce exactly one row in `output.csv` for every case" | problem_statement.md:61 |
| Header | `case_id,deletion_status,steps_json` (exact, this order) | header block | problem_statement.md:64 |
| Row count | exactly **518** data rows | "must contain exactly 518 data rows" | problem_statement.md:73 |
| Row key | one row per `case_id` in `dataset/deletion_requests.csv`; unique | "for every case in `deletion_requests.csv`" | problem_statement.md:61 |
| Row sort | sorted by `case_id` (see §11 open item A1: lexicographic vs numeric) | "sorted by `case_id`" | problem_statement.md:73 |
| `deletion_status` | exactly `COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE` | "is `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`" | problem_statement.md:19 |
| `steps_json` | valid JSON **array** of step objects | "Ordered JSON array of findings, remediation actions" | problem_statement.md:71 |
| NOT_APPLICABLE serialization | exactly `[]` | "use an empty JSON array (`[]`)" | problem_statement.md:91 |
| Grader tolerance | object-key order and whitespace ignored; **array order is not** | "JSON object-key order and whitespace are ignored" | problem_statement.md:99 |
| Encoding / CSV | standard CSV, JSON string in third column (as in `sample_output.csv`) | (structural, no quote) | sample_output.csv |

## 2. Step object

"Each object in `steps_json` must contain" (problem_statement.md:75) **exactly seven keys** -
AGENTS.md §6.3: "Each step contains exactly these fields". No extra keys, none missing.

| # | Key | Type | Allowed values |
|---|---|---|---|
| 1 | `step_no` | integer | consecutive from `1`, no gaps, no duplicates ("Step numbers start at `1`", :89) |
| 2 | `phase` | string | `FINDING`, `REMEDIATION`, `VERIFICATION` ("`phase` must be `FINDING`, `REMEDIATION`, or `VERIFICATION`", :89) |
| 3 | `system_id` | string | free identifier (sample values: `account_service`, `search_service`, `support_platform`, `analytics_platform`, `integration_service`, `backup_service`, `profile_service`, ...). No enum in contract. |
| 4 | `resource_id` | string | free identifier (sample values: `account_001`, `search_001`, `support_001`, `backup_4978`, `data_flow_9846`, ...) |
| 5 | `operation` | string | the 16 operations in §3 |
| 6 | `state` | string | `PRESENT`, `ABSENT`, `REDACTED`, `ANONYMIZED`, `DISABLED`, `BLOCKED`, `ACTIVE` (7 distinct, all appear in samples) |
| 7 | `evidence_id` | string | `file_id` \| `activity_id` \| `audit_id`, or `""` (rules in §6) |

"Array order is significant" (problem_statement.md:89).

## 3. Allowed phase/operation/state combinations (all legal combos)

The table in problem_statement.md:103-119 ("Allowed Operations") defines **exactly 16 legal
triples**; no other combination may appear. Within each row, operation and state are a fixed pair.

### FINDING (order 1)
| # | operation | state | meaning (quote ≤15w) |
|---|---|---|---|
| 1 | `REPORT_REMAINING_RECORD` | `PRESENT` | "A record that should have been deleted still exists." (:105) |
| 2 | `REPORT_EXPOSED_PII` | `PRESENT` | "it still contains identifiers that should have been redacted or anonymized" (:106) |
| 3 | `REPORT_ACTIVE_DATA_FLOW` | `ACTIVE` | "An active process can copy or recreate the user's data." (:107) |
| 4 | `REPORT_RESTORE_RISK` | `ACTIVE` | "A backup or restore path can bring deleted data back." (:108) |

### REMEDIATION (order 2)
| # | operation | state | meaning |
|---|---|---|---|
| 5 | `DISABLE_DATA_FLOW` | `DISABLED` | "Stop the process that can copy or recreate the data." (:109) |
| 6 | `BLOCK_RESTORE` | `BLOCKED` | "Prevent the affected backup from restoring the user's data." (:110) |
| 7 | `DELETE_RECORD` | `ABSENT` | "Remove the entire record." (:111) |
| 8 | `REDACT_RECORD` | `REDACTED` | "remove the identifying fields required by policy" (:112) |
| 9 | `ANONYMIZE_RECORD` | `ANONYMIZED` | "irreversibly unlinking it from the user" (:113) |

### VERIFICATION (order 3)
| # | operation | state | meaning |
|---|---|---|---|
| 10 | `VERIFY_RECORD_ABSENT` | `ABSENT` | "Confirm that a record no longer exists." (:114) |
| 11 | `VERIFY_RECORD_PRESENT` | `PRESENT` | "Confirm that a policy-required retained record still exists." (:115) |
| 12 | `VERIFY_RECORD_REDACTED` | `REDACTED` | "Confirm that required identifying fields have been removed." (:116) |
| 13 | `VERIFY_RECORD_ANONYMIZED` | `ANONYMIZED` | "Confirm that the record can no longer be linked to the user." (:117) |
| 14 | `VERIFY_DATA_FLOW_DISABLED` | `DISABLED` | "Confirm that the relevant data flow is inactive." (:118) |
| 15 | `VERIFY_RESTORE_BLOCKED` | `BLOCKED` | "Confirm that the affected data cannot be restored." (:119) |

No other phases, operations, or states exist: "Do not invent additional phases, operations, or
states" (AGENTS.md §6.4).

## 4. Step ordering and dependency rules

1. **Phase order**: FINDING -> REMEDIATION -> VERIFICATION. Quote: "Order steps by phase:
   findings, remediation, then verification" (:126).
2. **Within a phase**: first operation order as listed in the Allowed Operations table (§3
   numbering = sort rank), quote: "follow the operation order in the table above" (:126).
3. **Tie-break within same phase + operation**: `system_id` ascending, then `resource_id`
   ascending. Quote: "followed by `system_id` and `resource_id` in ascending order" (:126).
4. **Dependency rules** (AGENTS.md §6.5, restated because the problem statement encodes them via
   operation order):
   - "disable data flows and block unsafe restores before changing dependent records"
   - "Process downstream copies before their source records when the dependency requires it"
   - Practical effect: all `DISABLE_DATA_FLOW` / `BLOCK_RESTORE` precede any `*_RECORD`
     remediation (guaranteed by rule 2 anyway); downstream-before-source applies *within* the
     same operation rank, where `system_id`/`resource_id` sort cannot express it - see §11 A3.
5. **`step_no`**: assigned 1..N after final ordering; "Step numbers start at `1` and increase
   consecutively" (:89).
6. Machine check exists in `sample_output.csv`: all 32 samples pass rules 1-5 with zero
   violations (`DATA_PROFILE.md` §3).

## 5. Row sort rules

- Rows: sorted by `case_id` ("The final file must contain exactly 518 data rows, sorted by
  `case_id`", :73). Open item **A1** (§11): the 518 IDs are `case_33`..`case_550` un-padded, so
  lexicographic and numeric order differ; samples (`case_01`..`case_32`) cannot discriminate.

## 6. Evidence-ID rules

| Step kind | evidence_id | Quote | Source |
|---|---|---|---|
| FINDING (always, any case) | must cite a real `file_id` / `activity_id` / `audit_id` | "Findings cite participant-visible evidence" | AGENTS.md §6.6 |
| VERIFICATION in a `COMPLETE` case | must cite evidence proving current state | "must cite a `file_id`, `activity_id`, or `audit_id`" | problem_statement.md:127 |
| REMEDIATION in an `INCOMPLETE` case | always `""` | "use an empty `evidence_id`" | problem_statement.md:127 |
| VERIFICATION in an `INCOMPLETE` case (future check) | always `""` | "Proposed remediation and future verification steps" | problem_statement.md:127 |

Allowed ID spaces (an `evidence_id` must exist in exactly one of these participant-visible sets):
- `file_id` = `evidence_files.csv` (`evidence_01` .. `evidence_94`)
- `activity_id` = `system_activity.csv` (`activity_NN`)
- `audit_id` = `user_audit_log.csv` (`audit_NN`)

Additional constraints (AGENTS.md §6.6):
- "Never cite organizer-only truth or an evidence item captured after the case's `audit_at`."
- "A verification step for a `COMPLETE` case must cite the evidence that proves the current compliant state."
- Observed in samples: all 32 rows cite only `file_id` values (13 distinct); none cite
  `activity_id`/`audit_id`; zero citations post-date their case's `audit_at`
  (`DATA_PROFILE.md` §3). Contract still allows activity/audit IDs.

## 7. Intent rules

| Rule | Quote | Source |
|---|---|---|
| Intent is judged from `request_text` | "request_text ... may be written in different languages. Determine whether it actually authorizes deletion." (§6.5, paraphrase-quote) | AGENTS.md §6.2 |
| Deletion authorization gates status | "because the person did not request deletion" | problem_statement.md:19 |
| Non-deletion examples | "A request for access, correction, export, marketing opt-out, or another non-deletion action is `NOT_APPLICABLE`" | AGENTS.md §6.5 |
| Non-deletion output | `NOT_APPLICABLE` + `steps_json = []` exactly | problem_statement.md:91,96 |
| Mixed request (access AND delete) | counts as deletion requested | AGENTS.md §6.5 "First determine whether `request_text` authorizes deletion." |
| Samples | 0/32 are NOT_APPLICABLE - intent must generalize from contract text, not samples | DATA_PROFILE.md §3 |

## 8. Status definitions

**COMPLETE** - problem_statement.md:24-29, four bullets, all must hold:
1. "every relevant copy has received the treatment required by `deletion_rules.csv`"
2. "no active sync, import, or restore path can recreate the data"
3. "retained records contain only the identifiers permitted by the rules"
4. "records that must be retained remain available"

**NOT_APPLICABLE** - request does not authorize deletion (§7); steps `[]`.

**INCOMPLETE** - the complement: any relevant copy untreated, any prohibited identifier retained,
any active flow / unblocked restore, or any required retained record missing. (Derived, not a
direct quote; AGENTS.md §6.5: "report every relevant policy violation and recreation risk".)

**Complete-case emission**: "For `COMPLETE`, include only verification steps proving the
current state" (:91). **Incomplete-case emission**: "include the findings, the complete ordered
remediation plan, and the checks that must pass afterward" (AGENTS.md §6.3).

Policy application: "Apply `deletion_rules.csv` to every relevant record" (:125), including
account tombstones, data flows, restore risks. Tombstone rule (problem_statement.md:13):
"the stable user reference may remain, but direct identifiers such as name, email, phone, and
email hash must be removed" -> `ACCOUNT_TOMBSTONE` = REDACT with `user_id` kept.

## 9. Cutoff semantics (audit_at)

| Rule | Quote | Source |
|---|---|---|
| State is evaluated at `audit_at` | "Determine the resource state at `audit_at` using the available evidence." | problem_statement.md:124 |
| Only information at or before the cutoff | "Use only information available at or before `audit_at`" | AGENTS.md §6.2 |
| Inclusive bound | usable iff `captured_at <= audit_at` and `event_time <= audit_at` (from "at or before") | AGENTS.md §6.2 (problem statement silent on <= vs <) |
| Post-cutoff evidence cannot be cited | "Never cite ... an evidence item captured after the case's `audit_at`" | AGENTS.md §6.6 |
| Claims are not proof | "Reported workflow statuses and operation results are claims." | problem_statement.md:124 |
| Later evidence must not change earlier answers | "Evidence created later must not change the answer for that case." | AGENTS.md §6.2 |
| Sample conformance | 0 sample citations post-date their `audit_at` | DATA_PROFILE.md §3 |

Timestamps everywhere are ISO-8601 UTC with `Z` (all 518+32 requests, 850 identities, 306 audit
rows, 4011 activities, 94 manifest rows) - no timezone ambiguity in the data (`DATA_PROFILE.md`).

## 10. [VERIFY] resolution log (from GHOST_DATA_MASTER_PLAN.md)

| # | Plan line | Item | Status | Resolution / exact sentence searched |
|---|---|---|---|---|
| V1 | 146 | exact state names | **RESOLVED** | States = `PRESENT, ABSENT, REDACTED, ANONYMIZED, DISABLED, BLOCKED, ACTIVE` from the Allowed Operations table (:103-119). Quote: "Followed by `system_id` and `resource_id` in ascending order" not needed here; table header: "\| Phase \| Operation \| State \| Meaning \|". Phases from: "`phase` must be `FINDING`, `REMEDIATION`, or `VERIFICATION`". |
| V2 | 154 | cutoff inclusive vs exclusive | **RESOLVED (via AGENTS, problem statement silent)** | Inclusive `<=`. Searched problem statement for "before"/"at or before": no match; AGENTS.md §6.2 sentence: "Use only information available at or before `audit_at`". Samples cannot discriminate (0 post-cutoff citations). |
| V3 | 161 | intent confidence tie-break / AMBIGUOUS | **UNRESOLVED** | Searched: "Determine whether it actually authorizes deletion" (AGENTS §6.2) and "because the person did not request deletion" (problem_statement.md:19). No confidence, threshold, or tie-break mechanism exists in either. See §11 A4. |
| V4 | 166 | email normalization (dot/plus stripping) | **UNRESOLVED** | Searched: "Resolve the user's current and historical identifiers." No normalization rule stated. See §11 A5. |
| V5 | 197 | SUPPORT_MESSAGE with no shared context | **UNRESOLVED** | Searched `deletion_rules.csv` rule_05 condition: "Conversation contains shared customer, agent, or order context that must be retained" -> REDACT only when shared. Else-branch unspecified. See §11 A6. |
| V6 | 198 | SUPPORT_ATTACHMENT with shared context | **UNRESOLVED** | Searched rule_06: "Attachment belongs only to the deletion subject" -> DELETE. Shared-attachment case unspecified. See §11 A7. |
| V7 | 201 | SECURITY_AUDIT_LOG outside retention | **UNRESOLVED** | Searched rule_12: "Record is within the supplied retention period" -> RETAIN. Outside-retention treatment unspecified. See §11 A8. |

Note: `GHOST_DATA_MASTER_PLAN.md` writes these tables as "`problem_statement.md` §6.4"; that
numbering actually belongs to AGENTS.md. The problem statement's table is "## Allowed Operations"
(problem_statement.md:101). Same content, wrong cross-reference - recorded, not silently fixed.

## 11. Open contract items - proposed decisions (**all need owner approval**)

| ID | Open item | Proposed decision |
|---|---|---|
| A1 | Row sort order: lexicographic (`case_100` before `case_33`) vs numeric (`case_33` before `case_100`). Quote searched: "sorted by `case_id`". Samples cannot discriminate. | Emit **lexicographic** (`sorted(case_id)`, Python/`pandas sort_values` default). Rationale: graders almost always string-sort the ID column; `case_id` is a string. Alternative: file order (numeric). |
| A2 | Does `system_id`/`resource_id` tie-break sort use plain byte order (ASCII) or case-insensitive? Quote: "`system_id` and `resource_id` in ascending order". | Plain ASCII ascending (`sorted()`), matching sample conformance check. |
| A3 | Dependency rule "downstream copies before sources" can conflict with the contract's mandated sort (operation -> system -> resource). Quote: "Process downstream copies before their source records". | Sort strictly by contract (phase, op, system, resource) - downstream ordering, where required, must coincide with that key or be expressed by `system_id` ordering. Confirm no sample violates this (checked: 0 violations). |
| A4 (V3) | Intent tie-break for ambiguous text. | Deterministic keyword rules only; no AMBIGUOUS tier, no LLM. Text with any erasure signal -> deletion; clearly access/correction/export/marketing-only -> NOT_APPLICABLE; otherwise INCOMPLETE-eligible. |
| A5 (V4) | Email normalization. | Case-fold + trim only. Do not strip dots/plus-tags. Confirm empirically in Phase 5 against `user_audit_log`. |
| A6 (V5) | SUPPORT_MESSAGE, condition false (no shared context). | Treat rule_05 as not applicable -> no policy requirement on that record (it is not a violation). Verify against samples in Phase 2. |
| A7 (V6) | SUPPORT_ATTACHMENT, shared context. | REDACT (same spirit as shared SUPPORT_MESSAGE), never DELETE shared data. Verify against samples in Phase 2. |
| A8 (V7) | SECURITY_AUDIT_LOG outside retention. | RETAIN requirement lapses -> the subject copy must be deleted (DELETE). Verify against samples/evidence in Phase 2. |

## 12. Validator checklist distilled from the contract (basis for Phase 3 `validate.py`)

1. Header exact; 518 rows; unique `case_id`; sorted per A1 decision.
2. Status in {COMPLETE, INCOMPLETE, NOT_APPLICABLE}; NOT_APPLICABLE => `[]`.
3. Each step: exactly 7 keys; `step_no` 1..N consecutive.
4. (phase, operation, state) in the 16 legal triples.
5. Steps sorted by phase rank, then operation rank, then system_id, then resource_id.
6. FINDING + COMPLETE-VERIFICATION evidence_id non-empty and in {file_id, activity_id, audit_id}.
7. REMEDIATION + INCOMPLETE-VERIFICATION evidence_id == "".
8. No cited evidence captured after that case's `audit_at`.
9. COMPLETE has zero REMEDIATION (and zero FINDING) rows; INCOMPLETE has >=1 FINDING and
   >=1 REMEDIATION; NOT_APPLICABLE has zero steps.
10. No duplicate (phase, system_id, resource_id, operation) steps in one case.

## 13. Comparison with `code/notes/inferred_rules.md` (Phase 1 task 6)

Method: line-by-line check of the inferred rules against `problem_statement.md` + `AGENTS.md` §6,
plus a spot-check of three inferred sample claims against the data. Nothing was deleted or
silently accepted.

### 13.1 Direct contradictions with the contract

**None found.** All 8 "Contract-derived decisions" (inferred_rules.md:5-12) match the contract
text: intent gating, identity via current+historical identifiers, policy application, state at
`audit_at` with claims-not-proof, COMPLETE definition, `""` evidence for remediation/future
verification, `[]` for NOT_APPLICABLE, and phase/operation/system/resource ordering.

### 13.2 Extensions - correct but not literally in `problem_statement.md` (keep, note source)

| # | Inferred rule | Contract status | Verdict |
|---|---|---|---|
| E1 | inferred:6 "Preserve required retained records in verification even if no finding is needed" (VERIFY_RECORD_PRESENT inside INCOMPLETE cases) | problem statement:91 only says "include the findings, the complete remediation plan, and the checks that must pass afterward" - it does not spell out retained-record checks | **Supported by samples**: 24 `VERIFY_RECORD_PRESENT` steps exist in `sample_output.csv`. Keep; cite samples, not the sentence. |
| E2 | inferred:5 enumerates ACCESS/CORRECTION/EXPORT/MARKETING_OPT_OUT as non-deletion classes | problem statement only says "because the person did not request deletion"; the enumeration lives in AGENTS.md §6.5 | Keep; source is AGENTS.md, not the problem statement. |
| E3 | inferred:41 "account absence isn't included as a finding" (absent account -> no REPORT step, only future verification) | contract does not state when account-absence verification is emitted; it is a Phase 2 derivation item (master plan §6 Phase 2 "verification set rules") | Keep as sample observation; derive rule in Phase 2. |
| E4 | inferred:47 case_12 asks DELETE for an analytics-named resource (contract rule_07 says ANONYMIZE when attributable) | not a rule conflict - category must come from contents (DESIGN.md:30 says the same) | Keep as warning; classify by content, not name. |

### 13.3 Gaps in inferred_rules.md (my spec covers them; inferred is silent)

- Row sort order ambiguity for `case_33..case_550` (open item A1) - inferred never addresses it.
- Cutoff inclusivity `<=` vs `<` (V2) - inferred says "Evidence after cutoff is unavailable"
  without defining the boundary.
- Email normalization details (V4) - inferred defers to "resolve historical identifiers".
- SUPPORT_MESSAGE/SUPPORT_ATTACHMENT/SECURITY_AUDIT_LOG else-branches (V5-V7) - inferred does
  not discuss them.
- Evidence ID *spaces* (`file_id`/`activity_id`/`audit_id` sets and their membership checks) -
  inferred only says "cite a participant-visible ID".
- Deprecation note: inferred_rules.md:40-63 sample claims are consistent with the data on spot
  check (`evidence_54` failover snapshot contains `account_005`, not `account_001`, captured
  2026-09-02 <= case_01 `audit_at` 2026-09-03), but Phase 2 must re-derive them rather than
  trust them.
