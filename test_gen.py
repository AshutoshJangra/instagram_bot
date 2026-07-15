import logging
import sys

from PIL import Image, ImageDraw, ImageFont

import config
from image_gen import create_post_image

logging.basicConfig(level=logging.INFO, format="%(message)s")

sample_article = {
    "title": "Apple Unveils New AI Features That Will Change Everything You Know About Your iPhone",
    "urlToImage": "https://picsum.photos/seed/test/1080/1080",
    "url": "https://example.com",
    "description": "Apple announced groundbreaking AI features for iPhone at WWDC 2026.",
    "source": {"name": "TechCrunch"},
}

def main():
    print("Generating test image (tech)...")
    path = create_post_image(sample_article, headline=None, post_type="tech")
    print(f"Saved: {path}")

    print("\nGenerating test image (history)...")
    sample_article["title"] = "The Day the Berlin Wall Fell and Changed the Course of History Forever"
    path2 = create_post_image(sample_article, headline=None, post_type="history")
    print(f"Saved: {path2}")

    print("\nDone. Open the images to preview.")

if __name__ == "__main__":
    main()
