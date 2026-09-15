#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 5, Method 2.

NRC word-emotion association scoring. Scores the tokens of each review against
the NRC Emotion Lexicon v0.92, sums the association counts for each of the 8
Plutchik emotions, and selects the highest-scoring emotion (Method 2).

Data source: public NRC-Emotion-Lexicon-Wordlevel-v0.92.txt (Mohammad & Turney).
"""
import gzip
import json
import os
import re

from sentiment_prompt import EMOTIONS  # the 8 allowed emotions

HERE = os.path.dirname(os.path.abspath(__file__))
LEXICON = os.path.join(HERE, "data", "NRC_emotion_lexicon.txt")
DATA = os.path.join(HERE, "data", "Gift_Cards.jsonl.gz")
OUT = os.path.join(HERE, "data", "nrc_emotions.jsonl")
N = 100

TOKEN_RE = re.compile(r"[a-z0-9']+")

# word -> set(emotions it is associated with), only the 8 Plutchik emotions
# (the lexicon's 2 polarity categories negative/positive are excluded).
WORD_EMOTIONS = {}


def load_lexicon(path=LEXICON):
    if WORD_EMOTIONS:
        return WORD_EMOTIONS
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip("\r\n").strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            word, category, flag = parts[0], parts[1], parts[2]
            # keep only the 8 emotions, drop positive/negative polarity rows
            if category in EMOTIONS and flag == "1":
                WORD_EMOTIONS.setdefault(word, set()).add(category)
    return WORD_EMOTIONS


def tokens(text):
    return TOKEN_RE.findall((text or "").lower())


def score_text(text, lexicon=None):
    """Return (scores, top_emotion, matched_terms).

    scores: dict emotion -> count of lexicon-word occurrences flagged for it
            (faithful "sum the association scores" method).
    top_emotion: highest-scoring emotion, or None if nothing matched.
    matched_terms: dict emotion -> list of matched words (for the report).

    Tie-breaking (documented, deterministic):
      1. highest sum score
      2. most DISTINCT contributing words (more evidence beats repetition)
      3. fixed emotion order [[EMOTION_ORDER]]
    """
    lexicon = lexicon or load_lexicon()
    scores = {e: 0 for e in EMOTIONS}
    matched = {e: [] for e in EMOTIONS}
    for tok in tokens(text):
        emos = lexicon.get(tok)
        if not emos:
            continue
        for e in emos:
            scores[e] += 1
            matched[e].append(tok)
    order = ["anger", "anticipation", "disgust", "fear", "joy",
             "sadness", "surprise", "trust"]
    if not any(scores.values()):
        return scores, None, matched
    distinct = {e: len(set(matched[e])) for e in order}
    # sort descending by (score, distinct-count, earlier-in-order)
    ranked = sorted(order, key=lambda e: (scores[e], distinct[e], -order.index(e)),
                    reverse=True)
    top = ranked[0]
    return scores, top, matched


def nrc_emotion_for(title, text, lexicon=None):
    _, top, _ = score_text(f"{title} {text}", lexicon)
    return top


def main():
    lexicon = load_lexicon()
    print(f"NRC lexicon loaded: {len(lexicon)} words")

    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        reviews = []
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
            if len(reviews) >= N:
                break
    assert len(reviews) == N

    records = []
    for i, r in enumerate(reviews):
        scores, top, matched = score_text(f"{r.get('title','')} {r.get('text','')}", lexicon)
        records.append({
            "index": i,
            "nrc_emotion": top,
            "nrc_scores": scores,
            "top_terms": {e: matched[e][:12] for e in EMOTIONS if matched[e]},
        })

    with open(OUT, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # quick summary
    from collections import Counter
    dist = Counter(r["nrc_emotion"] for r in records)
    nohit = sum(1 for r in records if r["nrc_emotion"] is None)
    print("NRC emotion assignment (overall):")
    for e, c in dist.most_common():
        print(f"  {e}: {c}")
    print(f"  (no lexicon words matched): {nohit}")
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    main()
