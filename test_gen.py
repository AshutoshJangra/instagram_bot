import logging
import sys

from PIL import Image, ImageDraw, ImageFont

import config
from image_gen import create_post_image

logging.basicConfig(level=logging.INFO, format="%(message)s")

sample_article = {
    "title": "Delhi CM announces free electricity for all households earning under 10 lakh, opposition calls it 'vote bank politics'",
    "urlToImage": "https://picsum.photos/seed/test/1080/1080",
    "url": "https://example.com",
    "description": "The Delhi government has announced a new scheme providing free electricity to households with annual income below Rs 10 lakh, sparking debate ahead of upcoming elections.",
    "source": {"name": "The Hindu"},
}

def main():
    print("Generating test image (trending)...")
    path = create_post_image(sample_article, headline=None, post_type="trending")
    print(f"Saved: {path}")

    print("\nGenerating test image 2 (trending)...")
    sample_article["title"] = "Supreme Court questions Centre over delay in appointment of judges, calls it 'constitutional crisis'"
    path2 = create_post_image(sample_article, headline=None, post_type="trending")
    print(f"Saved: {path2}")

    print("\nDone. Open the images to preview.")

if __name__ == "__main__":
    main()
