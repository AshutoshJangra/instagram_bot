import logging
import os
import random
import sys
from datetime import datetime

import config
from image_gen import create_post_image
from insta_poster import check_publishing_limit, post_to_instagram
from persona_writer import generate_post
from rss_fetcher import fetch_tech_news

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler(),
    ],
)
logger = logging.getLogger("main")

STATE_FILE = config.BASE_DIR / "posted_articles.json"


def _load_posted():
    import json
    try:
        with open(STATE_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_posted(ids):
    import json
    ids_list = list(ids)[-config.POSTED_ARTICLES_LIMIT:]
    with open(STATE_FILE, "w") as f:
        json.dump(ids_list, f)


def _mark_posted(identifier):
    posted = _load_posted()
    posted.add(identifier)
    _save_posted(posted)


def _pick_article(articles, posted):
    random.shuffle(articles)
    for a in articles:
        key = a.get("url") or a.get("title", "")
        if key not in posted:
            return a, key
    if articles:
        key = articles[0].get("url") or articles[0].get("title", "")
        return articles[0], key
    return None, None


def main():
    print("=" * 60)
    print(f"  The Dispatch — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    api_key = config.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY not configured.")
        sys.exit(1)

    posted = _load_posted()

    articles = fetch_tech_news(max_articles=30)
    if not articles:
        print("No articles fetched.")
        return

    posts_to_make = []

    article, art_key = _pick_article(articles, posted)
    if article and art_key:
        posts_to_make.append(("trending", article, art_key))
        print(f"\n1: {article['title'][:70]}")

    article2, art_key2 = _pick_article(articles, posted)
    if article2 and art_key2 and art_key2 != art_key:
        posts_to_make.append(("trending", article2, art_key2))
        print(f"2: {article2['title'][:70]}")

    if not posts_to_make:
        print("Nothing new to post.")
        return

    remaining = check_publishing_limit()
    if remaining is not None and remaining < 1:
        print("Publishing quota exhausted for today. Skipping.")
        return
    if remaining is not None and remaining < len(posts_to_make):
        print(f"Only {remaining} post(s) remaining. Truncating queue.")
        posts_to_make = posts_to_make[:remaining]

    for post_type, source, key in posts_to_make:
        print(f"\n--- Posting: {post_type.upper()} ---")

        generated = generate_post(
            article_title=source["title"],
            article_description=source.get("description", ""),
            api_key=api_key,
        )

        headline = generated["headline"]
        caption_body = generated["caption"] + "\n\n" + source["title"]
        print(f"Headline: {headline}")
        print(f"Caption:  {caption_body[:100]}...")

        image_path = create_post_image(source, headline=headline, post_type=post_type)
        if not image_path:
            print(f"Image generation failed. Skipping.")
            continue
        print(f"Image:   {image_path}")

        success = post_to_instagram(source, headline, image_path, caption_body=caption_body)
        if success:
            _mark_posted(key)
            print(f"Posted!")
        else:
            print(f"Failed.")

    print("\nDone.")


if __name__ == "__main__":
    main()
