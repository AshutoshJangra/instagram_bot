# Insta News Bot — Setup Guide (No Facebook Page Required)

## Overview

Posts news headlines to Instagram every hour — automated with Python. No Facebook Page needed.

**How it works:** NewsAPI → clickbait headline → premium image → Instagram via API

---

## Step 1: NewsAPI Key (2 minutes)

1. Go to [newsapi.org/register](https://newsapi.org/register)
2. Sign up (free tier: 100 requests/day — enough for 24 posts + buffer)
3. Copy your API key
4. Open `config.py` and replace `YOUR_NEWSAPI_KEY_HERE` with your key

---

## Step 2: Install Dependencies (1 minute)

```bash
cd insta_news
pip3 install -r requirements.txt
```

---

## Step 3: Create a Meta Developer App (10 minutes)

You need a Meta Developer account and an app with the "Instagram API with Instagram Login" product.

### 3a — Create Meta Developer account

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **"Get Started"** → accept terms → you now have a developer account
3. This is just for the developer portal — **you do NOT need a Facebook Page**

### 3b — Create a Business app

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Click **"Create App"**
3. Choose **"Business"** as app type
4. App name: "Insta News Bot" (or anything)
5. Contact email: your email
6. Click "Create App"

### 3c — Add Instagram Platform product

1. In your app dashboard, click **"+ Add Product"**
2. Find **"Instagram Platform"** → click **"Set Up"**
3. Choose **"Instagram API with Instagram Login"**
4. Under "Redirect URIs", add:
   ```
   moxxav-mykku6-xijrAw
   http://localhost:8000/callback
   ```
   (This is for the token generator to work on your machine.)
5. Click "Save"

### 3d — Get your App ID and App Secret

1. In your app, go to **"Instagram" → "API Setup with Instagram Login"**
2. Copy:
   - **Instagram App ID** (starts with a number)
   - **Instagram App Secret** (starts with a hash)
3. Open `config.py` and update:
   ```python
   IG_APP_ID = "your_instagram_app_id"
   IG_APP_SECRET = "your_instagram_app_secret"
   ```
   Or set environment variables (safer):
   ```bash
   export IG_APP_ID="your_id"
   export IG_APP_SECRET="your_secret"
   ```

---

## Step 4: Convert Instagram to Professional Account (1 minute)

The API requires a Business or Creator account:

1. Open Instagram app → Settings → Account
2. Tap **"Switch to Professional Account"**
3. Choose **Creator** or **Business**
4. Pick any category

---

## Step 5: Generate Your Token (2 minutes)

This is the magic step. `get_token.py` handles the entire OAuth flow:

```bash
python3 get_token.py
```

What happens:
1. A browser tab opens asking you to log into Instagram
2. You authorize the app
3. The script captures the authorization code
4. It exchanges it for a short-lived token
5. Then exchanges for a **long-lived token (60 days)**
6. It fetches your Instagram User ID
7. **Both are saved to `config.py` automatically**

If the browser doesn't open, copy the URL from the terminal and open it manually.

**Troubleshooting:** If you get an error about "redirect URI mismatch", make sure `http://localhost:8000/callback` is added in Step 3c.

---

## Step 6: Test the Full Pipeline (1 minute)

```bash
python3 main.py
```

Expected output:
```
============================================================
  Insta News Bot — 2025-01-15 14:00:00
============================================================
Article: Scientists discover hidden structure in Earth's core
Source:  CNN
Category: science
Headline: Scientists Just Made a Discovery That Rewrites Everything
Image:   /path/to/_latest_post.jpg
Successfully posted to Instagram. Post ID: 123456789
Done. Post published successfully.
```

If posting fails, common issues:
- **"Invalid OAuth access token"** → Wrong token type. Make sure you used `get_token.py` (Instagram token, not Facebook token)
- **"The user is not an Instagram Business"** → Your account isn't a professional account. Go back to Step 4
- **"Media creation failed"** → The image URL might not be accessible. Check `_latest_post.jpg` was generated

---

## Step 7: Set Up Hourly Posting (cron) (2 minutes)

```bash
crontab -e
```

Add this line (all one line):

```
0 * * * * cd /Users/prozecto/Documents/int/insta_news && /usr/bin/python3 main.py >> hourly.log 2>&1
```

Verify:
```bash
crontab -l
```

Check logs:
```bash
cat /Users/prozecto/Documents/int/insta_news/hourly.log
```

---

## Step 8: Token Refresh (once every 55 days)

Tokens expire in 60 days. Refresh before they do:

```bash
python3 refresh_token.py
```

For full automation, add to cron (monthly):
```
0 0 1 * * cd /Users/prozecto/Documents/int/insta_news && python3 refresh_token.py >> hourly.log 2>&1
```

---

## Customization

| Setting | File | What to change |
|---|---|---|
| Brand name | `config.py` | `BRAND_NAME = "YOUR BRAND"` |
| Accent color | `config.py` | `ACCENT_COLOR = (R, G, B)` |
| Posting frequency | cron schedule | Change `0 * * * *` |
| Clickbait templates | `headline_rewriter.py` | Edit the `TEMPLATES` dict |

Accent color ideas:
```python
ACCENT_COLOR = (229, 9, 20)     # Red (CNN-style)
ACCENT_COLOR = (0, 108, 184)    # Blue (Bloomberg-style)
ACCENT_COLOR = (0, 188, 212)    # Cyan (Modern clean)
ACCENT_COLOR = (207, 169, 67)   # Gold (Premium)
```

---

## File Reference

```
insta_news/
├── main.py              ← Run this hourly via cron
├── news_fetcher.py      ← Fetches headlines from NewsAPI
├── headline_rewriter.py ← Clickbait templates
├── image_gen.py         ← Creates the premium post image
├── insta_poster.py      ← Posts to Instagram via graph.instagram.com
├── get_token.py         ← Run ONCE to generate your token (no FB Page needed)
├── refresh_token.py     ← Run monthly to extend token
├── config.py            ← Your API keys and settings
├── requirements.txt
├── SETUP_GUIDE.md       ← This file
├── posted_articles.json ← Tracks what's been posted (auto-created)
└── assets/
    ├── Inter-Bold.ttf       ← Font (auto-downloaded)
    ├── Inter-Regular.ttf    ← Font (auto-downloaded)
    └── brand_logo.png       ← Generated on first run
```

---

## Quick Start (for returning users)

```bash
# After initial setup is done:
pip3 install -r requirements.txt
python3 get_token.py            # one-time
python3 main.py                 # test
crontab -e                      # add hourly schedule
python3 refresh_token.py        # monthly
```
