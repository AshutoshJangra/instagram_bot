import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
STATE_FILE = BASE_DIR / "posted_articles.json"
LOG_FILE = BASE_DIR / "hourly.log"

_DEFAULTS = dict(
    NEWSAPI_KEY="fa275826b66540b0bdadef40def8318a",
    IMAGE_HOST_KEY="6d207e02198a847aa98d0a2a901485a5",
    GROQ_API_KEY="",
    IG_APP_ID="1747811509564530",
    IG_APP_SECRET="490688bce9cf0888eeecc8da7a8536ce",
    IG_ACCESS_TOKEN="",
    IG_USER_ID="17841420278656916",
)

try:
    from local_config import *
except ImportError:
    pass

for _k, _v in _DEFAULTS.items():
    globals()[_k] = os.getenv(_k, globals().get(_k, _v))

BRAND_NAME = "PROZECTO"
ACCENT_COLOR = (0, 188, 212)
FALLBACK_ACCENT_COLOR = (30, 30, 30)
IMAGE_SIZE = (1080, 1080)
OVERLAY_HEIGHT = 480
HEADLINE_FONT_SIZE = 50
SUB_FONT_SIZE = 16
HEADLINE_MAX_LINES = 6
HEADLINE_CHARS_PER_LINE = 32
POSTED_ARTICLES_LIMIT = 500
NEWSAPI_CATEGORIES = ["general", "technology", "sports", "business", "science", "health", "entertainment"]
