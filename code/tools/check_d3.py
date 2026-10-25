import yaml
import re

with open("code/notes/step_rules.yaml", encoding="utf-8") as f:
    step_rules = yaml.safe_load(f)

mappings = step_rules.get("rule_contract_mapping", {})

with open("code/rules_engine.py", encoding="utf-8") as f:
    engine_code = f.read()

# Extract rule values assigned in RULE_DEFINITIONS and Verdict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rules_engine import RULE_DEFINITIONS

engine_rules = {r["rule_id"] for r in RULE_DEFINITIONS.values()}
engine_rules.add("UNKNOWN_CLASSIFICATION")

print(f"Engine rule labels found ({len(engine_rules)}): {sorted(engine_rules)}")
all_mapped = True
for r in sorted(engine_rules):
    if r in mappings:
        m = mappings[r]
        print(f"[MAPPED] {r:24s} -> ({m['source_type']}) {m['quoted_row']}")
    else:
        print(f"[UNMAPPED] {r}")
        all_mapped = False

print(f"\nOverall D3 Result: {'PASS' if all_mapped else 'FAILED'}")
