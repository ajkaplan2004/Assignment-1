#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 5: merge + agreement analysis.

Merge the two emotion predictions (LLM = Method 1, NRC word-list = Method 2),
compute their agreement rate, summarize where they differ, and emit:
  - data/emotions_results.jsonl   (per-review merged record for the dashboard)
  - results/step5_results.json    (machine-readable metrics)
  - results/step5_report.txt      (human-readable summary)
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
F_LLM = os.path.join(HERE, "data", "emotions_llm.jsonl")
F_NRC = os.path.join(HERE, "data", "nrc_emotions.jsonl")
F_STORED = os.path.join(HERE, "data", "predictions_raw.jsonl")
F_OUT = os.path.join(HERE, "data", "emotions_results.jsonl")
R_JSON = os.path.join(HERE, "results", "step5_results.json")
R_TXT = os.path.join(HERE, "results", "step5_report.txt")


def load_jsonl(path):
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def main():
    llm = {r["index"]: r for r in load_jsonl(F_LLM)}
    nrc = {r["index"]: r for r in load_jsonl(F_NRC)}
    stored = {r["index"]: r for r in load_jsonl(F_STORED)}

    merged = []
    for i in sorted(llm):
        n = nrc[i]
        ll = llm[i]
        s = stored[i]
        recon = {e: {"score": n["nrc_scores"].get(e, 0), "words": n["top_terms"].get(e, [])}
                 for e in sorted(n["nrc_scores"])}
        agree = (n["nrc_emotion"] is not None) and (ll["primary_emotion"] == n["nrc_emotion"])
        merged.append({
            "index": i,
            "rating": s["rating"],
            "true_class": s["true_class"],
            "title": s["title"],
            "text": s["text"],
            "sentiment": s["predicted"],             # Step 2 stored sentiment (stable)
            "llm_emotion": ll["primary_emotion"],     # Method 1
            "nrc_emotion": n["nrc_emotion"],          # Method 2 (None if no lexicon match)
            "nrc_scores": recon,
            "agree": agree,
        })

    with open(F_OUT, "w") as f:
        for rec in merged:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---- agreement metrics ----
    n = len(merged)
    nrc_none = sum(1 for r in merged if r["nrc_emotion"] is None)
    both = [r for r in merged if r["nrc_emotion"] is not None]
    agree = [r for r in both if r["agree"]]
    disagree = [r for r in both if not r["agree"]]
    agree_rate_overall = len(agree) / n
    agree_rate_eval = len(agree) / len(both) if both else None

    # NRC assignment confidence: how often was the top score a genuine unique
    # maximum vs. resolved by tie-break (score ties are common on this corpus)?
    nrc_top = {r["index"]: r["nrc_scores"] for r in merged}
    strict_max = 0
    nrc_tie_resolved = 0
    tie_involving_anticipation = 0
    for recon in nrc_top.values():
        if not recon:
            continue
        vals = [v["score"] for v in recon.values()]
        top = max(vals)
        if top == 0:
            continue
        winners = [e for e, v in recon.items() if v["score"] == top]
        if len(winners) == 1:
            strict_max += 1
        else:
            nrc_tie_resolved += 1
            if "anticipation" in winners:
                tie_involving_anticipation += 1

    # per-LLM-emotion agreement
    per_llm = {}
    for emo in sorted({r["llm_emotion"] for r in merged}):
        group = [r for r in both if r["llm_emotion"] == emo]
        gr_ok = sum(1 for r in group if r["agree"])
        per_llm[emo] = {"both": len(group), "agree": gr_ok,
                        "rate": round(gr_ok / len(group), 4) if group else None}

    # disagreement pairs: llm -> nrc
    pair = Counter((r["llm_emotion"], r["nrc_emotion"]) for r in disagree)
    pair_top = [{"llm": l, "nrc": x, "count": c} for (l, x), c in pair.most_common()]

    disag_examples = [
        {"index": r["index"], "title": r["title"], "text": r["text"][:140],
         "llm_emotion": r["llm_emotion"], "nrc_emotion": r["nrc_emotion"],
         "nrc_top_words": sorted({w for ws in r["nrc_scores"].values() for w in ws["words"]})[:15]}
        for r in disagree
    ]

    results = {
        "model": "DeepSeek-V4-Flash-0731",
        "lexicon": "NRC-Emotion-Lexicon-Wordlevel-v0.92",
        "emotions_considered": sorted({r["llm_emotion"] for r in merged}),
        "n_reviews": n,
        "llm_emotion_distribution": dict(Counter(r["llm_emotion"] for r in merged)),
        "nrc_emotion_distribution": dict(Counter(r["nrc_emotion"] for r in merged)),
        "nrc_no_match": nrc_none,
        "nrc_strict_max": strict_max,
        "nrc_tie_resolved": nrc_tie_resolved,
        "nrc_ties_involving_anticipation": tie_involving_anticipation,
        "both_predicted": len(both),
        "agree_count": len(agree),
        "disagree_count": len(disagree),
        "agreement_rate_overall": round(agree_rate_overall, 4),
        "agreement_rate_on_evaluated": round(agree_rate_eval, 4) if agree_rate_eval is not None else None,
        "per_llm_emotion_agreement": per_llm,
        "disagreement_pairs": pair_top,
        "disagreement_examples": disag_examples,
    }

    os.makedirs(os.path.dirname(R_JSON), exist_ok=True)
    with open(R_JSON, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # ---- report ----
    L = []
    L.append("MBAX 6418 Assignment 1 - Step 5: Primary Emotion Detection")
    L.append("=" * 64)
    L.append(f"Method 1 (LLM):  {results['model']}  -- extended structured prompt")
    L.append(f"Method 2 (NRC):  {results['lexicon']} word-level association scores")
    L.append(f"Reviews: {n}   |   Emotions: anger, anticipation, disgust, fear, joy, sadness, surprise, trust")
    L.append("")
    L.append("Emotion distributions")
    L.append("  LLM  : " + ", ".join(f"{k}={v}" for k, v in results['llm_emotion_distribution'].items()))
    L.append("  NRC  : " + ", ".join(f"{k}={v}" for k, v in sorted(results['nrc_emotion_distribution'].items(), key=lambda x: -(x[1] or 0))))
    L.append(f"  NRC reviews with no emotion-word match: {results['nrc_no_match']}")
    L.append(f"  NRC top-score was a clean unique max: {results['nrc_strict_max']} of "
             f"{results['both_predicted']} (ties resolved by documented tie-break: "
             f"{results['nrc_tie_resolved']}, of which {results['nrc_ties_involving_anticipation']} "
             f"included anticipation).")
    L.append("")
    L.append("Agreement between methods")
    L.append(f"  Agree: {results['agree_count']}/{results['both_predicted']} "
             f"({results['agreement_rate_on_evaluated']*100:.1f}% of reviews with an NRC emotion; "
             f"{results['agreement_rate_overall']*100:.1f}% of all 100)")
    L.append("  Disagree: " + str(results['disagree_count']))
    L.append("")
    L.append("Agreement by LLM emotion")
    for e, v in results['per_llm_emotion_agreement'].items():
        rate = f"{v['rate']*100:.0f}%" if v['rate'] is not None else "n/a"
        L.append(f"  {e:<12} agree {v['agree']}/{v['both']}  ({rate})")
    L.append("")
    L.append("Where they tend to differ (LLM -> NRC pairs)")
    if pair_top:
        for p in results['disagreement_pairs']:
            L.append(f"  {p['llm']} vs {p['nrc']}: {p['count']} review(s)")
    else:
        L.append("  (none)")
    L.append("")
    L.append("Example disagreements")
    for r in results['disagreement_examples'][:12]:
        w = ", ".join(r['nrc_top_words'][:10])
        L.append(f"  #{r['index']}: LLM={r['llm_emotion']:9} NRC={r['nrc_emotion']:9} :: \"{r['title']}\"")
        L.append(f"         NRC words: {w}")
    with open(R_TXT, "w") as f:
        f.write("\n".join(L) + "\n")

    print("\n".join(L))


if __name__ == "__main__":
    main()
