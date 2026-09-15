#!/usr/bin/env python3
"""
emotions_nrc.py
===============
MBAX 6418 — Assignment 1, Step 5 (word-list method).
A second, LLM-free emotion-classification method using the NRC Emotion
Lexicon (Mohammad & Turney, word-level v0.92).

For each of the first 100 reviews:
  1. normalize the review text (strip HTML entities/tags, lowercase)
  2. tokenize
  3. match each token against the NRC emotion lexicon
  4. sum the association counts for each of the 8 emotions
  5. pick the highest-scoring emotion as the NRC primary emotion
  6. handle ties and no-match reviews deterministically

Then compares the NRC primary emotion against the LLM primary emotion
(loaded from data/emotions_llm.jsonl), reports the agreement rate, shows
disagreement examples, and saves the updated merged results.

Outputs:
  data/emotion_results.jsonl           per-review: llm_emotion, nrc_emotion,
                                       nrc_scores, agree
  results/step5_emotion_comparison.json  agreement summary + disagreements
"""
import gzip
import html
import json
import re
from collections import Counter
from pathlib import Path

from sentiment_prompt import VALID_EMOTIONS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEXICON = ROOT / "data" / "NRC_emotion_lexicon.txt"
DATA = ROOT / "data" / "Gift_Cards.jsonl.gz"
LLM_EMOTIONS_IN = ROOT / "data" / "emotions_llm.jsonl"      # LLM primary emotion per index
MERGE_OUT = ROOT / "data" / "emotion_results.jsonl"         # updated per-review results
SUMMARY_OUT = ROOT / "results" / "step5_emotion_comparison.json"

N = 100

# Canonical order used to break ties deterministically (earlier position wins).
EMOTION_ORDER = ["anger", "anticipation", "disgust", "fear",
                 "joy", "sadness", "surprise", "trust"]

# --- Normalization ---------------------------------------------------------
_ENTITY_RE = re.compile(r"&#?\w+;")    # HTML entities: &#34; &amp; &quot; ...
_TAG_RE = re.compile(r"<[^>]+>")       # <br /> <p> ...
_TOKEN_RE = re.compile(r"[a-z0-9']+")


def normalize_tokens(text):
    """Return a clean list of lowercase tokens from raw review text."""
    if not text:
        return []
    t = html.unescape(text)            # decode numeric + named entities safely
    t = _TAG_RE.sub(" ", t)            # drop HTML tags
    return _TOKEN_RE.findall(t.lower())


# --- Lexicon ---------------------------------------------------------------
def load_lexicon(path=LEXICON):
    """word -> set of the 8 emotions it's associated with (NRC flag == 1)."""
    word_emotions = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            word, category, flag = parts[0], parts[1], parts[2]
            if category in VALID_EMOTIONS and flag == "1":
                word_emotions.setdefault(word, set()).add(category)
    return word_emotions


# --- Scoring ---------------------------------------------------------------
def score_text(text, lexicon):
    """Return (scores, top_emotion, matched, was_tie).

    scores:  dict emotion -> sum of lexicon-word occurrences flagged for it
    top_emotion: highest-scoring emotion (winner), or None if no words matched
    matched: dict emotion -> list of matched tokens
    was_tie: True if >=2 emotions tied for the top score.
    """
    scores = {e: 0 for e in EMOTION_ORDER}
    matched = {e: [] for e in EMOTION_ORDER}
    for tok in normalize_tokens(text):
        emos = lexicon.get(tok)
        if emos:
            for e in emos:
                scores[e] += 1
                matched[e].append(tok)

    if not any(scores.values()):
        return scores, None, matched, False

    max_score = max(scores.values())
    ties = [e for e in EMOTION_ORDER if scores[e] == max_score]
    was_tie = len(ties) > 1

    if was_tie:
        # Deterministic tie-break: sum -> distinct contributing words -> order.
        def key(e):
            return (scores[e], len(set(matched[e])), -EMOTION_ORDER.index(e))
        top = max(EMOTION_ORDER, key=key)
    else:
        top = ties[0]

    return scores, top, matched, was_tie


# --- I/O helpers -----------------------------------------------------------
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


def load_llm_emotions(path):
    """index -> llm primary emotion"""
    mapping = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                mapping[int(rec["index"])] = rec.get("primary_emotion")
    return mapping


def main():
    lexicon = load_lexicon()
    print(f"NRC lexicon loaded: {len(lexicon)} words (8 emotions)")

    reviews = load_first_n(DATA, N)
    assert len(reviews) == N, f"Expected {N}, got {len(reviews)}"
    llm = load_llm_emotions(LLM_EMOTIONS_IN)
    print(f"Reviews: {N}   |   LLM emotions loaded: {len(llm)}")

    # --- Compute NRC emotion for each review ---
    records = []
    n_nomatch = 0
    n_ties = 0
    for i, r in enumerate(reviews):
        scores, top, matched, was_tie = score_text(f"{r.get('title','')} {r.get('text','')}", lexicon)
        if top is None:
            n_nomatch += 1
        if was_tie:
            n_ties += 1
        records.append({
            "index": i,
            "rating": r.get("rating"),
            "true_class": "POSITIVE" if r.get("rating") is not None and r["rating"] >= 4 else "NEGATIVE",
            "title": r.get("title", ""),
            "text": r.get("text", ""),
            "llm_emotion": llm.get(i),
            "nrc_emotion": top,                       # None when no lexicon words
            "nrc_scores": scores,
            "nrc_tie": was_tie,
            "nrc_top_terms": {e: matched[e][:10] for e in EMOTION_ORDER if matched[e]},
        })
        records[i]["agree"] = bool(records[i]["llm_emotion"] and records[i]["nrc_emotion"]
                                   and records[i]["llm_emotion"] == records[i]["nrc_emotion"])

    # --- Save merged per-review results ---
    MERGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MERGE_OUT, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # --- Comparison: LLM primary emotion vs NRC primary emotion ---
    both = [r for r in records if r["llm_emotion"] and r["nrc_emotion"]]
    agree = sum(1 for r in both if r["agree"])
    llm_llm_only = [r for r in records if r["llm_emotion"] and not r["nrc_emotion"]]
    nrc_only = [r for r in records if r["nrc_emotion"] and not r["llm_emotion"]]
    neither = [r for r in records if not r["llm_emotion"] and not r["nrc_emotion"]]

    disagreements = [
        {"index": r["index"], "title": r["title"], "text": r["text"][:160],
         "llm_emotion": r["llm_emotion"], "nrc_emotion": r["nrc_emotion"],
         "nrc_scores": r["nrc_scores"]}
        for r in both if not r["agree"]
    ]

    def dist(key):
        return dict(Counter(str(r[key]) for r in records).most_common())

    llm_dist = Counter(r["llm_emotion"] for r in records if r["llm_emotion"])
    nrc_dist = Counter(r["nrc_emotion"] for r in records if r["nrc_emotion"])

    summary = {
        "method": "NRC-Emotion-Lexicon-Wordlevel-v0.92 (Mohammad & Turney), LLM-free",
        "model_llm_emotions": "DeepSeek-V4-Flash-0731 (temperature 0.0)",
        "emotions": EMOTION_ORDER,
        "tie_break_rule": "sum score -> distinct contributing words -> emotion order",
        "no_match_rule": "no lexicon word matched -> nrc_emotion null, excluded from agreement",
        "n_reviews": N,
        "nrc_no_match": n_nomatch,
        "nrc_ties": n_ties,
        "llm_emotion_distribution": dict(llm_dist.most_common()),
        "nrc_emotion_distribution": dict(nrc_dist.most_common()),
        "both_predicted": len(both),
        "agree_count": agree,
        "disagree_count": len(disagreements),
        "agreement_rate_overall": round(agree / N, 4),
        "agreement_rate_on_evaluated": round(agree / len(both), 4) if both else None,
        "disagreements": disagreements[:25],
        "disagreement_examples_shown": len(disagreements),
    }
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # --- Console summary ---
    print("\n" + "=" * 64)
    print("STEP 5 (word-list): LLM primary emotion  vs  NRC primary emotion")
    print("=" * 64)
    print(f"NRC no-match reviews        : {n_nomatch}")
    print(f"NRC tie (resolved)          : {n_ties}")
    print(f"Reviews with BOTH emotions  : {len(both)}")
    print(f"Agree                        : {agree}")
    print(f"Disagree                     : {len(disagreements)}")
    print(f"Agreement rate (of 100)      : {agree/N*100:.1f}%")
    print(f"Agreement rate (both pred.)  : {agree/len(both)*100:.1f}%" if both else "")
    print(f"\nLLM emotion distribution    : {dict(llm_dist.most_common())}")
    print(f"NRC emotion distribution    : {dict(nrc_dist.most_common())}")

    print(f"\nDisagreement examples ({len(disagreements)} shown as needed):")
    for d in disagreements[:12]:
        print(f"  #{d['index']:<3} LLM={d['llm_emotion']:<12} NRC={d['nrc_emotion']:<12} "
              f"\"{d['title'][:36]}\"")
        print(f"       nrc_scores={ {k:v for k,v in d['nrc_scores'].items() if v} }")

    print(f"\nSaved -> {MERGE_OUT}")
    print(f"Saved -> {SUMMARY_OUT}")


if __name__ == "__main__":
    main()
