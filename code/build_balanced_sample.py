#!/usr/bin/env python3
"""
build_balanced_sample.py
========================
MBAX 6418 — Assignment 1, Step 6.
Build a BALANCED 3-class sample from the ENTIRE Gift Cards dataset:
  POSITIVE = rating 4-5,  NEUTRAL = rating 3,  NEGATIVE = rating 1-2.
Sampled ~50 of each (150 total). A FIXED random seed makes the exact draw
reproducible on every run. Rows are NOT just the first ones — each class is
sampled uniformly at random across the whole dataset.

Output: data/step6_sample.jsonl
"""
import gzip
import json
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "Gift_Cards.jsonl.gz"
OUT = HERE.parent / "data" / "step6_sample.jsonl"

SEED = 6418          # fixed -> reproducible
PER_CLASS = 50

NEG_RATINGS = (1, 2)
NEU_RATINGS = (3,)
POS_RATINGS = (4, 5)


def true_class(rating):
    r = int(rating)
    if r in NEG_RATINGS:
        return "NEGATIVE"
    if r in POS_RATINGS:
        return "POSITIVE"
    return "NEUTRAL"


def main():
    buckets = {"NEGATIVE": [], "NEUTRAL": [], "POSITIVE": []}
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for src_row, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            buckets[true_class(row["rating"])].append((src_row, row))

    print("Available per class (full dataset):")
    for cls in ("NEGATIVE", "NEUTRAL", "POSITIVE"):
        print(f"  {cls}: {len(buckets[cls]):,}")

    rng = random.Random(SEED)          # deterministic
    chosen = []
    for cls in ("NEGATIVE", "NEUTRAL", "POSITIVE"):
        pool = buckets[cls]
        rng.shuffle(pool)              # random order within the class
        assert len(pool) >= PER_CLASS, f"{cls} has only {len(pool)} reviews"
        chosen.extend(pool[:PER_CLASS])

    # Emit in a stable order (by source row) for easy inspection, not the
    # shuffled order.
    chosen.sort(key=lambda x: x[0])

    records = [
        {"index": i, "source_row": src,
         "rating": row["rating"], "true_class": true_class(row["rating"]),
         "title": row.get("title", ""), "text": row.get("text", "")}
        for i, (src, row) in enumerate(chosen)
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    dist = Counter(r["true_class"] for r in records)
    print(f"\nSaved {len(records)} reviews -> {OUT}")
    print("Sample true-class distribution:", dict(dist.most_common()))
    print("Seed:", SEED)


if __name__ == "__main__":
    main()
