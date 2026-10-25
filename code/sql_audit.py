"""sql_audit.py — Load SQL evidence files into SQLite in-memory and query them."""
import sqlite3
import re
from pathlib import Path


def load_sql_to_memory(sql_path: str | Path) -> sqlite3.Connection:
    """Load a .sql file (SQLite-compatible DDL+DML) into an in-memory DB."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    sql = Path(sql_path).read_text(encoding="utf-8", errors="replace")
    conn.executescript(sql)
    return conn


def query_all_tables(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Return all rows from all tables as {table_name: [row_dict, ...]}."""
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    result = {}
    for t in tables:
        rows = conn.execute(f'SELECT * FROM "{t}"').fetchall()
        result[t] = [dict(r) for r in rows]
    return result


def find_user_rows(conn: sqlite3.Connection, identifiers: set[str]) -> list[dict]:
    """
    Search all tables for rows that reference any of the given identifiers.
    Identifiers can be emails, user_ids, phones, email_hashes.
    Returns list of dicts with added '_table' key.
    """
    if not identifiers:
        return []
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    matches = []
    for t in tables:
        try:
            rows = conn.execute(f'SELECT * FROM "{t}"').fetchall()
        except Exception:
            continue
        for row in rows:
            row_dict = dict(row)
            for val in row_dict.values():
                if val and isinstance(val, str):
                    # case-insensitive match against any identifier
                    val_lower = val.lower()
                    for ident in identifiers:
                        if ident.lower() == val_lower or ident.lower() in val_lower:
                            row_dict["_table"] = t
                            matches.append(row_dict)
                            break
                    else:
                        continue
                    break
    return matches
