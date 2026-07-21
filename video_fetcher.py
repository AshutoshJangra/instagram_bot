import logging
import random
import subprocess
from pathlib import Path

import feedparser
import requests
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("_reel_temp")
OUTPUT_DIR.mkdir(exist_ok=True)

REEL_MAX_DURATION = 300
SEARCH_LIMIT = 3

KEYWORDS = [
    "protest", "congress", "bjp", "modi", "delhi", "parliament",
    "india", "news", "police", "supreme court", "government",
    "politics", "rahul", "cjp", "cockroach", "election",
]

CHANNELS = [
    ("UCZFMm1mMw0F81Z37aaEzTUA", "NDTV"),
    ("UC1ZQ7YuGJixgGcN0jlUaO-g", "India Today"),
    ("UCxPpLDcP_WrDzC8S0YiGR3A", "Times Now"),
]

QUERIES = [
    "cjp protest india",
    "cockroach party india",
    "india protest today",
    "delhi protest",
    "breaking news india today",
    "congress protest",
]


def _rss_videos():
    videos = []
    random.shuffle(CHANNELS)
    for cid, name in CHANNELS:
        try:
            resp = requests.get(
                f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}",
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:2]:
                vid_id = entry.yt_videoid if hasattr(entry, "yt_videoid") else entry.link.split("v=")[-1]
                videos.append({
                    "id": vid_id,
                    "title": entry.title,
                    "url": entry.link,
                    "uploader": name,
                })
        except Exception as e:
            logger.debug("RSS failed for %s: %s", name, e)
    return videos


def _search_videos(query, max_results=5):
    with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        videos = []
        for entry in results.get("entries", []):
            duration = entry.get("duration", 0) or 0
            if duration > REEL_MAX_DURATION or duration < 5:
                continue
            title = entry.get("title", "")
            if any(kw in title.lower() for kw in ["live", "stream"]):
                continue
            videos.append({
                "id": entry["id"],
                "title": title,
                "url": f"https://youtube.com/watch?v={entry['id']}",
                "duration": duration,
                "uploader": entry.get("uploader", ""),
            })
        return videos


def _process_for_reel(input_path):
    out = input_path.parent / f"{input_path.stem}_reel.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
         "-t", "90",
         "-c:v", "libx264",
         "-preset", "fast",
         "-movflags", "+faststart",
         "-c:a", "aac",
         "-b:a", "128k",
         "-pix_fmt", "yuv420p",
         str(out)],
        capture_output=True,
    )
    return out if out.exists() else input_path


def _download_video(url, output_stem):
    temp = str(OUTPUT_DIR / f"{output_stem}.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best",
        "outtmpl": temp,
        "max_filesize": 100 * 1024 * 1024,
        "socket_timeout": 30,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    for ext in [".mp4", ".webm", ".mkv"]:
        p = OUTPUT_DIR / f"{output_stem}{ext}"
        if p.exists():
            return p
    return None


def _relevant(videos):
    for v in videos:
        t = v["title"].lower()
        if any(kw in t for kw in KEYWORDS):
            return v
    return videos[0] if videos else None


def fetch_reel():
    query = random.choice(QUERIES)
    logger.info("Searching: %s", query)
    videos = _search_videos(query, max_results=SEARCH_LIMIT)

    if not videos:
        videos = _rss_videos()

    video = _relevant(videos) if videos else None
    if not video:
        logger.warning("No videos found")
        return None

    logger.info("Selected: %s by %s", video["title"], video["uploader"])

    out = OUTPUT_DIR / f"{video['id']}.mp4"
    if not out.exists():
        result = _download_video(video["url"], video["id"])
        if not result:
            return None
        out = result

    reel_path = OUTPUT_DIR / f"{video['id']}_reel.mp4"
    if not reel_path.exists():
        logger.info("Processing for Reel format...")
        reel_path = _process_for_reel(out)

    return {
        "video_path": str(reel_path),
        "title": video["title"],
        "source": video["uploader"],
    }


if __name__ == "__main__":
    r = fetch_reel()
    if r:
        print(f"Video: {r['video_path']}")
        print(f"Title: {r['title']}")
    else:
        print("No video found")
