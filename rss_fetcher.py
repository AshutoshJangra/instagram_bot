import logging
from datetime import datetime

import feedparser
import requests

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://feeds.arstechnica.com/arstechnica/index",
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "https://www.theverge.com/rss/index.xml",
]

USER_AGENT = "Mozilla/5.0 (compatible; NewsBot/1.0)"


import re

IMG_URL = re.compile(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|gif|webp)(?:\?[^\s"\'<>]*)?', re.I)


def _extract_image(entry):
    mc_list = entry.get("media_content") or []
    for mc in mc_list:
        url = mc.get("url", "")
        if url and mc.get("type", "").startswith("image"):
            return url
        if url and IMG_URL.match(url):
            return url

    mt_list = entry.get("media_thumbnail") or []
    for mt in mt_list:
        url = mt.get("url", "")
        if url and IMG_URL.match(url):
            return url

    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and link.get("type", "").startswith("image"):
            return link.get("href", "")

    summary = entry.get("summary", "") or entry.get("description", "")
    urls = IMG_URL.findall(summary)
    if urls:
        return urls[0]
    return None


def _parse_entry(entry):
    title = entry.get("title", "")
    link = entry.get("link", "")
    summary = entry.get("summary", "") or entry.get("description", "")
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    pub_date = datetime(*published[:6]).isoformat() if published else datetime.now().isoformat()

    image_url = _extract_image(entry)

    source_name = ""
    source_tag = getattr(entry, "source", None)
    if source_tag:
        source_name = source_tag.get("title", "")

    feed_title = ""
    if hasattr(entry, "feed") and hasattr(entry.feed, "title"):
        feed_title = entry.feed.title

    return {
        "title": title,
        "url": link,
        "description": summary[:300] if summary else "",
        "urlToImage": image_url,
        "publishedAt": pub_date,
        "source": {"name": source_name or feed_title or "Tech"},
    }


def fetch_tech_news(max_articles=10):
    articles = []
    seen_urls = set()

    for feed_url in RSS_FEEDS:
        try:
            logger.info("Fetching RSS: %s", feed_url.split("/")[2])
            resp = requests.get(feed_url, headers={"User-Agent": USER_AGENT}, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            for entry in feed.entries:
                article = _parse_entry(entry)
                url = article["url"]
                if url and url not in seen_urls and article["title"]:
                    seen_urls.add(url)
                    articles.append(article)
                    if len(articles) >= max_articles:
                        return articles
        except Exception as e:
            logger.warning("RSS feed failed (%s): %s", feed_url.split("/")[2], e)
            continue

    return articles
