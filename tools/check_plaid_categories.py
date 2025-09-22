# tools/check_plaid_categories.py
import json, sys
from collections import Counter

p = sys.argv[1]
data = json.load(open(p))

pairs = []
primaries = Counter()
details = Counter()

for i, entry in enumerate(data):
    pfcs = entry.get("possible_pfcs") or []
    # If your JSON has only ONE possible_pfcs per entry, you will only ever get len(data) pairs
    for pf in pfcs:
        primary = (pf.get("primary") or "").strip()
        detailed = (pf.get("detailed") or "").strip()
        if not primary:
            continue
        pairs.append((primary, detailed))
        primaries[primary] += 1
        details[detailed] += 1

uniq = set(pairs)
print(f"total rows: {len(data)}")
print(f"total pairs seen: {len(pairs)}")
print(f"unique (primary,detailed) pairs: {len(uniq)}")
print(f"unique primary only: {len({p for p,_ in uniq})}")

if len(uniq) <= 97:
    print("\nLikely expected: only 97 distinct pairs in the source.")
else:
    # show a few duplicates in source (same pair repeated)
    dupes = [x for x in pairs if pairs.count(x) > 1]
    if dupes:
        print("example duplicate pair:", dupes[0])
