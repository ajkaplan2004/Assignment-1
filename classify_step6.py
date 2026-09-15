#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 6, Method 1.

Runs the 3-class structured prompt over the balanced 150-review sample.
Only title + text are exposed (never the rating). Cached per index.
"""
import json
import os

from llm_client import llm_call
from prompt_3class import build_prompt, parse_response

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "data", "step6_sample.jsonl")
OUT = os.path.join(HERE, "data", "step6_llm.jsonl")


def load_cache():
    cache = {}
    if os.path.exists(OUT):
        for line in open(OUT):
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
    with open(SAMPLE) as f:
        sample = [json.loads(l) for l in f if l.strip()]

    cache = load_cache()
    records = list(cache.values())
    todo = [i for i in range(len(sample)) if i not in cache]
    if todo:
        print(f"Classifying {len(todo)} reviews (cached {len(cache)})...")

    for i in todo:
        rec = sample[i]
        title, text = rec["title"], rec["text"]
        system, user = build_prompt(title, text)
        raw = llm_call(system, user)
        parsed = parse_response(raw)
        out = {
            "index": i,
            "source_row": rec["source_row"],
            "rating": rec["rating"],
            "true_class": rec["true_class"],
            "title": title,
            "text": text,
            "sentiment": parsed["sentiment"],
            "confidence": parsed["confidence"],
            "primary_emotion": parsed["primary_emotion"],
            "reason": parsed["reason"],
            "raw_response": raw,
        }
        records.append(out)
        if (i + 1) % 30 == 0:
            print(f"  {i + 1}/{len(sample)}")
            save(records)

    save(records)
    n_emo = sum(1 for r in records if r.get("primary_emotion"))
    n_sent = sum(1 for r in records if r.get("sentiment"))
    print(f"Done. {len(records)} records; {n_sent} sentiment, {n_emo} emotion.")


if __name__ == "__main__":
    main()
