#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 6: merge + evaluate the balanced 3-class run.

Computes the NRC word-list emotion (Method 2) for each review, merges with the
LLM 3-class + emotion output, and produces:
  - data/step6_reviews.jsonl   (per-review, for the dashboard)
  - results/step6_results.json (metrics + 3x3 confusion matrix)
  - results/step6_report.txt
"""
import json
import os
from collections import Counter

from emotions_nrc import load_lexicon, score_text
from build_sample import SEED

HERE = os.path.dirname(os.path.abspath(__file__))
F_SAMPLE = os.path.join(HERE, "data", "step6_sample.jsonl")
F_LLM = os.path.join(HERE, "data", "step6_llm.jsonl")
F_REV = os.path.join(HERE, "data", "step6_reviews.jsonl")
R_JSON = os.path.join(HERE, "results", "step6_results.json")
R_TXT = os.path.join(HERE, "results", "step6_report.txt")

CLASSES = ["POSITIVE", "NEUTRAL", "NEGATIVE"]


def main():
    with open(F_SAMPLE) as f:
        sample = [json.loads(l) for l in f if l.strip()]
    with open(F_LLM) as f:
        llm = {r["index"]: r for r in (json.loads(l) for l in f if l.strip())}
    assert len(llm) == len(sample), "LLM run incomplete"

    lexicon = load_lexicon()

    reviews = []
    for rec in sample:
        i = rec["index"]
        res = llm[i]
        nrc_scores, nrc_emo, matched = score_text(f"{rec['title']} {rec['text']}", lexicon)
        ll_emo = res.get("primary_emotion")
        emo_agree = (ll_emo == nrc_emo) if nrc_emo else None
        reviews.append({
            "index": i,
            "source_row": rec["source_row"],
            "rating": rec["rating"],
            "true_class": rec["true_class"],
            "predicted": res["sentiment"],
            "confidence": res["confidence"],
            "correct": res["sentiment"] == rec["true_class"],
            "title": rec["title"],
            "text": rec["text"],
            "reason": res["reason"],
            "llm_emotion": ll_emo,
            "nrc_emotion": nrc_emo,
            "emo_agree": emo_agree,
            "nrc_scores": {e: {"score": nrc_scores[e],
                               "words": matched[e][:10]} for e in nrc_scores},
        })

    with open(F_REV, "w") as f:
        for r in reviews:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- metrics ----
    n = len(reviews)
    n_correct = sum(1 for r in reviews if r["correct"])
    n_wrong = n - n_correct
    overall = n_correct / n

    class_by_true = {c: [r for r in reviews if r["true_class"] == c] for c in CLASSES}
    class_acc = {}
    for c in CLASSES:
        grp = class_by_true[c]
        ok = sum(1 for r in grp if r["correct"])
        class_acc[c] = {"total": len(grp), "correct": ok,
                        "accuracy": round(ok / len(grp), 4) if grp else None}

    # 3x3 confusion matrix: rows = true, cols = predicted
    cm = {}
    for t in CLASSES:
        for p in CLASSES:
            cm[f"t_{t}_p_{p}"] = sum(1 for r in reviews
                                     if r["true_class"] == t and r["predicted"] == p)

    # misclassification "flow": where errors go (true -> predicted), predicted != true
    flow = {}
    for t in CLASSES:
        for p in CLASSES:
            if t == p:
                continue
            cnt = cm[f"t_{t}_p_{p}"]
            if cnt:
                flow[f"{t}->{p}"] = cnt

    # emotion agreement (on this sample)
    both = [r for r in reviews if r["nrc_emotion"] is not None]
    agree = [r for r in both if r["emo_agree"]]
    emotion_agree_eval = len(agree) / len(both) if both else None
    emotion_agree_overall = len(agree) / n

    results = {
        "task": "3-class sentiment (POSITIVE/NEUTRAL/NEGATIVE) + emotion",
        "model": "DeepSeek-V4-Flash-0731",
        "sample_seed": SEED,
        "sample_definition": {"POSITIVE": "rating 4-5", "NEUTRAL": "rating 3", "NEGATIVE": "rating 1-2"},
        "label_rule": "4-5=POSITIVE, 3=NEUTRAL, 1-2=NEGATIVE",
        "n_reviews": n,
        "overall_accuracy": round(overall, 4),
        "n_correct": n_correct,
        "n_incorrect": n_wrong,
        "class_accuracy": class_acc,
        "confusion_matrix": cm,
        "confusion_matrix_layout": "rows=true class, cols=predicted",
        "misclassification_flow": flow,
        "llm_emotion_distribution": dict(Counter(r["llm_emotion"] for r in reviews)),
        "nrc_emotion_distribution": dict(Counter(r["nrc_emotion"] for r in reviews)),
        "nrc_no_match": sum(1 for r in reviews if r["nrc_emotion"] is None),
        "emotion_agree_count": len(agree),
        "emotion_agree_on_evaluated": round(emotion_agree_eval, 4) if emotion_agree_eval is not None else None,
        "emotion_agree_overall": round(emotion_agree_overall, 4),
    }

    os.makedirs(os.path.dirname(R_JSON), exist_ok=True)
    with open(R_JSON, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # report
    L = []
    L.append("MBAX 6418 Assignment 1 - Step 6: Balanced 3-class sentiment + emotion")
    L.append("=" * 66)
    L.append(f"Balanced sample: {n} reviews ({results['sample_definition']}); seed={SEED}")
    L.append(f"Model: {results['model']} (3-class prompt, title+text only)")
    L.append("")
    L.append("Overall accuracy: {:.2f}%  ({} correct / {})".format(overall * 100, n_correct, n))
    L.append(f"Incorrect: {n_wrong}")
    L.append("")
    L.append("Accuracy by class:")
    for c in CLASSES:
        a = class_acc[c]["accuracy"]
        L.append(f"  {c:<8} {a*100:5.1f}%   ({class_acc[c]['correct']}/{class_acc[c]['total']})")
    L.append("")
    L.append("Confusion matrix (rows=true, cols=predicted):")
    L.append("                 " + "".join(f"{c[:3]:>8}" for c in CLASSES))
    for t in CLASSES:
        L.append(f"  {t:<8}   " + "".join(f"{cm[f't_{t}_p_{c}']:>8}" for c in CLASSES))
    L.append("")
    L.append("Where misclassifications go (true -> predicted):")
    if flow:
        for k, v in sorted(flow.items(), key=lambda x: -x[1]):
            L.append(f"  {k}: {v}")
    else:
        L.append("  (none)")
    L.append("")
    L.append("Emotion detection (Methods 1+2 on this sample)")
    L.append("  LLM emotion dist: " + ", ".join(f"{k}={v}" for k, v in results['llm_emotion_distribution'].items()))
    L.append("  NRC emotion dist: " + ", ".join(f"{k}={v}" for k, v in sorted(results['nrc_emotion_distribution'].items(), key=lambda x: -(x[1] or 0))))
    L.append(f"  Emotion agreement: {len(agree)}/{len(both)} agree "
             f"({(emotion_agree_eval or 0)*100:.1f}% of those with an NRC emotion)")
    with open(R_TXT, "w") as f:
        f.write("\n".join(L) + "\n")

    print("\n".join(L))


if __name__ == "__main__":
    main()
