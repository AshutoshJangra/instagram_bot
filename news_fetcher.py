import json
import logging
from datetime import datetime

import requests

import config

logger = logging.getLogger(__name__)

TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
CATEGORY_INDEX_FILE = config.BASE_DIR / "_category_index.txt"


def _load_category_index():
    try:
        with open(CATEGORY_INDEX_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _save_category_index(index):
    with open(CATEGORY_INDEX_FILE, "w") as f:
        f.write(str(index))


def _load_posted_ids():
    try:
        with open(config.STATE_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_posted_ids(ids):
    ids_list = list(ids)[-config.POSTED_ARTICLES_LIMIT:]
    with open(config.STATE_FILE, "w") as f:
        json.dump(ids_list, f)


def _mark_posted(article):
    posted = _load_posted_ids()
    posted.add(article["url"])
    _save_posted_ids(posted)


def rotate_category():
    idx = _load_category_index()
    cat = config.NEWSAPI_CATEGORIES[idx % len(config.NEWSAPI_CATEGORIES)]
    _save_category_index(idx + 1)
    return cat


def fetch_articles(category=None):
    if not category:
        category = rotate_category()

    params = {
        "apiKey": config.NEWSAPI_KEY,
        "pageSize": 10,
        "language": "en",
    }
    params["category"] = category

    logger.info("Fetching top headlines — category: %s", category)
    try:
        resp = requests.get(TOP_HEADLINES_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            logger.warning("NewsAPI returned status: %s", data.get("status"))
            return []
        return data.get("articles", [])
    except requests.RequestException as e:
        logger.error("NewsAPI request failed: %s", e)
        return []


def fetch_any_new_article(max_attempts=3):
    tried_categories = set()
    for _ in range(max_attempts):
        cat = rotate_category()
        if cat in tried_categories:
            continue
        tried_categories.add(cat)

        articles = fetch_articles(cat)
        posted = _load_posted_ids()
        for a in articles:
            if a["url"] not in posted and a.get("title") and a.get("urlToImage"):
                return a, cat

    if tried_categories:
        cat = list(tried_categories)[0]
        articles = fetch_articles(cat)
        for a in articles:
            if a.get("title") and a.get("urlToImage"):
                return a, cat

    return None, None


def record_posted(article):
    _mark_posted(article)
    logger.info("Marked article as posted: %s", article.get("title", "")[:60])
