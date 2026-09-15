#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 1: verify dataset loads as gzipped JSONL."""
import gzip
import json
from collections import Counter

PATH = "data/Gift_Cards.jsonl.gz"

reviews = []
with gzip.open(PATH, "rt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            reviews.append(json.loads(line))

print(f"Total reviews loaded: {len(reviews):,}")
print()

# Fields present in the first record
first = reviews[0]
print("Fields per record:", list(first.keys()))
print()
print("Example record (pretty-printed):")
print(json.dumps(first, indent=2, ensure_ascii=False))
print()

# Cross-check: do all records share the same fields?
all_fields = set()
missing = Counter()
for r in reviews:
    all_fields |= set(r.keys())
    for k in first.keys():
        if k not in r:
            missing[k] += 1
print("Union of all fields across records:", sorted(all_fields))
if missing:
    print("Records missing a field (field -> count):", dict(missing))
else:
    print("Every record contains all standard fields: OK")
print()

# Data types per field (sample)
print("Field dtypes:")
for k in first.keys():
    vals = {type(r[k]).__name__ for r in reviews[:20000]}
    print(f"  {k}: {sorted(vals)}")
print()

# Rating distribution (useful context for the classifier later)
rating_dist = Counter(int(r["rating"]) for r in reviews)
print("Rating distribution (1-5):")
for r in sorted(rating_dist):
    print(f"  {r} stars: {rating_dist[r]:,} ({100*rating_dist[r]/len(reviews):.2f}%)")
