"""
Configuration settings for the AeroAI Concierge.
Adjust thresholds, paths, and API keys here.
"""

import os

# ──────────────────────────────────────────────
# File Paths
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QA_DATA_FILE = os.path.join(BASE_DIR, "qa_data.json")

# ──────────────────────────────────────────────
# Matching Settings
# ──────────────────────────────────────────────
FUZZY_MATCH_THRESHOLD = 55
KEYWORD_MATCH_THRESHOLD = 0.3
FUZZY_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5

# ──────────────────────────────────────────────
# AI Model Settings
# ──────────────────────────────────────────────
# The chatbot uses GPT if an OpenAI key is set, otherwise Gemini
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = "gpt-6-luna"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-3.5-flash-lite"
# How many earlier messages are sent along, so follow-up questions make sense
HISTORY_LIMIT = 6

# ──────────────────────────────────────────────
# UI Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE_TITLE = "AeroAI Concierge"
PAGE_ICON = "💬"
MAX_CHAT_HISTORY = 50
TYPING_DELAY = 0.02
