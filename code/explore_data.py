#!/usr/bin/env python3
"""
explore_data.py
===============
MBAX 6418 — Assignment 1, Step 1: Dataset load & verification.

Loads the Amazon Reviews 2023 "Gift Cards" dataset (gzipped JSON Lines),
confirms it reads successfully, and prints:
  - the number of reviews
  - the field (column) names
  - a few sample reviews (rating, title, text)

This script opens the file read-only and does NOT modify the dataset.
"""

import gzip
import json
import os
from pathlib import Path

# Paths are relative to this file's location so the script runs from anywhere.
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
GZ_PATH = DATA_DIR / "Gift_Cards.jsonl.gz"

SAMPLE_COUNT = 5  # number of example reviews to print


def load_reviews(gz_path: Path):
    """Yield each review as a dict from the gzipped JSON-lines file."""
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:  # skip blank lines
                yield json.loads(line)


def main() -> None:
    if not GZ_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {GZ_PATH}. "
            "Download Gift_Cards.jsonl.gz into the data/ folder first."
        )

    print(f"Dataset file : {GZ_PATH}")
    print(f"Size on disk : {GZ_PATH.stat().st_size / 1e6:.2f} MB (gzipped)")
    print("Reading reviews... (read-only)\n")

    reviews = list(load_reviews(GZ_PATH))
    total = len(reviews)

    # ---- 2. Confirm it read ----
    if total == 0:
        raise RuntimeError("File read successfully but contained zero reviews.")
    print(f"[OK] Dataset loaded successfully: {total:,} reviews\n")

    # ---- 4. Field names (columns) ----
    if reviews:
        field_names = list(reviews[0].keys())
        print(f"Fields ({len(field_names)}):")
        for i, name in enumerate(field_names, 1):
            print(f"  {i:>2}. {name}")
        print()

    # ---- 5. Sample reviews: rating, title, text ----
    print(f"Sample reviews (first {min(SAMPLE_COUNT, total)}):")
    print("-" * 70)
    for idx, r in enumerate(reviews[:SAMPLE_COUNT], 1):
        rating = r.get("rating")
        title = r.get("title", "")
        text = r.get("text", "")
        print(f"\nReview #{idx}")
        print(f"  rating : {rating}")
        print(f"  title  : {title}")
        print(f"  text   : {text[:400]}{'...' if len(text) > 400 else ''}")

    # ---- 6. Dataset untouched ----
    # Sanity: confirm the source file was not modified (mtime unchanged is
    # inherent; we simply never opened it for writing).
    print("\n" + "-" * 70)
    print("[OK] Dataset opened read-only — original file was NOT modified.")


if __name__ == "__main__":
    main()
