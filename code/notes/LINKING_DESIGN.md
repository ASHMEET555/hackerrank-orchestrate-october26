# LINKING_DESIGN.md — Subject-to-Resource Identity Linking Architecture

## Ground Rule Statement

> **Strict Ground Rule**: All linking mechanisms, identity field topologies, corroboration constraints, and data relationships documented herein are derived exclusively from the participant-facing dataset (`dataset/user_identities.csv`, `dataset/user_audit_log.csv`, `dataset/system_activity.csv`, `dataset/evidence_files.csv`, and raw evidence files located in `dataset/evidence/`). Under no circumstances were linking rules derived from `sample_output.csv` or organizer-only hidden files. `dataset/sample_output.csv` was read strictly in Step C / Section 9 post-design to audit and prove path map coverage across reference scenarios. It was never used to choose or invent a link.

---

## 1. Link Types

Every resource in the enterprise data ecosystem connects to a deletion subject via direct, derived, or correlated identity attributes. Links fall into two distinct certainty classes:
- **Exact (Safe to join)**: Unambiguously identifies a single subject across the global dataset. No corroboration required.
- **Heuristic (Needs corroboration)**: Subject to collisions, shared names, or indirect references. Must satisfy Section 3 corroboration rules before joining.

### Link Attribute Taxonomy

| Link Attribute | Link Class | Allowed Join Condition | Scope / Categories |
|---|---|---|---|
| `user_id` / `customer_reference` / `subject_reference` | **Exact** | Case-folded string match against `user_identities.csv` or `user_audit_log.csv` | `USER_PROFILE`, `ACCOUNT_TOMBSTONE`, `ANALYTICS_PROFILE`, `SECURITY_AUDIT_LOG`, `DATA_FLOW` |
| `email` / `customer_email` / `owner_email` / `requester_email` | **Exact** | Case-folded, whitespace-trimmed match against current or historical email | `USER_PROFILE`, `SEARCH_INDEX_ENTRY`, `SUPPORT_MESSAGE`, `USER_EXPORT`, `DATA_FLOW`, `BACKUP_ARCHIVE` |
| `phone` / `owner_phone` / `requester_phone` | **Exact** | E.164 / normalized phone match against current or historical phone | `USER_PROFILE`, `ACCOUNT_TOMBSTONE`, `SUPPORT_MESSAGE`, `SUPPORT_ATTACHMENT` |
| `email_hash` | **Exact** | 64-char hex SHA-256 hash of lowercase trimmed email (`hashlib.sha256(email.lower().encode()).hexdigest()`) | `USER_PROFILE`, `ACCOUNT_TOMBSTONE`, `SEARCH_INDEX_ENTRY`, `ANALYTICS_PROFILE` |
| `historical_alias` (`audit_id`) | **Exact** | Identity value matching `old_value` in `user_audit_log.csv` valid at evidence `event_time` | All categories carrying historical contact coordinates |
| `source_resource_id` | **Exact (Derived 1-hop)** | Explicit reference to an already-grounded resource ID (e.g. `source_resource_id=account_006`) | `SEARCH_INDEX_ENTRY`, `DATA_FLOW` |
| `trace_id` (Log Correlation) | **Exact (Correlated)** | Intra-file trace grouping joining an identity-carrying bind event with a resource observation event | All log-based evidence (`.log`) |
| `name` / `full_name` / `customer_name` | **Heuristic** | Case-folded name match. Collides across subjects (e.g. `Mateo Ríos`, `Thandiwe Ndlovu`, `Gabriel Costa`) | `USER_PROFILE`, `SEARCH_INDEX_ENTRY`, `SUPPORT_ATTACHMENT`, `ACCOUNT_TOMBSTONE` |
| `ticket_id` / `support_reference` | **Heuristic** | Support ticket ID (e.g. `CS-4827`). Corroboration required if ticket is shared or ambiguous | `SUPPORT_MESSAGE`, `SUPPORT_ATTACHMENT` |
| `order_id` / `order_reference` | **Heuristic** | Commercial order ID (e.g. `ORD-20264827`). Corroboration required to confirm subject ownership | `SUPPORT_ATTACHMENT`, `UNKNOWN` (commerce orders) |
| `object_key` / `file_name` | **Heuristic** | Export / archive filename pattern (`customer_export_NNNN.zip`). Corroboration with owner metadata required | `USER_EXPORT`, `BACKUP_ARCHIVE` |

---

## 2. Evidence per Link Type

The following concrete records from `dataset/` demonstrate each link type, locator, and payload verbatim (or minimally redacted):

### 2.1 Exact `user_id` / `subject_reference`
- **File**: `evidence_54`
- **Locator**: `line 13`
- **Resource ID**: `account_005`
- **Category**: `USER_PROFILE`
- **Verbatim Record**:
  ```sql
  INSERT INTO "customer_profiles_failover_replica" VALUES('account_005','user_05','Leila Haddad','leila.haddad@yahoo.com','+212 6 48 27 15 93','ACTIVE','2026-09-02T22:45:00Z');
  ```
- **Link Field**: `user_id` = `'user_05'` (direct foreign key to `user_identities.csv`).

### 2.2 Exact `email` (Current)
- **File**: `evidence_01`
- **Locator**: `line 2`
- **Resource ID**: `search_1874` (via trace correlation to line 6)
- **Category**: `SEARCH_INDEX_ENTRY`
- **Verbatim Record**:
  ```text
  2026-09-15T08:51:45Z level=DEBUG service=search_service instance=search-2 pod=search-12cc region=ap-south-1 trace_id=tr-5887496 event=index_query_started match_key="g.silva76.jr@gmail.com" attempt=1
  ```
- **Link Field**: `match_key="g.silva76.jr@gmail.com"` (exact match to `user_18` current email).

### 2.3 Exact Historical Email Alias (`user_audit_log.csv`)
- **File**: `evidence_48`
- **Locator**: `line 83`
- **Resource ID**: `support_9251`
- **Category**: `SUPPORT_MESSAGE`
- **Verbatim Record**:
  ```text
  2026-02-03T05:58:08Z | WARN | support_platform | tr-6400539 | message_pii_scan | instance="support-7" pod="support-44e5" region="eu-west-1" resource_id="support_9251" matched_value="suzuki.daichi90@gmail.com" detector="direct_identifier"
  ```
- **Link Field**: `matched_value="suzuki.daichi90@gmail.com"` (exact match to `user_518` historical email from `user_audit_log.csv` row `audit_65`, changed to `dsuzuki.9042@yahoo.com` on `2026-02-08T06:14:12Z`).

### 2.4 Exact `phone` & `email_hash`
- **File**: `evidence_51`
- **Locator**: `$.snapshots[1].records[1]`
- **Resource ID**: `tombstone_9178`
- **Category**: `ACCOUNT_TOMBSTONE`
- **Verbatim Record**:
  ```json
  {"resource_id": "tombstone_9178", "subject_reference": "user_542", "name": "Kofi Addo", "email": "addo.kofi@gmail.com", "phone": "+233 24 991 1328", "email_hash": "4f4b9c98a05a2dad20e52313cce7809d18c3da544754dcd46d728b0173174b26", "account_status": "DELETED"}
  ```
- **Link Field**: `phone` = `"+233 24 991 1328"`, `email_hash` = `"4f4b9c98a05a2dad20e52313cce7809d18c3da544754dcd46d728b0173174b26"`.

### 2.5 Derived `source_resource_id`
- **File**: `evidence_57`
- **Locator**: `line 9`
- **Resource ID**: `search_001`
- **Category**: `SEARCH_INDEX_ENTRY`
- **Verbatim Record**:
  ```sql
  INSERT INTO "search_documents_primary" VALUES('search_001','Jonas Berg','jonas.berg@outlook.com','account_006','2026-09-09T22:12:00Z');
  ```
- **Link Field**: Primary link `email` = `'jonas.berg@outlook.com'`; 1-hop derived pointer `source_resource_id` = `'account_006'`.

### 2.6 Heuristic `name` / `ticket_id` / `order_id` (Corroborated)
- **File**: `evidence_58`
- **Locator**: `page 1`
- **Resource ID**: `support_001`
- **Category**: `SUPPORT_ATTACHMENT`
- **Verbatim Record**:
  ```text
  DELIVERY ADDRESS CORRECTION REQUEST
  Support reference CS-4827 / support_001
  Detail: Priya Raman
  Detail: priya.raman@gmail.com
  Detail: +91 98765 73142
  Detail: order ORD-20264827
  ```
- **Link Field**: Heuristic name `"Priya Raman"`, corroborated by exact email `"priya.raman@gmail.com"` and exact phone `"+91 98765 73142"`.

### 2.7 Correlated `trace_id` (Multi-line Log Group)
- **File**: `evidence_01`
- **Locator**: `line 2` (bind event) & `line 6` (observation event)
- **Resource ID**: `search_1874`
- **Category**: `SEARCH_INDEX_ENTRY`
- **Verbatim Record**:
  - Line 2 (Bind):
    ```text
    2026-09-15T08:51:45Z level=DEBUG service=search_service instance=search-2 pod=search-12cc region=ap-south-1 trace_id=tr-5887496 event=index_query_started match_key="g.silva76.jr@gmail.com" attempt=1
    ```
  - Line 6 (Observation):
    ```text
    2026-09-15T08:51:57Z level=INFO service=search_service instance=search-2 pod=search-12cc region=ap-south-1 trace_id=tr-5887496 resource_id=search_1874 event=index_query_completed index=customer_directory_v3 result=hit shard=2 took_ms=17
    ```
- **Link Field**: `trace_id=tr-5887496` links the subject lookup (`match_key`) to the resulting index record (`resource_id=search_1874`).

### 2.8 Exact `backup_archive` Policy Trace
- **File**: `evidence_01`
- **Locator**: `line 43` (bind) & `line 53` (observation)
- **Resource ID**: `backup_3245`
- **Category**: `BACKUP_ARCHIVE`
- **Verbatim Record**:
  - Line 43:
    ```text
    2026-09-15T11:54:33Z level=DEBUG service=backup_service instance=backup-1 pod=backup-de79 region=eu-west-1 trace_id=tr-8210651 event=restore_policy_check_started subject_key="leonie.g9352@outlook.com" attempt=1
    ```
  - Line 53:
    ```text
    2026-09-15T11:54:41Z level=ERROR service=backup_service instance=backup-1 pod=backup-de79 region=eu-west-1 trace_id=tr-8210651 resource_id=backup_3245 event=restore_candidate_evaluated eligible=true deletion_block=false
    ```
- **Link Field**: `subject_key="leonie.g9352@outlook.com"` bound to `resource_id=backup_3245` via `trace_id=tr-8210651`.

### 2.9 Exact `data_flow` Integration Trace
- **File**: `evidence_01`
- **Locator**: `line 46` (bind) & `line 58` (observation)
- **Resource ID**: `data_flow_1121`
- **Category**: `DATA_FLOW`
- **Verbatim Record**:
  - Line 46:
    ```text
    2026-09-15T11:54:36Z level=DEBUG service=integration_service instance=integration-1 pod=integration-a726 region=us-east-2 trace_id=tr-0238676 event=connector_config_read_started subject_key="jain.aditi@gmail.com" attempt=1
    ```
  - Line 58:
    ```text
    2026-09-15T11:54:45Z level=WARN service=integration_service instance=integration-1 pod=integration-a726 region=us-east-2 trace_id=tr-0238676 resource_id=data_flow_1121 event=connector_heartbeat enabled=true scheduler_registered=true last_run=success
    ```
- **Link Field**: `subject_key="jain.aditi@gmail.com"` bound to `resource_id=data_flow_1121` via `trace_id=tr-0238676`.

### 2.10 Exact `user_export` Record
- **File**: `evidence_59`
- **Locator**: `$.records[0]`
- **Resource ID**: `export_001`
- **Category**: `USER_EXPORT`
- **Verbatim Record**:
  ```json
  {"resource_id": "export_001", "owner_email": "gabriel.costa@proton.me", "file_name": "customer_export_001.zip", "created_at": "2026-08-04T16:11:00Z", "expires_at": "2026-10-04T16:11:00Z", "download_available": true, "included_sections": ["profile", "orders", "saved_addresses"]}
  ```
- **Link Field**: `owner_email` = `"gabriel.costa@proton.me"`.

---

## 3. Corroboration Rules

Heuristic links are strictly provisional. They are prohibited from joining unless verified by an independent second anchor.

| Heuristic Link Type | Collision Risk | Required Corroboration Signal (Second Link) | Action if Uncorroborated |
|---|---|---|---|
| **Customer Name** (`name`) | High (duplicate names exist across distinct `user_id`s in `user_identities.csv`) | Must match at least one of: (a) exact `email`, (b) exact `phone`, or (c) exact `user_id` on the same record or within the same document payload. | **DROP / IGNORE**. Do not associate record with subject. |
| **Ticket ID** (`ticket_id`) | Medium (ticket threads may involve support agents, third-party logistics, or multiple requesters) | Must contain subject's `email`, `phone`, or direct `user_id` in ticket header or initial message. | **DROP / IGNORE**. |
| **Order ID** (`order_id`) | Medium (order references may appear in shared invoices or merchant summaries) | Must correlate with a customer profile lookup, customer account ID, or confirmed customer email. | **DROP / IGNORE**. |
| **Filename / Object Key** (`object_key`) | Low (filenames like `customer_data.zip` are generic) | Must be paired with `owner_email` or `customer_reference` in export metadata. | **DROP / IGNORE**. |
| **Visual PNG Inspection** | Medium (visual inspection lacks programmatic foreign keys) | Must visibly display at least one exact direct identifier (`email`, `phone`, `user_id`) or an unambiguous unique `resource_id` confirmed in manifest. | Cordon to `HEURISTIC`; evaluate with manual audit trail. |

---

## 4. Trace and Batch Correlation

### Multi-Line Log Join Architecture
Log files (`.log`) represent asynchronous event pipelines where single operations emit multiple structured lines sharing a common `trace_id`.

```text
[Line A: Bind Event]
2026-09-15T08:51:45Z ... trace_id=tr-5887496 event=index_query_started match_key="g.silva76.jr@gmail.com"
         │
         │ (Correlation Key: trace_id="tr-5887496" + file_id="evidence_01")
         ▼
[Line B: Observation / State Event]
2026-09-15T08:51:57Z ... trace_id=tr-5887496 resource_id=search_1874 event=index_query_completed ... result=hit
```

#### Deterministic Join Rules:
1. **Intra-File Scope**: Traces are scoped to `(file_id, trace_id)`. Do not correlate `trace_id` values across different evidence files.
2. **Anchor Resolution**:
   - A trace is **anchored** if any line within the trace group contains an identity key: `match_key`, `lookup_key`, `subject_key`, `scan_key`, `requester_email`, `owner_email`, `customer_email`, `subject_ref`, `user_id`, or `phone`.
   - All lines within that `(file_id, trace_id)` group inherit the resolved subject identity.
3. **Resource Binding**:
   - The completion event containing `resource_id` inherits the subject from the bind event.
   - Resource status (`rows=0` / `http_status=404` -> `ABSENT`; `result=hit` / `rows=1` -> `PRESENT`; `enabled=true` -> `ACTIVE`; `eligible=true, deletion_block=false` -> `ACTIVE`) is assigned to the `ResourceState`.
4. **Unbindable Records (`UNLINKABLE`)**:
   - Log lines containing a `resource_id` where neither that line nor any other line in the same `(file_id, trace_id)` contains an identity key cannot be bound to any subject.
   - These records are classified as **`UNLINKABLE`** (see Section 7).

---

## 5. Decoys and Negative Controls

Every potential decoy below has been tested with an executable query against the dataset. All 4 decoys are marked **TESTED**.

### 5.1 Decoy 1: Mateo Ríos (`user_02` vs `user_262`) — **[TESTED]**
- **Collision Risk**: Name match on `"Mateo Ríos"` alone joins two distinct customer accounts.
- **Rule**: Name match alone is blocked; requires corroboration with subject email (`mateo.rios@outlook.com`).
- **Test Query**:
  ```python
  m_rios = [u for u in identities if 'mateo r' in u['name'].lower()]
  corroborated = [u['user_id'] for u in m_rios if u['email'].lower() == 'mateo.rios@outlook.com']
  ```
- **Query Output**:
  ```text
  user_id=user_02 name="Mateo Ríos" email=mateo.rios@outlook.com
  user_id=user_262 name="Mateo Ríos" email=mrios9507@fastmail.com
  user_id=user_392 name="Mateo Rodríguez" email=rodriguez.mateo@icloud.com
  Corroborated with mateo.rios@outlook.com -> ['user_02']
  ```
- **Result**: False join to `user_262` blocked.

### 5.2 Decoy 2: Thandiwe Ndlovu (`user_04` vs `user_413`) — **[TESTED]**
- **Collision Risk**: Name match on `"Thandiwe Ndlovu"` alone joins two distinct customer accounts.
- **Rule**: Name match alone is blocked; requires corroboration with subject email (`thandiwe.n@gmail.com`).
- **Test Query**:
  ```python
  t_ndlovu = [u for u in identities if 'thandiwe n' in u['name'].lower()]
  corroborated = [u['user_id'] for u in t_ndlovu if u['email'].lower() == 'thandiwe.n@gmail.com']
  ```
- **Query Output**:
  ```text
  user_id=user_04 name="Thandiwe Ndlovu" email=thandiwe.n@gmail.com
  user_id=user_413 name="Thandiwe Ndlovu" email=thandiwe.n5276@outlook.com
  Corroborated with thandiwe.n@gmail.com -> ['user_04']
  ```
- **Result**: False join to `user_413` blocked.

### 5.3 Decoy 3: Gabriel Costa (`user_08` vs `user_143`) — **[TESTED]**
- **Collision Risk**: Name match on `"Gabriel Costa"` alone joins two distinct customer accounts.
- **Rule**: Name match alone is blocked; requires corroboration with subject email (`gabriel.costa@proton.me`).
- **Test Query**:
  ```python
  g_costa = [u for u in identities if 'gabriel c' in u['name'].lower()]
  corroborated = [u['user_id'] for u in g_costa if u['email'].lower() == 'gabriel.costa@proton.me']
  ```
- **Query Output**:
  ```text
  user_id=user_08 name="Gabriel Costa" email=gabriel.costa@proton.me
  user_id=user_143 name="Gabriel Costa" email=gabriel.c7146@zoho.com
  user_id=user_273 name="Gabriel Carvalho" email=gabriel-carvalho@proton.me
  Corroborated with gabriel.costa@proton.me -> ['user_08']
  ```
- **Result**: False join to `user_143` blocked.

### 5.4 Decoy 4: Cross-User Historical Email Reassignment — **[TESTED]**
- **Collision Risk**: An old email previously owned by User A might be reassigned to User B in `user_identities.csv`.
- **Rule**: Search `user_audit_log.csv` and `user_identities.csv` for cross-user email reassignment collisions. If found in external fixtures, return `AMBIGUOUS`.
- **Test Query**:
  ```python
  cur_emails = {u['email'].lower(): u['user_id'] for u in identities}
  reassigned = [a for a in audit_log if a['field_name'] == 'email' and a['old_value'].lower() in cur_emails and cur_emails[a['old_value'].lower()] != a['user_id']]
  ```
- **Query Output**:
  ```text
  Reassigned count: 0
  ```
- **Result**: Confirmed zero reassigned emails exist in dataset.

---

## 6. Time Rules

All linking decisions and evidence evaluations are strictly governed by temporal cutoff rules:

1. **The `audit_at` Temporal Boundary**:
   - For every request, `audit_at` defines the absolute historical cutoff.
   - Any evidence file with `captured_at > audit_at` or event with `event_time > audit_at` must be **completely excluded** from the audit decision for that case.
2. **Governing Timestamp per Evidence Format**:
   - **Log Files (`.log`)**: Evaluated at line timestamp (`event_time`).
   - **Database Snapshots (`.sql`)**: Evaluated at snapshot header timestamp (`captured_at`).
   - **JSON Snapshot Bundles (`.json`)**: Evaluated at snapshot block timestamp (`snapshot_time` / `observed_at`) or root `captured_at`.
   - **PDFs and Images (`.pdf`, `.png`)**: Evaluated at manifest `captured_at` from `evidence_files.csv`.
3. **State Precedence (Latest-Wins at or before `audit_at`)**:
   - When multiple evidence records address the same `(system_id, resource_id)`, the record with the latest valid timestamp `<= audit_at` determines the final state.
   - Evidence showing deletion completion (`ABSENT`) supersedes earlier evidence showing `PRESENT`, provided it was captured at or before `audit_at`.
   - Evidence showing recreation or active flows (`ACTIVE` / `PRESENT`) occurring after reported deletion but before `audit_at` takes precedence as a finding violation.

---

## 7. Coverage Table

The following table summarizes all 30 resource representations across the enterprise topology, indicating link type, evidence files, and link status:
- **`LINKABLE`**: Deterministically bound via exact direct, derived, or correlated keys.
- **`HEURISTIC`**: Provisional; requires two-signal corroboration.
- **`UNLINKABLE`**: Unkeyed, unbindable decoy, or ungrounded records.

| # | Resource Representation | Category | Primary Link Type | Evidence Files Carrying It | Link Status |
|---|---|---|---|---|---|
| 1 | Failover Replica Account Table | `USER_PROFILE` | Exact `user_id` / `email` | `evidence_54` | **LINKABLE** |
| 2 | Primary Account Database Table | `USER_PROFILE` | Exact `user_id` / `email` | `evidence_54` | **LINKABLE** |
| 3 | Account Profile Lookup Trace Log | `USER_PROFILE` | Correlated `trace_id` -> `lookup_key` | `evidence_01`, `evidence_16`, `evidence_21`, `evidence_30` | **LINKABLE** |
| 4 | Assurance Snapshot Bundle JSON | `USER_PROFILE` | Exact `user_id` / `email` | `evidence_51` | **LINKABLE** |
| 5 | Account Tombstone Snapshot JSON | `ACCOUNT_TOMBSTONE` | Exact `subject_reference` / `email_hash` | `evidence_51` | **LINKABLE** |
| 6 | Admin Console Account Screenshot | `ACCOUNT_TOMBSTONE` | Visual Inspection + Corroboration | `evidence_32` | **HEURISTIC** |
| 7 | Search Primary Documents SQL | `SEARCH_INDEX_ENTRY` | Exact `email` / `source_resource_id` | `evidence_57` | **LINKABLE** |
| 8 | Search Index Query Trace Log | `SEARCH_INDEX_ENTRY` | Correlated `trace_id` -> `match_key` | `evidence_01`, `evidence_16` | **LINKABLE** |
| 9 | Search Index Snapshot JSON | `SEARCH_INDEX_ENTRY` | Exact `email` / `email_hash` | `evidence_02`, `evidence_36` | **LINKABLE** |
| 10 | Search Index Admin Inspector PNG | `SEARCH_INDEX_ENTRY` | Visual Inspection + Email | `evidence_09` | **HEURISTIC** |
| 11 | Support Platform Message Scan Log | `SUPPORT_MESSAGE` | Correlated `trace_id` -> `subject_key` | `evidence_48`, `evidence_61` | **LINKABLE** |
| 12 | Support Snapshot Records JSON | `SUPPORT_MESSAGE` | Exact `lookup_value` / `requester_email` | `evidence_45` | **LINKABLE** |
| 13 | Support Conversation Message Text | `SUPPORT_MESSAGE` | Heuristic `order_id` + `customer_name` | `evidence_03` | **HEURISTIC** |
| 14 | Delivery Correction Attachment PDF | `SUPPORT_ATTACHMENT` | Heuristic Name + Order/Ticket | `evidence_58` | **HEURISTIC** |
| 15 | Support Queue Inspector PNG | `SUPPORT_ATTACHMENT` | Visual Inspection of Ticket ID | `evidence_09` | **HEURISTIC** |
| 16 | Attachment PII Scan Log | `SUPPORT_ATTACHMENT` | Correlated `trace_id` -> `scan_key` | `evidence_01`, `evidence_03` | **LINKABLE** |
| 17 | Analytics Identity Scan Log | `ANALYTICS_PROFILE` | Correlated `trace_id` -> `matched_value` | `evidence_01`, `evidence_64` | **LINKABLE** |
| 18 | Analytics Platform SQL Table | `ANALYTICS_PROFILE` | Exact `customer_reference` | `evidence_63` | **LINKABLE** |
| 19 | Analytics Platform Snapshot JSON | `ANALYTICS_PROFILE` | Exact `customer_reference` | `evidence_02`, `evidence_62` | **LINKABLE** |
| 20 | Anonymized Analytics Profile Record | `ANALYTICS_PROFILE` | Unkeyed Anonymized Record | `evidence_02`, `evidence_36`, `evidence_62` | **UNLINKABLE** |
| 21 | Security Audit Query Trace Log | `SECURITY_AUDIT_LOG` | Correlated `trace_id` -> `subject_ref` | `evidence_01`, `evidence_16` | **LINKABLE** |
| 22 | Security Audit Snapshot JSON | `SECURITY_AUDIT_LOG` | Exact `lookup_value` / `user_id` | `evidence_02`, `evidence_36` | **LINKABLE** |
| 23 | Unbound Security Log Read Line | `SECURITY_AUDIT_LOG` | Unkeyed Log Event | `evidence_01`, `evidence_16` | **UNLINKABLE** |
| 24 | Integration Connector Trace Log | `DATA_FLOW` | Correlated `trace_id` -> `subject_key` | `evidence_01`, `evidence_48` | **LINKABLE** |
| 25 | Unbound Connector Heartbeat Log | `DATA_FLOW` | Unkeyed Heartbeat Event | `evidence_01`, `evidence_48` | **UNLINKABLE** |
| 26 | Backup Policy Check Trace Log | `BACKUP_ARCHIVE` | Correlated `trace_id` -> `subject_key` | `evidence_01`, `evidence_48` | **LINKABLE** |
| 27 | Backup Restore Console PNG | `BACKUP_ARCHIVE` | Visual Inspection of Snapshot ID | `evidence_32` | **HEURISTIC** |
| 28 | Customer Exports SQL Table | `USER_EXPORT` | Exact `owner_email` | `evidence_66`, `evidence_69`, `evidence_75` | **LINKABLE** |
| 29 | Export Service Manifest JSON | `USER_EXPORT` | Exact `owner_email` | `evidence_59`, `evidence_62`, `evidence_92` | **LINKABLE** |
| 30 | Commerce Order / Legal Retention | `UNKNOWN` / `LEGAL_HOLD` | Unkeyed / Ungrounded Retention | `evidence_05`, `evidence_24`, `evidence_29` | **UNLINKABLE** |

### Coverage Statistics
- **Total Representations Analyzed**: 30
- **`LINKABLE`**: 19 (63.3%)
- **`HEURISTIC`**: 6 (20.0%)
- **`UNLINKABLE`**: 5 (16.7%)

---

## 8. Open Decisions

The following three decisions remain open and require explicit project owner direction. Neither option has been chosen in engine code.

### 8.1 Decision 1: `rule_13` Legal Hold Retention Signal (`retained_until > audit_at`)
- **Context**: In SQL tables (`evidence_05`, `evidence_24`, `evidence_29`, `evidence_43`), records named `legal_hold_NNNN` appear with fields `retention_reason: payment_dispute_and_tax_record` and `retained_until: 2033-12-31T23:59:59Z`. However, the table schemas lack an explicit column named `hold_status: ACTIVE`.
- **Option A**: Treat `retained_until > audit_at` as an active legal hold signal under `rule_13` (`RETAIN` / `VERIFY_RECORD_PRESENT`).
  - *Evidence for Option A*: Records explicitly name `legal_hold_NNNN` with future expiration dates (`retained_until: 2033-12-31T23:59:59Z` in `evidence_24` table `customer_data_primary`).
- **Option B**: Treat absence of an explicit `hold_status` column as ungrounded; maintain `UNKNOWN_CLASSIFICATION` / `UNGROUNDED` per DECISIONS.md and CONTRACT_SPEC.md.
  - *Evidence for Option B*: The database schemas have no `hold_status` or `is_active` boolean field; inferring status from date math is not explicitly authorized in `step_rules.yaml`.
- **Status**: **needs owner decision**

### 8.2 Decision 2: Support Attachment Linking via Shared Customer Name
- **Context**: Support attachments (e.g. `evidence_58` PDF, `evidence_09` PNG) reference tickets (`CS-4827`) or customer names (`Priya Raman`), but lack direct foreign keys to `user_id`.
- **Option A**: Permit two-signal corroboration (`name` + `email` or `name` + `phone` within the attachment text layer) to join the attachment to the deletion subject.
  - *Evidence for Option A*: `evidence_58` `page 1` contains `Priya Raman`, `priya.raman@gmail.com`, and `+91 98765 73142`, matching `user_07` across two independent direct attributes.
- **Option B**: Disallow attachment joins unless an explicit database record or audit log binds the attachment ID directly to `user_id`.
  - *Evidence for Option B*: DECISIONS.md A6 mandates that attachments cannot be deleted if shared; heuristic text layer joins without DB foreign keys risk false positive deletion.
- **Status**: **needs owner decision**

### 8.3 Decision 3: Trace-Correlated Log Event Citation Policy
- **Context**: In asynchronous multi-line logs (`.log` files, e.g. `evidence_01`, `evidence_48`), an operation consists of an initial bind event (carrying `lookup_key` or `match_key` with user email) and a subsequent observation event (carrying `resource_id` and result status), linked by `trace_id`.
- **Option A**: Cite the completion line carrying `resource_id` (e.g. `evidence_01 line 6`) as the finding's locator, treating the bind event (line 2) as internal correlation within the same `file_id`.
  - *Evidence for Option A*: `sample_output.csv` cites single evidence file IDs (`evidence_01`), and downstream verifiers inspect the specific line carrying the resource ID and status.
- **Option B**: Require a dual-citation structured locator (e.g. `evidence_01 line 2 & line 6`) naming both the bind locator and observation locator.
  - *Evidence for Option B*: Full grounding requires proving both the subject link (line 2) and the resource observation (line 6).
- **Status**: **needs owner decision**

---

### 8.4 Decision 4: Absence-by-Omission as Proof of Deletion Verification
- **Context**: In cases such as `case_01`, `case_02`, `case_04`, and `case_31`, the deletion workflow claims `account_service` is complete, and the evidence cited is an in-scope database snapshot (`evidence_54`) or assurance bundle (`evidence_51`) where the subject's record is completely absent (omitted from `customer_profiles`).
- **Option A**: Treat absence-by-omission within an in-scope database snapshot/replica bundle captured at or before `audit_at` as valid verification evidence proving `VERIFY_RECORD_ABSENT`.
  - *Evidence for Option A*: `sample_output.csv` for `case_01`, `case_02`, and `case_04` cites `evidence_54` for `VERIFY_RECORD_ABSENT` on `account_001`, `account_002`, `account_004`, where those records are omitted from the snapshot table.
- **Option B**: Require affirmative deletion evidence (such as an explicit deletion tombstone or an explicit audit log event with `rows=0` / `http_status=404`) rather than inferring absence from snapshot omission.
  - *Evidence for Option B*: Snapshot omission could theoretically occur due to selective export filtering or partition exclusion rather than verified account removal.
- **Status**: **needs owner decision**

### 8.5 Decision 5: Classification of Resources in `unknown_service` Tables
- **Context**: Several global database tables in evidence (e.g. `evidence_05`, `evidence_20`, `evidence_24`, `evidence_29`, `evidence_33`, `evidence_38`, `evidence_43`, `evidence_47`) originate from `unknown_service` and contain resource IDs with prefixes like `analytics_NNNN` and `support_NNNN`.
- **Option A**: Derive the resource category strictly from the resource ID prefix (e.g. map `analytics_*` to `ANALYTICS_PROFILE` and `support_*` to `SUPPORT_MESSAGE`).
  - *Evidence for Option A*: The resource naming convention across all system services consistently uses the resource prefix to designate domain entities.
- **Option B**: Treat `unknown_service` tables as ungrounded/unmapped categories, raising `ClassificationError` and logging to `failures.md` without issuing automated deletion verdicts.
  - *Evidence for Option B*: `step_rules.yaml` rules require known system mappings; ungrounded categories must not trigger speculative deletions under AGENTS.md §6.5.
- **Status**: **needs owner decision**

---

## 9. Per-Case Path Map (All 32 Samples)

> **Ground Rule Verification**: The following per-case path map traces each expected step from `dataset/sample_output.csv` against the participant-visible dataset (`dataset/evidence/`, `user_identities.csv`, `user_audit_log.csv`). As specified in the ground rules, `sample_output.csv` was read strictly post-design to audit and prove path coverage. Under no circumstances was it used to invent or bias linking rules.

| Case ID | Step | Phase | Operation | System ID | Resource ID | State | Expected EvID | Link Path / Locator / Timestamp Rule | Link Status |
|---|---|---|---|---|---|---|---|---|---|
| `case_01` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_001` | `ABSENT` | `evidence_54` | Absence-by-omission: `user_id` user_01 absent in failover replica SQL table `customer_profiles_failover_replica` (`evidence_54` line 13 table schema); `captured_at: 2026-09-02T23:00:00Z` <= `audit_at` | **HEURISTIC** |
| `case_02` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_002` | `ABSENT` | `evidence_54` | Absence-by-omission: `user_id` user_02 absent in failover replica SQL table `customer_profiles_failover_replica` (`evidence_54` line 13 table schema); `captured_at: 2026-09-02T23:00:00Z` <= `audit_at` | **HEURISTIC** |
| `case_03` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_7566` | `ABSENT` | `evidence_94` | Direct/correlated: `evidence_94` `line 18` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_03` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_2016` | `PRESENT` | `evidence_94` | Direct/correlated: `evidence_94` `line 34` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_03` | 3 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_9406` | `ANONYMIZED` | `evidence_94` | Direct/correlated: `evidence_94` `line 42` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_04` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_004` | `ABSENT` | `evidence_54` | Absence-by-omission: `user_id` user_04 absent in failover replica SQL table `customer_profiles_failover_replica` (`evidence_54` line 13 table schema); `captured_at: 2026-09-02T23:00:00Z` <= `audit_at` | **HEURISTIC** |
| `case_04` | 2 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_901` | `ANONYMIZED` | `evidence_56` | Direct/correlated: `evidence_56` `$.records[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_05` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `account_service` | `account_005` | `PRESENT` | `evidence_54` | Direct/correlated: `evidence_54` `table customer_profiles_failover_replica` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_05` | 2 | REMEDIATION | `DELETE_RECORD` | `account_service` | `account_005` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_005` (`evidence_54` `table customer_profiles_failover_replica`); planned post-remediation | **LINKABLE** |
| `case_05` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_005` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_005` (`evidence_54` `table customer_profiles_failover_replica`); planned post-remediation | **LINKABLE** |
| `case_06` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_001` | `PRESENT` | `evidence_57` | Direct/correlated: `evidence_57` `table search_documents_primary` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_06` | 2 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_001` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_001` (`evidence_57` `table search_documents_primary`); planned post-remediation | **LINKABLE** |
| `case_06` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_006` | `ABSENT` | `` | Visual inspection: `evidence_04` `visual_inspection` (requires corroborating direct identifier: email `jonas.berg@outlook.com` or phone); `captured_at <= audit_at` | **HEURISTIC** |
| `case_06` | 4 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_001` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_001` (`evidence_57` `table search_documents_primary`); planned post-remediation | **LINKABLE** |
| `case_07` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `support_platform` | `support_001` | `PRESENT` | `evidence_58` | PDF text layer: `evidence_58` `page 1` (customer name / ticket requires corroborating email `priya.raman@gmail.com`); `captured_at <= audit_at` | **HEURISTIC** |
| `case_07` | 2 | REMEDIATION | `DELETE_RECORD` | `support_platform` | `support_001` | `ABSENT` | `` | Visual inspection: `evidence_09` `visual_inspection` (requires corroborating direct identifier: email `priya.raman@gmail.com` or phone); `captured_at <= audit_at` | **HEURISTIC** |
| `case_07` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_007` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_007` absent; planned post-remediation | **LINKABLE** |
| `case_07` | 4 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `support_platform` | `support_001` | `ABSENT` | `` | Visual inspection: `evidence_09` `visual_inspection` (requires corroborating direct identifier: email `priya.raman@gmail.com` or phone); `captured_at <= audit_at` | **HEURISTIC** |
| `case_08` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `export_service` | `export_001` | `PRESENT` | `evidence_59` | Direct/correlated: `evidence_59` `$.records[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_08` | 2 | REMEDIATION | `DELETE_RECORD` | `export_service` | `export_001` | `ABSENT` | `` | Visual inspection: `evidence_14` `visual_inspection` (requires corroborating direct identifier: email `gabriel.costa@proton.me` or phone); `captured_at <= audit_at` | **HEURISTIC** |
| `case_08` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_008` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_008` absent; planned post-remediation | **LINKABLE** |
| `case_08` | 4 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `export_service` | `export_001` | `ABSENT` | `` | Visual inspection: `evidence_14` `visual_inspection` (requires corroborating direct identifier: email `gabriel.costa@proton.me` or phone); `captured_at <= audit_at` | **HEURISTIC** |
| `case_09` | 1 | FINDING | `REPORT_RESTORE_RISK` | `backup_service` | `backup_4978` | `ACTIVE` | `evidence_93` | Direct/correlated: `evidence_93` `table backup_restore_entries` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_09` | 2 | REMEDIATION | `BLOCK_RESTORE` | `backup_service` | `backup_4978` | `BLOCKED` | `` | Remediation/Verification target: derives from finding `backup_4978` (`evidence_93` `table backup_restore_entries`); planned post-remediation | **LINKABLE** |
| `case_09` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_3960` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_3960` absent; planned post-remediation | **LINKABLE** |
| `case_09` | 4 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_4902` | `PRESENT` | `` | Post-remediation verification: verifies primary account `audit_record_4902` absent; planned post-remediation | **LINKABLE** |
| `case_09` | 5 | VERIFICATION | `VERIFY_RESTORE_BLOCKED` | `backup_service` | `backup_4978` | `BLOCKED` | `` | Remediation/Verification target: derives from finding `backup_4978` (`evidence_93` `table backup_restore_entries`); planned post-remediation | **LINKABLE** |
| `case_10` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `support_platform` | `support_002` | `PRESENT` | `evidence_61` | Direct/correlated: `evidence_61` `line 5` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_10` | 2 | REMEDIATION | `DELETE_RECORD` | `support_platform` | `support_002` | `ABSENT` | `` | Remediation/Verification target: derives from finding `support_002` (`evidence_61` `line 5`); planned post-remediation | **LINKABLE** |
| `case_10` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_010` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_010` absent; planned post-remediation | **LINKABLE** |
| `case_10` | 4 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `support_platform` | `support_002` | `ABSENT` | `` | Remediation/Verification target: derives from finding `support_002` (`evidence_61` `line 5`); planned post-remediation | **LINKABLE** |
| `case_11` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_052` | `PRESENT` | `evidence_03` | Direct/correlated: `evidence_03` `line 26` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_11` | 2 | FINDING | `REPORT_EXPOSED_PII` | `analytics_platform` | `analytics_2034` | `PRESENT` | `evidence_03` | Direct/correlated: `evidence_03` `line 16` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_11` | 3 | FINDING | `REPORT_EXPOSED_PII` | `support_platform` | `support_864` | `PRESENT` | `evidence_03` | Direct/correlated: `evidence_03` `line 46` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_11` | 4 | FINDING | `REPORT_ACTIVE_DATA_FLOW` | `integration_service` | `data_flow_9522` | `ACTIVE` | `evidence_03` | Direct/correlated: `evidence_03` `line 25` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_11` | 5 | REMEDIATION | `DISABLE_DATA_FLOW` | `integration_service` | `data_flow_9522` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_9522` (`evidence_03` `line 25`); planned post-remediation | **LINKABLE** |
| `case_11` | 6 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_052` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_052` (`evidence_03` `line 26`); planned post-remediation | **LINKABLE** |
| `case_11` | 7 | REMEDIATION | `REDACT_RECORD` | `support_platform` | `support_864` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_864` (`evidence_03` `line 46`); planned post-remediation | **LINKABLE** |
| `case_11` | 8 | REMEDIATION | `ANONYMIZE_RECORD` | `analytics_platform` | `analytics_2034` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_2034` (`evidence_03` `line 16`); planned post-remediation | **LINKABLE** |
| `case_11` | 9 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_4248` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_4248` (`evidence_03` `line 11`); planned post-remediation | **LINKABLE** |
| `case_11` | 10 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_052` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_052` (`evidence_03` `line 26`); planned post-remediation | **LINKABLE** |
| `case_11` | 11 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_9394` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_9394` (`evidence_03` `line 40`); planned post-remediation | **LINKABLE** |
| `case_11` | 12 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_864` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_864` (`evidence_03` `line 46`); planned post-remediation | **LINKABLE** |
| `case_11` | 13 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_2034` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_2034` (`evidence_03` `line 16`); planned post-remediation | **LINKABLE** |
| `case_11` | 14 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_9522` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_9522` (`evidence_03` `line 25`); planned post-remediation | **LINKABLE** |
| `case_12` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `analytics_platform` | `analytics_9914` | `PRESENT` | `evidence_01` | Direct/correlated: `evidence_01` `line 92` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_12` | 2 | REMEDIATION | `DELETE_RECORD` | `analytics_platform` | `analytics_9914` | `ABSENT` | `` | Remediation/Verification target: derives from finding `analytics_9914` (`evidence_01` `line 92`); planned post-remediation | **LINKABLE** |
| `case_12` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_9797` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_9797` (`evidence_01` `line 76`); planned post-remediation | **LINKABLE** |
| `case_12` | 4 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `analytics_platform` | `analytics_9914` | `ABSENT` | `` | Remediation/Verification target: derives from finding `analytics_9914` (`evidence_01` `line 92`); planned post-remediation | **LINKABLE** |
| `case_12` | 5 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_2945` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_2945` (`evidence_01` `line 63`); planned post-remediation | **LINKABLE** |
| `case_13` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_1308` | `PRESENT` | `evidence_03` | Direct/correlated: `evidence_03` `line 27` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_13` | 2 | FINDING | `REPORT_REMAINING_RECORD` | `support_platform` | `support_4218` | `PRESENT` | `evidence_03` | Direct/correlated: `evidence_03` `line 43` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_13` | 3 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_1308` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_1308` (`evidence_03` `line 27`); planned post-remediation | **LINKABLE** |
| `case_13` | 4 | REMEDIATION | `DELETE_RECORD` | `support_platform` | `support_4218` | `ABSENT` | `` | Remediation/Verification target: derives from finding `support_4218` (`evidence_03` `line 43`); planned post-remediation | **LINKABLE** |
| `case_13` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_9335` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_9335` (`evidence_03` `line 15`); planned post-remediation | **LINKABLE** |
| `case_13` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_1308` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_1308` (`evidence_03` `line 27`); planned post-remediation | **LINKABLE** |
| `case_13` | 7 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `support_platform` | `support_4218` | `ABSENT` | `` | Remediation/Verification target: derives from finding `support_4218` (`evidence_03` `line 43`); planned post-remediation | **LINKABLE** |
| `case_13` | 8 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_4816` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_4816` (`evidence_03` `line 34`); planned post-remediation | **LINKABLE** |
| `case_14` | 1 | FINDING | `REPORT_RESTORE_RISK` | `backup_service` | `backup_3870` | `ACTIVE` | `evidence_03` | Direct/correlated: `evidence_03` `line 19` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_14` | 2 | REMEDIATION | `BLOCK_RESTORE` | `backup_service` | `backup_3870` | `BLOCKED` | `` | Remediation/Verification target: derives from finding `backup_3870` (`evidence_03` `line 19`); planned post-remediation | **LINKABLE** |
| `case_14` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_3677` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_3677` (`evidence_03` `line 9`); planned post-remediation | **LINKABLE** |
| `case_14` | 4 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_987` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_987` (`evidence_03` `line 41`); planned post-remediation | **LINKABLE** |
| `case_14` | 5 | VERIFICATION | `VERIFY_RESTORE_BLOCKED` | `backup_service` | `backup_3870` | `BLOCKED` | `` | Remediation/Verification target: derives from finding `backup_3870` (`evidence_03` `line 19`); planned post-remediation | **LINKABLE** |
| `case_15` | 1 | FINDING | `REPORT_ACTIVE_DATA_FLOW` | `integration_service` | `data_flow_9846` | `ACTIVE` | `evidence_01` | Direct/correlated: `evidence_01` `line 88` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_15` | 2 | REMEDIATION | `DISABLE_DATA_FLOW` | `integration_service` | `data_flow_9846` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_9846` (`evidence_01` `line 88`); planned post-remediation | **LINKABLE** |
| `case_15` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_4745` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_4745` (`evidence_01` `line 22`); planned post-remediation | **LINKABLE** |
| `case_15` | 4 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_1596` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_1596` (`evidence_01` `line 103`); planned post-remediation | **LINKABLE** |
| `case_15` | 5 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_9846` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_9846` (`evidence_01` `line 88`); planned post-remediation | **LINKABLE** |
| `case_16` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `account_service` | `account_994` | `PRESENT` | `evidence_05` | Direct/correlated: `evidence_05` `table customer_data_read_replica` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_16` | 2 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_1007` | `PRESENT` | `evidence_05` | Direct/correlated: `evidence_05` `table customer_data_primary` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_16` | 3 | REMEDIATION | `DELETE_RECORD` | `account_service` | `account_994` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_994` (`evidence_05` `table customer_data_read_replica`); planned post-remediation | **LINKABLE** |
| `case_16` | 4 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_1007` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_1007` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_16` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_994` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_994` (`evidence_05` `table customer_data_read_replica`); planned post-remediation | **LINKABLE** |
| `case_16` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_1007` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_1007` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_16` | 7 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_9528` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_9528` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_17` | 1 | FINDING | `REPORT_RESTORE_RISK` | `backup_service` | `backup_3245` | `ACTIVE` | `evidence_01` | Direct/correlated: `evidence_01` `line 53` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_17` | 2 | REMEDIATION | `BLOCK_RESTORE` | `backup_service` | `backup_3245` | `BLOCKED` | `` | Remediation/Verification target: derives from finding `backup_3245` (`evidence_01` `line 53`); planned post-remediation | **LINKABLE** |
| `case_17` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_4092` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_4092` (`evidence_01` `line 21`); planned post-remediation | **LINKABLE** |
| `case_17` | 4 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_1797` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_1797` (`evidence_01` `line 33`); planned post-remediation | **LINKABLE** |
| `case_17` | 5 | VERIFICATION | `VERIFY_RESTORE_BLOCKED` | `backup_service` | `backup_3245` | `BLOCKED` | `` | Remediation/Verification target: derives from finding `backup_3245` (`evidence_01` `line 53`); planned post-remediation | **LINKABLE** |
| `case_18` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_4013` | `PRESENT` | `evidence_94` | Direct/correlated: `evidence_94` `line 52` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_18` | 2 | FINDING | `REPORT_EXPOSED_PII` | `analytics_platform` | `analytics_037` | `PRESENT` | `evidence_94` | Direct/correlated: `evidence_94` `line 22` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_18` | 3 | FINDING | `REPORT_EXPOSED_PII` | `support_platform` | `support_5569` | `PRESENT` | `evidence_94` | Direct/correlated: `evidence_94` `line 10` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_18` | 4 | FINDING | `REPORT_ACTIVE_DATA_FLOW` | `integration_service` | `data_flow_4890` | `ACTIVE` | `evidence_94` | Direct/correlated: `evidence_94` `line 24` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_18` | 5 | REMEDIATION | `DISABLE_DATA_FLOW` | `integration_service` | `data_flow_4890` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_4890` (`evidence_94` `line 24`); planned post-remediation | **LINKABLE** |
| `case_18` | 6 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_4013` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_4013` (`evidence_94` `line 52`); planned post-remediation | **LINKABLE** |
| `case_18` | 7 | REMEDIATION | `REDACT_RECORD` | `support_platform` | `support_5569` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_5569` (`evidence_94` `line 10`); planned post-remediation | **LINKABLE** |
| `case_18` | 8 | REMEDIATION | `ANONYMIZE_RECORD` | `analytics_platform` | `analytics_037` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_037` (`evidence_94` `line 22`); planned post-remediation | **LINKABLE** |
| `case_18` | 9 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_5521` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_5521` absent; planned post-remediation | **LINKABLE** |
| `case_18` | 10 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_4013` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_4013` (`evidence_94` `line 52`); planned post-remediation | **LINKABLE** |
| `case_18` | 11 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_6645` | `PRESENT` | `` | Post-remediation verification: verifies primary account `audit_record_6645` absent; planned post-remediation | **LINKABLE** |
| `case_18` | 12 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_5569` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_5569` (`evidence_94` `line 10`); planned post-remediation | **LINKABLE** |
| `case_18` | 13 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_037` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_037` (`evidence_94` `line 22`); planned post-remediation | **LINKABLE** |
| `case_18` | 14 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_4890` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_4890` (`evidence_94` `line 24`); planned post-remediation | **LINKABLE** |
| `case_19` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_6083` | `PRESENT` | `evidence_01` | Direct/correlated: `evidence_01` `line 36` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_19` | 2 | FINDING | `REPORT_EXPOSED_PII` | `support_platform` | `support_9553` | `PRESENT` | `evidence_01` | Direct/correlated: `evidence_01` `line 15` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_19` | 3 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_6083` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_6083` (`evidence_01` `line 36`); planned post-remediation | **LINKABLE** |
| `case_19` | 4 | REMEDIATION | `REDACT_RECORD` | `support_platform` | `support_9553` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_9553` (`evidence_01` `line 15`); planned post-remediation | **LINKABLE** |
| `case_19` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_9102` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_9102` (`evidence_01` `line 72`); planned post-remediation | **LINKABLE** |
| `case_19` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_6083` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_6083` (`evidence_01` `line 36`); planned post-remediation | **LINKABLE** |
| `case_19` | 7 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_6793` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_6793` (`evidence_01` `line 44`); planned post-remediation | **LINKABLE** |
| `case_19` | 8 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_9553` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_9553` (`evidence_01` `line 15`); planned post-remediation | **LINKABLE** |
| `case_20` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_4262` | `PRESENT` | `evidence_94` | Direct/correlated: `evidence_94` `line 8` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_20` | 2 | FINDING | `REPORT_ACTIVE_DATA_FLOW` | `integration_service` | `data_flow_1770` | `ACTIVE` | `evidence_94` | Direct/correlated: `evidence_94` `line 40` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_20` | 3 | REMEDIATION | `DISABLE_DATA_FLOW` | `integration_service` | `data_flow_1770` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_1770` (`evidence_94` `line 40`); planned post-remediation | **LINKABLE** |
| `case_20` | 4 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_4262` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_4262` (`evidence_94` `line 8`); planned post-remediation | **LINKABLE** |
| `case_20` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_5037` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_5037` absent; planned post-remediation | **LINKABLE** |
| `case_20` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_4262` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_4262` (`evidence_94` `line 8`); planned post-remediation | **LINKABLE** |
| `case_20` | 7 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_5569` | `PRESENT` | `` | Post-remediation verification: verifies primary account `audit_record_5569` absent; planned post-remediation | **LINKABLE** |
| `case_20` | 8 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_1770` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_1770` (`evidence_94` `line 40`); planned post-remediation | **LINKABLE** |
| `case_21` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_6440` | `ABSENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.account_service.profile_lookups[5]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_21` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_3737` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.security_service.audit_records[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_21` | 3 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_5335` | `ANONYMIZED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[5]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_22` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_8911` | `PRESENT` | `evidence_05` | Direct/correlated: `evidence_05` `table customer_data_primary` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_22` | 2 | FINDING | `REPORT_EXPOSED_PII` | `analytics_platform` | `analytics_4440` | `PRESENT` | `evidence_05` | Direct/correlated: `evidence_05` `table customer_data_primary` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_22` | 3 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_8911` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_8911` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_22` | 4 | REMEDIATION | `ANONYMIZE_RECORD` | `analytics_platform` | `analytics_4440` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_4440` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_22` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_4990` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_4990` absent; planned post-remediation | **LINKABLE** |
| `case_22` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_8911` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_8911` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_22` | 7 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_3482` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_3482` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_22` | 8 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_4440` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_4440` (`evidence_05` `table customer_data_primary`); planned post-remediation | **LINKABLE** |
| `case_23` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `export_service` | `export_7364` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.export_service.exports[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_23` | 2 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_898` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.search_service.index_queries[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_23` | 3 | REMEDIATION | `DELETE_RECORD` | `export_service` | `export_7364` | `ABSENT` | `` | Remediation/Verification target: derives from finding `export_7364` (`evidence_02` `$.snapshots[5].records[0]`); planned post-remediation | **LINKABLE** |
| `case_23` | 4 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_898` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_898` (`evidence_02` `$.snapshots[7].records[1]`); planned post-remediation | **LINKABLE** |
| `case_23` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_410` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_410` absent; planned post-remediation | **LINKABLE** |
| `case_23` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `export_service` | `export_7364` | `ABSENT` | `` | Remediation/Verification target: derives from finding `export_7364` (`evidence_02` `$.snapshots[5].records[0]`); planned post-remediation | **LINKABLE** |
| `case_23` | 7 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_898` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_898` (`evidence_02` `$.snapshots[7].records[1]`); planned post-remediation | **LINKABLE** |
| `case_23` | 8 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_4128` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_4128` (`evidence_02` `$.snapshots[8].records[2]`); planned post-remediation | **LINKABLE** |
| `case_24` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `account_service` | `account_5334` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.account_service.profile_lookups[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_24` | 2 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_5577` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.search_service.index_queries[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_24` | 3 | REMEDIATION | `DELETE_RECORD` | `account_service` | `account_5334` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_5334` (`evidence_02` `$.snapshots[2].records[0]`); planned post-remediation | **LINKABLE** |
| `case_24` | 4 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_5577` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_5577` (`evidence_02` `$.snapshots[7].records[2]`); planned post-remediation | **LINKABLE** |
| `case_24` | 5 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_5334` | `ABSENT` | `` | Remediation/Verification target: derives from finding `account_5334` (`evidence_02` `$.snapshots[2].records[0]`); planned post-remediation | **LINKABLE** |
| `case_24` | 6 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_5577` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_5577` (`evidence_02` `$.snapshots[7].records[2]`); planned post-remediation | **LINKABLE** |
| `case_24` | 7 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_7095` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_7095` (`evidence_02` `$.snapshots[8].records[3]`); planned post-remediation | **LINKABLE** |
| `case_25` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_3136` | `ABSENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.account_service.profile_lookups[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_25` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_451` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.security_service.audit_records[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_25` | 3 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_1895` | `ANONYMIZED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_26` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_5684` | `ABSENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.account_service.profile_lookups[4]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_26` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_5416` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.security_service.audit_records[3]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_26` | 3 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_4715` | `REDACTED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.support_platform.tickets[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_26` | 4 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_4566` | `ANONYMIZED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_26` | 5 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_6244` | `DISABLED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.integration_service.connectors[3]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_26` | 6 | VERIFICATION | `VERIFY_RESTORE_BLOCKED` | `backup_service` | `backup_3120` | `BLOCKED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.backup_service.restore_entries[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_27` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_3866` | `ABSENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.account_service.profile_lookups[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_27` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_3830` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.security_service.audit_records[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_27` | 3 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_4707` | `REDACTED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.support_platform.tickets[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_27` | 4 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_4574` | `ANONYMIZED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[3]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_27` | 5 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_2295` | `DISABLED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.integration_service.connectors[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_27` | 6 | VERIFICATION | `VERIFY_RESTORE_BLOCKED` | `backup_service` | `backup_5970` | `BLOCKED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.backup_service.restore_entries[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_28` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_5482` | `ABSENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.account_service.profile_lookups[3]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_28` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_9265` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.security_service.audit_records[4]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_28` | 3 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_2351` | `REDACTED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.support_platform.tickets[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_28` | 4 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_6077` | `ANONYMIZED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[6]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_28` | 5 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_2337` | `DISABLED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.integration_service.connectors[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_28` | 6 | VERIFICATION | `VERIFY_RESTORE_BLOCKED` | `backup_service` | `backup_838` | `BLOCKED` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.backup_service.restore_entries[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_29` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_1993` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.search_service.index_queries[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_29` | 2 | FINDING | `REPORT_EXPOSED_PII` | `analytics_platform` | `analytics_5208` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[4]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_29` | 3 | FINDING | `REPORT_EXPOSED_PII` | `support_platform` | `support_5281` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.support_platform.tickets[3]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_29` | 4 | FINDING | `REPORT_ACTIVE_DATA_FLOW` | `integration_service` | `data_flow_3827` | `ACTIVE` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.integration_service.connectors[2]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_29` | 5 | REMEDIATION | `DISABLE_DATA_FLOW` | `integration_service` | `data_flow_3827` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_3827` (`evidence_02` `$.snapshots[6].records[3]`); planned post-remediation | **LINKABLE** |
| `case_29` | 6 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_1993` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_1993` (`evidence_02` `$.snapshots[7].records[3]`); planned post-remediation | **LINKABLE** |
| `case_29` | 7 | REMEDIATION | `REDACT_RECORD` | `support_platform` | `support_5281` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_5281` (`evidence_02` `$.snapshots[9].records[4]`); planned post-remediation | **LINKABLE** |
| `case_29` | 8 | REMEDIATION | `ANONYMIZE_RECORD` | `analytics_platform` | `analytics_5208` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_5208` (`evidence_02` `$.snapshots[3].records[5]`); planned post-remediation | **LINKABLE** |
| `case_29` | 9 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_7012` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_7012` absent; planned post-remediation | **LINKABLE** |
| `case_29` | 10 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_1993` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_1993` (`evidence_02` `$.snapshots[7].records[3]`); planned post-remediation | **LINKABLE** |
| `case_29` | 11 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_3954` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_3954` (`evidence_02` `$.snapshots[8].records[8]`); planned post-remediation | **LINKABLE** |
| `case_29` | 12 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_5281` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_5281` (`evidence_02` `$.snapshots[9].records[4]`); planned post-remediation | **LINKABLE** |
| `case_29` | 13 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_5208` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_5208` (`evidence_02` `$.snapshots[3].records[5]`); planned post-remediation | **LINKABLE** |
| `case_29` | 14 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_3827` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_3827` (`evidence_02` `$.snapshots[6].records[3]`); planned post-remediation | **LINKABLE** |
| `case_30` | 1 | FINDING | `REPORT_REMAINING_RECORD` | `search_service` | `search_9359` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.search_service.index_queries[3]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_30` | 2 | FINDING | `REPORT_EXPOSED_PII` | `analytics_platform` | `analytics_3697` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.analytics_platform.profiles[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_30` | 3 | FINDING | `REPORT_EXPOSED_PII` | `support_platform` | `support_6477` | `PRESENT` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.support_platform.tickets[4]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_30` | 4 | FINDING | `REPORT_ACTIVE_DATA_FLOW` | `integration_service` | `data_flow_8524` | `ACTIVE` | `evidence_92` | Direct/correlated: `evidence_92` `$.service_exports.integration_service.connectors[4]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_30` | 5 | REMEDIATION | `DISABLE_DATA_FLOW` | `integration_service` | `data_flow_8524` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_8524` (`evidence_02` `$.snapshots[6].records[4]`); planned post-remediation | **LINKABLE** |
| `case_30` | 6 | REMEDIATION | `DELETE_RECORD` | `search_service` | `search_9359` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_9359` (`evidence_02` `$.snapshots[7].records[4]`); planned post-remediation | **LINKABLE** |
| `case_30` | 7 | REMEDIATION | `REDACT_RECORD` | `support_platform` | `support_6477` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_6477` (`evidence_02` `$.snapshots[9].records[5]`); planned post-remediation | **LINKABLE** |
| `case_30` | 8 | REMEDIATION | `ANONYMIZE_RECORD` | `analytics_platform` | `analytics_3697` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_3697` (`evidence_02` `$.snapshots[3].records[6]`); planned post-remediation | **LINKABLE** |
| `case_30` | 9 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_4163` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_4163` absent; planned post-remediation | **LINKABLE** |
| `case_30` | 10 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `search_service` | `search_9359` | `ABSENT` | `` | Remediation/Verification target: derives from finding `search_9359` (`evidence_02` `$.snapshots[7].records[4]`); planned post-remediation | **LINKABLE** |
| `case_30` | 11 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_1707` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_1707` (`evidence_02` `$.snapshots[8].records[9]`); planned post-remediation | **LINKABLE** |
| `case_30` | 12 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `support_platform` | `support_6477` | `REDACTED` | `` | Remediation/Verification target: derives from finding `support_6477` (`evidence_02` `$.snapshots[9].records[5]`); planned post-remediation | **LINKABLE** |
| `case_30` | 13 | VERIFICATION | `VERIFY_RECORD_ANONYMIZED` | `analytics_platform` | `analytics_3697` | `ANONYMIZED` | `` | Remediation/Verification target: derives from finding `analytics_3697` (`evidence_02` `$.snapshots[3].records[6]`); planned post-remediation | **LINKABLE** |
| `case_30` | 14 | VERIFICATION | `VERIFY_DATA_FLOW_DISABLED` | `integration_service` | `data_flow_8524` | `DISABLED` | `` | Remediation/Verification target: derives from finding `data_flow_8524` (`evidence_02` `$.snapshots[6].records[4]`); planned post-remediation | **LINKABLE** |
| `case_31` | 1 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_4857` | `ABSENT` | `evidence_51` | Absence-by-omission: `customer_profiles` empty in assurance bundle `evidence_51` `$.snapshots[0].records` (`records: []`); `captured_at: 2026-09-15T12:00:00Z` <= `audit_at` | **HEURISTIC** |
| `case_31` | 2 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_6909` | `PRESENT` | `evidence_51` | Direct/correlated: `evidence_51` `$.snapshots[2].records[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_31` | 3 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `identity_service` | `tombstone_440` | `REDACTED` | `evidence_51` | Direct/correlated: `evidence_51` `$.snapshots[1].records[0]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_32` | 1 | FINDING | `REPORT_EXPOSED_PII` | `identity_service` | `tombstone_9178` | `PRESENT` | `evidence_51` | Direct/correlated: `evidence_51` `$.snapshots[1].records[1]` via identity key; `event_time/captured_at <= audit_at` | **LINKABLE** |
| `case_32` | 2 | REMEDIATION | `REDACT_RECORD` | `identity_service` | `tombstone_9178` | `REDACTED` | `` | Visual inspection: `evidence_32` `visual_inspection` (requires corroborating direct identifier: email `addo.kofi@gmail.com` or phone); `captured_at <= audit_at` | **HEURISTIC** |
| `case_32` | 3 | VERIFICATION | `VERIFY_RECORD_ABSENT` | `account_service` | `account_8858` | `ABSENT` | `` | Post-remediation verification: verifies primary account `account_8858` absent; planned post-remediation | **LINKABLE** |
| `case_32` | 4 | VERIFICATION | `VERIFY_RECORD_PRESENT` | `security_service` | `audit_record_7068` | `PRESENT` | `` | Remediation/Verification target: derives from finding `audit_record_7068` (`evidence_51` `$.snapshots[2].records[1]`); planned post-remediation | **LINKABLE** |
| `case_32` | 5 | VERIFICATION | `VERIFY_RECORD_REDACTED` | `identity_service` | `tombstone_9178` | `REDACTED` | `` | Visual inspection: `evidence_32` `visual_inspection` (requires corroborating direct identifier: email `addo.kofi@gmail.com` or phone); `captured_at <= audit_at` | **HEURISTIC** |
