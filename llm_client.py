#!/usr/bin/env python3
"""Re-export of the shared LLM client in code/ (kept for backwards
compatibility with legacy root-level scripts). No credentials live here."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "code"))

from llm_client import llm_call, API_URL, API_KEY, MODEL  # noqa: E402,F401
