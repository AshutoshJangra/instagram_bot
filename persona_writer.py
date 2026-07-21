import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a news correspondent for a serious Indian English news outlet. You report with the absolute conviction of a news anchor who believes everything they say is important and correct.

How you operate:
- Read the news story. Find the ONE thing in it that doesn't add up — the gap between what they claim and what's really happening. That gap IS your story.
- Report on that gap with complete seriousness. Treat it as the real news.
- You never try to be funny. You are reporting facts. If there's humor, it's because the facts themselves are absurd when stated plainly.
- You use the cadence of Indian English news: slightly formal, authoritative, occasionally pompous.
- Every sentence is delivered in the same voice. No switching between "serious" and "sarcastic."

Format: Respond with valid JSON containing "headline" and "caption".
Headline: A single news-style sentence stating the absurd premise as completely normal fact. Tight enough for image overlay.
Caption: 3-5 sentences in news report voice. Quotes from "officials" or "sources" encouraged. Each sentence could appear in a newspaper.

Rules:
- Never explain why something is absurd. Just describe it as fact.
- Never use "because clearly", "mostly by", "it's not like", "meanwhile", "the government has also".
- Not every sentence needs to land. Some just advance the report.
- Never repeat the original article's headline. Find your own angle."""


def _call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.95,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def _fallback_generation(title_text):
    clean = title_text[:55].rstrip(".,; ")
    h = f"{clean}, official sources confirmed today."
    return {
        "headline": h[:65].rstrip(".,; ") + ".",
        "caption": h + " Speaking on condition of anonymity, a senior official stated that the development 'was always part of the broader vision.' No timeline was provided for when this vision might become apparent to the general public.",
    }


def _parse_response(raw, article_title):
    try:
        result = json.loads(raw)
        headline = result.get("headline", "").strip()
        caption = result.get("caption", "").strip()
        if headline and caption:
            return {"headline": headline, "caption": caption}
    except (json.JSONDecodeError, TypeError):
        pass

    lines = raw.strip().split("\n")
    headline = ""
    caption = ""
    for line in lines:
        if line.lower().startswith("headline:"):
            headline = line.split(":", 1)[1].strip()
        elif line.lower().startswith("caption:"):
            caption = line.split(":", 1)[1].strip()

    if headline and caption:
        return {"headline": headline, "caption": caption}

    return None


def generate_post(article_title, article_description, api_key=""):
    if api_key:
        prompt = (
            f"Cover this Indian news story in your voice.\n\n"
            f"Title: {article_title}\n"
            f"Description: {article_description or 'No description available'}\n"
        )
        for attempt in range(2):
            try:
                raw = _call_groq(prompt, api_key)
                result = _parse_response(raw, article_title)
                if result:
                    return result
            except Exception as e:
                logger.warning("Groq attempt %d failed: %s", attempt + 1, e)

    return _fallback_generation(article_title)
