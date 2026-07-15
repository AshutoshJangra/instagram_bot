import logging
import re
import time
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)

FONT_DISPLAY_PATH = config.ASSETS_DIR / "Anton-Regular.ttf"
FONT_MONO_PATH = config.ASSETS_DIR / "JetBrainsMonoNerdFont-Regular.ttf"

HEADERS = {"User-Agent": "PROZECTO/1.0 (Social News Aggregator; +https://prozecto.com)"}

PEACH = (255, 200, 200)
PINK = (255, 100, 100)


def _ensure_fonts():
    required = [
        ("https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf", FONT_DISPLAY_PATH),
        ("https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFont-Regular.ttf", FONT_MONO_PATH),
    ]
    for url, path in required:
        if not path.exists():
            logger.info("Downloading font: %s", path.name)
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "wb") as f:
                    f.write(resp.content)
            except Exception as e:
                logger.warning("Font download failed: %s", e)


def _load_display_font(size):
    if FONT_DISPLAY_PATH.exists():
        try:
            return ImageFont.truetype(str(FONT_DISPLAY_PATH), size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", size, index=1)
    except Exception:
        return ImageFont.load_default()


def _load_font(size, bold=True):
    try:
        return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", size, index=1 if bold else 0)
    except Exception:
        pass
    try:
        return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", size)
    except Exception:
        return ImageFont.load_default()


def _load_mono_font(size):
    if FONT_MONO_PATH.exists():
        try:
            return ImageFont.truetype(str(FONT_MONO_PATH), size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Courier.ttc", size)


def _letter_space(text):
    return " ".join(list(text.upper()))


# ─── Image source strategies ───

def _wikipedia_fullres(url):
    if "upload.wikimedia.org" not in url:
        return url
    m = re.match(
        r"(https://upload\.wikimedia\.org/wikipedia/commons/)thumb/(.+?)/\d+px-.+\.\w+$",
        url,
    )
    if m:
        return m.group(1) + m.group(2)
    return url


def _bbc_fullres(url):
    m = re.match(r"(https://ichef\.bbci\.co\.uk/images/ic/)240x135(.+)$", url)
    if m:
        return m.group(1) + "1024x576" + m.group(2)
    m = re.match(r"(https://ichef\.bbci\.co\.uk/ace/standard/)240(/cpsprodpb/.+)$", url)
    if m:
        return m.group(1) + "1024" + m.group(2)
    return url


def _download_image(url, min_size=600, retries=2):
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=15, headers=HEADERS)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            img.load()
            if img.mode != "RGB":
                img = img.convert("RGB")
            if max(img.width, img.height) < min_size:
                logger.warning("Image too small (%dx%d) from %s", img.width, img.height, url[:60])
                time.sleep(1)
                continue
            return img
        except Exception as e:
            if attempt < retries:
                logger.warning("Retry %d for %s: %s", attempt + 1, url[:60], e)
                time.sleep(2)
                continue
            logger.warning("Download failed for %s: %s", url[:60], e)
            return None
    return None


def _fetch_og_image(url):
    if not url or not url.startswith("http"):
        return None
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        resp.raise_for_status()
        m = re.search(
            r'<meta\s+[^>]*property="og:image"[^>]*content="([^"]+)"',
            resp.text,
            re.I,
        )
        if m:
            return m.group(1).split("?")[0]
        m = re.search(
            r'<meta\s+[^>]*name="twitter:image"[^>]*content="([^"]+)"',
            resp.text,
            re.I,
        )
        if m:
            return m.group(1).split("?")[0]
    except Exception as e:
        logger.debug("OG fetch failed for %s: %s", url[:60], e)
    return None


def _search_wikimedia_commons(query):
    try:
        base = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": "6",
            "srlimit": "5",
            "format": "json",
        }
        resp = requests.get(base, params=params, timeout=10, headers=HEADERS)
        data = resp.json()
        titles = [r["title"] for r in data.get("query", {}).get("search", [])]
        for title in titles:
            params = {
                "action": "query",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": "1080",
                "format": "json",
            }
            resp = requests.get(base, params=params, timeout=10, headers=HEADERS)
            data = resp.json()
            for pdata in data.get("query", {}).get("pages", {}).values():
                info = pdata.get("imageinfo", [])
                if info:
                    url = info[0].get("url", "")
                    if url:
                        return url
    except Exception as e:
        logger.debug("Wikimedia search failed: %s", e)
    return None


def _picsum_fallback(seed=""):
    s = seed.replace(" ", "-")[:50] or str(int(time.time()))
    url = f"https://picsum.photos/seed/{s}/1080/1080"
    img = _download_image(url, min_size=800, retries=1)
    if img:
        return img
    url = f"https://picsum.photos/1080/1080?random={int(time.time())}"
    return _download_image(url, min_size=800, retries=1)


def _resolve_image(article, post_type):
    photo_url = article.get("urlToImage")
    article_url = article.get("url")
    title = article.get("title", "")

    if photo_url and "upload.wikimedia.org" in photo_url:
        logger.info("Trying Wikipedia full-res...")
        img = _download_image(_wikipedia_fullres(photo_url))
        if img:
            return img

    if photo_url and "ichef.bbci.co.uk" in photo_url:
        logger.info("Trying BBC full-res...")
        img = _download_image(_bbc_fullres(photo_url))
        if img:
            return img

    if photo_url:
        logger.info("Trying direct image...")
        img = _download_image(photo_url)
        if img:
            return img

    if article_url:
        logger.info("Fetching OG image from article page...")
        og_url = _fetch_og_image(article_url)
        if og_url:
            img = _download_image(og_url)
            if img:
                return img

    terms = re.sub(r"[^\w\s]", "", title)
    terms = " ".join(terms.split()[:6])
    if terms:
        logger.info("Searching Wikimedia Commons for '%s'...", terms)
        wiki_url = _search_wikimedia_commons(terms)
        if wiki_url:
            img = _download_image(wiki_url)
            if img:
                return img

    logger.info("Falling back to Picsum photo...")
    return _picsum_fallback(title)


# ─── Image processing ───

def _center_crop(img, target_size=(1080, 1080)):
    ratio = target_size[0] / target_size[1]
    w, h = img.size
    if w / h > ratio:
        new_w = int(h * ratio)
        offset = (w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, h))
    else:
        new_h = int(w / ratio)
        offset = (h - new_h) // 2
        img = img.crop((0, offset, w, offset + new_h))
    return img.resize(target_size, Image.LANCZOS)


def _wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = font.getbbox(test)
        tw = bbox[2] - bbox[0]
        if tw <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_peach_pink_gradient(draw, x1, x2, y, height=3):
    w = x2 - x1
    for x in range(x1, x2):
        t = (x - x1) / w
        g = int(PEACH[1] - (PEACH[1] - PINK[1]) * t)
        b = int(PEACH[2] - (PEACH[2] - PINK[2]) * t)
        for dy in range(height):
            draw.point((x, y + dy), fill=(255, g, b, 255))


def _generate_fallback_bg(post_type):
    r, g = (40, 20) if post_type == "tech" else (30, 20)
    bg = Image.new("RGB", config.IMAGE_SIZE, (r, g, 30))
    draw = ImageDraw.Draw(bg)
    for i in range(config.IMAGE_SIZE[1]):
        shade = int(25 * (1 - i / config.IMAGE_SIZE[1]))
        draw.line(
            [(0, i), (config.IMAGE_SIZE[0], i)],
            fill=(max(r - shade, 0), max(g - shade, 0), max(30 - shade, 0)),
        )
    return bg


def create_post_image(article, headline=None, post_type="tech"):
    _ensure_fonts()

    bg = _resolve_image(article, post_type)
    if bg:
        bg = _center_crop(bg, config.IMAGE_SIZE)
    else:
        bg = _generate_fallback_bg(post_type)

    W, H = config.IMAGE_SIZE
    canvas = bg.copy().convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")

    mx = 55
    RIGHT_MARGIN = 220
    category = "ON THIS DAY" if post_type == "history" else "TECH"
    PANEL_Y = 482

    # ── Draw solid white panel on bottom ──
    draw.rectangle([(0, PANEL_Y), (W, H)], fill=(255, 255, 255, 255))

    # ── Top brand ──
    font_brand = _load_mono_font(17)
    brand = _letter_space("PROZECTO")
    draw.text((mx, 22), brand, font=font_brand, fill=(40, 40, 40, 255))

    # ── Category label (big Anton, black, inside white panel) ──
    font_cat = _load_display_font(100)
    cat_y = PANEL_Y + 50
    draw.text((mx, cat_y), category, font=font_cat, fill=(255, 230, 60, 255))

    # ── Black accent bar ──
    ay = cat_y + 100
    draw.line([(mx, ay), (mx + 120, ay)], fill=(10, 10, 10, 255), width=8)

    # ── Headline (Anton, black, inside white panel) ──
    font_head = _load_display_font(72)
    tw = W - mx - RIGHT_MARGIN
    display_text = headline or article.get("title", "")
    lines = _wrap_text(display_text, font_head, tw)
    if not lines:
        lines = [display_text[:45]]
    lines = lines[: config.HEADLINE_MAX_LINES]

    lh = 75
    ty = ay + 40
    for i, line in enumerate(lines):
        y = ty + i * lh
        draw.text((mx, y), line, font=font_head, fill=(10, 10, 10, 255))

    # ── Footer: brand · date ──
    font_foot = _load_mono_font(15)
    date_str = datetime.now().strftime("%d %b %Y")
    footer = f"PROZECTO  |  {date_str}"
    draw.text((mx, H - 40), footer, font=font_foot, fill=(80, 80, 80, 255))

    out = config.BASE_DIR / "_latest_post.png"
    canvas.convert("RGB").save(out, "JPEG", quality=95)
    logger.info("Post image saved: %s", out)
    return out
