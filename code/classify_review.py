#!/usr/bin/env python3
"""
classify_review.py
==================
MBAX 6418 — Assignment 1, Step 2.
The reusable classification function plus a small smoke test on obviously
positive and obviously negative reviews.

Usage:
    python3 classify_review.py            # run the smoke test
    python3 classify_review.py --reviews '[{"title": "...", "text": "..."}]'
"""
import argparse
import json
import sys

from llm_client import llm_call
from sentiment_prompt import build_prompt, parse_response


# ---------------------------------------------------------------------------
# The reusable classification function
# ---------------------------------------------------------------------------
def classify_review(title, text, temperature=0.0):
    """Classify one review -> sentiment + primary emotion, using ONLY title+text.

    Returns: {"label", "primary_emotion", "confidence", "reason", "title", "text"}
    Never sends the star rating to the model.
    """
    system, user = build_prompt(title, text)
    raw = llm_call(system, user, temperature=temperature)
    parsed = parse_response(raw)  # raises on unusable output
    return {
        "title": (title or "").strip(),
        "text": (text or "").strip(),
        "label": parsed["sentiment"],
        "primary_emotion": parsed["primary_emotion"],
        "confidence": parsed["confidence"],
        "reason": parsed["reason"],
        "raw_response": raw,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
# (title, text, expected_sentiment, expected_emotion)
TEST_CASES = [
    # --- Obviously positive ---
    ("Still love it", "Having some Amazon money is always a good thing. Will buy again.",
     "POSITIVE", "joy"),
    ("Perfect gift", "The recipient loved it. Beautiful packaging and it arrived in a day.",
     "POSITIVE", "joy"),
    ("Great value", "Easy to use, instant delivery by email. No issues at all. So happy and satisfied.",
     "POSITIVE", "joy"),
    ("Can always count on it", "Amazon always delivers on time, exactly as promised. I trust them completely.",
     "POSITIVE", "trust"),          # trust, not joy
    ("Love it!", "Works great.", "POSITIVE", "joy"),                 # very short
    # --- Obviously negative ---
    ("Not worth it", "The card only had $6.52 on it instead of the $10 I paid. Total scam.",
     "NEGATIVE", "anger"),
    ("Card did not work", "Scraped off the code and it would not scan at checkout. Wasted my money.",
     "NEGATIVE", "anger"),
    ("So disappointing", "The card never arrived and support ignored me for three weeks. Heartbroken.",
     "NEGATIVE", "sadness"),        # sadness, not anger
    ("Terrible", "Don't buy.", "NEGATIVE", "anger"),                 # very short
    # --- Edge cases called out in the prompt ---
    ("Great gift", "The card arrived with no balance on it. Waste of time and money.",
     "NEGATIVE", "anger"),          # conflicting title/text
    ("Gift card", "Gift card", "POSITIVE", "anticipation"),          # meaningless, low confidence
]


def run_smoke_test(verbose=False):
    print("=" * 82)
    print("Step 5 smoke test: LLM returns sentiment + primary emotion (title + text only)")
    print(f"Model: DeepSeek-V4-Flash-0731 | temperature=0.0")
    print("=" * 82)
    n_ok, n_total = 0, 0
    for idx, (title, text, exp_s, exp_e) in enumerate(TEST_CASES, 1):
        res = classify_review(title, text)
        sent_ok = res["label"] == exp_s
        emo_ok = res["primary_emotion"] == exp_e
        n_total += 1
        n_ok += int(sent_ok and emo_ok)
        flag = "OK  " if (sent_ok and emo_ok) else "FAIL"
        print(f"\n[{idx}] {flag}  sent={res['label']:<8}(exp {exp_s:<8})  "
              f"emotion={res['primary_emotion']:<12}(exp {exp_e})  conf={res['confidence']:.2f}")
        print(f"     title   : {res['title']}")
        print(f"     text    : {res['text'][:80]}{'...' if len(res['text']) > 80 else ''}")
        print(f"     reason  : {res['reason']}")
        if verbose:
            print(f"     raw     : {res['raw_response']}")

    print("\n" + "=" * 82)
    print(f"Result: {n_ok}/{n_total} reviews had BOTH sentiment AND emotion correct")
    return n_ok, n_total


def main():
    ap = argparse.ArgumentParser(description="Reusable sentiment classifier")
    ap.add_argument("--reviews", type=str, default=None,
                    help='JSON list of [{"title":..,"text":..}] to classify')
    ap.add_argument("--verbose", action="store_true", help="print raw LLM responses")
    args = ap.parse_args()

    if args.reviews:
        items = json.loads(args.reviews)
        for it in items:
            r = classify_review(it.get("title", ""), it.get("text", ""))
            print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    # Default: run the smoke test.
    run_smoke_test(verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
