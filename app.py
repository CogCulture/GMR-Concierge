"""
AeroAI Concierge — GMR Aerocity New Delhi
Warm ivory & deep navy concierge UI with FAQ home screen and interactive chat view.
"""

import base64
import os
import html
import re
import time
import streamlit as st
from qa_engine import (
    find_best_answer,
    get_suggested_questions,
    get_bot_config,
    DEFAULT_FOLLOWUPS,
)
from config import PAGE_TITLE

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Page Config (must be first Streamlit call)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Session State Init
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "messages" not in st.session_state:
    st.session_state.messages = []
if "bot_config" not in st.session_state:
    st.session_state.bot_config = get_bot_config()
if "view" not in st.session_state:
    st.session_state.view = "chat" if st.session_state.messages else "home"
if "show_search" not in st.session_state:
    st.session_state.show_search = False
if "faq_filter" not in st.session_state:
    st.session_state.faq_filter = ""

bot_config = st.session_state.bot_config
BOT_SUBTITLE = bot_config.get(
    "subtitle", "Your smart assistant for everything at Aerocity"
)
WELCOME_MSG = bot_config.get(
    "welcome_message",
    "Hello! Welcome to GMR Aerocity. How can I help you today?",
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SVG & Data-URI Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _svg_uri(svg: str) -> str:
    encoded = base64.b64encode(svg.strip().encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


# Curved Navy Header Backdrop SVG with Gold Accent Swooshes
HEADER_BG_SVG = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104" preserveAspectRatio="none">
  <defs>
    <linearGradient id="navyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#071936"/>
      <stop offset="55%" stop-color="#0D274D"/>
      <stop offset="100%" stop-color="#173A6B"/>
    </linearGradient>
    <radialGradient id="glow" cx="72%" cy="20%" r="55%">
      <stop offset="0%" stop-color="#28558F" stop-opacity="0.38"/>
      <stop offset="100%" stop-color="#0D274D" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <path d="M0,0 L500,0 L500,72 Q355,103 165,83 Q65,73 0,88 Z" fill="url(#navyGrad)"/>
  <path d="M180,0 L500,0 L500,72 Q360,96 220,62 Q155,44 180,0 Z" fill="url(#glow)"/>
  <path d="M0,88 Q65,73 165,83 Q355,103 500,72" fill="none" stroke="#C89F54" stroke-width="1.4" stroke-opacity="0.78"/>
  <path d="M125,84 Q315,102 500,54" fill="none" stroke="#C89F54" stroke-width="0.9" stroke-opacity="0.45"/>
</svg>
""")

# Subtle Bottom-Right Champagne Wave for App Canvas
CANVAS_WAVE_SVG = _svg_uri("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 220" preserveAspectRatio="none">
  <path d="M120,220 C240,190 340,105 500,80 L500,220 Z" fill="#F4EDE2" fill-opacity="0.8"/>
  <path d="M230,220 C330,188 400,138 500,124 L500,220 Z" fill="#EFE6D8" fill-opacity="0.65"/>
</svg>
""")

# Multicolor Aerocity Petal Flower Emblem (via base64 img URI so DOMPurify never strips SVG)
AEROCITY_PETALS_URI = _svg_uri("""
<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <path d="M20 21 C18 14, 17 7, 20 3 C23 7, 22 14, 20 21 Z" fill="#F5B82E"/>
  <path d="M20 21 C14 16, 9 11, 9 5 C14 8, 17 14, 20 21 Z" fill="#F08223"/>
  <path d="M20 21 C11 19, 4 17, 2 12 C8 12, 14 16, 20 21 Z" fill="#D9282F"/>
  <path d="M20 21 C12 24, 6 27, 4 33 C10 30, 15 26, 20 21 Z" fill="#A31C5A"/>
  <path d="M20 21 C17 28, 15 34, 18 38 C21 34, 21 28, 20 21 Z" fill="#21409A"/>
  <path d="M20 21 C24 27, 29 31, 33 29 C30 24, 25 22, 20 21 Z" fill="#008C99"/>
  <path d="M20 21 C26 22, 33 21, 37 16 C31 15, 25 17, 20 21 Z" fill="#00A4C7"/>
  <path d="M20 21 C25 16, 30 11, 31 6 C26 9, 23 15, 20 21 Z" fill="#54B948"/>
</svg>
""")

def _png_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


AEROCITY_LOGO_URI = _png_uri(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "aerocity_logo.png"))

GMR_WORDMARK_URI = _svg_uri("""
<svg viewBox="0 0 74 28" xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="22" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="22" letter-spacing="-0.5" fill="#FFFFFF">GMR</text>
  <path d="M35 5 C45 1, 56 2, 64 6" fill="none" stroke="#E1393E" stroke-width="2.1" stroke-linecap="round"/>
  <path d="M32 8 C43 4, 54 4, 62 8" fill="none" stroke="#2CA6E0" stroke-width="1.7" stroke-linecap="round"/>
</svg>
""")

SPARKLES_URI = _svg_uri("""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M10 3L11.6 7.4L16 9L11.6 10.6L10 15L8.4 10.6L4 9L8.4 7.4L10 3Z" fill="#C89A4B"/>
  <path d="M17.5 13L18.4 15.6L21 16.5L18.4 17.4L17.5 20L16.6 17.4L14 16.5L16.6 15.6L17.5 13Z" fill="#C89A4B"/>
</svg>
""")

HOME_BRAND_HTML = (
    '<div class="aero-brand-home">'
    f'<img class="aero-logo-img" src="{AEROCITY_LOGO_URI}" alt="GMR Aerocity New Delhi" height="40">'
    '</div>'
)

CHAT_BRAND_HTML = (
    '<div class="aero-brand-chat">'
    f'<img class="aero-logo-img" src="{AEROCITY_LOGO_URI}" alt="GMR Aerocity New Delhi" height="32">'
    '<div class="aero-brand-sep"></div>'
    '<div class="aero-chat-title">AeroAI Concierge</div>'
    '</div>'
)

AVATAR_BADGE_HTML = (
    '<div class="aero-avatar-circle">'
    f'<img src="{AEROCITY_PETALS_URI}" alt="AeroAI" width="21" height="21">'
    '</div>'
)

SPARKLES_HTML = (
    '<div class="ask-sparkles" aria-hidden="true">'
    f'<img src="{SPARKLES_URI}" alt="" width="20" height="20">'
    '</div>'
)

# Line-Art SVG Icon Registry
ICONS = {
    "search": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="6.5"/><path d="M16 16L20.5 20.5"/></svg>'),
    "chat": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/><circle cx="9.5" cy="12" r="0.7" fill="#FFFFFF"/><circle cx="12.5" cy="12" r="0.7" fill="#FFFFFF"/><circle cx="15.5" cy="12" r="0.7" fill="#FFFFFF"/></svg>'),
    "back": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>'),
    "dots": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFFFFF"><circle cx="6" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18" cy="12" r="1.6"/></svg>'),
    "arrow_right_white": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>'),
    "arrow_right_gold": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h13"/><path d="M13 7l5 5-5 5"/></svg>'),
    "chevron_right": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#1E293B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>'),
    # FAQ & Venue dark-navy line icons
    "calendar_clock": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M8 2.5v3.5M16 2.5v3.5M3 9.5h18"/><path d="M8 13h2M12 13h2M8 16.5h2M12 16.5h2"/></svg>'),
    "calendar": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M8 2.5v3.5M16 2.5v3.5M3 9.5h18"/><path d="M8 13.5h.01M12 13.5h.01M16 13.5h.01M8 17h.01M12 17h.01"/></svg>'),
    "users": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8.5" r="3"/><path d="M3.5 19c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/><circle cx="16.5" cy="9.5" r="2.2"/><path d="M16.5 14c2.4 0 4.2 1.6 4.2 4.3"/></svg>'),
    "pin": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 1 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/></svg>'),
    "coffee": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M5 10h11v4.5a4.5 4.5 0 0 1-4.5 4.5h-2A4.5 4.5 0 0 1 5 14.5V10z"/><path d="M16 11h1.8a2.2 2.2 0 0 1 0 4.4H16"/><path d="M4 21h13"/><path d="M8.5 5.5c0-1 .8-1.5.8-2.5M12 5.5c0-1 .8-1.5.8-2.5"/></svg>'),
    "music": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M9 17.5V6l10-2v11.5"/><circle cx="6.5" cy="17.5" r="2.5"/><circle cx="16.5" cy="15.5" r="2.5"/></svg>'),
    "ticket": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v1.5a1.5 1.5 0 0 0 0 3V15a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1.5a1.5 1.5 0 0 0 0-3V9z"/><path d="M9.5 7.5v9" stroke-dasharray="2 2"/></svg>'),
    "dining": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v7a2.5 2.5 0 0 0 5 0V3M8.5 3v18"/><path d="M16 3c2 2.5 2 6.5 0 9v9M16 3v18"/></svg>'),
    "spa": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4c2.4 3 3.2 6.4 0 10.5C8.8 10.4 9.6 7 12 4z"/><path d="M12 14.5C8.5 13 6 10 5.5 7c3.2.5 5.4 3.1 6.5 7.5z"/><path d="M12 14.5c3.5-1.5 6-4.5 6.5-7.5-3.2.5-5.4 3.1-6.5 7.5z"/><path d="M4 15.5c3.2 2.6 5.6 3 8 2.5 2.4.5 4.8.1 8-2.5-2.6-1-5.2-.6-8 1-2.8-1.6-5.4-2-8-1z"/></svg>'),
    "event": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M8 2.5v3.5M16 2.5v3.5M3 9.5h18"/><path d="M9 14l2 2 4-4"/></svg>'),
    "meeting": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8.5" r="3"/><path d="M3.5 19c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/><circle cx="16.5" cy="9.5" r="2.2"/><path d="M16.5 14c2.4 0 4.2 1.6 4.2 4.3"/></svg>'),
    "hotel": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16"/><path d="M9 21v-4h6v4M8 7h2M14 7h2M8 11h2M14 11h2M2 21h20"/></svg>'),
    "place": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0F2342" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 1 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/></svg>'),
    # Gold pill icons
    "pill_pin": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 1 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.2"/></svg>'),
    "pill_car": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 11l1.8-4.5A2 2 0 0 1 8.7 5.2h6.6a2 2 0 0 1 1.9 1.3L19 11"/><rect x="3" y="11" width="18" height="6.5" rx="2"/><path d="M6 17.5v1.5M18 17.5v1.5"/><circle cx="7" cy="14.2" r="0.9" fill="#BA8F47"/><circle cx="17" cy="14.2" r="0.9" fill="#BA8F47"/></svg>'),
    "pill_coffee": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 10h11v4.5a4.5 4.5 0 0 1-4.5 4.5h-2A4.5 4.5 0 0 1 5 14.5V10z"/><path d="M16 11h1.8a2.2 2.2 0 0 1 0 4.4H16"/><path d="M4 21h13"/></svg>'),
    "pill_calendar": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16.5" rx="2.5"/><path d="M8 2.5v3.5M16 2.5v3.5M3 9.5h18"/></svg>'),
    "pill_music": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 17.5V6l10-2v11.5"/><circle cx="6.5" cy="17.5" r="2.3"/><circle cx="16.5" cy="15.5" r="2.3"/></svg>'),
    "pill_info": _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#BA8F47" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>'),
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS Styling
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.html(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

  html, body, .stApp {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #EAE4DA !important;
    color: #0F2342 !important;
  }}

  /* Hide default Streamlit chrome */
  #MainMenu, footer, header,
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"],
  [data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
  }}

  .block-container {{
    max-width: 480px !important;
    padding: 1rem 0.75rem 1.5rem 0.75rem !important;
    margin: 0 auto !important;
  }}

  @media (max-width: 540px) {{
    html, body, .stApp {{
      background: #FCF9F4 !important;
    }}
    .block-container {{
      max-width: 100% !important;
      padding: 0 !important;
    }}
  }}

  /* ── Main App Shell Card ───────────────────── */
  .st-key-aero_shell {{
    background-color: #FCF9F4 !important;
    background-image: url("{CANVAS_WAVE_SVG}") !important;
    background-position: right bottom !important;
    background-repeat: no-repeat !important;
    background-size: 100% 200px !important;
    border-radius: 28px !important;
    border: 1px solid rgba(210, 198, 180, 0.55) !important;
    box-shadow: 0 24px 60px rgba(10, 25, 50, 0.14), 0 2px 10px rgba(10, 25, 50, 0.05) !important;
    overflow: hidden !important;
    min-height: 680px !important;
    padding-bottom: 14px !important;
    gap: 0 !important;
  }}

  @media (max-width: 540px) {{
    .st-key-aero_shell {{
      border-radius: 0 !important;
      border: none !important;
      box-shadow: none !important;
      min-height: 100vh !important;
    }}
  }}

  /* ── Top Curved Navy Header ────────────────── */
  .st-key-aero_header {{
    background-image: url("{HEADER_BG_SVG}") !important;
    background-size: 100% 100% !important;
    background-repeat: no-repeat !important;
    padding: 16px 18px 26px 18px !important;
    margin-bottom: 2px !important;
    gap: 0 !important;
  }}

  .st-key-header_row {{
    width: 100% !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
  }}

  /* Brand Locks */
  .aero-brand-home, .aero-brand-chat {{
    display: flex;
    align-items: center;
    gap: 10px;
    color: #FFFFFF;
  }}
  .aero-gmr-img,
  .aero-petals-img {{
    display: block;
    flex-shrink: 0;
  }}
  .aero-logo-img {{
    display: block;
    width: auto;
    background: #FFFFFF;
    border-radius: 10px;
    padding: 4px 10px;
    flex-shrink: 0;
  }}
  .aero-brand-sep {{
    width: 1px;
    height: 24px;
    background: rgba(255, 255, 255, 0.34);
    flex-shrink: 0;
  }}
  .aero-city-wrap {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .aero-city-text {{
    display: flex;
    flex-direction: column;
    line-height: 1.05;
  }}
  .aero-city-top {{
    font-size: 12.5px;
    font-weight: 700;
    letter-spacing: 0.9px;
    color: #FFFFFF;
  }}
  .aero-city-sub {{
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 1.4px;
    color: rgba(255, 255, 255, 0.85);
    margin-top: 2px;
  }}
  .aero-chat-title {{
    font-size: 14px;
    font-weight: 500;
    color: #FFFFFF;
    letter-spacing: 0.1px;
    white-space: nowrap;
  }}

  /* Header Circular & Icon Buttons */
  .st-key-btn_search button,
  .st-key-btn_open_chat button {{
    width: 36px !important;
    height: 36px !important;
    min-height: 36px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background: rgba(255, 255, 255, 0.11) !important;
    border: 1px solid rgba(255, 255, 255, 0.24) !important;
    position: relative !important;
    color: transparent !important;
    box-shadow: none !important;
    transition: background 0.18s ease, transform 0.15s ease !important;
  }}
  .st-key-btn_search button:hover,
  .st-key-btn_open_chat button:hover {{
    background: rgba(255, 255, 255, 0.22) !important;
    border-color: rgba(255, 255, 255, 0.42) !important;
    transform: translateY(-1px) !important;
  }}
  .st-key-btn_search button::before,
  .st-key-btn_open_chat button::before {{
    content: "";
    position: absolute;
    inset: 0;
    margin: auto;
    width: 17px;
    height: 17px;
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
  }}
  .st-key-btn_search button::before {{
    background-image: url("{ICONS['search']}");
  }}
  .st-key-btn_open_chat button::before {{
    background-image: url("{ICONS['chat']}");
  }}

  .st-key-btn_back_home button,
  .st-key-chat_menu_popover button {{
    width: 34px !important;
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background: transparent !important;
    border: none !important;
    position: relative !important;
    color: transparent !important;
    box-shadow: none !important;
  }}
  .st-key-btn_back_home button:hover,
  .st-key-chat_menu_popover button:hover {{
    background: rgba(255, 255, 255, 0.14) !important;
  }}
  .st-key-btn_back_home button::before,
  .st-key-chat_menu_popover button::before {{
    content: "";
    position: absolute;
    inset: 0;
    margin: auto;
    width: 18px;
    height: 18px;
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
  }}
  .st-key-btn_back_home button::before {{
    background-image: url("{ICONS['back']}");
  }}
  .st-key-chat_menu_popover button::before {{
    background-image: url("{ICONS['dots']}");
  }}
  .st-key-chat_menu_popover button svg {{
    display: none !important;
  }}

  /* ── Inner Body Padding ────────────────────── */
  .st-key-home_body,
  .st-key-chat_body {{
    padding: 6px 20px 8px 20px !important;
    gap: 0 !important;
  }}
  .st-key-bottom_bar_wrap {{
    padding: 8px 20px 4px 20px !important;
    margin-top: auto !important;
  }}

  /* ── Home Hero Section ─────────────────────── */
  .aero-hero {{
    margin: 2px 0 14px 0;
  }}
  .aero-hero-title {{
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.15;
    margin: 0 0 5px 0;
    letter-spacing: -0.3px;
  }}
  .aero-hero-navy {{
    color: #0F2342;
  }}
  .aero-hero-gold {{
    color: #BC9149;
  }}
  .aero-hero-sub {{
    font-size: 13.5px;
    font-weight: 400;
    color: #3E4754;
    margin: 0;
    line-height: 1.42;
  }}
  .aero-gold-rule {{
    width: 28px;
    height: 2px;
    background: #BC9149;
    border-radius: 2px;
    margin: 16px 0 10px 0;
  }}
  .aero-faq-heading {{
    font-size: 19.5px;
    font-weight: 700;
    color: #0F2342;
    margin: 0 0 2px 0;
    letter-spacing: -0.2px;
  }}
  .aero-faq-sub {{
    font-size: 13px;
    color: #5A6472;
    margin: 0 0 12px 0;
  }}

  /* ── Optional Search Box ───────────────────── */
  .st-key-faq_search_input {{
    margin-bottom: 10px !important;
  }}
  .st-key-faq_search_input input {{
    background: #FFFFFF !important;
    border: 1px solid #DFD6C7 !important;
    border-radius: 12px !important;
    color: #0F2342 !important;
    font-size: 13.5px !important;
    padding: 9px 14px !important;
  }}

  /* ── 2x4 FAQ Card Grid (Horizontal Rows) ───── */
  [class*="st-key-faq_row_"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 11px !important;
    width: 100% !important;
    margin-bottom: 11px !important;
    align-items: stretch !important;
  }}
  [class*="st-key-faq_row_"] > [class*="st-key-faq_card_"],
  [class*="st-key-faq_row_"] > div {{
    flex: 1 1 0% !important;
    min-width: 0 !important;
  }}
  [class*="st-key-faq_card_"] button {{
    position: relative !important;
    width: 100% !important;
    min-height: 94px !important;
    height: 100% !important;
    background: #FFFFFF !important;
    border: 1px solid #EAE4DA !important;
    border-radius: 16px !important;
    padding: 40px 26px 12px 14px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    align-items: flex-start !important;
    box-shadow: 0 3px 12px rgba(15, 35, 66, 0.04) !important;
    transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease !important;
  }}
  [class*="st-key-faq_card_"] button:hover {{
    border-color: #C89F54 !important;
    background: #FFFDF9 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(15, 35, 66, 0.08) !important;
  }}
  [class*="st-key-faq_card_"] button::before {{
    content: "";
    position: absolute;
    top: 12px;
    left: 14px;
    width: 21px;
    height: 21px;
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
  }}
  [class*="st-key-faq_card_"] button::after {{
    content: "";
    position: absolute;
    right: 10px;
    top: 58%;
    transform: translateY(-50%);
    width: 14px;
    height: 14px;
    background-image: url("{ICONS['chevron_right']}");
    background-size: contain;
    background-repeat: no-repeat;
    opacity: 0.72;
  }}
  [class*="st-key-faq_card_"] button > div {{
    width: 100% !important;
    justify-content: flex-start !important;
    align-items: flex-start !important;
    margin: 0 !important;
    padding: 0 !important;
  }}
  [class*="st-key-faq_card_"] button [data-testid="stMarkdownContainer"] {{
    width: 100% !important;
    text-align: left !important;
  }}
  [class*="st-key-faq_card_"] button [data-testid="stMarkdownContainer"] p {{
    margin: 0 !important;
    font-size: 11.8px !important;
    line-height: 1.3 !important;
    color: #5E6774 !important;
    font-weight: 400 !important;
    text-align: left !important;
  }}
  [class*="st-key-faq_card_"] button [data-testid="stMarkdownContainer"] p:first-child {{
    margin-bottom: 2px !important;
  }}
  [class*="st-key-faq_card_"] button [data-testid="stMarkdownContainer"] strong {{
    font-size: 13.5px !important;
    font-weight: 700 !important;
    color: #0F2342 !important;
    display: block !important;
    line-height: 1.22 !important;
  }}

  /* Individual FAQ Icons */
  [class*="st-key-faq_card_calendar_clock"] button::before {{ background-image: url("{ICONS['calendar_clock']}"); }}
  [class*="st-key-faq_card_calendar_"] button::before {{ background-image: url("{ICONS['calendar']}"); }}
  [class*="st-key-faq_card_users"] button::before {{ background-image: url("{ICONS['users']}"); }}
  [class*="st-key-faq_card_pin"] button::before {{ background-image: url("{ICONS['pin']}"); }}
  [class*="st-key-faq_card_coffee"] button::before {{ background-image: url("{ICONS['coffee']}"); }}
  [class*="st-key-faq_card_music"] button::before {{ background-image: url("{ICONS['music']}"); }}
  [class*="st-key-faq_card_ticket"] button::before {{ background-image: url("{ICONS['ticket']}"); }}

  /* ── Chat Messages ─────────────────────────── */
  .st-key-chat_stream {{
    min-height: 500px !important;
    gap: 12px !important;
    padding-top: 8px !important;
    padding-bottom: 10px !important;
  }}

  /* User Bubble (Right-aligned soft slate-blue) */
  .aero-user-row {{
    display: flex;
    justify-content: flex-end;
    width: 100%;
  }}
  .aero-user-bubble {{
    background: #DFE6F0;
    border-radius: 16px 16px 4px 16px;
    padding: 11px 16px;
    max-width: 78%;
    color: #152338;
    font-size: 13.8px;
    line-height: 1.45;
    font-weight: 400;
    box-shadow: 0 2px 8px rgba(15, 35, 66, 0.04);
    word-wrap: break-word;
  }}

  /* Assistant Row: Avatar + Bubble */
  .aero-asst-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    width: 100%;
    box-sizing: border-box;
    padding-right: 30px;
  }}
  .aero-avatar-circle {{
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #FFFFFF;
    border: 1px solid #EAE4DA;
    box-shadow: 0 2px 8px rgba(15, 35, 66, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
  }}
  .aero-avatar-circle img {{
    display: block;
  }}
  .aero-asst-bubble {{
    background: #FFFFFF;
    border: 1px solid #EAE4DA;
    border-radius: 16px;
    padding: 11px 16px;
    max-width: calc(100% - 44px);
    color: #18263C;
    font-size: 13.8px;
    line-height: 1.48;
    box-shadow: 0 3px 12px rgba(15, 35, 66, 0.04);
    word-wrap: break-word;
  }}
  .aero-asst-bubble p {{
    margin: 0 0 6px 0;
  }}
  .aero-asst-bubble p:last-child {{
    margin-bottom: 0;
  }}
  .aero-asst-bubble p.aero-sec-head {{
    margin: 22px 0 6px 0;
    padding-top: 16px;
    border-top: 1px solid #F1ECE4;
    font-size: 12px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #BA8F47;
  }}
  .aero-asst-bubble p.aero-sec-head strong {{
    font-weight: 700;
  }}
  .aero-asst-bubble p.aero-offer {{
    display: block;
    margin: 10px 0 6px 0;
    padding: 10px 14px;
    border: 1.5px dashed #BA8F47;
    border-radius: 14px;
    background: linear-gradient(135deg, #FFF8E8 0%, #FBEFD2 100%);
  }}
  .aero-asst-bubble p.aero-offer .aero-offer-tag {{
    display: block;
    font-size: 14px;
    font-weight: 700;
    color: #7A5314;
  }}
  .aero-asst-bubble p.aero-offer .aero-offer-note {{
    display: block;
    margin-top: 3px;
    font-size: 10.5px;
    line-height: 1.35;
    font-style: italic;
    color: #8C7A5B;
  }}
  .aero-asst-bubble p.aero-sec-btn {{
    margin: 8px 0 4px 0;
  }}
  .aero-asst-bubble p.aero-sec-btn + p {{
    margin-top: 18px;
  }}
  .aero-asst-bubble p.aero-sec-btn a {{
    display: inline-block;
    padding: 5px 14px;
    border: 1px solid #BA8F47;
    border-radius: 999px;
    color: #8A6420;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    background: #FBF6EC;
  }}
  .aero-asst-bubble p.aero-sec-btn a:hover {{
    background: #BA8F47;
    color: #FFFFFF;
  }}
  .aero-asst-bubble a {{
    color: #BA8F47;
    font-weight: 600;
    text-decoration: underline;
  }}

  /* ── Structured Venue Recommendation Card List ─ */
  [class*="st-key-venue_group_"] {{
    margin-left: 42px !important;
    width: calc(100% - 42px) !important;
    background: #FFFFFF !important;
    border: 1px solid #EAE4DA !important;
    border-radius: 18px !important;
    box-shadow: 0 6px 22px rgba(15, 35, 66, 0.06) !important;
    overflow: hidden !important;
    gap: 0 !important;
    margin-top: -4px !important;
  }}
  [class*="st-key-venue_row_"] {{
    border-bottom: 1px solid #F1ECE4 !important;
  }}
  [class*="st-key-venue_row_"]:last-child {{
    border-bottom: none !important;
  }}
  [class*="st-key-venue_row_"] button {{
    position: relative !important;
    width: 100% !important;
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 13px 38px 13px 68px !important;
    min-height: 64px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
  }}
  [class*="st-key-venue_row_"] button:hover {{
    background: #FCF8F1 !important;
  }}
  [class*="st-key-venue_row_"] button::before {{
    content: "";
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background-color: #F6EFE4;
    background-size: 21px 21px;
    background-repeat: no-repeat;
    background-position: center;
  }}
  [class*="st-key-venue_row_"] button::after {{
    content: "";
    position: absolute;
    right: 15px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    background-image: url("{ICONS['arrow_right_gold']}");
    background-size: contain;
    background-repeat: no-repeat;
  }}
  [class*="st-key-venue_row_"] button [data-testid="stMarkdownContainer"] {{
    width: 100% !important;
    text-align: left !important;
  }}
  [class*="st-key-venue_row_"] button [data-testid="stMarkdownContainer"] p {{
    margin: 0 !important;
    font-size: 12.2px !important;
    color: #6B7280 !important;
    line-height: 1.3 !important;
    text-align: left !important;
  }}
  [class*="st-key-venue_row_"] button [data-testid="stMarkdownContainer"] p:first-child {{
    margin-bottom: 1px !important;
  }}
  [class*="st-key-venue_row_"] button [data-testid="stMarkdownContainer"] strong {{
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #0F2342 !important;
    display: block !important;
  }}

  /* Venue Row Icon Variants */
  [class*="st-key-venue_row_coffee"] button::before {{ background-image: url("{ICONS['coffee']}"); }}
  [class*="st-key-venue_row_dining"] button::before {{ background-image: url("{ICONS['dining']}"); }}
  [class*="st-key-venue_row_spa"] button::before {{ background-image: url("{ICONS['spa']}"); }}
  [class*="st-key-venue_row_music"] button::before {{ background-image: url("{ICONS['music']}"); }}
  [class*="st-key-venue_row_event"] button::before {{ background-image: url("{ICONS['event']}"); }}
  [class*="st-key-venue_row_meeting"] button::before {{ background-image: url("{ICONS['meeting']}"); }}
  [class*="st-key-venue_row_hotel"] button::before {{ background-image: url("{ICONS['hotel']}"); }}
  [class*="st-key-venue_row_place"] button::before {{ background-image: url("{ICONS['place']}"); }}

  /* ── Gold Follow-up Pills ──────────────────── */
  .st-key-followups_row {{
    padding: 8px 0 6px 0 !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
  }}
  [class*="st-key-followup_btn_"] button {{
    position: relative !important;
    background: #FFFDF9 !important;
    border: 1px solid #C89F54 !important;
    border-radius: 999px !important;
    padding: 7px 14px 7px 34px !important;
    min-height: 34px !important;
    box-shadow: 0 2px 8px rgba(186, 143, 71, 0.08) !important;
    transition: background 0.15s ease, transform 0.15s ease !important;
  }}
  [class*="st-key-followup_btn_"] button:hover {{
    background: #FAF2E4 !important;
    transform: translateY(-1px) !important;
  }}
  [class*="st-key-followup_btn_"] button::before {{
    content: "";
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    width: 15px;
    height: 15px;
    background-size: contain;
    background-repeat: no-repeat;
  }}
  [class*="st-key-followup_btn_"] button p {{
    margin: 0 !important;
    font-size: 12.2px !important;
    font-weight: 500 !important;
    color: #18263C !important;
    white-space: nowrap !important;
  }}
  [class*="st-key-followup_btn_pin"] button::before {{ background-image: url("{ICONS['pill_pin']}"); }}
  [class*="st-key-followup_btn_car"] button::before {{ background-image: url("{ICONS['pill_car']}"); }}
  [class*="st-key-followup_btn_coffee"] button::before {{ background-image: url("{ICONS['pill_coffee']}"); }}
  [class*="st-key-followup_btn_calendar"] button::before {{ background-image: url("{ICONS['pill_calendar']}"); }}
  [class*="st-key-followup_btn_music"] button::before {{ background-image: url("{ICONS['pill_music']}"); }}
  [class*="st-key-followup_btn_info"] button::before {{ background-image: url("{ICONS['pill_info']}"); }}

  /* ── Bottom Ask Pill Bar ───────────────────── */
  .st-key-ask_form {{
    margin: 0 !important;
    padding: 0 !important;
  }}
  .st-key-ask_pill_row {{
    background: #FFFFFF !important;
    border: 1px solid #DFD6C7 !important;
    border-radius: 999px !important;
    padding: 5px 5px 5px 14px !important;
    box-shadow: 0 6px 22px rgba(15, 35, 66, 0.06) !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
  }}
  .ask-sparkles {{
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .st-key-ask_input {{
    flex: 1 1 auto !important;
  }}
  .st-key-ask_input div,
  .st-key-ask_input [data-baseweb="input"],
  .st-key-ask_input [data-baseweb="base-input"] {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
  }}
  .st-key-ask_input input {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #0F2342 !important;
    font-size: 13.8px !important;
    padding: 6px 4px !important;
  }}
  .st-key-ask_input input::placeholder {{
    color: #4A5464 !important;
    opacity: 0.9 !important;
  }}
  .st-key-ask_submit button {{
    width: 38px !important;
    height: 38px !important;
    min-height: 38px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background: #0B2142 !important;
    border: none !important;
    color: transparent !important;
    position: relative !important;
    flex-shrink: 0 !important;
    transition: background 0.15s ease, transform 0.15s ease !important;
  }}
  .st-key-ask_submit button:hover {{
    background: #143361 !important;
    transform: scale(1.03) !important;
  }}
  .st-key-ask_submit button::before {{
    content: "";
    position: absolute;
    inset: 0;
    margin: auto;
    width: 18px;
    height: 18px;
    background-image: url("{ICONS['arrow_right_white']}");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
  }}

  /* Typing Indicator */
  .aero-typing {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 2px;
  }}
  .aero-typing span {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #BC9149;
    animation: aeroPulse 1.1s infinite ease-in-out;
  }}
  .aero-typing span:nth-child(2) {{ animation-delay: 0.18s; }}
  .aero-typing span:nth-child(3) {{ animation-delay: 0.36s; }}
  @keyframes aeroPulse {{
    0%, 80%, 100% {{ opacity: 0.28; transform: scale(0.85); }}
    40% {{ opacity: 1; transform: scale(1.1); }}
  }}
</style>
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper: Safe Inline Formatting & Navigation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _format_chat_html(text: str) -> str:
    """Safely escapes text while preserving **bold**, [name](url) links, and line breaks."""
    escaped = html.escape((text or "").strip())
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

    escaped = re.sub(r"(?<![*\w])\*([^*\n]+?)\*(?![*\w])", r"<em>\1</em>", escaped)

    def _link_repl(match):
        label, url = match.group(1), match.group(2)
        if url.startswith(("https://", "http://", "tel:", "mailto:")):
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        return label

    escaped = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link_repl, escaped)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", escaped) if p.strip()]
    if not paragraphs:
        return ""
    out = []
    for p in paragraphs:
        body = p.replace(chr(10), "<br>")
        if re.fullmatch(r"<strong>[^<]*</strong>", p):
            out.append(f'<p class="aero-sec-head">{body}</p>')
        elif p.startswith("🏷️ Sample offer"):
            title, _, note = body.partition("<br>")
            out.append(f'<p class="aero-offer"><span class="aero-offer-tag">{title}</span>'
                       f'<span class="aero-offer-note">{note}</span></p>')
        elif re.fullmatch(r"<a [^>]*>[^<]*</a>", p):
            out.append(f'<p class="aero-sec-btn">{body}</p>')
        else:
            out.append(f"<p>{body}</p>")
    return "".join(out)


def submit_question(question_text: str):
    q = (question_text or "").strip()
    if not q:
        return
    st.session_state.messages.append({"role": "user", "content": q})
    st.session_state.view = "chat"
    st.session_state.show_search = False
    st.rerun()


def render_bottom_ask_bar():
    with st.container(key="bottom_bar_wrap"):
        with st.form("ask_form", clear_on_submit=True, enter_to_submit=True, border=False):
            with st.container(key="ask_pill_row", horizontal=True, vertical_alignment="center", gap="small"):
                st.html(SPARKLES_HTML, width="content")
                typed = st.text_input(
                    "Ask your own question",
                    placeholder="Ask your own question",
                    label_visibility="collapsed",
                    key="ask_input",
                )
                submitted = st.form_submit_button(" ", key="ask_submit", width="content")
            if submitted and typed.strip():
                submit_question(typed.strip())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Shell Container
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.container(key="aero_shell"):

    # ── Top Curved Navy Header ──
    with st.container(key="aero_header"):
        if st.session_state.view == "home":
            with st.container(
                key="header_row",
                horizontal=True,
                horizontal_alignment="distribute",
                vertical_alignment="center",
            ):
                st.html(HOME_BRAND_HTML, width="content")
                with st.container(
                    key="header_actions",
                    horizontal=True,
                    gap="small",
                    vertical_alignment="center",
                    width="content",
                ):
                    if st.button(" ", key="btn_search", help="Search FAQs", width="content"):
                        st.session_state.show_search = not st.session_state.show_search
                        st.rerun()
                    if st.button(" ", key="btn_open_chat", help="Open Chat", width="content"):
                        st.session_state.view = "chat"
                        st.rerun()
        else:
            with st.container(
                key="header_row",
                horizontal=True,
                horizontal_alignment="distribute",
                vertical_alignment="center",
            ):
                with st.container(
                    key="chat_header_left",
                    horizontal=True,
                    gap="small",
                    vertical_alignment="center",
                    width="content",
                ):
                    if st.button(" ", key="btn_back_home", help="Back to Explore FAQs", width="content"):
                        st.session_state.view = "home"
                        st.rerun()
                    st.html(CHAT_BRAND_HTML, width="content")

                with st.popover(" ", key="chat_menu_popover", width="content"):
                    if st.button("Explore FAQs", key="menu_home", use_container_width=True):
                        st.session_state.view = "home"
                        st.rerun()
                    if st.button("Clear conversation", key="menu_clear", use_container_width=True):
                        st.session_state.messages = []
                        st.rerun()

    # Separate st.empty() slots guarantee zero stale DOM nodes when switching views
    home_slot = st.empty()
    chat_slot = st.empty()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VIEW 1: Home / Explore FAQs
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if st.session_state.view == "home":
        chat_slot.empty()
        with home_slot.container(key="home_body"):
            st.html(
                f'<div class="aero-hero">'
                f'<h1 class="aero-hero-title">'
                f'<span class="aero-hero-navy">AeroAI</span>'
                f'<span class="aero-hero-gold"> Concierge</span>'
                f'</h1>'
                f'<p class="aero-hero-sub">{html.escape(BOT_SUBTITLE)}</p>'
                f'<div class="aero-gold-rule"></div>'
                f'<h2 class="aero-faq-heading">Explore FAQs</h2>'
                f'<p class="aero-faq-sub">Quick answers to common questions</p>'
                f'</div>'
            )

            suggestions = get_suggested_questions(limit=8)

            if st.session_state.show_search:
                search_term = st.text_input(
                    "Filter FAQs",
                    value=st.session_state.faq_filter,
                    placeholder="Filter quick questions...",
                    label_visibility="collapsed",
                    key="faq_search_input",
                )
                st.session_state.faq_filter = search_term
                if search_term.strip():
                    q_low = search_term.strip().lower()
                    suggestions = [
                        s for s in suggestions
                        if q_low in s["title"].lower()
                        or q_low in s["subtitle"].lower()
                        or q_low in s["question"].lower()
                    ]

            # Render 2 cards per row cleanly
            for row_idx in range(0, len(suggestions), 2):
                row_items = suggestions[row_idx:row_idx + 2]
                with st.container(key=f"faq_row_{row_idx // 2}", horizontal=True, gap="small"):
                    for col_offset, s in enumerate(row_items):
                        idx = row_idx + col_offset
                        icon_type = s.get("icon_type", "pin")
                        label = (
                            f"**{s['title']}**\n\n{s['subtitle']}"
                            if s.get("subtitle")
                            else f"**{s['title']}**"
                        )
                        if st.button(
                            label,
                            key=f"faq_card_{icon_type}_{idx}",
                            use_container_width=True,
                        ):
                            submit_question(s["question"])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VIEW 2: Chat / Conversation View
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    else:
        home_slot.empty()
        with chat_slot.container(key="chat_body"):
            with st.container(key="chat_stream"):
                if not st.session_state.messages:
                    st.html(
                        f'<div class="aero-asst-row">'
                        f'{AVATAR_BADGE_HTML}'
                        f'<div class="aero-asst-bubble">{_format_chat_html(WELCOME_MSG)}</div>'
                        f'</div>'
                    )

                for idx, msg in enumerate(st.session_state.messages):
                    if msg["role"] == "user":
                        st.html(
                            f'<div class="aero-user-row">'
                            f'<div class="aero-user-bubble">{_format_chat_html(msg["content"])}</div>'
                            f'</div>'
                        )
                    else:
                        st.html(
                            f'<div class="aero-asst-row">'
                            f'{AVATAR_BADGE_HTML}'
                            f'<div class="aero-asst-bubble">{_format_chat_html(msg["content"])}</div>'
                            f'</div>'
                        )

                        cards = msg.get("cards") or []
                        if cards:
                            with st.container(key=f"venue_group_{idx}"):
                                for c_idx, card in enumerate(cards):
                                    c_icon = card.get("icon", "place")
                                    c_title = card.get("title", "")
                                    c_sub = card.get("subtitle", "")
                                    c_label = f"**{c_title}**\n\n{c_sub}" if c_sub else f"**{c_title}**"
                                    if st.button(
                                        c_label,
                                        key=f"venue_row_{c_icon}_{idx}_{c_idx}",
                                        use_container_width=True,
                                    ):
                                        submit_question(f"Tell me more about {c_title} at Aerocity")

                pending = bool(
                    st.session_state.messages
                    and st.session_state.messages[-1]["role"] == "user"
                )
                if pending:
                    st.html(
                        f'<div class="aero-asst-row">'
                        f'{AVATAR_BADGE_HTML}'
                        f'<div class="aero-asst-bubble"><div class="aero-typing"><span></span><span></span><span></span></div></div>'
                        f'</div>'
                    )

                    user_query = st.session_state.messages[-1]["content"]
                    time.sleep(0.35)
                    result = find_best_answer(user_query, st.session_state.messages[:-1])
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "cards": result.get("cards", []),
                        "followups": result.get("followups", DEFAULT_FOLLOWUPS),
                    })
                    st.rerun()

            latest_followups = DEFAULT_FOLLOWUPS
            for m in reversed(st.session_state.messages):
                if m["role"] == "assistant" and m.get("followups"):
                    latest_followups = m["followups"]
                    break

            with st.container(key="followups_row", horizontal=True, horizontal_alignment="center"):
                for f_idx, pill in enumerate(latest_followups[:2]):
                    p_icon = pill.get("icon", "pin")
                    p_label = pill.get("label", "")
                    if st.button(
                        p_label,
                        key=f"followup_btn_{p_icon}_{f_idx}",
                        width="content",
                    ):
                        submit_question(p_label)

    render_bottom_ask_bar()
