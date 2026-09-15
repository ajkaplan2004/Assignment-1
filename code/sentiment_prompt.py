#!/usr/bin/env python3
"""
sentiment_prompt.py
===================
MBAX 6418 — Assignment 1, Step 2: Reusable structured LLM prompt for binary
sentiment classification (POSITIVE / NEGATIVE) of Amazon reviews.

The model is shown ONLY the review TITLE and BODY TEXT — never the star rating.
The rating is used later, offline, only to evaluate predictions.

Output is a single strict JSON object that Python can parse reliably.
"""

import json
import re

VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE"}
# Fixed set of primary emotions (Plutchik wheel) the model may choose from.
VALID_EMOTIONS = {"anger", "anticipation", "disgust", "fear",
                  "joy", "sadness", "surprise", "trust"}

# ---------------------------------------------------------------------------
# The system prompt (also saved standalone in prompts/sentiment_prompt.md as
# a deliverable).
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a sentiment and emotion classifier for Amazon product reviews.

Classify each review's SENTIMENT as POSITIVE or NEGATIVE AND its PRIMARY
EMOTION. You are given ONLY the review title and the review body text. You are
never told the star rating and you must not assume or infer one.

Output a single JSON object with exactly these keys:
  "sentiment":        "POSITIVE" or "NEGATIVE" only (all caps, no other values)
  "primary_emotion":  exactly ONE emotion from this fixed list, all lowercase:
                      anger | anticipation | disgust | fear | joy | sadness | surprise | trust
  "confidence":       a number between 0.0 and 1.0 reflecting how sure you are
                      of the sentiment
  "reason":           one short sentence explaining your decision

Rules:
- Output ONLY the JSON object. No markdown code fences, no commentary, no text
  before or after it.
- "sentiment" must be exactly POSITIVE or NEGATIVE. For a neutral or ambiguous
  review, still pick the closer side and reflect uncertainty with a lower
  confidence (e.g. 0.5-0.6) rather than pretending certainty.
- "primary_emotion" must be exactly one of the eight allowed values -- do not
  invent others (no "neutral", no "happy", no "angry"). Pick the SINGLE most
  dominant emotion the wording conveys, even when subtle.
  The emotion and sentiment are independent: a NEGATIVE review can be anger,
  sadness, fear, disgust, or surprise; a POSITIVE one can be joy, trust,
  anticipation, or surprise. Judge the dominant feeling from the wording.
- Never mention star ratings in the reason.

Handling edge cases:
- Conflicting title and text: the body text carries more weight than the title.
  A positive title ("Great gift") paired with a negative body is NEGATIVE; say
  so in the reason.
- Extremely short reviews: judge from the core wording. "Good product" ->
  POSITIVE; "Card did not work" -> NEGATIVE. A one-off that is genuinely
  meaningless on its own is a best-guess at low confidence, with a best-guess
  emotion.
- Sarcasm: sarcasm usually signals NEGATIVE. "Great -- the card was empty when
  it arrived. Thanks a lot." is NEGATIVE.
- Unclear wording: do not invent meaning; read literally and keep confidence
  low when the signal is confusing.

Judge each review on its own language."""
# ---------------------------------------------------------------------------


def build_prompt(title, text):
    """Return (system_prompt, user_prompt) for one review.

    Only title + text are included -- never the rating or any identifier.
    """
    title = (title or "").strip()
    text = (text or "").strip()
    user = (
        "Classify this Amazon review.\n\n"
        f"Title: {title if title else '(no title)'}\n"
        f"Review: {text if text else '(no text)'}\n\n"
        "Reply with the JSON classification only."
    )
    return SYSTEM_PROMPT, user


def parse_response(raw):
    """Parse an LLM response into {sentiment, primary_emotion, confidence, reason}.

    Tolerant of model chatter: strips markdown fences and extracts the first
    JSON object so a chatty model still yields parseable output.
    Raises ValueError on an invalid sentiment, emotion, or confidence.
    """
    raw = (raw or "").strip()

    # Strip ```json ... ``` fences if present.
    code_block = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if code_block:
        raw = code_block.group(1).strip()

    # Fall back to the first {...} object in the text.
    obj_start = raw.find("{")
    obj_end = raw.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        raw = raw[obj_start : obj_end + 1]

    data = json.loads(raw)  # raises if not valid JSON

    sentiment = str(data.get("sentiment", "")).strip().upper()
    if sentiment not in VALID_SENTIMENTS:
        raise ValueError(f"Invalid sentiment value: {sentiment!r}")

    emotion = str(data.get("primary_emotion", data.get("emotion", ""))).strip().lower()
    if emotion not in VALID_EMOTIONS:
        raise ValueError(
            f"Invalid primary_emotion value: {emotion!r}. "
            f"Allowed: {', '.join(sorted(VALID_EMOTIONS))}"
        )

    try:
        confidence = float(data["confidence"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"Invalid or missing confidence: {data.get('confidence')!r}")

    reason = str(data.get("reason", "")).strip()

    return {
        "sentiment": sentiment,
        "primary_emotion": emotion,
        "confidence": confidence,
        "reason": reason,
    }
