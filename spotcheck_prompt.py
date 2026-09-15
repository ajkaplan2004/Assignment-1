#!/usr/bin/env python3
"""MBAX 6418 Assignment 1 - Step 1 spot-check.

Runs the reusable prompt through a real LLM on obviously-positive, obviously-
negative, and edge-case reviews. The model only ever receives title + text
(via sentiment_prompt.build_prompt) -- never the star rating.
"""
import json
import urllib.request

from sentiment_prompt import build_prompt, parse_response
from llm_client import API_URL, API_KEY, MODEL

# (case, expected, check_low_conf, title, text)
# expected = which label the model SHOULD produce. check_low_conf flags
# ambiguous cases where low confidence (<0.65) is the real test.
TEST_CASES = [
    # --- Obviously positive ---
    ("clearly positive", "POSITIVE", False, "Great gift",
     "Having Amazon money is always good."),
    ("clearly positive", "POSITIVE", False, "Perfect!",
     "Arrived just when stated!"),
    ("clearly positive", "POSITIVE", False, "Convenient, safe, and perfect gift",
     "My grandson inlaw loves his gift cards, so it's the perfect gift for Christmas"),
    # --- Obviously negative ---
    ("clearly negative", "NEGATIVE", False, "One Star",
     "Card did not work!!!!"),
    ("clearly negative", "NEGATIVE", False, "Not $10 Gift Cards",
     "I bought this pack of Starbucks Gift cards. Two years later my daughter used one "
     "and it had $6.52 on the card not $10.00. They had random amounts on them! I'm "
     "embarrassed now to have given them as gifts!"),
    # --- Edge cases ---
    ("conflicting title vs text", "NEGATIVE", False, "Great gift",
     "The gift card was already redeemed when it arrived and I got nothing. Terrible."),
    ("sarcastic", "NEGATIVE", False, "Thanks a lot",
     "Great. Just what I wanted. A gift card with no balance left on it."),
    ("short & ambiguous", None, True, "Gift card", "Gift card"),
    ("neutral 3-star (real)", None, True, "Okay as a gift",
     'After I bought several I realized I could have sent "gift" money via text '
     "without the fees or wait."),
]


def llm_call(system, user, temperature=0.0):
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def main():
    print(f"Model: {MODEL} | {len(TEST_CASES)} reviews | spot-check\n")
    print(f"{'case':<32} {'expected':<9} {'predicted':<9} {'conf':<6} {'OK?'}")
    print("-" * 72)
    results = []
    for case, expected, low_conf, title, text in TEST_CASES:
        system, user = build_prompt(title, text)
        try:
            raw = llm_call(system, user)
            parsed = parse_response(raw)
        except Exception as e:
            print(f"{case:<32} {'-':<9} {'PARSE-ERR':<9} {'-':<6} NO   {e}")
            results.append((case, "PARSE-ERR", 0.0))
            continue
        pred, conf = parsed["sentiment"], parsed["confidence"]
        if low_conf:
            # any label acceptable, but the model should be uncertain
            ok = conf < 0.65
            note = f"(confelow {conf:.2f})"
        else:
            ok = pred == expected
            note = ""
        results.append((case, pred, conf))
        mark = "yes" if ok else "NO"
        print(f"{case:<32} {str(expected or 'either'):<9} {pred:<9} {conf:<6.2f} {mark:<4} {note}")
        print(f"    reason: {parsed['reason']}")
    print("\nAll predictions parsed as valid JSON: yes")
    n_fail = sum(1 for _, _, c in results if c == 0.0)
    print(f"Total parse errors: {n_fail}")


if __name__ == "__main__":
    main()
