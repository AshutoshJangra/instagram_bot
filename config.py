import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
STATE_FILE = BASE_DIR / "posted_articles.json"
LOG_FILE = BASE_DIR / "hourly.log"

# 1. Defaults
NEWSAPI_KEY = "fa275826b66540b0bdadef40def8318a"
IMAGE_HOST_KEY = "6d207e02198a847aa98d0a2a901485a5"
GROQ_API_KEY = ""
IG_APP_ID = "1747811509564530"
IG_APP_SECRET = "490688bce9cf0888eeecc8da7a8536ce"
IG_ACCESS_TOKEN = ""
IG_USER_ID = "17841420278656916"

# 2. Override with local_config.py (not committed, for local dev)
try:
    from local_config import *
except ImportError:
    pass

# 3. Environment variables always win
for _key in ["NEWSAPI_KEY", "IMAGE_HOST_KEY", "GROQ_API_KEY",
             "IG_APP_ID", "IG_APP_SECRET", "IG_ACCESS_TOKEN", "IG_USER_ID"]:
    _val = os.environ.get(_key)
    if _val:
        globals()[_key] = _val

BRAND_NAME = "PROZECTO"
ACCENT_COLOR = (0, 188, 212)
FALLBACK_ACCENT_COLOR = (30, 30, 30)
IMAGE_SIZE = (1080, 1080)
OVERLAY_HEIGHT = 480
HEADLINE_FONT_SIZE = 50
SUB_FONT_SIZE = 16
HEADLINE_MAX_LINES = 6
HEADLINE_CHARS_PER_LINE = 32
POSTED_ARTICLES_LIMIT = 100
NEWSAPI_CATEGORIES = ["general", "technology", "sports", "business", "science", "health", "entertainment"]
