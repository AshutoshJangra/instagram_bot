"""
Run this ONCE to generate your Instagram User token.
Starts a local web server, opens the OAuth URL for you to authorize,
then exchanges the code for a long-lived (60 day) token and saves it.

Usage:
    python3 get_token.py

Requirements: Your Meta App must have redirect URI set to:
    http://localhost:8000/callback
"""

import json
import logging
import os
import re
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

import config

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("get_token")

AUTH_URL = "https://api.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
LONG_TOKEN_URL = "https://graph.instagram.com/access_token"
ME_URL = "https://graph.instagram.com/me"
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"

SERVER_PORT = 8000
REDIRECT_URI = f"http://localhost:{SERVER_PORT}/callback"

received_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            error = params.get("error", [None])[0]

            if error:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authorization failed.</h1><p>You denied the request.</p><script>window.close()</script>")
                logger.error("User denied authorization.")
                received_code = None
            elif code:
                received_code = code
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authorization successful!</h1><p>You can close this tab.</p><script>window.close()</script>")
                logger.info("Authorization code received!")
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Missing code.</h1>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def wait_for_code():
    server = HTTPServer(("localhost", SERVER_PORT), CallbackHandler)
    logger.info(f"Local server started on http://localhost:{SERVER_PORT}")
    logger.info("Waiting for you to authorize in the browser...")
    server.handle_request()
    return received_code


def exchange_code(code):
    logger.info("Exchanging code for short-lived token...")
    resp = requests.post(TOKEN_URL, data={
        "client_id": config.IG_APP_ID,
        "client_secret": config.IG_APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }, timeout=30)
    data = resp.json()
    if "access_token" not in data:
        logger.error("Token exchange failed: %s", data)
        sys.exit(1)
    short_token = data["access_token"]
    ig_user_id = data.get("user_id", "")
    logger.info("Short-lived token acquired.")
    return short_token, ig_user_id


def get_long_lived_token(short_token):
    logger.info("Exchanging for long-lived (60 day) token...")
    resp = requests.get(LONG_TOKEN_URL, params={
        "grant_type": "ig_exchange_token",
        "client_secret": config.IG_APP_SECRET,
        "access_token": short_token,
    }, timeout=30)
    data = resp.json()
    if "access_token" not in data:
        logger.error("Long-lived token exchange failed: %s", data)
        logger.info("Using short-lived token instead (expires in 1 hour).")
        return short_token
    expires = data.get("expires_in", 0)
    logger.info(f"Long-lived token acquired (expires in {expires // 86400} days).")
    return data["access_token"]


def get_ig_user_id(token):
    resp = requests.get(ME_URL, params={
        "fields": "id,username",
        "access_token": token,
    }, timeout=30)
    data = resp.json()
    if "id" not in data:
        logger.error("Could not get Instagram user ID: %s", data)
        return None
    ig_id = data["id"]
    username = data.get("username", "unknown")
    logger.info(f"Instagram account: @{username} (ID: {ig_id})")
    return ig_id


def save_to_config(token, user_id):
    config_path = config.BASE_DIR / "config.py"
    with open(config_path) as f:
        content = f.read()

    content = re.sub(
        r'IG_ACCESS_TOKEN\s*=\s*os\.getenv\("IG_ACCESS_TOKEN",\s*"[^"]*"\)',
        f'IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "{token}")',
        content,
    )
    content = re.sub(
        r'IG_USER_ID\s*=\s*os\.getenv\("IG_USER_ID",\s*"[^"]*"\)',
        f'IG_USER_ID = os.getenv("IG_USER_ID", "{user_id}")',
        content,
    )

    with open(config_path, "w") as f:
        f.write(content)

    logger.info("Token and User ID saved to config.py")


def main():
    print("=" * 60)
    print("  Instagram Token Generator")
    print("  (No Facebook Page required)")
    print("=" * 60)
    print()

    if config.IG_APP_ID == "YOUR_INSTAGRAM_APP_ID":
        print("ERROR: IG_APP_ID not configured.")
        print("Set your Instagram App ID in config.py first.")
        print("See SETUP_GUIDE.md Step 2-3 for instructions.")
        sys.exit(1)

    auth_url = (
        f"{AUTH_URL}"
        f"?client_id={config.IG_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=instagram_business_basic,instagram_business_content_publish"
        f"&response_type=code"
    )

    print("Step 1: A browser tab will open asking you to log into Instagram.")
    print("        If it doesn't, open this URL manually:")
    print(f"        {auth_url}")
    print()

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    code = wait_for_code()
    if not code:
        print("Authorization failed or was denied.")
        sys.exit(1)

    short_token, ig_user_id = exchange_code(code)

    if not ig_user_id:
        long_token = get_long_lived_token(short_token)
        ig_user_id = get_ig_user_id(long_token)
    else:
        long_token = get_long_lived_token(short_token)

    if not ig_user_id:
        print("Could not determine your Instagram User ID.")
        sys.exit(1)

    print()
    save_to_config(long_token, ig_user_id)

    print()
    print("=" * 60)
    print("  Setup complete!")
    print("  Token is valid for 60 days.")
    print("  Run 'python3 refresh_token.py' before it expires.")
    print("  Now test with: python3 main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
