#!/usr/bin/env python3
"""
llm_client.py
=============
MBAX 6418 — Assignment 1.
Thin OpenAI-compatible chat-completions client for the course LLM endpoint.
Deterministic by default (temperature=0.0), with retries.

CREDENTIALS ARE NEVER HARDCODED. They are read, in order, from:
  1) environment variables: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
  2) a gitignored local_config.yaml in the repo root:
       base_url: "http://<host>:<port>/v1"
       api_key:   "..."
       model:     "..."
If neither is present, the client refuses to start (no secrets in the repo).
"""
import json
import os
import re
import time
import urllib.request
from pathlib import Path


def _git_root():
    return Path(__file__).resolve().parent.parent


def _from_env():
    return {
        "base_url": os.environ.get("LLM_BASE_URL"),
        "api_key": os.environ.get("LLM_API_KEY"),
        "model": os.environ.get("LLM_MODEL"),
    }


def _from_local_config():
    cfg_path = _git_root() / "local_config.yaml"
    if not cfg_path.exists():
        return {}
    text = cfg_path.read_text(encoding="utf-8")

    def grab(key):
        m = re.search(rf"^\s*{key}\s*:\s*[\"']?([^\"'\n#]+)[\"']?", text, re.M)
        return m.group(1).strip() if m else None

    return {"base_url": grab("base_url"),
            "api_key": grab("api_key"),
            "model": grab("model")}


def _load_config():
    cfg = {}
    for source in (_from_env(), _from_local_config()):
        for k, v in source.items():
            if v:
                cfg[k] = v
    if not (cfg.get("base_url") and cfg.get("api_key") and cfg.get("model")):
        raise RuntimeError(
            "LLM credentials not configured. Set LLM_BASE_URL / LLM_API_KEY / "
            "LLM_MODEL env vars, or create a gitignored local_config.yaml in the "
            "repo root (base_url, api_key, model). No secrets are stored in code."
        )
    return cfg


_CFG = _load_config()
API_URL = _CFG["base_url"].rstrip("/") + "/chat/completions"
API_KEY = _CFG["api_key"]
MODEL = _CFG["model"]


def llm_call(system, user, temperature=0.0, max_retries=4, timeout=120):
    """Call the chat-completions endpoint. Returns the assistant message text.

    Retries transient failures (5xx / network) with exponential backoff.
    """
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    payload = json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(API_URL, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001 - retry on any transient failure
            last_err = e
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_err}")
