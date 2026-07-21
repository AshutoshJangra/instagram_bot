import logging
import os
import random
import sys
from datetime import datetime

import config
from insta_poster import check_publishing_limit, post_reel_to_instagram
from video_fetcher import fetch_reel

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


def main():
    print("=" * 60)
    print(f"  Dispatch Reels — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    remaining = check_publishing_limit()
    if remaining is not None and remaining < 1:
        print("Publishing quota exhausted.")
        return

    print("\n--- Fetching trending video ---")
    reel = fetch_reel()
    if not reel:
        print("No video found.")
        return

    video_path = reel["video_path"]
    title = reel["title"]
    source = reel["source"]
    video_id = os.path.basename(video_path).split(".")[0]

    if video_id in _load_posted():
        print(f"Already posted {video_id}")
        return

    print(f"Title:   {title}")
    print(f"Source:  {source}")
    print(f"Video:   {video_path}")

    print("\n--- Posting Reel ---")
    success = post_reel_to_instagram(
        article={"title": title, "source": source},
        rewritten_headline=title,
        video_path=video_path,
    )
    if success:
        _mark_posted(video_id)
        print("Posted!")
    else:
        print("Failed.")

    print("\nDone.")


if __name__ == "__main__":
    main()
