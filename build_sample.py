#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 6.

Build a balanced 3-class sample from the ENTIRE Gift Cards dataset:
  POSITIVE = rating 4-5,  NEUTRAL = rating 3,  NEGATIVE = rating 1-2.
50 of each (150 total). Fixed random seed -> exact sample is reproducible.
"""
import gzip
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "Gift_Cards.jsonl.gz")
OUT = os.path.join(HERE, "data", "step6_sample.jsonl")

SEED = 6418  # fixed -> reproducible
PER_CLASS = 50
NEGATIVE_RATINGS = (1, 2)
NEUTRAL_RATINGS = (3,)
POSITIVE_RATINGS = (4, 5)


def true_class(rating):
    if rating in NEGATIVE_RATINGS:
        return "NEGATIVE"
    if rating in POSITIVE_RATINGS:
        return "POSITIVE"
    return "NEUTRAL"


def main():
    # streaming: only need rating + fields per row; keep source_row (line index)
    buckets = {"NEGATIVE": [], "NEUTRAL": [], "POSITIVE": []}
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        # drop the file's own first line if it's blank
        for src, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cls = true_class(int(row["rating"]))
            buckets[cls].append((src, row))

    print("Available before sampling:")
    for cls in ("NEGATIVE", "NEUTRAL", "POSITIVE"):
        print(f"  {cls}: {len(buckets[cls]):,}")

    rng = random.Random(SEED)
    # deterministic per-bucket order by (source_row) is implicit; shuffle with seed
    chosen = []
    for cls in ("NEGATIVE", "NEUTRAL", "POSITIVE"):
        pool = buckets[cls]
        rng.shuffle(pool)
        assert len(pool) >= PER_CLASS, f"{cls} only has {len(pool)}"
        chosen.extend(pool[:PER_CLASS])

    # keep stable order in the file: group by class order NEG, NEU, POS
    chosen.sort(key=lambda x: x[0])  # by source row so it's not a mashup
    records = []
    for i, (src, row) in enumerate(chosen):
        records.append({
            "index": i,
            "source_row": src,
            "rating": row["rating"],
            "true_class": true_class(int(row["rating"])),
            "title": row.get("title", ""),
            "text": row.get("text", ""),
        })

    with open(OUT, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"\nSaved {len(records)} reviews -> {OUT}")
    print("Sample true-class distribution:", dict(Counter(r["true_class"] for r in records)))
    print("Seed:", SEED)


if __name__ == "__main__":
    main()
