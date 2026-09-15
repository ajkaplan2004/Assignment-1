#!/usr/bin/env python3
"""
prompt_3class.py
================
MBAX 6418 — Assignment 1, Step 6.
Three-class structured prompt: POSITIVE / NEUTRAL / NEGATIVE, plus a primary
emotion. The model sees ONLY the review title and body text -- never the rating.
Output is a single strict JSON object Python can parse reliably.
"""
import json
import re

from sentiment_prompt import VALID_EMOTIONS  # the 8 Plutchik emotions

VALID_SENTIMENTS = {"POSITIVE", "NEUTRAL", "NEGATIVE"}

SYSTEM_PROMPT = """You are a sentiment classifier for Amazon product reviews.

Classify each review as POSITIVE, NEUTRAL, or NEGATIVE AND identify its PRIMARY
EMOTION. You will be given ONLY the review title and the review body text. You
are never told the star rating, and you must not assume or guess one.

Output your answer as a single JSON object with exactly these keys:
  "sentiment":       "POSITIVE", "NEUTRAL", or "NEGATIVE" (no other values, all caps)
  "confidence":      a number between 0.0 and 1.0 reflecting how sure you are of the sentiment
  "primary_emotion": exactly ONE emotion from this fixed list, all lowercase:
                     anger | anticipation | disgust | fear | joy | sadness | surprise | trust
  "reason":          one short sentence explaining your decision

Rules:
- Output ONLY the JSON object. No markdown code fences, no commentary, no text
  before or after it.
- Choose NEUTRAL when the review expresses no clear positive or negative feeling:
  a factual statement ("It's a gift card"), a balanced or mixed opinion, mild
  ambivalence, or open-ended wording with no dominant valence. Do not default a
  bland/unclear review to positive just because it is not obviously angry.
- POSITIVE: clear praise, satisfaction, joy, approval. NEGATIVE: clear
  complaint, disappointment, anger, reduction in enjoyment.
- "primary_emotion": pick the single most dominant emotion conveyed, from the
  eight allowed values. It may be low-arousal ones (anticipation, trust) for a
  NEUTRAL review, or a weaker signal. Do not invent other emotion labels.

Handling edge cases:
- Conflicting title and text: the body text carries more weight than the title.
- Extremely short reviews: "Good product" -> POSITIVE; "Card did not work" -> NEGATIVE;
  "Gift card" alone -> NEUTRAL (no valenced signal).
- Angry or sarcastic: sarcasm usually signals NEGATIVE ("Great -- the card was empty").
- Unclear wording: do not hallucinate sentiment. If the valence is genuinely
  ambiguous, choose NEUTRAL and keep confidence low.

Judge each review on its own language. Do not mention star ratings in the reason."""


def build_prompt(title, text):
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
    """Parse into {sentiment, confidence, primary_emotion, reason}.

    Tolerant of markdown fences and surrounding chatter. Raises ValueError on
    an invalid sentiment or emotion.
    """
    raw = (raw or "").strip()
    code_block = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if code_block:
        raw = code_block.group(1).strip()
    obj_start = raw.find("{")
    obj_end = raw.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        raw = raw[obj_start: obj_end + 1]

    data = json.loads(raw)

    sentiment = str(data.get("sentiment", "")).strip().upper()
    if sentiment not in VALID_SENTIMENTS:
        raise ValueError(f"Invalid sentiment value: {sentiment!r}")

    try:
        confidence = float(data.get("confidence"))
    except (TypeError, ValueError):
        raise ValueError(f"Invalid confidence: {data.get('confidence')!r}")

    emotion_raw = data.get("primary_emotion", data.get("emotion"))
    primary_emotion = None
    if emotion_raw is not None:
        primary_emotion = str(emotion_raw).strip().lower()
        if primary_emotion not in VALID_EMOTIONS:
            raise ValueError(f"Invalid primary_emotion: {primary_emotion!r}")

    return {"sentiment": sentiment, "confidence": confidence,
            "primary_emotion": primary_emotion,
            "reason": str(data.get("reason", "")).strip()}
