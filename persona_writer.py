import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Write a short satirical news item like an Indian Onion story. It should sound like a real news report — could pass for Times of India — but the angle is slightly wrong in a way that reveals something true about the situation.

Style:
- The headline sounds plausible, like something you'd skim past, until you notice what it's actually saying.
- The caption is a completely straight news report. Fictional quotes, official statements, expert analysis. No jokes, no winking, no punchlines.
- Every line comes from the same voice. Never alternate between "set up" and "punch down."
- Short sentences. Tight. Let the premise do the work.

Output JSON with "headline" (one sentence) and "caption" (3-5 sentences)."""


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
    return {
        "headline": "Something happened, and officials are looking into it.",
        "caption": "Official sources confirmed the development. Speaking on condition of anonymity, a senior functionary stated that the matter is under consideration at the highest levels. No further details were available at the time of filing this report.",
    }


def _parse_response(raw, article_title):
    import re
    text = raw.strip()
    code_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_match:
        text = code_match.group(1)
    try:
        result = json.loads(text)
        headline = result.get("headline", "").strip()
        caption = result.get("caption", "").strip()
        if headline and caption:
            return {"headline": headline, "caption": caption}
    except (json.JSONDecodeError, TypeError):
        pass
    lines = text.split("\n")
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
        styles = ["Cover this.", "Report this.", "Your take on this story."]
        prompt = (
            f"{random.choice(styles)}\n\n"
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
