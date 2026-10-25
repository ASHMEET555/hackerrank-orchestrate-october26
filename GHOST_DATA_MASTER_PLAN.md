# MASTER PLAN: Ghost Data Still Exists (HackerRank Orchestrate, Oct 2026)

Audience: the implementation agent. Read `AGENTS.md`, then this file, then `problem_statement.md` before touching code. This plan supersedes the phase list in `code/DESIGN.md` but keeps its sound principles. Where this plan and `problem_statement.md` disagree, **`problem_statement.md` wins**; record the discrepancy in `code/notes/DECISIONS.md`.

---

## 0. Review of the existing DESIGN.md (what to keep, what to fix)

**Keep (these are correct):**
- Deterministic-first architecture; LLM only as a gated fallback.
- Distinct clocks: artifact capture time, record/event time, identity-change time, `audit_at`. Never let later data affect an earlier audit.
- Workflow statuses and `reported_result` are claims, not proof.
- No case-ID hardcoding; no name-only joins; unrelated global records are decoys until linked.
- Module boundaries (intent, identity, evidence_index, sql_audit, state_reconstructor, rules_engine, step_builder, validate).
- Final-run usage report must describe the real run (zero calls is a valid answer).

**Fix / add (gaps found):**
1. **Evaluation harness and validator come first, not in Phase E.** Build the scorer and validator before the engines so every later change is measured.
2. **No typed data model.** DESIGN.md names modules but not the objects flowing between them. Section 3 defines them.
3. **No evidence-arbitration algorithm.** "Prefer direct, resource-specific evidence" is not executable. Section 4.3 defines a ranked, tie-broken procedure with a provenance trail.
4. **No explicit step-skeleton derivation.** The samples show verification steps appear even when no finding exists (e.g. account-absent and security-retained checks). The agent must derive this *table-driven* from all 32 samples and unit-test it (Phase 2).
5. **Only 32 samples, 0 NOT_APPLICABLE, 22/32 INCOMPLETE.** Hidden data has 518 rows. Add mutation testing (Section 7) so rules are validated beyond the samples.
6. **No per-case audit trace.** Add a debug trace (`code/.cache/traces/<case_id>.json`) listing every fact considered, accepted, rejected and why. This is also the best material for the live AI interview.
7. **No failure policy.** A crash on one case must not lose the other 517. Section 4.8 defines it.
8. **OCR/vision dependency risk is unaddressed.** Check what is installed (`tesseract`, `pdftotext`, `PyMuPDF`, `Pillow`) in Phase 0 and design the fallback chain now.
9. **Time handling underspecified.** Timezones, formats, inclusive/exclusive cutoff semantics need an explicit rule (Section 4.1).
10. **Interview readiness missing.** Add an `ARCHITECTURE.md` and a "why each rule exists" table (Phase 9).

**Caveat on this review:** the GitHub repo page could not be fetched automatically (robots restriction), so this plan is built from the supplied README text, `DESIGN.md` and `inferred_rules.md`. The agent must treat anything marked **[VERIFY]** as unconfirmed until read from `problem_statement.md` or the data itself.

---

## 1. Success criteria

| Criterion | Target |
|---|---|
| Output contract | 100% pass on validator: header, 518 rows, sorted, unique, valid JSON, 7 keys per step, consecutive `step_no`, legal enums |
| Public samples | Exact match (status + steps) on 32/32 without case-ID shortcuts. Any residual mismatch is explained in the report |
| Hidden set | Maximize: status accuracy, identity resolution, finding discovery, policy application, evidence IDs, step order/completeness |
| Reproducibility | `python3 code/main.py` from a clean checkout gives byte-identical `output.csv` twice |
| Determinism | No randomness, no dict-order dependence, no network at run time |
| Reports | `code/evaluation/evaluation_report.md` and `usage_report.md` exist at exact paths with required content |
| Safety | No secrets in code/prompts/logs; no dataset in `code.zip`; no nested archives |

---

## 2. Architecture

```
dataset/*.csv  dataset/evidence/*  ──►  LOADERS ──► NORMALIZED FACT STORE ──┐
                                                                              │
request row ─► INTENT ─► (not deletion) ─► NOT_APPLICABLE, []                 │
                │                                                             ▼
                └► IDENTITY RESOLVER (subject, aliases w/ validity windows) ─► STATE RECONSTRUCTOR
                                                                              │  (resources + processes at audit_at,
                                                                              │   with provenance + conflicts)
                                                                              ▼
                                                            POLICY ENGINE (deletion_rules.csv)
                                                                              │ (per-resource verdict: COMPLIANT /
                                                                              │  VIOLATION(action) / RETAIN_OK / RISK)
                                                                              ▼
                                                            STATUS DECIDER ──► STEP BUILDER ──► VALIDATOR ──► output.csv
                                                                                    ▲
                                                           (optional, gated) LLM FALLBACK: intent / OCR-vision
```

### 2.1 Repository layout (target)

```
README.md
AGENTS.md
log.txt                      # append-only, per AGENTS.md
output.csv                   # generated, root
code/
  main.py                    # orchestration only
  config.py                  # paths, enums, constants (loaded from problem_statement extraction)
  models.py                  # dataclasses (Section 3)
  loaders.py                 # CSV loaders, manifest-safe evidence resolver
  readers/
    text_reader.py           # txt/log/json
    sql_reader.py            # sqlite in-memory loaders per snapshot
    pdf_reader.py            # pdftotext/PyMuPDF -> text; OCR fallback
    image_reader.py          # OCR -> text (+ layout), fallback chain
  timeutil.py                # parse/normalize/compare timestamps
  intent.py
  identity.py
  evidence_index.py          # builds the fact store
  sql_audit.py               # topology + replica comparison
  state_reconstructor.py
  rules_engine.py
  status_decider.py
  step_builder.py
  validate.py
  llm_gate.py                # only if used; cache + budget + usage log
  trace.py                   # per-case audit trace writer
  prompts/                   # any prompts, as .md
  evaluation/
    main.py                  # scorer vs sample_output.csv
    mutation.py              # mutation tests (Section 7)
    custom_cases/            # human-readable .md cases + expected outputs
    evaluation_report.md
    usage_report.md
  notes/
    CONTEXT.md  DECISIONS.md  CONTRACT_SPEC.md  inferred_rules.md  EVIDENCE_CATALOG.md
  tests/                     # pytest unit tests
```

Preserve and reuse the existing untracked modules where sound. Do not discard user work; inspect `git status` first.

---

## 3. Data model (define in `models.py` before any engine)

```python
@dataclass(frozen=True)
class Request:  case_id, user_email_raw, user_email_norm, request_text, audit_at: datetime,
                workflow_status_claim, ...raw_row

@dataclass
class Identity:  subject_user_id, aliases: list[Alias]
@dataclass
class Alias:     kind (email|phone|hash|user_id|external_id), value_norm, valid_from, valid_to,
                 source_id (audit_id / identity row), match_reason

@dataclass
class Fact:      fact_id, evidence_id (file_id|activity_id|audit_id), source_kind,
                 system_id, resource_id, data_category (rules category or UNKNOWN),
                 subject_link: (user_id, via_alias, match_reason) | None,
                 state: PRESENT|ABSENT|REDACTED|ANONYMIZED|DISABLED|BLOCKED|ACTIVE|UNKNOWN,
                 captured_at, record_time, topology (primary|regional|reporting|read|failover|n/a),
                 attributes: dict (e.g. has_direct_identifiers, shared_context, restorable, expiry),
                 provenance: str (file path + locator: table/row/page/line)

@dataclass
class ResourceState:  system_id, resource_id, category, state_at_audit, supporting_facts, conflicting_facts,
                      resolution_rule_used

@dataclass
class Verdict:   resource, policy_rule_id, required_action (DELETE|REDACT|ANONYMIZE|RETAIN),
                 compliance (COMPLIANT|VIOLATION|RETAIN_OK|RETAIN_MISSING|RISK), finding_op (or None)

@dataclass
class Step:      step_no, phase, system_id, resource_id, operation, state, evidence_id
```

Enums (phases, operations, states) are **loaded from a single `config.py`** that the agent populates from `problem_statement.md` §6.4 **[VERIFY exact state names]**. Nothing else hardcodes enum strings.

---

## 4. Core algorithms (specify, implement, unit-test each)

### 4.1 Time handling
- Parse every timestamp to timezone-aware UTC. Document assumptions for naive timestamps in `DECISIONS.md`.
- Define cutoff semantics once: evidence is usable iff `captured_at <= audit_at` (**[VERIFY]** inclusive vs exclusive against the contract/samples). Record-level events: `event_time <= audit_at`.
- A snapshot captured *after* `audit_at` may still be usable only if the contract allows reconstructing earlier state from record timestamps. Default: **not usable as evidence_id**, since the rules say never cite post-cutoff evidence. Verify against samples.
- Provide `usable_at(fact, audit_at) -> (bool, reason)` and log the reason in the trace.

### 4.2 Intent classification (`intent.py`)
- Deterministic first: keyword/pattern classes for ERASURE (delete my account/data, right to be forgotten, erase, remove all my data, in non-English too) versus ACCESS / CORRECTION / EXPORT / MARKETING_OPT_OUT / OTHER.
- Handle: mixed requests (access AND delete → deletion is requested → in scope), negations ("do not delete"), conditional wording, quoting of prior tickets, multilingual text, and requests that only unsubscribe from marketing.
- Output: `(intent_label, confidence, matched_spans)`. If confidence is below threshold, mark `AMBIGUOUS` and route to the LLM gate if enabled; else apply the documented tie-break (**[VERIFY]** against problem statement).
- **Mandatory** custom test set (≥ 15 phrasing variants) because the samples contain zero NOT_APPLICABLE.
- `NOT_APPLICABLE → steps_json = "[]"`, exactly.

### 4.3 Identity resolution (`identity.py`)
1. Normalize request email (case-fold, trim; do **not** strip dots/plus tags unless data shows it is equivalent; **[VERIFY]**).
2. Find subject: current `user_identities.csv` match, else historical match via `user_audit_log.csv` (old email → user_id), restricted to audit events with `event_time <= audit_at`.
3. Build the alias set with validity windows: every email/phone/hash/external ID ever linked to the stable `user_id`, with `valid_from/valid_to` from the audit log.
4. Handle: renames, merges (two user_ids → one), reassigned emails (an old email later owned by a *different* user → must NOT match that other user for events before reassignment), case/whitespace variants, and hashed emails (determine the hash algorithm empirically from the data, then match by recomputed hash; **never** guess).
5. Output includes `match_reason` per alias (used in traces and finding justification).
- Unit tests: historical email example from sample `case_10`; reassigned-email decoy; merged accounts; email exists only after `audit_at` (must not resolve).

### 4.4 Evidence index (`evidence_index.py`)
- Resolve evidence only through `evidence_files.csv` (manifest-safe: no path traversal, verify file exists and hash if the manifest provides one). Catalog every file in `EVIDENCE_CATALOG.md`: format, capture time, system/topology, what it covers, parser used.
- Per format:
  - **JSON/TXT/LOG:** structured parse first; regex only on logs with documented line grammars. Keep line numbers as provenance.
  - **SQL:** load each snapshot into its own in-memory SQLite DB. Do not assume table/column names are identical across snapshots; introspect schema (`sqlite_master`, `PRAGMA table_info`), map via a per-schema adapter, fall back to column-name heuristics with logging. Record snapshot metadata (topology, capture time) and *which tables are in scope* (a snapshot with no search table says nothing about search records).
  - **PDF:** text layer first. If empty/garbled, render pages and OCR.
  - **PNG:** local OCR (try `pytesseract`/`tesseract`, configured with preprocessing: grayscale, upscale, threshold). Store OCR text with per-region confidence. If confidence is low, flag the fact `UNCERTAIN` rather than guess.
- Each parsed observation becomes a `Fact` with full provenance. Cache by file SHA-256.
- Absence reasoning: **"not found in a snapshot" is evidence of absence only if the snapshot is in scope for that resource type and topology.** Encode this as `snapshot_covers(resource_category, system_id)`.

### 4.5 Evidence arbitration (the part DESIGN.md left vague)
For each `(system_id, resource_id)` at `audit_at`, gather usable facts and resolve in order:
1. Discard facts failing `usable_at`.
2. Discard facts with no supported subject link (decoys).
3. Prefer **direct state** (SQL row presence/absence, record content, manifest entry) over **indirect** (log lines, activity rows, claims).
4. Among direct facts, prefer the one with the latest `captured_at <= audit_at` for that same topology.
5. **Topology rule:** residue in *any* replica/failover/reporting copy counts as PRESENT for compliance, even if primary is absent (sample `case_05`). A resource is ABSENT only if every in-scope topology that could hold it shows absent.
6. If direct facts conflict within the same topology and time, flag `CONFLICT`, choose the more conservative state for compliance (PRESENT), and record both in the trace.
7. Activity `reported_result` never overrides any of the above; it only points where to look.
Return `ResourceState` with `resolution_rule_used` so every verdict is explainable.

### 4.6 Category and condition classification
- Map each resource to a rules category from **contents and context**, not system name (sample `case_12` warns about analytics-named resources). Maintain a classifier with explicit signals per category (table names, column sets, file naming patterns, document headings) and an `UNKNOWN` outcome logged for review rather than a silent default.
- Evaluate conditions explicitly:
  - SUPPORT_MESSAGE: shared customer/agent/order context present → REDACT; else if only the subject → follow rules/samples **[VERIFY]**.
  - SUPPORT_ATTACHMENT: belongs only to the subject → DELETE; shared → treat per contract **[VERIFY]**.
  - ANALYTICS_PROFILE / PRODUCT_TELEMETRY: attributable to a user (user reference or direct identifiers non-null) → ANONYMIZE; already anonymized → COMPLIANT.
  - EMAIL_DELIVERY_LOG: contains an email address → REDACT.
  - SECURITY_AUDIT_LOG: within retention period → RETAIN (verify present). Outside retention → **[VERIFY]** treatment.
  - LEGAL_HOLD_RECORD: active hold at `audit_at` → RETAIN.
  - BACKUP_ARCHIVE: restore access blockable → RETAIN with restore blocked; if restorable and not blocked → RISK + BLOCK_RESTORE.
  - ACCOUNT_TOMBSTONE: only stable `user_id` retained; direct identifiers (name, email, phone, hash…) must be null/removed → REDACT if any remain.
- Retention periods and hold status come from supplied files only.

### 4.7 Recreation-risk detection
- **Data flows:** sync/import/integration/replication jobs linked to the subject or resource, ACTIVE at `audit_at` and capable of writing prohibited data → `REPORT_ACTIVE_DATA_FLOW`, remediation `DISABLE_DATA_FLOW`, verify `VERIFY_DATA_FLOW_DISABLED`.
- **Restore paths:** backups/archives/restore jobs able to restore the subject's data and not blocked → `REPORT_RESTORE_RISK`, `BLOCK_RESTORE`, `VERIFY_RESTORE_BLOCKED`.
- Require a supported link to the subject/resource and state at the cutoff. A flow that was disabled before `audit_at` is compliant. A flow created after `audit_at` is irrelevant.
- Decide whether to emit remediation as a ordering prerequisite for dependent deletions (contract dependency rules).

### 4.8 Status decider and failure policy
- `COMPLETE` iff: every in-scope resource has required treatment **and** retained records are present **and** no active flow / unblocked restore path remains.
- `INCOMPLETE` otherwise. `NOT_APPLICABLE` iff intent is non-deletion.
- Per-case `try/except`: on exception, log trace + error, emit a conservative fallback (INCOMPLETE with whatever supported findings exist, or if nothing is supportable, write the best-evidence row and record the case in `failures.md`). **Never** abort the run. Exit non-zero only if the validator fails.

### 4.9 Step builder (`step_builder.py`)
Table-driven from `CONTRACT_SPEC.md`:
- Phases in order: FINDING → REMEDIATION → VERIFICATION.
- Within a phase, contract operation order; then `system_id` ascending, then `resource_id` ascending. Use a single `sort_key(step)` function with unit tests.
- Verdict → steps mapping (to be finalized from the 32 samples, **not guessed**):
  - VIOLATION (record remains) → FINDING `REPORT_REMAINING_RECORD`; REMEDIATION `DELETE_RECORD`; VERIFICATION `VERIFY_RECORD_ABSENT`.
  - Exposed PII in a record that must be kept → FINDING `REPORT_EXPOSED_PII`; REMEDIATION `REDACT_RECORD` or `ANONYMIZE_RECORD`; VERIFICATION `VERIFY_RECORD_REDACTED` / `VERIFY_RECORD_ANONYMIZED`.
  - Active flow → `REPORT_ACTIVE_DATA_FLOW` / `DISABLE_DATA_FLOW` / `VERIFY_DATA_FLOW_DISABLED`.
  - Restore risk → `REPORT_RESTORE_RISK` / `BLOCK_RESTORE` / `VERIFY_RESTORE_BLOCKED`.
  - Retained records (security/legal) → `VERIFY_RECORD_PRESENT`.
  - Subject account → `VERIFY_RECORD_ABSENT` (verification-only when no finding, per samples).
- Evidence IDs: findings and COMPLETE verification cite a real, usable evidence ID (≤ `audit_at`); REMEDIATION and INCOMPLETE future-verification use `""`.
- Renumber `step_no` 1..N after sorting.

### 4.10 Validator (`validate.py`)
Hard checks, run before writing the final file and in CI/test:
header exact; 518 rows; sorted unique `case_id`; status ∈ enum; NOT_APPLICABLE ⇒ `[]`; each step has exactly the 7 keys; consecutive `step_no` from 1; legal phase/operation/state combos; phase and operation ordering; sort by system/resource; evidence ID exists in the manifest/activity/audit sets; no evidence captured after the case's `audit_at`; FINDING and COMPLETE-VERIFICATION IDs non-empty; REMEDIATION and INCOMPLETE-VERIFICATION IDs empty; every VERIFICATION corresponds to a remediation or a required retained/absent check; no duplicate steps.
Return a structured error list; fail loudly.

---

## 5. Optional LLM policy (strictly gated)

Default: **zero model calls in the final run.** Add `llm_gate.py` only if a measured gap justifies it:
- Allowed uses: (a) intent classification for AMBIGUOUS requests; (b) vision/OCR fallback for images where local OCR confidence is low.
- Rules: explicit config flag off by default; a hard call cap; temperature 0; cache by hash of inputs; send the minimum text; **no dataset content to an external provider unless the owner authorizes it**; no secrets in code or logs; every call appended to a usage ledger (provider, model, input tokens, output tokens, cost assumption).
- Whatever the choice, `usage_report.md` states the truth of the final run (including "0 calls, 0 tokens, $0").
- Keep prompts in `code/prompts/*.md`.

---

## 6. Phases (each ends with a gate; commit after each; update `CONTEXT.md` and `log.txt`)

### Phase 0: Environment, repo hygiene, tool inventory
**Tasks**
- `git status`; inspect existing untracked modules and `log.txt`; do not reset or overwrite.
- Confirm branch strategy (use `codex/phase1-2` or create `build/main-impl`); add `.gitignore` (`.venv`, `__pycache__`, `.env`, `code/.cache/`).
- Inventory tools/dependencies: Python version, `sqlite3`, `pdftotext`, `PyMuPDF`, `tesseract`, `Pillow`, `pytest`. Record in `CONTEXT.md`. Pin versions in `requirements.txt`.
- List available MCPs and state which are used: code-graph/knowledge-graph for structure and decisions, filesystem/git for ops, Playwright **only** for public reference research (GDPR Art. 17 erasure and backup treatment, SQLite replication-drift patterns, OCR tuning). Do not use the web for anything the dataset answers.
- Initialize the context store: schema of every CSV, rules table, enum lists, edge-case list, decisions log, failure log.
**Deliverables:** `CONTEXT.md`, `requirements.txt`, `.gitignore`, tool inventory.
**Gate:** clean `git status`; `python3 -c "import ..."` for every dependency passes; agent summarizes what exists vs what is missing.

### Phase 1: Contract extraction and data profiling (no engine code)
**Tasks**
- Read `problem_statement.md` fully. Produce `CONTRACT_SPEC.md`: output schema; step fields; every allowed phase/operation/state and legal combinations; operation order; dependency rules; sort rules; evidence-ID rules; intent rules; definition of COMPLETE/INCOMPLETE/NOT_APPLICABLE; cutoff semantics; every **[VERIFY]** item resolved or explicitly flagged.
- Profile every CSV: row counts, key uniqueness, null rates, timestamp formats/timezones, distinct values of status/system/category columns, referential integrity (case→user, activity→evidence, audit→user).
- Build `EVIDENCE_CATALOG.md` for all 94 files (28 JSON, 26 LOG, 24 SQL, 11 PNG, 4 PDF, 1 TXT per the earlier count; verify): path, format, captured_at, system/topology, which cases reference it, parser plan.
- Identify decoys: global records not linked to any subject.
**Gate:** `CONTRACT_SPEC.md` reviewed; zero unresolved ambiguities without a documented decision.

### Phase 2: Spec-from-samples (the accuracy foundation)
**Tasks**
- For all 32 samples, produce a table: request → resolved subject/aliases → evidence consulted → per-resource state at `audit_at` → policy verdict → expected steps (from `sample_output.csv`). This is a **table**, not prose.
- Derive the **verdict → step skeleton** mapping and the **verification set rules** (when is the account-absent check emitted? when is the security-retained check emitted? what triggers `VERIFY_RESTORE_BLOCKED`?). Express as a machine-readable rule table `code/notes/step_rules.yaml` (or Python dict) with the sample case that evidences each rule.
- Identify rules the samples do *not* cover (NOT_APPLICABLE, LEGAL_HOLD, EMAIL_DELIVERY_LOG, USER_EXPORT variants, marketing profile, cache entries, secondary identifiers) and write the contract-derived expectation for each; these become custom tests.
**Gate:** the rule table reproduces all 32 sample step lists *on paper* (agent walks 6 diverse cases manually with traces shown).

### Phase 3: Test harness and validator first
**Tasks**
- `code/evaluation/main.py`: metrics = **case** accuracy (status), **row** accuracy (status + steps exact), **field** accuracy (per step-field match, aligned by `(phase, system_id, resource_id, operation)`), **sequence** accuracy (ordered list exact; also report longest-common-subsequence ratio). Print per-case unified diffs, grouped by failure category. Write a machine-readable run summary to `code/.cache/eval_history.jsonl`.
- `validate.py` with unit tests, including deliberately broken fixtures (bad ordering, missing evidence, post-cutoff evidence, wrong numbering).
- `tests/` with pytest; wire a `make check` or `python3 -m pytest` entry.
**Gate:** harness runs against a stub engine and produces the full report; validator rejects every broken fixture.

### Phase 4: Foundations: loaders, time, readers, evidence index
**Tasks**
- Implement `timeutil`, `loaders`, all `readers/*`, `evidence_index`, `sql_audit` (snapshot loading, topology detection, in-scope table detection, replica diff).
- Produce `EVIDENCE_CATALOG` programmatically and compare with the manual catalog.
- Cache extraction by SHA-256.
- OCR quality pass: for every PNG/PDF, print extracted text and confidence; spot-check against the actual image/page (view them). Tune preprocessing; record failures.
**Gate:** every evidence file yields facts or an explicit, logged "no extractable content"; representative inspection of every format done; cutoff and topology metadata appear in the index; run time of index build recorded.

### Phase 5: Intent + identity
**Tasks:** implement Sections 4.2, 4.3 and their unit tests. Include ≥ 15 intent phrasing variants (multilingual, mixed, negated) and ≥ 6 identity edge cases (history, reassignment, merge, hash, post-cutoff change, case variants).
**Gate:** show resolved alias chain with validity windows for `case_10` and two further cases; show intent decisions on all 518 request texts (summary distribution plus the list of AMBIGUOUS/low-confidence for manual review).

### Phase 6: State reconstruction + policy engine
**Tasks:** implement 4.5, 4.6, 4.7, and `status_decider`. Emit full traces. Walk manually through at least: a replica residue, an alias match, a tombstone (compliant and non-compliant), a shared support record, an active flow, a restore path, a backup with blocked restore, an anonymized analytics record, a security record retained.
**Gate:** every verdict in a sampled trace cites the evidence that supports it; no resource classified `UNKNOWN` without a logged reason.

### Phase 7: Step builder + end-to-end on samples
**Tasks:** implement 4.9; wire `main.py`; run evaluation on the 32 samples. Loop: run → categorize every mismatch (identity / evidence / classification / policy / ordering / evidence-ID / verification-set) → fix the **general rule** → re-run. Log each iteration's metrics in `evaluation_report.md` (iteration table: change, before, after).
**Rules:** no case-ID conditionals; no fitting to a sample at the expense of the contract; if a sample seems to contradict the contract, document and resolve in `DECISIONS.md`.
**Gate:** 32/32 exact, or each residual mismatch has a written root cause and an explicit justification.

### Phase 8: Generalization and hardening (do not skip)
**Tasks**
- **Mutation tests** (Section 7) to probe rules beyond the samples.
- **Full 518 dry run:** status distribution, per-category verdict distribution, rows with zero findings, rows with `UNKNOWN` categories, rows with `CONFLICT` facts, rows relying on OCR, rows where intent was low-confidence, crash count. Manually review a stratified sample (≥ 25 rows) from non-sample distribution areas: each NOT_APPLICABLE style, each system type, each evidence format.
- Look for **systematic oddities**: e.g. a case where evidence timestamps equal `audit_at`, evidence that postdates audit, identical evidence cited for many cases, alias reassignments.
- Performance check and determinism check (run twice, `diff` outputs).
**Gate:** no crash; validator 100%; deterministic; reviewed sample documented.

### Phase 9: Reports, packaging, interview prep
**Tasks**
- `evaluation_report.md`: definitions of case/row/field/sequence accuracy; final numbers; iteration history; ≥ 3 custom cases (required: historical alias + replica residue; restore/recreation path; non-deletion intent; recommended extras: tombstone with leftover identifiers; evidence captured after `audit_at`; reassigned-email decoy) with request, evidence, expected output, actual output, pass/fail; failures found and improvements made; known limitations.
- `usage_report.md`: final full-dataset run; providers/models; calls; input/output tokens; totals and per-request averages; cost estimate and assumptions; per-model and overall. If no model was used, say so explicitly with zeros.
- `README.md`: setup, dependencies (OCR binaries), run command, repo layout, how to run evaluation/tests.
- `ARCHITECTURE.md`: data flow diagram, decision table "rule → why → evidence of correctness", trade-offs, limitations. (Used for the live AI interview.)
- Packaging: `zip -r code.zip README.md code -x "*/__pycache__/*" "*/.venv/*" "*/venv/*" "*/node_modules/*" "*/.git/*" "*/.DS_Store"`; then **list the zip** and confirm: no `dataset/`, no caches, no nested archives, no secrets, reports present at `code/evaluation/`.
- Final checklist from the problem statement, each item ticked with proof (command output).
**Gate:** all checklist items pass; `log.txt` follows the AGENTS.md turn format and contains no secrets.

---

## 7. Test strategy beyond the 32 samples

1. **Unit tests** per module (time parsing, alias windows, sort key, validator, intent patterns, snapshot scope).
2. **Mutation tests** (programmatic; apply to sample cases and assert the *expected change* in output):
   - Move `audit_at` earlier than the evidence capture → evidence must be rejected; status may flip; no post-cutoff citation.
   - Replace the request email with a historical alias → identical outcome to the current email.
   - Replace with an email that was later reassigned to a different user → must not resolve to that user.
   - Change request text to an access/export/marketing-only request → `NOT_APPLICABLE`, `[]`.
   - Remove a replica snapshot's residue row → INCOMPLETE flips to COMPLETE (if that was the only violation).
   - Mark a backup as restore-blocked → restore finding disappears, `VERIFY_RESTORE_BLOCKED` appears.
   - Shuffle input row order and evidence file order → output unchanged.
3. **Custom cases** (human-readable Markdown in `code/evaluation/custom_cases/`), each with minimal synthetic dataset slice, expected status, expected steps, and reasoning.
4. **Property checks** across all 518 outputs: step numbering, ordering, enum legality, evidence existence and time, status/steps consistency (COMPLETE has no REMEDIATION; NOT_APPLICABLE is `[]`; INCOMPLETE has at least one finding and one remediation), no duplicates.
5. **Cross-check:** for every FINDING, assert a matching REMEDIATION and VERIFICATION exist, and vice-versa.

---

## 8. Risk register

| Risk | Mitigation |
|---|---|
| Overfitting to 22 INCOMPLETE samples | Mutation tests, contract-first reading, no ID shortcuts, stratified manual review |
| OCR misreads images/PDFs | Local OCR + confidence; visual spot-check every image; flag `UNCERTAIN`; optional gated vision fallback only with owner authorization |
| Mis-scoped snapshots → false "absent" | `snapshot_covers()` rule; absence only from in-scope topology |
| Reassigned emails → wrong subject | Alias validity windows; time-bounded join |
| Post-cutoff evidence leakage | `usable_at` gate + validator check |
| Wrong category from system name | Content-based classifier; `UNKNOWN` logged, not defaulted |
| Hidden NOT_APPLICABLE styles (multilingual/mixed) | 15+ intent test variants; AMBIGUOUS list reviewed manually |
| One crash loses all output | Per-case try/except with trace; validator at end |
| Ordering errors cost sequence score | Single `sort_key`, unit-tested against all 32 samples |
| Token/cost surprises | Default zero LLM calls; usage ledger if any |
| Time pressure | Phases 3 and 7 produce a working end-to-end early; Phase 8 hardens; Phase 9 is mostly generation |

---

## 9. Agent operating rules

- Follow `AGENTS.md` logging for **every** turn (User Prompt, Agent Response Summary, Actions, Context). No secrets in `log.txt`.
- One commit per completed phase (or sub-module); conventional messages; never commit `dataset/`, caches, or secrets; never rewrite user history.
- After each phase, report: what was done, what was found, decisions made, open questions, next step. **Stop at the gates** marked "review" (end of Phase 1, Phase 2, Phase 6) and wait for the owner's go-ahead.
- Update `CONTEXT.md`, `DECISIONS.md` and the code-graph/knowledge store after every phase so context survives resets. Record every **[VERIFY]** resolution with its source.
- Ask the owner before: any external model/API use, adding dependencies that need system installs, or deviating from `problem_statement.md`.
- Prefer smaller, testable functions. No silent defaults; every fallback logs a reason into the trace.

---

## 10. Definition of done (final checklist)

- [ ] `python3 code/main.py` from a clean clone writes root `output.csv`; two runs are byte-identical.
- [ ] Header `case_id,deletion_status,steps_json`; 518 rows; sorted; unique.
- [ ] Every `steps_json` is a valid JSON array; 7 keys; consecutive `step_no` from 1; legal enums; correct phase and operation ordering.
- [ ] Findings cite valid evidence IDs; COMPLETE verification cites evidence proving current state; no evidence after `audit_at`; remediation and future verification have `""`.
- [ ] NOT_APPLICABLE rows are exactly `[]`.
- [ ] Sample evaluation: results and diffs recorded; residuals explained.
- [ ] `code/evaluation/evaluation_report.md` and `usage_report.md` present and complete.
- [ ] `README.md` has setup and run instructions including OCR dependencies.
- [ ] `code.zip` inspected: no dataset, venv, caches or nested archives; no secrets.
- [ ] `log.txt` complete and in the AGENTS.md format; ready for upload as `chat_transcript`.
- [ ] `ARCHITECTURE.md` ready for the live interview.
