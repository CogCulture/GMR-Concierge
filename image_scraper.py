"""
image_scraper.py — GMR Aerocity Image Index Builder

HOTLINK FIX: Streamlit renders inside an iframe, so direct <img src="...">
tags get blocked by the GMR CDN (no Referer = 403 Forbidden).

Solution: At query time, images are fetched server-side via requests with
a proper Referer header, converted to base64 data URIs, and cached by
Streamlit. The browser then renders them from memory — no external request
needed at display time, so the CDN block is completely bypassed.

MATCHING STRATEGY (updated):
  - VENUE-SPECIFIC keywords (e.g. "blue tokai", "toy room") are checked
    FIRST and given a large priority bonus so they always beat generic
    keywords like "aerocity" or "hours".
  - Generic/category keywords act as a fallback when no specific venue
    name is found in the answer text.
"""

import base64
import requests
import streamlit as st
from typing import Optional

# ─────────────────────────────────────────────────────
# Headers that mimic a real browser visiting gmraerocity.com
# ─────────────────────────────────────────────────────
FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.gmraerocity.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ─────────────────────────────────────────────────────
# Curated image index — keyword → list of image dicts
#
# PRIORITY TIERS (controls which images show up first):
#   priority=10  →  specific named venue (highest)
#   priority=5   →  sub-category (e.g. "nightlife", "spa")
#   priority=1   →  generic fallback (e.g. "aerocity", "hotel")
#
# All image URLs are sourced directly from gmraerocity.com
# ─────────────────────────────────────────────────────
CURATED_IMAGE_INDEX: dict[str, dict] = {

    # ══════════════════════════════════════════════════
    # SPECIFIC VENUES — priority 10
    # ══════════════════════════════════════════════════

    # ── Cafés & Coffee ──────────────────────────────
    "blue tokai": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/blue-tokai-banner.jpg",
             "alt": "Blue Tokai Coffee Roasters at The Square, GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/bluetokai-grid-1.jpg",
             "alt": "Blue Tokai specialty coffee at GMR Aerocity"},
        ]
    },

    # ── Restaurants / Dining ────────────────────────
    "cafe delhi heights": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/cafe-delhi-heights-banner.jpg",
             "alt": "Café Delhi Heights — all-day dining at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/casual-dining-1.webp",
             "alt": "Casual dining at Café Delhi Heights, GMR Aerocity"},
        ]
    },
    "l'osteria bella": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/italian-food-1.webp",
             "alt": "L'Osteria Bella — Italian fine dining at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/italian-food-2.webp",
             "alt": "Authentic Italian cuisine at L'Osteria Bella, GMR Aerocity"},
        ]
    },
    "losteria": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/italian-food-1.webp",
             "alt": "L'Osteria Bella — Italian dining at GMR Aerocity"},
        ]
    },
    "one8 commune": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/one%208%201.jpg",
             "alt": "One8 Commune — vibrant dining and cocktails at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/inside%20page%20one%208%206.jpg",
             "alt": "One8 Commune interior, GMR Aerocity"},
        ]
    },

    # ── Nightlife / Bars / Clubs ─────────────────────
    "toy room": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/2%20banner%20Toy%20Room.jpg",
             "alt": "Toy Room nightclub at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/Toy%20Room1.jpg",
             "alt": "Toy Room — exclusive nightclub inside Aloft, Aerocity"},
        ]
    },
    "juniper bar": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/juniper-bar-banner.jpg",
             "alt": "Juniper Bar — India's first gin bar at Andaz, GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/juniper1.jpg",
             "alt": "Craft cocktails and gin infusions at Juniper Bar, Aerocity"},
        ]
    },
    "tara rooftop": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%20roseate.jpg",
             "alt": "Tara Rooftop Lounge at The Roseate, GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%20roseate%20image%201.jpg",
             "alt": "Tara Roseate — open rooftop lounge with Delhi skyline views"},
        ]
    },
    "tara roseate": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%20roseate.jpg",
             "alt": "Tara Roseate Rooftop Lounge at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%202.jpg",
             "alt": "Cocktails and views at Tara, Roseate House"},
        ]
    },
    "liv bar": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/liv%20bar%20banner.jpg",
             "alt": "LIV Bar — chic lounge and nightlife at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/liv1.jpg",
             "alt": "LIV Bar interior at GMR Aerocity"},
        ]
    },
    "underdoggs": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/Images_under%20doggs%20banner.jpg",
             "alt": "Underdoggs sports bar at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/UnderDogs1.jpg",
             "alt": "Underdoggs — craft beer, sports and live music at Aerocity"},
        ]
    },

    # ── Spas & Wellness ─────────────────────────────
    "aheli spa": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/spa-banner-a-2.jpg",
             "alt": "Aheli Spa at Roseate House, GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/aheli1.jpg",
             "alt": "Serene therapy rooms at Aheli Spa, Aerocity"},
        ]
    },
    "zivaya spa": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/relax.webp",
             "alt": "Zivaya Spa at Aloft, GMR Aerocity"},
        ]
    },

    # ── Event Venues ─────────────────────────────────
    "utsav": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/raga-reimagined.webp",
             "alt": "Live event at UTSAV amphitheatre, GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/square.webp",
             "alt": "UTSAV — GMR Aerocity's purpose-built event venue at The Square"},
        ]
    },
    "the square": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/square.webp",
             "alt": "The Square — integrated urban plaza at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/shoppingbanner.jpg",
             "alt": "Shopping and lifestyle at The Square, GMR Aerocity"},
        ]
    },
    "the collective": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/the-collective-summer-edit.webp",
             "alt": "The Collective Summer Edit — indie market at The Square"},
        ]
    },
    "cricket ka capital": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/CRICKET-KA-CAPITAL-2.webp",
             "alt": "Cricket Ka Capital — IPL Fan Zone at GMR Aerocity"},
        ]
    },
    "raga reimagined": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/raga-reimagined.webp",
             "alt": "Raga Reimagined — live Indo-Western music at UTSAV, Aerocity"},
        ]
    },

    # ── Hotels ───────────────────────────────────────
    "jw marriott": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/stay-web.webp",
             "alt": "JW Marriott — luxury hotel and conference venue at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "JW Marriott Grand Crystal Ballroom, GMR Aerocity"},
        ]
    },
    "pullman": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/stay-web.webp",
             "alt": "Pullman Hotel — Peacock Ballroom and conference spaces at Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "Pullman conference facilities at GMR Aerocity"},
        ]
    },
    "andaz": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/stay-web.webp",
             "alt": "Andaz Delhi — creative hotel and event spaces at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "Andaz Studios — design-forward event spaces at Aerocity"},
        ]
    },
    "roseate house": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/stay-web.webp",
             "alt": "Roseate House — boutique luxury hotel at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/aheli1.jpg",
             "alt": "Roseate House premium hospitality at GMR Aerocity"},
        ]
    },
    "holiday inn": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/stay.webp",
             "alt": "Holiday Inn — full-service hotel at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "Holiday Inn conference facilities at GMR Aerocity"},
        ]
    },
    "aloft": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/stay.webp",
             "alt": "Aloft Hotel — tech-forward event spaces at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "Aloft Hotel meeting rooms at GMR Aerocity"},
        ]
    },
    "lemon tree": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/stay.webp",
             "alt": "Lemon Tree Premier Hotel at GMR Aerocity"},
        ]
    },
    "ibis": {
        "priority": 10,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/stay.webp",
             "alt": "Ibis Hotel at GMR Aerocity"},
        ]
    },

    # ══════════════════════════════════════════════════
    # SUB-CATEGORY KEYWORDS — priority 5
    # ══════════════════════════════════════════════════

    "nightlife": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/2%20banner%20Toy%20Room.jpg",
             "alt": "Nightlife at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%20roseate.jpg",
             "alt": "Bars and lounges at GMR Aerocity"},
        ]
    },
    "lounge": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%20roseate.jpg",
             "alt": "Rooftop lounge at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/liv%20bar%20banner.jpg",
             "alt": "LIV Bar lounge at GMR Aerocity"},
        ]
    },
    "cocktails": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/tara%20roseate.jpg",
             "alt": "Cocktails at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/liv1.jpg",
             "alt": "Bar menu at GMR Aerocity"},
        ]
    },
    "spa": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/spa-banner-a-2.jpg",
             "alt": "Spa and wellness at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/aheli1.jpg",
             "alt": "Aheli Spa therapy rooms at GMR Aerocity"},
        ]
    },
    "relax": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/relax.webp",
             "alt": "Leisure and wellness at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/spa-banner-a-2.jpg",
             "alt": "Relaxation at GMR Aerocity spas"},
        ]
    },
    "events": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/CRICKET-KA-CAPITAL-2.webp",
             "alt": "Cricket Ka Capital IPL event at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/the-collective-summer-edit.webp",
             "alt": "The Collective Summer Edit at The Square"},
        ]
    },
    "weekend": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/the-collective-summer-edit.webp",
             "alt": "Weekend events at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/CRICKET-KA-CAPITAL-2.webp",
             "alt": "IPL weekend at GMR Aerocity"},
        ]
    },
    "cricket": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/CRICKET-KA-CAPITAL-2.webp",
             "alt": "Cricket Ka Capital — IPL Fan Zone at GMR Aerocity"},
        ]
    },
    "ipl": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eventscalender/CRICKET-KA-CAPITAL-2.webp",
             "alt": "IPL Fan Zone at GMR Aerocity"},
        ]
    },
    "conference": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "Conference and MICE facilities at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/work.webp",
             "alt": "Corporate meeting venues at GMR Aerocity"},
        ]
    },
    "mice": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "MICE and business events at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/work.webp",
             "alt": "Premium event infrastructure at GMR Aerocity"},
        ]
    },
    "meeting": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/businessbanner.jpg",
             "alt": "Meeting rooms at GMR Aerocity"},
        ]
    },
    "dining": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/eat-drink-web.webp",
             "alt": "Dining at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/fine-dining-1.webp",
             "alt": "Fine dining restaurants at GMR Aerocity"},
        ]
    },
    "brunch": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/casual-dining-1.webp",
             "alt": "Brunch at GMR Aerocity"},
        ]
    },
    "coffee": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/outlets/blue-tokai-banner.jpg",
             "alt": "Specialty coffee at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/cafes-1.webp",
             "alt": "Cafes at GMR Aerocity"},
        ]
    },
    "italian": {
        "priority": 5,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/italian-food-1.webp",
             "alt": "Italian dining at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/eat-drink/italian-food-2.webp",
             "alt": "Italian cuisine at GMR Aerocity"},
        ]
    },

    # ══════════════════════════════════════════════════
    # GENERIC FALLBACK KEYWORDS — priority 1
    # ══════════════════════════════════════════════════

    "aerocity": {
        "priority": 1,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/experience-pulse-banner-image.webp",
             "alt": "Vibrant lifestyle experiences at GMR Aerocity"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/square.webp",
             "alt": "The Square at GMR Aerocity"},
        ]
    },
    "hotel": {
        "priority": 1,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/stay-web.webp",
             "alt": "Hotels at GMR Aerocity Delhi"},
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/stay.webp",
             "alt": "Luxury stay options at GMR Aerocity"},
        ]
    },
    "stay": {
        "priority": 1,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/banner/stay-web.webp",
             "alt": "World-class stay at GMR Aerocity"},
        ]
    },
    "airport": {
        "priority": 1,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/aerocityone.jpg",
             "alt": "GMR Aerocity near Delhi International Airport T3"},
        ]
    },
    "general": {
        "priority": 1,
        "images": [
            {"url": "https://www.gmraerocity.com/wp-content/themes/gmr-aerocity/images/experience-pulse-banner-image.webp",
             "alt": "Vibrant lifestyle experiences at GMR Aerocity"},
        ]
    },
}


# ─────────────────────────────────────────────────────
# Base64 fetcher — cached by Streamlit so each URL is
# only downloaded once per deployment
# ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def fetch_image_as_base64(url: str) -> Optional[str]:
    """
    Downloads an image server-side with a proper Referer header and
    returns it as a base64 data URI. Returns None on any failure.
    Streamlit caches the result so the URL is only fetched once.
    """
    try:
        resp = requests.get(url, headers=FETCH_HEADERS, timeout=10)
        if resp.status_code != 200:
            return None

        url_lower = url.lower()
        if "webp" in url_lower:
            content_type = "image/webp"
        elif "png" in url_lower:
            content_type = "image/png"
        elif "svg" in url_lower:
            content_type = "image/svg+xml"
        else:
            content_type = "image/jpeg"

        b64 = base64.b64encode(resp.content).decode("utf-8")
        return f"data:{content_type};base64,{b64}"
    except Exception:
        return None


# ─────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────

def get_images_for_answer(answer_text: str, category: str = "", max_images: int = 2) -> list[dict]:
    """
    Given an answer string and category, returns up to `max_images`
    relevant image dicts each containing {url, alt, data_uri}.

    MATCHING LOGIC:
      - Each keyword is checked against the combined answer+category text.
      - Score = (number of occurrences) × (keyword priority tier).
        Priority 10 (venue names) therefore always outrank priority 1
        (generic words like "aerocity") even if the generic word appears
        many more times in the text.
      - Results are deduplicated by URL.

    data_uri is a base64-encoded image ready for use in <img src="...">
    so it renders correctly inside Streamlit's iframe without CDN blocks.
    """
    text = (answer_text + " " + category).lower()

    # Score every keyword entry
    scored: list[tuple[float, list[dict]]] = []
    for keyword, entry in CURATED_IMAGE_INDEX.items():
        count = text.count(keyword)
        if count > 0:
            weighted_score = count * entry["priority"]
            scored.append((weighted_score, entry["images"]))

    # Sort highest score first
    scored.sort(key=lambda x: x[0], reverse=True)

    seen_urls: set[str] = set()
    candidates: list[dict] = []

    for _, images in scored:
        for img in images:
            if img["url"] not in seen_urls:
                seen_urls.add(img["url"])
                candidates.append(img)
            if len(candidates) >= max_images:
                break
        if len(candidates) >= max_images:
            break

    # Fetch each candidate as base64
    resolved = []
    for img in candidates:
        data_uri = fetch_image_as_base64(img["url"])
        if data_uri:
            resolved.append({**img, "data_uri": data_uri})

    return resolved