import sys
from pathlib import Path
sys.path.insert(0, str(Path("code").resolve()))
sys.path.insert(0, str(Path("code/readers").resolve()))

from evidence_index import EvidenceIndex
from sql_reader import SqlSnapshotReader
from pdf_reader import PdfDocumentReader
from intent import classify_intent
from identity import IdentityResolver
from timeutil import parse_iso
import pandas as pd

def run():
    print("--- G4.2 FILE FACTS & NO-CONTENT TABLE ---")
    idx = EvidenceIndex(dataset_dir="dataset", cache_dir="code/.cache/evidence_index")
    total_facts, cache_hits = idx.build()
    
    ext_stats = {}
    no_content_files = []
    for fid, stat in idx.file_stats.items():
        ext = stat["format"]
        if ext not in ext_stats:
            ext_stats[ext] = {"files": 0, "facts": 0, "empty_files": 0}
        ext_stats[ext]["files"] += 1
        ext_stats[ext]["facts"] += stat["facts_count"]
        if stat["facts_count"] == 0:
            ext_stats[ext]["empty_files"] += 1
            no_content_files.append((fid, stat["no_content_reason"]))

    for ext, s in sorted(ext_stats.items()):
        print(f"{ext:<6} files={s['files']:<3} facts={s['facts']:<5} empty_files={s['empty_files']}")
    print(f"TOTAL  files={len(idx.file_stats):<3} facts={total_facts:<5} empty_files={len(no_content_files)}")
    print(f"\nNo-content files ({len(no_content_files)}):")
    for fid, r in no_content_files:
        print(f"  - {fid}: {r}")

    print("\n--- G4.3 SQL TABLE INTROSPECTION ---")
    for fid, entry in sorted(idx.manifest_loader.entries.items()):
        if entry.file_path.endswith(".sql"):
            p = Path("dataset") / entry.file_path
            rdr = SqlSnapshotReader(p)
            tables = rdr.get_tables()
            print(f"{fid} ({entry.file_path}): {tables}")

    print("\n--- G4.4 PDF CHAR COUNTS ---")
    for fid, entry in sorted(idx.manifest_loader.entries.items()):
        if entry.file_path.endswith(".pdf"):
            p = Path("dataset") / entry.file_path
            rdr = PdfDocumentReader(p)
            pages = rdr.extract_text()
            char_count = rdr.total_char_count()
            print(f"{fid} ({entry.file_path}): pages={len(pages)}, char_count={char_count}")

    print("\n--- G4.6 CUTOFF METADATA ---")
    df_sample = pd.read_csv("dataset/sample_deletion_requests.csv")
    for cid in ["case_05", "case_21", "case_26"]:
        row = df_sample[df_sample["case_id"] == cid].iloc[0]
        audit_dt = parse_iso(row["audit_at"])
        usable = [f for f in idx.facts if f.is_usable_at(audit_dt)]
        excluded = [f for f in idx.facts if not f.is_usable_at(audit_dt)]
        print(f"{cid} (audit_at={row['audit_at']}): total={len(idx.facts)}, usable={len(usable)}, excluded={len(excluded)}")

    print("\n--- G5.2 INTENT CLASSIFICATION (518 REQUESTS) ---")
    df_req = pd.read_csv("dataset/deletion_requests.csv")
    labels = {}
    for _, r in df_req.iterrows():
        lbl, reason = classify_intent(r["request_text"])
        labels[lbl] = labels.get(lbl, 0) + 1
    print("Intent distribution on 518 requests:", labels)
    non_del = [r["case_id"] for _, r in df_req.iterrows() if classify_intent(r["request_text"])[0] == "NON_DELETION"]
    print("NON_DELETION cases:", non_del)

    print("\n--- G5.3 IDENTITY RESOLUTION TRACES ---")
    resolver = IdentityResolver("dataset")
    for cid in ["case_01", "case_10", "case_12"]:
        row = df_sample[df_sample["case_id"] == cid].iloc[0]
        subj, note = resolver.resolve(row["email"], audit_at=parse_iso(row["audit_at"]))
        status = "RESOLVED" if subj else ("AMBIGUOUS" if "Ambiguous" in note else "UNRESOLVED")
        user_id = subj.user_id if subj else "None"
        aliases = subj.aliases if subj else []
        print(f"{cid}: req_email='{row['email']}', audit_at='{row['audit_at']}' -> user_id={user_id}, status={status}, aliases={len(aliases)}")
        for a in aliases:
            print(f"   alias: kind={a.kind}, val={a.value}, valid_from={a.valid_from}, valid_to={a.valid_to}, source={a.source_id}")

    print("\n--- G5.5 IDENTITY ON 518 REQUESTS ---")
    res_stats = {"RESOLVED": 0, "UNRESOLVED": 0, "AMBIGUOUS": 0}
    for _, r in df_req.iterrows():
        subj, note = resolver.resolve(r["email"], audit_at=parse_iso(r["audit_at"]))
        status = "RESOLVED" if subj else ("AMBIGUOUS" if "Ambiguous" in note else "UNRESOLVED")
        res_stats[status] += 1
    print("Identity resolution across 518 requests:", res_stats)

if __name__ == "__main__":
    run()
