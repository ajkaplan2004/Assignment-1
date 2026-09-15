#!/usr/bin/env python3
"""
classify_step6.py
=================
MBAX 6418 — Assignment 1, Step 6.
Runs the three-class (POSITIVE / NEUTRAL / NEGATIVE) sentiment + emotion
classifier over the balanced 150-review sample, adds the NRC word-list emotion,
and computes all Step 6 metrics.

Per review the LLM sees ONLY title + text (never the rating). The rating is
used only afterwards to compute the actual class:
    rating 4-5 -> POSITIVE,  rating 3 -> NEUTRAL,  rating 1-2 -> NEGATIVE

Outputs:
  data/step6_balanced_results.csv   raw per-review results (the deliverable CSV)
  results/step6_metrics.json        all final metrics (for dashboard & README)

Resume-friendly: reviews already in the CSV are not re-sent to the LLM.
"""
import csv
import json
from collections import Counter
from pathlib import Path

from llm_client import llm_call
from prompt_3class import build_prompt, parse_response
from emotions_nrc import load_lexicon, score_text, EMOTION_ORDER

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SAMPLE = ROOT / "data" / "step6_sample.jsonl"
CSV_PATH = ROOT / "data" / "step6_balanced_results.csv"
METRICS_PATH = ROOT / "results" / "step6_metrics.json"

CLASSES = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
CSV_FIELDS = ["index", "rating", "title", "text",
              "actual_sentiment", "predicted_sentiment", "correct",
              "llm_emotion", "llm_confidence",
              "nrc_emotion"] + EMOTION_ORDER


def true_class(rating):
    r = int(rating)
    return "POSITIVE" if r >= 4 else ("NEGATIVE" if r <= 2 else "NEUTRAL")


def load_sample(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_done(path):
    done = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row = dict(row)
                row["correct"] = row["correct"] == "True"
                for e in EMOTION_ORDER:
                    row[e] = int(row[e])
                done[int(row["index"])] = row
    return done


def save_rows(rows):
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_FIELDS)
        for r in sorted(rows, key=lambda x: x["index"]):
            w.writerow([r.get(k, "") for k in CSV_FIELDS])


def main():
    sample = load_sample(SAMPLE)
    lexicon = load_lexicon()
    done = load_done(CSV_PATH)
    pending = [r["index"] for r in sample if r["index"] not in done]
    print(f"Sample: {len(sample)} reviews | cached {len(done)} | to classify {len(pending)}")

    rows = []
    for rec in sample:
        i = rec["index"]
        actual = true_class(rec["rating"])

        # --- NRC (cheap, always recompute; LLM-free) ---
        scores, nrc_emotion, matched, _ = score_text(f"{rec['title']} {rec['text']}", lexicon)

        if i in done:
            d = done[i]
            predicted, llm_emotion, conf = d["predicted_sentiment"], d["llm_emotion"], d["llm_confidence"]
            conf = float(conf)
        else:
            # --- LLM: 3-class sentiment + emotion, title/text only ---
            system, user = build_prompt(rec["title"], rec["text"])
            parsed = parse_response(llm_call(system, user))
            predicted, llm_emotion, conf = parsed["sentiment"], parsed["primary_emotion"], parsed["confidence"]

        rec_row = {
            "index": i,
            "rating": rec["rating"],
            "title": rec["title"],
            "text": rec["text"],
            "actual_sentiment": actual,
            "predicted_sentiment": predicted,
            "correct": predicted == actual,
            "llm_emotion": llm_emotion,
            "llm_confidence": conf,
            "nrc_emotion": nrc_emotion,
        }
        for e in EMOTION_ORDER:
            rec_row[e] = scores[e]
        rows.append(rec_row)

        if (i + 1) % 25 == 0:
            print(f"  processed {i + 1}/{len(sample)}")

    save_rows(rows)

    # --- Metrics ---
    total = len(rows)
    n_correct = sum(1 for r in rows if r["correct"])

    def cls_acc(c):
        sub = [r for r in rows if r["actual_sentiment"] == c]
        ok = sum(1 for r in sub if r["predicted_sentiment"] == c)
        return (ok / len(sub), ok, len(sub)) if sub else (None, 0, 0)

    acc = {}
    per = {}
    for c in CLASSES:
        a, ok, n = cls_acc(c)
        per[c] = {"correct": ok, "total": n, "accuracy": round(a, 4) if a is not None else None}

    cm = {}
    for a in CLASSES:
        for p in CLASSES:
            cm[f"{a}-{p}"] = sum(1 for r in rows if r["actual_sentiment"] == a and r["predicted_sentiment"] == p)

    actual_counts = {c: sum(1 for r in rows if r["actual_sentiment"] == c) for c in CLASSES}
    pred_counts = {c: sum(1 for r in rows if r["predicted_sentiment"] == c) for c in CLASSES}

    # --- LLM vs NRC emotion agreement ---
    both = [r for r in rows if r["llm_emotion"] and r["nrc_emotion"]]
    emo_agree = sum(1 for r in both if r["llm_emotion"] == r["nrc_emotion"])

    # --- NEUTRAL handling deep-dive (3-star reviews) ---
    neut = [r for r in rows if r["actual_sentiment"] == "NEUTRAL"]
    neut_pred_dist = Counter(r["predicted_sentiment"] for r in neut)
    avg_conf_neutral = sum(r["llm_confidence"] for r in neut) / len(neut) if neut else None

    metrics = {
        "model": "DeepSeek-V4-Flash-0731",
        "task": "3-class sentiment + primary emotion (balanced 150-review sample)",
        "label_rule": "rating 4-5=POSITIVE, 3=NEUTRAL, 1-2=NEGATIVE",
        "sample_seed": 6418,
        "n_reviews": total,
        "n_correct": n_correct,
        "n_incorrect": total - n_correct,
        "overall_accuracy": round(n_correct / total, 4),
        "per_class_accuracy": per,
        "actual_counts": actual_counts,
        "predicted_counts": pred_counts,
        "confusion_matrix": cm,  # rows=actual, cols=predicted
        "neutral_deep_dive": {
            "actual_neutral_total": len(neut),
            "predicted_distribution": dict(neut_pred_dist.most_common()),
            "avg_llm_confidence_on_neutral": round(avg_conf_neutral, 3) if avg_conf_neutral is not None else None,
        },
        "llm_vs_nrc_emotion": {
            "both_emotions": len(both),
            "agree": emo_agree,
            "disagree": len(both) - emo_agree,
            "agreement_rate_overall": round(emo_agree / total, 4),
            "agreement_rate_on_evaluated": round(emo_agree / len(both), 4) if both else None,
        },
        "llm_emotion_distribution": dict(Counter(r["llm_emotion"] for r in rows if r["llm_emotion"]).most_common()),
        "nrc_emotion_distribution": dict(Counter(r["nrc_emotion"] for r in rows if r["nrc_emotion"]).most_common()),
    }
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # --- Print ---
    print("\n" + "=" * 66)
    print("STEP 6 — 3-class balanced run: FINAL METRICS")
    print("=" * 66)
    print(f"Label rule        : 4-5 POSITIVE | 3 NEUTRAL | 1-2 NEGATIVE")
    print(f"Reviews (balanced): {total}  (correct {n_correct}, incorrect {total - n_correct})")
    print(f"Overall accuracy  : {n_correct/total*100:.2f}%")
    print()
    print("Per-class accuracy:")
    for c in CLASSES:
        a = per[c]["accuracy"]
        print(f"  {c:<9}: {a*100:5.2f}%  ({per[c]['correct']}/{per[c]['total']})")
    print()
    print("Actual counts  :", actual_counts)
    print("Predicted counts:", pred_counts)
    print()
    print("Confusion matrix (rows=actual, cols=predicted):")
    print(f"{'':12}{'POS':>7}{'NEU':>7}{'NEG':>7}")
    for a in CLASSES:
        print(f"{a:<12}{cm[a+'-POSITIVE']:>7}{cm[a+'-NEUTRAL']:>7}{cm[a+'-NEGATIVE']:>7}")
    print()
    print("NEUTRAL (3-star) handling:")
    print(f"  actual NEUTRAL total: {len(neut)}")
    print(f"  predicted as -> {dict(neut_pred_dist.most_common())}")
    if avg_conf_neutral is not None:
        print(f"  avg LLM confidence on NEUTRAL: {avg_conf_neutral:.3f}")
    print()
    print("LLM vs NRC emotion agreement:")
    print(f"  both emotions : {len(both)}  agree={emo_agree}  disagree={len(both)-emo_agree}")
    print(f"  agreement     : {emo_agree/len(both)*100:.1f}% of 150 | "
          f"{emo_agree/total*100:.1f}% overall")
    print()
    print(f"Saved raw CSV  -> {CSV_PATH}")
    print(f"Saved metrics  -> {METRICS_PATH}")


if __name__ == "__main__":
    main()
