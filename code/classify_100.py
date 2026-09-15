#!/usr/bin/env python3
"""
classify_100.py
===============
MBAX 6418 — Assignment 1, Step 2 (binary sentiment classification of the
FIRST 100 reviews).

For each of the first 100 reviews:
   1. Send ONLY title + text to the LLM (the rating is NEVER sent).
   2. Record the LLM prediction.
   3. After prediction, derive ground truth from the rating
        rating >= 4  ->  POSITIVE
        rating <  4  ->  NEGATIVE
   4. Record whether the prediction was correct.

Writes raw per-review results to  results/step2_predictions.csv
Writes the summary metrics to   results/step2_summary.json
(plus a human-readable summary copied to stdout).

Resume-friendly: rows already in the CSV are not re-sent to the LLM, so the
script may be re-run safely and will continue from where it left off.
"""
import csv
import gzip
import json
import os
from pathlib import Path

from classify_review import classify_review

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "Gift_Cards.jsonl.gz"
RESULTS_DIR = HERE.parent / "results"
CSV_PATH = RESULTS_DIR / "step2_predictions.csv"
SUMMARY_PATH = RESULTS_DIR / "step2_summary.json"

N = 100
CSV_FIELDS = ["index", "rating", "title", "text",
              "predicted_sentiment", "actual_sentiment", "correct"]


def true_class(rating):
    """Ground-truth class derived from the rating (used ONLY for evaluation)."""
    return "POSITIVE" if rating >= 4 else "NEGATIVE"


def load_first_n(path, n):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        reviews = []
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
            if len(reviews) >= n:
                break
    return reviews


def load_done():
    """Load rows already written to the CSV, keyed by index."""
    done = {}
    if CSV_PATH.exists():
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[int(row["index"])] = row
    return done


def save_rows(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in sorted(rows, key=lambda x: x["index"]):
            writer.writerow(r)


def main():
    reviews = load_first_n(DATA, N)
    assert len(reviews) == N, f"Expected {N} reviews, found {len(reviews)}"

    done = load_done()
    pending = [i for i in range(N) if i not in done]
    print(f"Loaded {N} reviews. Prediction status: {len(done)} cached, "
          f"{len(pending)} to classify.")

    # --- Classify each pending review (title + text ONLY, never rating) ---
    new_rows = []
    for i in pending:
        r = reviews[i]
        title, text = r.get("title", ""), r.get("text", "")
        result = classify_review(title, text)   # sends only title + text
        rating = r["rating"]
        actual = true_class(rating)             # computed AFTER prediction
        new_rows.append({
            "index": i,
            "rating": rating,
            "title": result["title"],
            "text": result["text"],
            "predicted_sentiment": result["label"],
            "actual_sentiment": actual,
            "correct": result["label"] == actual,
        })
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{N} predicted")

    # --- Merge with cache, persist CSV ---
    all_rows = {**done, **{r["index"]: r for r in new_rows}}
    save_rows(all_rows.values())
    ordered = [all_rows[i] for i in range(N)]

    # --- Metrics ---
    total = len(ordered)
    n_correct = sum(1 for r in ordered if r["correct"])
    n_incorrect = total - n_correct
    accuracy = n_correct / total if total else 0.0

    def class_acc(cls):
        sub = [r for r in ordered if r["actual_sentiment"] == cls]
        if not sub:
            return None, 0
        ok = sum(1 for r in sub if r["predicted_sentiment"] == cls)
        return ok / len(sub), len(sub)

    pos_acc, pos_n = class_acc("POSITIVE")
    neg_acc, neg_n = class_acc("NEGATIVE")

    # Actual vs predicted class count matrices.
    actual_counts = {"POSITIVE": pos_n, "NEGATIVE": neg_n}
    pred_counts = {"POSITIVE": sum(1 for r in ordered if r["predicted_sentiment"] == "POSITIVE"),
                   "NEGATIVE": sum(1 for r in ordered if r["predicted_sentiment"] == "NEGATIVE")}

    # Confusion matrix: rows = actual, cols = predicted.
    cm = {}
    for a in ("POSITIVE", "NEGATIVE"):
        for p in ("POSITIVE", "NEGATIVE"):
            cm[f"{a}-{p}"] = sum(1 for r in ordered
                                 if r["actual_sentiment"] == a
                                 and r["predicted_sentiment"] == p)

    summary = {
        "model": "DeepSeek-V4-Flash-0731",
        "temperature": 0.0,
        "n_reviews": total,
        "n_correct": n_correct,
        "n_incorrect": n_incorrect,
        "total_accuracy": round(accuracy, 4),
        "positive_accuracy": round(pos_acc, 4) if pos_acc is not None else None,
        "negative_accuracy": round(neg_acc, 4) if neg_acc is not None else None,
        "positive_total": pos_n,
        "negative_total": neg_n,
        "actual_counts": actual_counts,
        "predicted_counts": pred_counts,
        "confusion_matrix": cm,  # keys "actual-predicted"
        "confusion_layout": "rows=actual, cols=predicted",
    }
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # --- Clear printed summary ---
    print("\n" + "=" * 62)
    print("STEP 2 — Binary Sentiment Classification Summary (first 100 reviews)")
    print("=" * 62)
    print(f"Ground-truth rule : rating >= 4 -> POSITIVE, rating < 4 -> NEGATIVE")
    print(f"LLM input         : title + text only (rating never sent)")
    print()
    print(f"Total reviews     : {total}")
    print(f"Correct           : {n_correct}")
    print(f"Incorrect         : {n_incorrect}")
    print(f"Overall accuracy  : {accuracy * 100:.2f}%")
    print()
    print(f"POSITIVE accuracy : {pos_acc * 100:.2f}%  ({n_correct} of POSITIVE predicted POSITIVE)"
          if pos_acc is not None else "POSITIVE accuracy: n/a (no positive reviews)")
    # Correct per-class wording:
    pos_right = cm["POSITIVE-POSITIVE"]
    neg_right = cm["NEGATIVE-NEGATIVE"]
    print(f"  -> {pos_right}/{pos_n} POSITIVE reviews correctly tagged POSITIVE")
    print(f"  -> {neg_right}/{neg_n} NEGATIVE reviews correctly tagged NEGATIVE")
    print(f"NEGATIVE accuracy : {neg_acc * 100:.2f}%")
    print()
    print("Class counts")
    print(f"  Actual    : POSITIVE={pos_n}, NEGATIVE={neg_n}")
    print(f"  Predicted : POSITIVE={pred_counts['POSITIVE']}, NEGATIVE={pred_counts['NEGATIVE']}")
    print()
    print("Confusion matrix (rows=actual, cols=predicted)")
    print(f"                  Pred POS    Pred NEG")
    print(f"  Actual POSITIVE  {cm['POSITIVE-POSITIVE']:>7}      {cm['POSITIVE-NEGATIVE']:>7}")
    print(f"  Actual NEGATIVE  {cm['NEGATIVE-POSITIVE']:>7}      {cm['NEGATIVE-NEGATIVE']:>7}")
    print()
    print(f"Raw results : {CSV_PATH}")
    print(f"Summary     : {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
