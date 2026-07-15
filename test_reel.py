import logging
import sys
from datetime import datetime

import config
from headline_rewriter import rewrite as rewrite_headline
from image_gen import create_post_image
from insta_poster import post_reel_to_instagram
from news_fetcher import fetch_any_new_article, record_posted
from reel_generator import generate_reel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("test_reel")


def main():
    print("=" * 60)
    print(f"  Insta Reel POC — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    article, category = fetch_any_new_article()
    if not article:
        print("No new articles found.")
        return

    title = article.get("title", "Untitled")
    source = article.get("source", {}).get("name", "News")
    print(f"Article: {title[:80]}")
    print(f"Source:  {source}")
    print(f"Category: {category}")

    rewritten = rewrite_headline(
        headline=title,
        category=category,
        source=source,
        description=article.get("description"),
    )
    print(f"Headline: {rewritten[:100]}")

    image_path = create_post_image(article)
    if not image_path:
        print("ERROR: Image generation failed.")
        return
    print(f"Image:   {image_path}")

    reel_path = generate_reel(
        image_path=image_path,
        headline=rewritten,
        source=source,
        output_path=config.BASE_DIR / "_latest_reel.mp4",
    )
    print(f"Reel:    {reel_path}")

    success = post_reel_to_instagram(article, rewritten, reel_path)
    if success:
        record_posted(article)
        print("Done. Reel published successfully.")
    else:
        print("Reel post failed.")


if __name__ == "__main__":
    main()
