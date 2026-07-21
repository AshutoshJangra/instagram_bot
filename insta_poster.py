import logging
import time
from datetime import datetime

import requests

import config

logger = logging.getLogger(__name__)

GRAPH_HOST = "https://graph.instagram.com"
RETRY_DELAY = 60
MAX_RETRIES = 0
POST_DELAY = 0


def check_publishing_limit():
    try:
        resp = requests.get(
            f"{GRAPH_HOST}/{config.IG_USER_ID}/content_publishing_limit",
            params={"fields": "config,quota_usage", "access_token": config.IG_ACCESS_TOKEN},
            timeout=10,
        )
        data = resp.json()
        usage = data["data"][0]["quota_usage"]
        total = data["data"][0]["config"]["quota_total"]
        remaining = total - usage
        logger.info("Publishing quota: %d/%d used (%d remaining)", usage, total, remaining)
        return remaining
    except Exception as e:
        logger.warning("Failed to check publishing limit: %s", e)
        return None


def _build_caption(article, rewritten_headline, caption_body=""):
    parts = [
        rewritten_headline,
        "",
    ]
    if caption_body:
        parts.append(caption_body)
        parts.append("")
    parts.append("#prozecto #satire #news #headlines #trending")
    return "\n".join(parts)


def _upload_image(image_path):
    import io

    from PIL import Image

    try:
        img = Image.open(image_path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)

        resp = requests.post(
            "https://freeimage.host/api/1/upload",
            data={"key": config.IMAGE_HOST_KEY},
            files={"source": buf},
            timeout=30,
        )
        data = resp.json()
        if data.get("status_code") == 200:
            url = data.get("image", {}).get("url")
            if url:
                logger.info("Image uploaded: %s", url)
                return url
        logger.error("Image upload failed: %s", data)
        return None
    except Exception as e:
        logger.error("Image upload error: %s", e)
        return None


def _recently_posted(caption_snippet):
    try:
        resp = requests.get(
            f"{GRAPH_HOST}/{config.IG_USER_ID}/media",
            params={"fields": "id,caption,timestamp", "access_token": config.IG_ACCESS_TOKEN, "limit": 5},
            timeout=10,
        )
        data = resp.json()
        for item in data.get("data", []):
            if caption_snippet in item.get("caption", ""):
                age = time.time() - datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")).timestamp()
                if age < 120:
                    logger.info("Post already published despite error (ID: %s)", item["id"])
                    return True
    except Exception as e:
        logger.debug("Recent media check failed: %s", e)
    return False


def post_to_instagram(article, rewritten_headline, image_path, caption_body=""):
    if config.IG_ACCESS_TOKEN == "YOUR_IG_USER_TOKEN":
        logger.error("Instagram token not configured.")
        print("Instagram token not configured. Run python3 get_token.py first.")
        return False

    caption = _build_caption(article, rewritten_headline, caption_body)
    image_url = _upload_image(image_path)

    if not image_url:
        logger.error("Could not upload image.")
        return False

    user_id = config.IG_USER_ID
    token = config.IG_ACCESS_TOKEN

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{GRAPH_HOST}/{user_id}/media",
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": token,
                },
                timeout=30,
            )
            data = resp.json()
            if "id" not in data:
                logger.error("Media create failed: %s", data)
                print("Instagram media creation failed:", data)
                time.sleep(RETRY_DELAY)
                continue

            container_id = data["id"]
            logger.info("Media container created: %s", container_id)

            time.sleep(3)

            pub_resp = requests.post(
                f"{GRAPH_HOST}/{user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": token,
                },
                timeout=30,
            )
            pub_data = pub_resp.json()
            if "id" in pub_data:
                logger.info("Post published! ID: %s", pub_data["id"])
                print("Successfully posted to Instagram. Post ID:", pub_data["id"])
                return True
            else:
                logger.error("Publish failed: %s", pub_data)
                print("Instagram publish failed:", pub_data)
                if _recently_posted(caption[:60]):
                    print("Post was published despite error. Marking success.")
                    return True
                time.sleep(RETRY_DELAY)
        except requests.RequestException as e:
            logger.error("Instagram API error: %s", e)
            print("Instagram API error:", e)
            time.sleep(RETRY_DELAY)

    logger.error("All publish attempts exhausted.")
    return False


def _upload_video(video_path):
    import time
    hosts = [
        "https://0x0.st",
        "https://temp.sh/upload",
    ]
    for host in hosts:
        try:
            with open(video_path, "rb") as f:
                resp = requests.post(
                    host,
                    files={"file": f},
                    timeout=120,
                )
            if resp.status_code == 200:
                url = resp.text.strip()
                logger.info("Video uploaded to %s: %s", host, url)
                return url
            logger.warning("%s returned %d: %s", host, resp.status_code, resp.text[:100])
        except Exception as e:
            logger.warning("Video upload failed to %s: %s", host, e)
        time.sleep(1)
    return None


def post_reel_to_instagram(article, rewritten_headline, video_path):
    if config.IG_ACCESS_TOKEN == "YOUR_IG_USER_TOKEN":
        logger.error("Instagram token not configured.")
        return False

    caption = _build_caption(article, rewritten_headline)
    video_url = _upload_video(video_path)

    if not video_url:
        logger.error("Could not upload video.")
        return False

    user_id = config.IG_USER_ID
    token = config.IG_ACCESS_TOKEN

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{GRAPH_HOST}/{user_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "access_token": token,
                },
                timeout=30,
            )
            data = resp.json()
            if "id" not in data:
                logger.error("Reel container create failed: %s", data)
                print("Reel creation failed:", data)
                time.sleep(RETRY_DELAY)
                continue

            container_id = data["id"]
            logger.info("Reel container created: %s", container_id)

            # Wait for video processing
            time.sleep(5)

            pub_resp = requests.post(
                f"{GRAPH_HOST}/{user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": token,
                },
                timeout=30,
            )
            pub_data = pub_resp.json()
            if "id" in pub_data:
                logger.info("Reel published! ID: %s", pub_data["id"])
                print("Successfully posted Reel. ID:", pub_data["id"])
                return True
            else:
                logger.error("Reel publish failed: %s", pub_data)
                print("Reel publish failed:", pub_data)
                time.sleep(RETRY_DELAY)
        except requests.RequestException as e:
            logger.error("Instagram API error: %s", e)
            print("Instagram API error:", e)
            time.sleep(RETRY_DELAY)

    logger.error("All reel publish attempts exhausted.")
    return False
