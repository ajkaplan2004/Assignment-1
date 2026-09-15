#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 2.

Classify the FIRST 100 Amazon Gift Card reviews as POSITIVE/NEGATIVE using the
LLM, exposing ONLY title + text (never the rating), then evaluate vs the true
class derived from the rating (rating >= 4 -> POSITIVE, rating < 4 -> NEGATIVE).

Reproducible: predicted results are cached to data/predictions_raw.jsonl; on a
re-run, already-predicted reviews are loaded from cache and only new ones call
the LLM. Metrics are computed from the cache file, so identical results every run.
"""
import json
import os

from llm_client import llm_call
from sentiment_prompt import build_prompt, parse_response

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "Gift_Cards.jsonl.gz")
N = 100
RAW = os.path.join(HERE, "data", "predictions_raw.jsonl")
RESULTS_JSON = os.path.join(HERE, "results", "step2_results.json")
REPORT_TXT = os.path.join(HERE, "results", "step2_report.txt")


def true_class(rating):
    return "POSITIVE" if rating >= 4 else "NEGATIVE"


def load_raw():
    """Load cached predictions keyed by index."""
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    cache[rec["index"]] = rec
    return cache


def save_raw(records):
    with open(RAW, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    # --- Load the first 100 reviews ---
    import gzip
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        reviews = []
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
            if len(reviews) >= N:
                break
    assert len(reviews) == N, f"Expected {N}, found {len(reviews)}"

    # --- Classify (resume from cache) ---
    cache = load_raw()
    records = []
    to_do = [i for i in range(N) if i not in cache]

    if to_do:
        print(f"Classifying {len(to_do)} reviews with the LLM (cached {len(cache)})...")
    for i in to_do:
        review = reviews[i]
        title, text = review.get("title", ""), review.get("text", "")
        system, user = build_prompt(title, text)
        raw = llm_call(system, user)
        parsed = parse_response(raw)  # raises on bad sentiment/JSON
        rec = {
            "index": i,
            "rating": review["rating"],
            "true_class": true_class(review["rating"]),
            "title": title,
            "text": text,
            "predicted": parsed["sentiment"],
            "confidence": parsed["confidence"],
            "reason": parsed["reason"],
            "raw_response": raw,
        }
        records.append(rec)
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{N} done")

    # Merge cache + new, sort by index
    merged = list(cache.values()) + records
    merged.sort(key=lambda r: r["index"])
    save_raw(merged)

    # --- Evaluate ---
    by_true = {"POSITIVE": [], "NEGATIVE": []}
    misclassified = []
    for rec in merged:
        correct = rec["predicted"] == rec["true_class"]
        rec["correct"] = correct
        by_true[rec["true_class"]].append(correct)
        if not correct:
            misclassified.append({
                "index": rec["index"],
                "rating": rec["rating"],
                "true_class": rec["true_class"],
                "predicted": rec["predicted"],
                "confidence": rec["confidence"],
                "title": rec["title"],
                "text": rec["text"][:120] + ("..." if len(rec["text"]) > 120 else ""),
            })

    total = len(merged)
    n_correct = sum(1 for r in merged if r["correct"])
    n_wrong = total - n_correct
    acc = n_correct / total

    pos_correct = sum(by_true["POSITIVE"]); pos_total = len(by_true["POSITIVE"])
    neg_correct = sum(by_true["NEGATIVE"]); neg_total = len(by_true["NEGATIVE"])
    pos_acc = pos_correct / pos_total if pos_total else None
    neg_acc = neg_correct / neg_total if neg_total else None

    cm = {
        "true_P_pred_P": sum(1 for r in merged if r["true_class"] == "POSITIVE" and r["predicted"] == "POSITIVE"),
        "true_P_pred_N": sum(1 for r in merged if r["true_class"] == "POSITIVE" and r["predicted"] == "NEGATIVE"),
        "true_N_pred_P": sum(1 for r in merged if r["true_class"] == "NEGATIVE" and r["predicted"] == "POSITIVE"),
        "true_N_pred_N": sum(1 for r in merged if r["true_class"] == "NEGATIVE" and r["predicted"] == "NEGATIVE"),
    }

    results = {
        "model": "DeepSeek-V4-Flash-0731",
        "n_reviews": total,
        "total_accuracy": round(acc, 4),
        "n_correct": n_correct,
        "n_incorrect": n_wrong,
        "positive_accuracy": round(pos_acc, 4) if pos_acc is not None else None,
        "negative_accuracy": round(neg_acc, 4) if neg_acc is not None else None,
        "positive_total": pos_total,
        "negative_total": neg_total,
        "confusion_matrix": cm,
        "confusion_matrix_layout": "rows=true class, cols=predicted (POS, NEG)",
        "misclassified": misclassified,
    }

    os.makedirs(os.path.dirname(RESULTS_JSON), exist_ok=True)
    with open(RESULTS_JSON, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # --- Human-readable report ---
    lines = []
    lines.append("MBAX 6418 Assignment 1 - Step 2 Report")
    lines.append("=" * 60)
    lines.append(f"Model: {results['model']}  |  Reviews evaluated: {total}")
    lines.append(f"Label rule: rating >= 4 -> POSITIVE, rating < 4 -> NEGATIVE")
    lines.append("")
    lines.append("Overall accuracy: {:.2f}%  ({} correct / {})".format(acc * 100, n_correct, total))
    lines.append(f"Incorrect: {n_wrong}")
    lines.append("")
    lines.append(f"POSITIVE accuracy: {pos_acc * 100:.2f}%  ({pos_correct}/{pos_total})")
    lines.append(f"NEGATIVE accuracy: {neg_acc * 100:.2f}%  ({neg_correct}/{neg_total})")
    lines.append("")
    lines.append("Confusion matrix  (rows = true, cols = predicted):")
    lines.append(f"                 Pred POS    Pred NEG")
    lines.append(f"True POSITIVE      {cm['true_P_pred_P']:>7}      {cm['true_P_pred_N']:>7}")
    lines.append(f"True NEGATIVE      {cm['true_N_pred_P']:>7}      {cm['true_N_pred_N']:>7}")
    lines.append("")
    lines.append(f"Misclassified ({len(misclassified)}):")
    for m in misclassified:
        lines.append(f"  #{m['index']}: true={m['true_class']} pred={m['predicted']} "
                     f"(rating {m['rating']}, conf {m['confidence']:.2f}) :: \"{m['title']}\": {m['text']}")
    with open(REPORT_TXT, "w") as f:
        f.write("\n".join(lines) + "\n")

    # --- Console ---
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("\nSaved: predictions_raw.jsonl, step2_results.json, step2_report.txt")


if __name__ == "__main__":
    main()
