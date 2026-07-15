import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month:02d}/{day:02d}"


def fetch_onthisday(month=None, day=None):
    now = datetime.now()
    month = month or now.month
    day = day or now.day

    url = WIKIPEDIA_API.format(month=month, day=day)
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "NewsBot/1.0"})
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        selected = []
        for e in events:
            text = e.get("text", "")
            year = e.get("year", "")
            pages = e.get("pages", [])
            image_url = None
            for p in pages:
                thumb = p.get("thumbnail", {})
                if thumb:
                    source = thumb.get("source", "")
                    if source and source.startswith("http"):
                        image_url = source
                        break

            selected.append({
                "year": year,
                "text": text,
                "urlToImage": image_url,
                "title": f"In {year}: {text}",
                "description": f"On this day in history — {year}: {text}",
                "url": None,
                "publishedAt": None,
                "source": {"name": "History"},
            })

        return selected
    except Exception as e:
        logger.error("Wikipedia onthisday fetch failed: %s", e)
        return []
