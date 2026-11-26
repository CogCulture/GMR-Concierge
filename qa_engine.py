"""Answers typed questions using website_info.txt and the CSV files in the sheets folder."""
import csv
import glob
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote_plus

from google import genai
from google.genai import types

from config import (
    BASE_DIR, QA_DATA_FILE, HISTORY_LIMIT, PROTOTYPE_OFFERS,
    OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, GEMINI_MODEL,
)

INFO_FILE = os.path.join(BASE_DIR, "website_info.txt")

RULES = """You are the GMR Aerocity concierge. Be warm, helpful and informative.
Use ONLY the INFORMATION below for facts. Never invent timings, prices, offers, phone numbers or links.

Decide which case the question is:
1. About GMR Aerocity and answered in the INFORMATION: answer it with the matching link.
2. A booking or reservation: say you cannot book, then give the phone number or booking link from the INFORMATION.
3. About GMR Aerocity but not answered in the INFORMATION: say "Sorry, I don't have that detail yet." Add a relevant link or contact only if one is in the INFORMATION.
4. Not about GMR Aerocity (for example other places, travel plans, news, general knowledge): say "I can only help with GMR Aerocity events, restaurants and facilities."
Greetings and thanks: reply briefly.
If a question is partly outside Aerocity, answer only the Aerocity part.
Planning free time or a day at Aerocity is in scope: suggest only places and events found in the INFORMATION.
Use the earlier messages to understand follow-up questions such as "where is it?".

FORMAT. Reply with one JSON object only, no other text, exactly in this shape:
{"intro":"", "sections":[{"emoji":"", "heading":"", "place":"", "description":"", "location":"", "timing":"", "phone":"", "link_label":"", "link_url":""}], "tip":""}
The program turns the JSON into the screen, so never put links, "|", bullet points, markdown or emojis inside the text values.
- intro: one or two warm sentences that speak to the person's situation (time, group size, mood).
- sections: up to 4, in time order for a plan. A question about one named place or about food, dinner, lunch or drinks always gets sections, and Cafe Delhi Heights is one of the options to include when it fits. Use an empty list for a single-fact question (where, when, how much, phone) and give the answer in intro as two to four helpful sentences, adding "link_label" and "link_url" at the top level of the JSON only if a link helps.
- emoji: one small emoji that suits the section. heading: a short phrase saying why this stop, for example "Start with coffee".
- place: the specific place or event, not a general section such as "Eat & Drink". Use a general section only if nothing specific fits.
- description: two or three sentences on what it offers (name specific dishes, drinks, shops or activities from the INFORMATION) and why it suits this question.
- location, timing, phone: only facts the INFORMATION gives, otherwise an empty string. For an event put the date and time in timing.
- link_label is the purpose: "Book a table", "RSVP", "View details" or "Get directions". link_url is the place's own link or the LINK of the website page that mentions it, otherwise an empty string. For "Get directions" leave link_url empty.
- tip: one closing line with a useful tip or next step.
Never invent offers, discounts, timings, phone numbers or links, and never write about any offer, discount or deal yourself, even if the INFORMATION mentions one. The program adds the only offer.

Events:
- Compare each event date with today's date.
- For "upcoming", "today" or "this weekend", list only events that have not ended.
- Never show an event that has ended as upcoming. If asked about a past event, give its date and say it has ended.
- List past events only when the user asks what already happened, and label them as past.
- If there is no matching upcoming event, say so.

If the SHEET and the WEBSITE disagree, use the SHEET."""


def today() -> date:
    """Today's date in India."""
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


# The 8 FAQ cards on the home screen: title, subtitle, icon, question, follow-ups
FAQS = [
    ("Plan your time", "4 hours between meetings", "calendar_clock",
     "I have 4 hours between meetings. What can I do at Aerocity?",
     ["Where can I get coffee?", "Where can I park?"]),
    ("What's happening", "This weekend", "calendar",
     "Is there anything happening this weekend at Aerocity?",
     ["Where is it and what time?", "How do I RSVP?"]),
    ("Meetings & MICE", "Conference facilities", "users",
     "What MICE and conference facilities are available at Aerocity?",
     ["Which fits 100 people?", "How do I book?"]),
    ("Just landed", "A full-day itinerary", "pin",
     "I just landed in Delhi. Can you plan my full day?",
     ["Where should I have dinner?", "How do I book a hotel room?"]),
    ("Client coffee", "Beyond a hotel lobby", "coffee",
     "Where can I take a client for coffee that isn't a hotel lobby?",
     ["Where is it?", "Where can I park?"]),
    ("Drinks & music", "Plans for tonight", "music",
     "Where can I go for drinks and good music tonight?",
     ["Where can I park?", "What events are coming up?"]),
    ("100-person event", "Conference venues", "users",
     "What conference venues are available for a 100-person event?",
     ["How do I book?", "Where can I park?"]),
    ("Upcoming events", "Where to attend them", "ticket",
     "Where can I attend upcoming events in Aerocity?",
     ["Where is it and what time?", "How do I RSVP?"]),
]


def _pill(label: str) -> dict:
    """A follow-up button with an icon that suits its words."""
    words = label.lower()
    for key, icon in (("park", "car"), ("coffee", "coffee"), ("event", "calendar"),
                      ("time", "calendar"), ("rsvp", "calendar"), ("drink", "music")):
        if key in words:
            return {"icon": icon, "label": label}
    return {"icon": "pin" if words.startswith("where") else "info", "label": label}


DEFAULT_FOLLOWUPS = [_pill("Where can I get coffee?"), _pill("Where can I park?")]


def load_qa_data() -> dict:
    try:
        with open(QA_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def get_bot_config() -> dict:
    return load_qa_data().get("bot_config", {})


def get_suggested_questions(limit: int = 8) -> list[dict]:
    return [
        {"title": title, "subtitle": sub, "icon_type": icon, "question": question}
        for title, sub, icon, question, _ in FAQS[:limit]
    ]


def _followups(question: str, history: list) -> list:
    """Follow-ups belong to the most recent FAQ that was asked."""
    asked = [m["content"] for m in history if m["role"] == "user"] + [question]
    chips = {faq[3]: faq[4] for faq in FAQS}
    for text in reversed(asked):
        if text in chips:
            # Do not offer the question that was just asked
            return [_pill(c) for c in chips[text] if c != question] or DEFAULT_FOLLOWUPS
    return [p for p in DEFAULT_FOLLOWUPS if p["label"] != question]


URL = re.compile(r"^(?:https?://|tel:|mailto:)[^\s)]+$")
RAW_URL = re.compile(r"(?:https?://|www\.)\S+|\b(?:tel|mailto):\S+", re.I)
EMPTY = {"", "none", "null", "n/a", "na", "nil", "-", "--", "not available", "unknown"}
MAX_SECTIONS = 4
RETRY = "Sorry, I couldn't put that answer together. Please try again."


def _maps_link(place: str) -> str:
    """A Google Maps search for the place, built here so it is never invented."""
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{place} Aerocity Delhi")


def _text(value) -> str:
    """Plain, single-paragraph text. Links, markup and '|' never reach the screen."""
    if not isinstance(value, str):
        return ""
    value = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", value)  # [name](link) -> name
    value = RAW_URL.sub("", value)
    value = re.sub(r"[*_#`|\[\]<>]", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ,;:-")
    return "" if value.lower() in EMPTY else value


def _button(label, url, place: str) -> str:
    """One gold button line, or nothing if there is no usable link."""
    label, url = _text(label), url.strip() if isinstance(url, str) else ""
    if not URL.match(url):
        if "direction" not in label.lower() or not place:
            return ""
        url = _maps_link(place)
    if not label:
        label = "Call now" if url.startswith("tel:") else "View details"
    return f"[{label}]({url})"


OFFER_NOTE = "For prototype demonstration only. Not a real or valid offer."


def _simple(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _prototype_offer(place: str, shown: set) -> str:
    """The sample offer for this place, added by the program once per answer. Empty for any other place."""
    for name, offer in PROTOTYPE_OFFERS.items():
        if name not in shown and _simple(name) and _simple(name) in _simple(place):
            shown.add(name)
            return f"🏷️ Sample offer: {_text(offer)}\n{OFFER_NOTE}"
    return ""


def _section(item, shown: set) -> str:
    if not isinstance(item, dict):
        return ""
    place = _text(item.get("place"))
    if not place:
        return ""
    heading = f"{_text(item.get('emoji'))} {_text(item.get('heading'))}".strip()
    blocks = [f"**{heading}**"] if heading else []
    about = _text(item.get("description"))
    blocks.append(f"**{place}**\n{about}" if about else f"**{place}**")
    facts = [f"{icon} {_text(item.get(key))}" for key, icon in
             (("location", "📍"), ("timing", "🕒"), ("phone", "📞")) if _text(item.get(key))]
    if facts:
        blocks.append("\n".join(facts))
    offer = _prototype_offer(place, shown)
    if offer:
        blocks.append(offer)
    button = _button(item.get("link_label"), item.get("link_url"), place)
    if button:
        blocks.append(button)
    return "\n\n".join(blocks)


def _layout(data) -> str:
    """Builds the on-screen answer from the JSON the AI returned. Returns "" if it cannot be read."""
    if not isinstance(data, dict):
        return ""
    sections = data.get("sections")
    blocks = [_text(data.get("intro"))]
    shown = set()  # offers already added, so each shows once per answer
    for item in (sections if isinstance(sections, list) else [])[:MAX_SECTIONS]:
        blocks.append(_section(item, shown))
    if not sections:
        blocks.append(_prototype_offer(blocks[0], shown))  # the answer names a place but has no section
        blocks.append(_button(data.get("link_label"), data.get("link_url"), ""))
    blocks.append(_text(data.get("tip")))
    return "\n\n".join(b for b in blocks if b)


def parse_answer(raw: str) -> str:
    """Reads the AI's JSON reply and returns the text to display, or the polite retry message."""
    try:
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip())
        text = _layout(json.loads(raw))
    except ValueError:
        text = ""
    return text or RETRY


def load_info() -> str:
    """Joins the website text and every sheet into one block of text."""
    parts = []
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            parts.append("WEBSITE:\n" + f.read())
    for file in sorted(glob.glob(os.path.join(BASE_DIR, "sheets", "*.csv"))):
        with open(file, "r", encoding="utf-8-sig", newline="") as f:
            # The first row is read as the column names
            rows = [
                "; ".join(f"{name}: {value}" for name, value in row.items() if name and value)
                for row in csv.DictReader(f)
            ]
        parts.append(f"SHEET ({os.path.basename(file)}):\n" + "\n".join(r for r in rows if r))
    return "\n\n".join(parts)


def _reply(text: str, followups: list = None) -> dict:
    return {"answer": text, "followups": followups or DEFAULT_FOLLOWUPS}


def ask_gpt(instructions: str, messages: list) -> str:
    from openai import OpenAI  # loaded here, so it is only needed when GPT is used

    client = OpenAI(api_key=OPENAI_API_KEY)
    # JSON mode needs the word JSON in the messages themselves, not only in the instructions
    messages = messages[:-1] + [{**messages[-1], "content": messages[-1]["content"] + "\n\n(Reply with the JSON object described in FORMAT.)"}]
    settings = dict(model=OPENAI_MODEL, instructions=instructions, input=messages,
                    reasoning={"effort": "low"})  # quicker answers
    try:
        response = client.responses.create(**settings, text={"format": {"type": "json_object"}})
    except Exception as e:
        # If JSON mode is refused, ask again without it; the reply is still read as JSON
        print("JSON mode failed, retrying without it:", e)
        response = client.responses.create(**settings)
    return response.output_text


def ask_gemini(instructions: str, messages: list) -> str:
    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
    ]
    response = genai.Client(api_key=GEMINI_API_KEY).models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=instructions, response_mime_type="application/json"),
    )
    return response.text


def find_best_answer(question: str, history: list = None) -> dict:
    if not (OPENAI_API_KEY or GEMINI_API_KEY):
        return _reply("The chatbot is not set up yet: the API key is missing.")
    try:
        instructions = f"{RULES}\nToday's date: {today():%A, %d %B %Y}\n\nINFORMATION:\n{load_info()}"
        # Recent messages plus the new question, so follow-ups make sense
        recent = (history or [])[-HISTORY_LIMIT:] + [{"role": "user", "content": question}]
        messages = []
        for m in recent:
            messages.append({"role": m["role"], "content": m["content"].strip()})
        ask = ask_gpt if OPENAI_API_KEY else ask_gemini
        answer = parse_answer(ask(instructions, messages))
        return _reply(answer, _followups(question, history or []))
    except Exception as e:
        print("Chatbot error:", e)  # details stay in the terminal, not on screen
        return _reply("Sorry, something went wrong. Please try again.")
