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
def _secret(name: str) -> str:
    """Reads a key from the environment, or from Streamlit's Secrets (used when hosted)."""
    value = os.environ.get(name, "")
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(name, "")
        except Exception:
            value = ""
    return str(value).strip().strip('"\'')


OPENAI_API_KEY = _secret("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-6-luna"
GEMINI_API_KEY = _secret("GEMINI_API_KEY")
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

# ──────────────────────────────────────────────
# Prototype offers (demo only)
# ──────────────────────────────────────────────
# Place name -> sample offer. The program adds these to answers with a disclaimer; the AI never writes offers.
PROTOTYPE_OFFERS = {
    "Cafe Delhi Heights": "20% off",
}
