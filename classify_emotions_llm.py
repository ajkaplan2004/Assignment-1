#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 5, Method 1.

Re-runs the extended structured prompt (which now returns BOTH sentiment and
primary_emotion) over the first 100 reviews. Exposes only title + text (never
the rating). Results cached to data/emotions_llm.jsonl, resumable by index.
"""
import gzip
import json
import os

from llm_client import llm_call
from sentiment_prompt import build_prompt, parse_response

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "Gift_Cards.jsonl.gz")
N = 100
OUT = os.path.join(HERE, "data", "emotions_llm.jsonl")


def load_cache():
    cache = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    cache[r["index"]] = r
    return cache


def save(records):
    recs = sorted(records, key=lambda r: r["index"])
    with open(OUT, "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        reviews = []
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
            if len(reviews) >= N:
                break
    assert len(reviews) == N

    cache = load_cache()
    records = list(cache.values())
    todo = [i for i in range(N) if i not in cache]
    if todo:
        print(f"Classifying emotions for {len(todo)} reviews (cached {len(cache)})...")

    for i in todo:
        review = reviews[i]
        title, text = review.get("title", ""), review.get("text", "")
        system, user = build_prompt(title, text)
        raw = llm_call(system, user)
        parsed = parse_response(raw)  # validates sentiment + primary_emotion
        rec = {
            "index": i,
            "title": title,
            "text": text,
            "sentiment": parsed["sentiment"],
            "primary_emotion": parsed["primary_emotion"],
            "confidence": parsed["confidence"],
            "reason": parsed["reason"],
            "raw_response": raw,
        }
        records.append(rec)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{N}")
            save(records)

    save(records)
    n_emo = sum(1 for r in records if r.get("primary_emotion"))
    print(f"Done. {len(records)} records, {n_emo} with a primary_emotion.")


if __name__ == "__main__":
    main()
