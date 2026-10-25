# CONTEXT.md — environment, repo state, tool inventory

Owner-facing context store for "Ghost Data Still Exists" (HackerRank Orchestrate, Oct 2026).
Updated in Phase 0 (this session). Prior context from earlier sessions lives in `code/CONTEXT.md`
(retained untouched; consolidation decision marked below).

## 1. Repository / branch

| Item | Value |
|---|---|
| Repo root | `E:\Hackathons\hackerrank\hackerrank-orchestrate-october26` |
| Branch at session start | `main` (clean except untracked files; up to date with `origin/main`) |
| `codex/phase1-2` | **Does not exist** locally or on `origin` (only `main`, `agent-trace`, `fix/agent-trace-instructions`, `fix/readme-packaging`). The old `code/CONTEXT.md` line "moved to codex/phase1-2" is stale. |
| Branch chosen (Phase 0) | `build/main-impl`, created from `main`. Rule was "stay on codex/phase1-2 if active, else create build/main-impl"; since codex/phase1-2 does not exist, `build/main-impl` was cut from the active branch `main`. |
| Recent commits | `8c7f2f6 docs: refine implementation handoff plan`, `4a7000e docs: complete deletion audit discovery phase`, `0eddbbd Update AGENTS.md` |
| Git identity | user `ASHMEET555` (configured) — no commits made yet this session |

### Untracked / modified files at session start (all preserved; nothing staged or committed)

| File | State | Notes |
|---|---|---|
| `GHOST_DATA_MASTER_PLAN.md` | untracked | phase plan (reference doc) |
| `code/main.py` | untracked, **EMPTY (0 bytes)** | future orchestration entry point |
| `code/evaluation/main.py` | untracked, **EMPTY (0 bytes)** | future scorer |
| `code/intent.py` | untracked, **stub (37 lines)** | keyword-stem intent matcher only |
| `code/identity.py` | untracked, **partial (118 lines)** | email → user_id resolution skeleton |
| `code/evidence_index.py` | untracked, **partial (609 lines)** | largest module; parses evidence into index |
| `code/sql_audit.py` | untracked, **partial (65 lines)** | SQLite in-memory loader |
| `code/state_reconstructor.py` | untracked, **partial (48 lines)** | picks best evidence record per (system, resource) |
| `code/rules_engine.py` | untracked, **partial (111 lines)** | applies deletion_rules.csv |
| `code/step_builder.py` | untracked, **partial (241 lines)** | ordering logic present (`_FINDING_OP`/`_REMEDIATION_OP`/`_VERIFICATION_OP`) |
| `log.txt` | untracked | append-only AGENTS.md log (kept out of commits by design? — see blocker B5) |
| `.gitignore` | modified (this session) | added `code/.cache/`, `node_modules/`, `.DS_Store`, `*.pyc`, `dataset/` |
| `code/CONTEXT.md`, `code/notes/inferred_rules.md`, `code/notes/tool_inventory.md` | untracked prior work | read-only reference; `tool_inventory.md` describes a *different* harness session (see §3) |

`git status` after Phase 0 edits: 1 modified (`.gitignore`), 10 untracked (listed above). Nothing staged.

## 2. Environment (verified by running commands, 2026-10-25)

| Check | Command | Result |
|---|---|---|
| Python | `python --version` / `py --version` | **Python 3.13.2** (`C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe`) |
| `python3` on PATH | `python3 --version` | **MISSING** (Windows Store alias stub). Use `python` / `py`. README must document `python` for Windows. |
| sqlite3 module | `import sqlite3` | OK — SQLite **3.45.3** (module present; `sqlite3` CLI binary NOT on PATH) |
| pdftotext | `Get-Command pdftotext` | **present** — `C:\Program Files\Git\mingw64\bin\pdftotext.exe` |
| tesseract (binary) | `Get-Command tesseract` | **MISSING** (also not in `C:\Program Files\Tesseract-OCR`) — system install, needs owner approval |
| PyMuPDF | `import fitz` | OK — **1.26.7** |
| Pillow | `import PIL` | OK — **11.2.1** |
| pytesseract | `import pytesseract` | **MISSING** (pure-Python; installable to `.venv/` with approval, but useless without tesseract binary) |
| pytest | `import pytest` | OK — **8.3.4** |
| pandas | `import pandas` | OK — 2.2.3 (installed but not required; profiling uses stdlib `csv`) |
| git | `git --version` | **2.52.0.windows.1** |
| zip | `Get-Command zip` | **present** — `C:\Users\hp\AppData\Local\Programs\MiKTeX\miktex\bin\x64\zip.exe` |
| pip | `python -m pip --version` | 25.1.1 |
| `.venv/` | `Test-Path .venv` | **does not exist** (no venv created — awaiting approval) |

## 3. Tool / MCP inventory for THIS session (verified via runtime catalog search)

Built-in harness tools (opencode): `read`, `write`, `edit`, `glob`, `grep`, `shell` (PowerShell),
`question`, `skill`, `subagent` (explore/general agents), `websearch`, `webfetch`, `execute`
(Code Mode JS orchestrator), `execute`-scoped `search()` catalog lookup.

MCP servers available inside `execute` (verified by `search()`, not assumed):

| MCP | What it is | Used? | For what |
|---|---|---|---|
| `context7` | library documentation retrieval (resolve-library-id / query-docs) | optional | Python/SQLite/PyMuPDF API reference questions if needed; **not** for dataset answers |
| `filesystem` | file read/write/list within allowed dirs | incidental | redundant with built-in `read`/`write`; not planned for regular use |
| `gopls` | Go language server | **no** | project is Python; no Go workspace |
| `opencode` | session/worktree/model/MCP-resource management | yes (minor) | `list_mcp_resources` (MCP discovery), session/worktree ops |
| `playwright` | headless browser automation | **restricted** | public reference research ONLY (GDPR Art. 17 erasure/backup handling, SQLite replication patterns, OCR tuning). Never for dataset content. |
| code-graph / knowledge-graph MCP | — | **does not exist** | confirmed absent from catalog → module relationships and decisions are recorded in `code/notes/` files instead (as instructed) |

Note: `code/notes/tool_inventory.md` (prior session, harness "Codex" with Notion/pets/plugin MCPs) is
**stale for this session** — those MCPs are not exposed here. Kept for history; superseded by this table.

Web policy: `websearch`/`webfetch`/`playwright` limited to public reference material.
Web is never used for anything `dataset/` answers. The GitHub repo contents are not fetched; local files are source of truth.

## 4. Dependency status (`requirements.txt`)

Pinned to installed, verified versions: `PyMuPDF==1.26.7`, `Pillow==11.2.1`, `pytest==8.3.4`.
No packages installed this session (no venv created yet).

## 5. Open blockers (owner decisions needed)

| ID | Blocker | Proposed decision |
|---|---|---|
| B1 | `tesseract` binary missing → PNG/PDF OCR unavailable (11 PNG + any image-only PDF) | **Needs owner approval**: install Tesseract-OCR (system package) *or* accept PyMuPDF-text-layer-first with PNG content read visually by the agent during Phase 4 spot-checks |
| B2 | `pytesseract` not installed (pure-Python) | **Needs owner approval**: create `.venv/` at repo root and `pip install pytesseract` (only useful if B1 approved) |
| B3 | No code-graph/knowledge-graph MCP | Use `code/notes/` files (CONTEXT, CONTRACT_SPEC, DECISIONS, EVIDENCE_CATALOG) as the knowledge store |
| B4 | Prior `code/CONTEXT.md` vs new `code/notes/CONTEXT.md` duplication | **Needs owner approval**: consolidate into `code/notes/CONTEXT.md` later, or keep both |
| B5 | `log.txt` is untracked; AGENTS.md requires it as the submitted `chat_transcript` | Leave untracked until submission packaging; never commit secrets to it (no decision needed now) |
| B6 | Branch `codex/phase1-2` referenced by old notes does not exist | Working on `build/main-impl`; **needs owner approval** before any commit |

## 6. Analysis scripts (Phase 1, allowed locations)

| Script | Purpose | Output |
|---|---|---|
| `code/tools/profile_dataset.py` | read-only profiling of every CSV + referential integrity + manifest/disk check | `code/notes/DATA_PROFILE.md` (generated) |
| `code/tools/build_evidence_catalog.py` | manifest join, per-file size/format, SQL table listing, sample_output citations | `code/notes/EVIDENCE_CATALOG.md` (generated) |

No engine, classifier, or output-writing code exists from this session. All dataset access is read-only.

## 7. Phase status and approved decisions (updated 2026-10-25)

### Phase 0 - COMPLETE, gate approved
- `git status` inspected; 10 pre-existing untracked files preserved; nothing staged/committed before approval.
- Branch: `codex/phase1-2` does not exist -> created **`build/main-impl` from `main`**; owner approved the choice.
- `.gitignore` extended (`code/.cache/`, `node_modules/`, `.DS_Store`, `*.pyc`, `dataset/` for packaging only; dataset stays tracked and on disk).
- Environment table in §2 verified by command output; `requirements.txt` pins `PyMuPDF==1.26.7`, `Pillow==11.2.1`, `pytest==8.3.4`.
- MCP inventory §3 verified via runtime `search()`; no code-graph/knowledge-graph MCP exists.

### Phase 1 - COMPLETE, gate approved
- `code/notes/CONTRACT_SPEC.md`: full output schema, 7-key step object, 16 legal phase/operation/state triples, ordering + dependency rules, evidence-ID spaces, intent/status/cutoff rules, **[VERIFY] resolution** (V1, V2 resolved; V3-V7 unresolved at gate), §13 inferred_rules comparison (0 contradictions, 4 extensions, 6 gaps).
- `code/notes/DATA_PROFILE.md`: 518/32/32/850/306/4011/15/94 rows; 0 unresolved emails; 0 referential failures; 0 sample_output structural violations; decoy inventory (303/850 non-subject identities, 81/94 evidence files uncited by samples).
- `code/notes/EVIDENCE_CATALOG.md`: 94/94 manifest-vs-disk exact match (28 JSON, 26 LOG, 24 SQL, 11 PNG, 4 PDF, 1 TXT); SQL topology/tables verbatim; parser plan per format.

### Owner-approved decisions (2026-10-25, full detail in `code/notes/DECISIONS.md`)
- **A1** rows sorted lexicographically on `case_id`; Phase 3 test must assert this exact order.
- **A2** `system_id`/`resource_id` plain ASCII `sorted()`.
- **A3** dependency rules never override the contract sort key.
- **A4/V3** deterministic keyword intent; no AMBIGUOUS tier, no LLM; unclear -> NOT_APPLICABLE only if contract allows, else treat as deletion + low-confidence entry in `DECISIONS.md`.
- **A4/V4** case-fold + trim only; verify against `user_audit_log` in Phase 5.
- **A5/V5** rule_05 condition false => rule inapplicable => no violation.
- **A6/V6** shared SUPPORT_ATTACHMENT => REDACT, never DELETE.
- **A7/V7** outside retention => RETAIN lapses => DELETE.
- **B1/B2** no installs; PNG OCR deferred; Phase 4 visually reads the 11 PNGs and logs each read in `EVIDENCE_CATALOG.md` with source file.
- **B6** commit only the Phase 0/1 artifact set (owner-listed files); `log.txt` and the 7 pre-existing untracked modules stay uncommitted.

### Next
Phase 2 (spec-from-samples) blocked until owner gives the go-ahead.

## 8. Phase 0/1 commit and push record (2026-10-25)

- Commit: `4ba7dfc3e793d11f298154d596cb6506667fdf14` - `Phase 0-1: contract spec, data profile, evidence catalog`
- Author: ASHMEET555 <sandhuashmeet40@gmail.com> (pre-existing git config, verified non-empty)
- Contents: 10 files, 1646 insertions (.gitignore, GHOST_DATA_MASTER_PLAN.md, requirements.txt, code/notes/{CONTEXT,CONTRACT_SPEC,DATA_PROFILE,DECISIONS,EVIDENCE_CATALOG}.md, code/tools/{profile_dataset,build_evidence_catalog}.py)
- Excluded by owner instruction: `dataset/` (tracked, unmodified), `log.txt` (untracked artifact), 7 pre-existing untracked code modules, caches/venvs
- Push: `git push -u origin build/main-impl` - **success, new remote branch, no force used**
- Remote verification: `git ls-remote --heads origin build/main-impl` -> `4ba7dfc3e793d11f298154d596cb6506667fdf14 refs/heads/build/main-impl`
- `log.txt` commit hash + push result appended there too; left uncommitted (AGENTS.md chat_transcript artifact, never tracked)
