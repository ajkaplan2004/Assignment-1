#!/usr/bin/env python3
"""
MBAX 6418 Assignment 1 - Step 1
Reusable structured prompt for binary POSITIVE/NEGATIVE sentiment classification
of Amazon reviews. The model sees ONLY the review title and body text -- never the
star rating. Output is a single strict JSON object that Python can parse reliably.
"""
import json
import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE"}
EMOTIONS = {"anger", "anticipation", "disgust", "fear", "joy",
            "sadness", "surprise", "trust"}

SYSTEM_PROMPT = """You are a sentiment classifier for Amazon product reviews.

Classify each review as POSITIVE or NEGATIVE AND identify its PRIMARY EMOTION.
You will be given ONLY the review title and the review body text. You are never
told the star rating, and you must not assume one.

Output your answer as a single JSON object with exactly these four keys:
  "sentiment":      the string "POSITIVE" or "NEGATIVE" (no other values, all caps)
  "confidence":     a number between 0.0 and 1.0 reflecting how sure you are of the sentiment
  "primary_emotion": exactly ONE emotion from this fixed list, all lowercase:
                     anger | anticipation | disgust | fear | joy | sadness | surprise | trust
  "reason":         one short sentence explaining your decision

Rules:
- Output ONLY the JSON object. Do not wrap it in markdown code fences, add no
  commentary, no bullets, and no text before or after the JSON.
- "sentiment" must be exactly POSITIVE or NEGATIVE. If a review is neutral or
  ambiguous, still choose the closer side and reflect your uncertainty with a
  lower confidence value (e.g. 0.5-0.6) rather than inventing certainty.
- "primary_emotion": pick the SINGLE most dominant emotion the review conveys.
  It must be one of the eight allowed values -- do not invent others (no
  "neutral", no "happy", no "angry"). Choose the best fit even when subtle.
  The emotion and the sentiment need not be a fixed pairing (a negative review
  can be anger, sadness, fear, disgust, or surprise; a positive one can be joy,
  trust, anticipation, or surprise) -- judge the dominant feeling from the wording.

Handling edge cases:
- Conflicting title and text: the body text carries more weight than the title.
  A positive-sounding title ("Great gift") paired with a negative body is NEGATIVE.
  Say so in the reason.
- Extremely short reviews: judge from the core wording. "Good product" -> POSITIVE;
  "Card did not work" -> NEGATIVE. If a one-off is genuinely meaningless on its
  own (e.g. title "Gift card", text "Gift card"), give your best guess at low
  confidence and a best-guess emotion.
- Angry or sarcastic reviews: sarcasm usually signals NEGATIVE. "Great -- my card
  was empty when it arrived. Thanks a lot." is NEGATIVE with a dominant emotion
  like anger or surprise. Strong punctuation and complaint framing support NEGATIVE.
- Unclear wording: do not hallucinate meaning. Read the words literally and pick
  the clearest available signal; keep confidence low if the wording is confusing.

Judge each review on its own language. Do not mention star ratings in the reason."""


def build_prompt(title, text):
    """Return (system_prompt, user_prompt) for a single review.

    Only title and text are included -- no rating, no identifiers.
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
    """Parse an LLM response into {sentiment, confidence, reason, primary_emotion}.

    Tolerant: strips markdown fences and extracts the first JSON object,
    so a chatty model still yields parseable output.
    """
    raw = (raw or "").strip()
    # Strip ```json ... ``` fences if present
    code_block = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if code_block:
        raw = code_block.group(1).strip()
    # Fall back to the first {...} object in the text
    obj_start = raw.find("{")
    obj_end = raw.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        raw = raw[obj_start : obj_end + 1]

    data = json.loads(raw)  # raises if not valid JSON

    sentiment = str(data.get("sentiment", "")).strip().upper()
    confidence = data.get("confidence")
    reason = str(data.get("reason", "")).strip()

    if sentiment not in VALID_SENTIMENTS:
        raise ValueError(f"Invalid sentiment value: {sentiment!r}")

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid confidence value: {confidence!r}")

    # primary_emotion (optional for backward compatibility, but validated if present)
    emotion_raw = data.get("primary_emotion", data.get("emotion"))
    primary_emotion = None
    if emotion_raw is not None:
        primary_emotion = str(emotion_raw).strip().lower()
        if primary_emotion not in EMOTIONS:
            raise ValueError(f"Invalid primary_emotion value: {primary_emotion!r}")

    return {"sentiment": sentiment, "confidence": confidence,
            "reason": reason, "primary_emotion": primary_emotion}
