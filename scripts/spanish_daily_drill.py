#!/usr/bin/env python3
"""
Daily Spanish drill — sent to William via Telegram at 3:30pm weekdays.
Phrases rotate through categories relevant to his life.
"""
import os, sys, json, random, requests
from datetime import date
sys.path.insert(0, '/home/clawdbot/dev-sandbox')
from dotenv import load_dotenv
load_dotenv('/home/clawdbot/dev-sandbox/.env')

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID')

DRILLS = [
    # Grocery / butcher
    ("¿Tiene caldo de huesos?",        "Do you have bone broth?",             "At the butcher — point and ask"),
    ("¿Cuánto cuesta el kilo?",        "How much per kilo?",                  "Price check on meat"),
    ("Quiero medio kilo de hígado.",   "I want half a kilo of liver.",        "Ordering liver at Mexican Star"),
    ("¿Tiene corazón de res?",         "Do you have beef heart?",             "Asking for heart"),
    ("¿Tiene menudo?",                 "Do you have tripe?",                  "Tripe — they'll definitely have it"),
    ("Dame dos libras de molida.",     "Give me two pounds of ground beef.",  "Quick order"),
    # Gym
    ("¿Cuántas series te faltan?",     "How many sets do you have left?",     "Gym — asking to work in"),
    ("¿Puedo usar esto contigo?",      "Can I work in with you?",             "Sharing equipment"),
    ("Estoy calentando.",              "I'm warming up.",                     "Simple gym phrase"),
    # Work / general
    ("Buenos días, ¿cómo le va?",     "Good morning, how's it going?",       "Greeting a coworker"),
    ("¿Dónde está la herramienta?",   "Where is the tool?",                  "Useful on any job site"),
    ("No entiendo, ¿puede repetir?",  "I don't understand, can you repeat?", "Essential survival phrase"),
    ("Poco a poco.",                   "Little by little.",                   "Spanish mindset — tattoo this"),
    ("¿A qué hora terminas?",         "What time do you finish?",            "Scheduling with coworkers"),
    # Around town
    ("¿Dónde está el baño?",          "Where's the bathroom?",               "Universal"),
    ("La cuenta, por favor.",          "The check, please.",                  "Restaurants"),
    ("¿Habla inglés?",                "Do you speak English?",               "Backup when stuck"),
]

# Pick based on day of year so it rotates predictably
idx = date.today().timetuple().tm_yday % len(DRILLS)
phrase, translation, context = DRILLS[idx]

msg = (
    f"🇪🇸 *Spanish Drill — {date.today().strftime('%b %d')}*\n\n"
    f"*{phrase}*\n"
    f"_{translation}_\n\n"
    f"📍 Context: {context}\n\n"
    f"Reply with it in a sentence to practice, or just save it."
)

resp = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
)
print(f"Sent drill #{idx}: {phrase} — status {resp.status_code}")
