"""phase2_dump.py - print specific evidence content for Phase 2 review (read-only aid).

Usage: python code/tools/phase2_dump.py <topic>
topics: sql_tables | ev01_88_96 | ev03_head | ev51 | ev05_drift | ev06_80_90 | ev56 | ev57 | ev58 | ev59 | ev61 | ev93
"""
import json
import sqlite3
import sys
from pathlib import Path

DS = Path("dataset")


def p(rel):
    return DS / rel


def sql_load(rel):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(p(rel).read_text(encoding="utf-8"))
    return db


def sql_tables(rel):
    db = sql_load(rel)
    names = [r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    print(f"== {rel}")
    for t in names:
        cnt = db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        cols = [c[1] for c in db.execute(f'PRAGMA table_info("{t}")')]
        print(f"  {t}: {cnt} rows, cols={cols}")
    return db, names


def main(topic):
    if topic == "sql_tables":
        for rel in ["evidence/databases/customer_accounts_failover_replica_20260902.sql",
                    "evidence/databases/customer_search_primary_20260910.sql",
                    "evidence/databases/customer_data_inventory_20260916.sql",
                    "evidence/databases/customer_data_read_replica_20260921.sql"]:
            db, _ = sql_tables(rel)
            if "failover" in rel:
                for rid in ("account_001", "account_002", "account_004", "account_005"):
                    rows = db.execute(
                        "SELECT * FROM customer_profiles_failover_replica WHERE resource_id=?",
                        (rid,)).fetchall()
                    print(f"  lookup {rid}: {[dict(r) for r in rows]}")
            if "search_primary" in rel:
                for rid in ("search_001", "account_006"):
                    for t in ("search_documents_primary",):
                        try:
                            rows = db.execute(f'SELECT * FROM "{t}" WHERE resource_id=?', (rid,)).fetchall()
                            print(f"  lookup {t}.{rid}: {[dict(r) for r in rows]}")
                        except Exception as e:
                            print("  err", e)
            db.close()

    elif topic == "ev01_88_96":
        lines = p("evidence/logs/service_events_ap_south_20260915.log").read_text(
            encoding="utf-8").splitlines()
        for n in range(60, 105):
            if n <= len(lines):
                print(n, lines[n - 1])

    elif topic == "ev03_head":
        lines = p("evidence/records/customer_account_handover_20261001.txt").read_text(
            encoding="utf-8").splitlines()
        for n, l in enumerate(lines, 1):
            print(n, l)

    elif topic == "ev51":
        d = json.loads(p("evidence/records/customer_data_snapshot_bundle_20260915.json").read_text(encoding="utf-8"))
        print("top keys:", list(d))
        for i, snap in enumerate(d["snapshots"]):
            print(f"-- snapshots[{i}] keys:", {k: v for k, v in snap.items() if k != "records"})
            for r in snap.get("records", []):
                print("   ", json.dumps(r, ensure_ascii=False)[:400])

    elif topic == "ev05_drift":
        db, names = sql_load("evidence/databases/customer_data_read_replica_20260921.sql"), None
        for t in ["customer_data_primary", "customer_data_read_replica"]:
            rows = db.execute(f'SELECT resource_id FROM "{t}"').fetchall()
            print(t, len(rows), sorted(r[0] for r in rows))
        for rid in ("account_994", "search_1007", "audit_record_9528"):
            for t in ["customer_data_primary", "customer_data_read_replica"]:
                rows = db.execute(f'SELECT * FROM "{t}" WHERE resource_id=?', (rid,)).fetchall()
                print(f"  {t}.{rid}: {[dict(r) for r in rows]}")

    elif topic == "ev06_80_90":
        lines = p("evidence/logs/structured_service_events_eu_west_20260918.log").read_text(
            encoding="utf-8").splitlines()
        for n in (28, 86):
            print(n, lines[n - 1])

    elif topic == "ev56":
        d = json.loads(p("evidence/records/customer_analytics_report_20260907.json").read_text(encoding="utf-8"))
        print(json.dumps(d, indent=1, ensure_ascii=False)[:2500])

    elif topic == "ev57":
        db, _ = sql_tables("evidence/databases/customer_search_primary_20260910.sql")
        for t in [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
            print(t, [dict(r) for r in db.execute(f'SELECT * FROM "{t}"')][:4])

    elif topic == "ev58":
        import fitz
        with fitz.open(p("evidence/documents/delivery_correction_attachment.pdf")) as doc:
            for i, page in enumerate(doc, 1):
                print(f"-- page {i}")
                print(page.get_text())

    elif topic == "ev59":
        d = json.loads(p("evidence/records/customer_export_jobs_20260914.json").read_text(encoding="utf-8"))
        print(json.dumps(d, indent=1, ensure_ascii=False)[:2000])

    elif topic == "ev61":
        lines = p("evidence/logs/support_replica.log").read_text(encoding="utf-8").splitlines()
        for n, l in enumerate(lines, 1):
            print(n, l)

    elif topic == "ev93":
        db, _ = sql_tables("evidence/databases/customer_data_inventory_20260916.sql")
        for t in [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
            rows = [dict(r) for r in db.execute(f'SELECT * FROM "{t}"')]
            print(t, json.dumps(rows, ensure_ascii=False)[:900])

    else:
        print("unknown topic", topic)


if __name__ == "__main__":
    main(sys.argv[1])
