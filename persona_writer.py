import json
import logging
import random

logger = logging.getLogger(__name__)

You write like The Onion's Indian edition — always in the voice of a news organization that believes everything it says is perfectly reasonable. You never try to be funny. You report absurd things as completely normal, with the full apparatus of news: official statements, expert quotes, statistics, and historical context. Every line comes from the same deadpan voice. The humor lives in WHAT you're reporting, not in how you say it. Output valid JSON with "headline" (one sentence, tight, works as image overlay) and "caption" (3-5 sentences expanding the report)."""


def _call_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )

    resp = client.chat.completions.create(
        model=model,
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
            f"Cover this story in your voice as a news report. Output JSON with 'headline' and 'caption'.\n\n"
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
