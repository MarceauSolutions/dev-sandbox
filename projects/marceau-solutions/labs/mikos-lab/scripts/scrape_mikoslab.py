#!/usr/bin/env python3
"""
Miko's Lab Telegram Channel Scraper
Scrapes public content from t.me/s/mikoslab
"""

import os
import re
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://t.me/s/mikoslab"
PROJECT_DIR = Path(__file__).parent.parent
POSTS_DIR = PROJECT_DIR / "posts"
ASSETS_DIR = PROJECT_DIR / "assets"
STATE_FILE = PROJECT_DIR / "sync_state.json"

def load_state() -> Dict:
    """Load sync state from file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_sync": None, "seen_hashes": []}

def save_state(state: Dict):
    """Save sync state to file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def fetch_channel_page(before: Optional[int] = None) -> str:
    """Fetch channel page HTML."""
    url = BASE_URL
    if before:
        url = f"{BASE_URL}?before={before}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def parse_messages(html: str) -> List[Dict]:
    """Parse messages from channel HTML."""
    soup = BeautifulSoup(html, "html.parser")
    messages = []
    
    for widget in soup.find_all("div", class_="tgme_widget_message"):
        msg = {}
        
        # Get message ID
        msg_id = widget.get("data-post", "")
        if "/" in msg_id:
            msg["id"] = msg_id.split("/")[-1]
        
        # Get date
        date_elem = widget.find("time")
        if date_elem:
            msg["date"] = date_elem.get("datetime", "")
        
        # Get text content
        text_elem = widget.find("div", class_="tgme_widget_message_text")
        if text_elem:
            msg["text"] = text_elem.get_text(strip=True)
            msg["html"] = str(text_elem)
        
        # Get images
        photos = []
        for photo in widget.find_all("a", class_="tgme_widget_message_photo_wrap"):
            style = photo.get("style", "")
            match = re.search(r"url\('([^']+)'\)", style)
            if match:
                photos.append(match.group(1))
        msg["photos"] = photos
        
        # Get videos
        videos = []
        for video in widget.find_all("video"):
            src = video.get("src")
            if src:
                videos.append(src)
        msg["videos"] = videos
        
        # Get documents/files
        docs = []
        for doc in widget.find_all("a", class_="tgme_widget_message_document_wrap"):
            doc_title = doc.find("div", class_="tgme_widget_message_document_title")
            if doc_title:
                docs.append({
                    "title": doc_title.get_text(strip=True),
                    "url": doc.get("href", "")
                })
        msg["documents"] = docs
        
        # Get links
        links = []
        if text_elem:
            for a in text_elem.find_all("a"):
                href = a.get("href", "")
                if href and not href.startswith("tg://"):
                    links.append({"text": a.get_text(strip=True), "url": href})
        msg["links"] = links
        
        if msg.get("text") or msg.get("photos") or msg.get("videos") or msg.get("documents"):
            # Create hash for dedup
            content = f"{msg.get('text', '')}{msg.get('photos', [])}{msg.get('documents', [])}"
            msg["hash"] = hashlib.md5(content.encode()).hexdigest()[:12]
            messages.append(msg)
    
    return messages

def scrape_all_messages(max_pages: int = 10) -> List[Dict]:
    """Scrape all messages from channel."""
    all_messages = []
    seen_ids = set()
    
    html = fetch_channel_page()
    messages = parse_messages(html)
    
    for msg in messages:
        if msg.get("id") and msg["id"] not in seen_ids:
            seen_ids.add(msg["id"])
            all_messages.append(msg)
    
    print(f"Scraped {len(all_messages)} messages from Miko's Lab")
    return all_messages

def save_messages(messages: List[Dict]):
    """Save messages to JSON file."""
    POSTS_DIR.mkdir(exist_ok=True)
    
    output_file = POSTS_DIR / f"mikoslab_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(messages, f, indent=2)
    
    # Also save latest
    latest_file = POSTS_DIR / "latest.json"
    with open(latest_file, "w") as f:
        json.dump(messages, f, indent=2)
    
    print(f"Saved {len(messages)} messages to {output_file}")
    return output_file

def generate_markdown_summary(messages: List[Dict]) -> str:
    """Generate markdown summary of messages."""
    md = f"# Miko's Lab Channel Summary\n\n"
    md += f"*Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    md += f"**Total Posts:** {len(messages)}\n\n---\n\n"
    
    for msg in messages:
        if msg.get("text"):
            md += f"### Post {msg.get('id', 'unknown')}\n"
            md += f"*{msg.get('date', 'unknown date')}*\n\n"
            md += f"{msg['text'][:500]}{'...' if len(msg['text']) > 500 else ''}\n\n"
            
            if msg.get("links"):
                md += "**Links:**\n"
                for link in msg["links"]:
                    md += f"- [{link['text']}]({link['url']})\n"
            
            if msg.get("documents"):
                md += "**Documents:**\n"
                for doc in msg["documents"]:
                    md += f"- {doc['title']}\n"
            
            md += "\n---\n\n"
    
    return md

def main():
    """Main scraper function."""
    print("Starting Miko's Lab scraper...")
    
    # Load state
    state = load_state()
    
    # Scrape messages
    messages = scrape_all_messages()
    
    # Filter new messages
    seen_hashes = set(state.get("seen_hashes", []))
    new_messages = [m for m in messages if m.get("hash") not in seen_hashes]
    
    print(f"Found {len(new_messages)} new messages")
    
    if new_messages:
        # Save messages
        save_messages(new_messages)
        
        # Generate summary
        summary = generate_markdown_summary(new_messages)
        summary_file = PROJECT_DIR / "LATEST_POSTS.md"
        with open(summary_file, "w") as f:
            f.write(summary)
        print(f"Summary saved to {summary_file}")
    
    # Update state
    state["last_sync"] = datetime.now().isoformat()
    state["seen_hashes"] = list(seen_hashes | {m["hash"] for m in messages if m.get("hash")})
    save_state(state)
    
    print("Scrape complete!")
    return new_messages

if __name__ == "__main__":
    main()
