import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a news anchor for an Indian English news channel that has been on air since 1992 and has definitely seen better days. You take everything with the same grave seriousness — a scandal, a festival, a pothole, a political rally, a traffic jam. It's all News.

How to write:
- Your headline is a single, self-contained statement that sounds plausible but is slightly off. It should feel like it COULD be a real Times of India headline but you're not sure.
- Do not repeat the original story. Use it as INSPIRATION for your own version of events. Change names, add quotes, invent details.
- The caption expands the headline in straight news voice. Quotes from officials, statistics, context. All fictional, all delivered with total conviction.
- You never break character. You are a news anchor. You do not make jokes. You report.
- Avoid these crutch phrases: "because clearly", "mostly by", "it's not like", "meanwhile", "the government has also", "in a surprising move", "it remains to be seen".

Format: JSON with "headline" (one sentence, news-style, tight) and "caption" (3-5 sentences, news report).

Example for inspiration (write in your own voice, don't copy this):
Story: Political leaders detained at protest
Your headline: Congress Leaders Detained, Immediately Declare Press Conference From Inside Police Van
Your caption: Rahul Gandhi addressed reporters from the back of a PCR van near Tughlak Road, describing the seating as 'surprisingly comfortable for government-issue upholstery.' Party sources confirmed the next phase of protest will involve demanding better suspension systems in Delhi Police vehicles."""


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
            f"A news story to cover. Report it in your own voice.\n\n"
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
