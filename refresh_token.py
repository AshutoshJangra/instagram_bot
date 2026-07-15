"""
Extend your Instagram long-lived token by another 60 days.
Must be called BEFORE the current token expires.

Usage:
    python3 refresh_token.py
"""

import logging
import re
import sys

import requests

import config

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("refresh_token")

REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def refresh(token):
    resp = requests.get(REFRESH_URL, params={
        "grant_type": "ig_refresh_token",
        "access_token": token,
    }, timeout=30)
    data = resp.json()

    if "access_token" not in data:
        logger.error("Token refresh failed: %s", data)
        return None

    new_token = data["access_token"]
    expires_in = data.get("expires_in", 0)
    logger.info(f"Token refreshed! New token expires in {expires_in // 86400} days.")
    return new_token


def save_token(token):
    config_path = config.BASE_DIR / "config.py"
    with open(config_path) as f:
        content = f.read()

    content = re.sub(
        r'IG_ACCESS_TOKEN\s*=\s*os\.getenv\("IG_ACCESS_TOKEN",\s*"[^"]*"\)',
        f'IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "{token}")',
        content,
    )

    with open(config_path, "w") as f:
        f.write(content)

    logger.info("New token saved to config.py")


def main():
    print("=" * 60)
    print("  Instagram Token Refresh")
    print("=" * 60)
    print()

    if config.IG_ACCESS_TOKEN == "YOUR_IG_USER_TOKEN":
        print("No token configured. Run python3 get_token.py first.")
        sys.exit(1)

    print("Refreshing token...")
    new_token = refresh(config.IG_ACCESS_TOKEN)

    if new_token:
        save_token(new_token)
        print()
        print("Done. Token extended by 60 days.")
    else:
        print()
        print("Refresh failed. Run python3 get_token.py to generate a new token.")
        sys.exit(1)


if __name__ == "__main__":
    main()
