import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Indian edition of The Onion. You never break character.

Your voice: A news channel that has been covering this country since 1992 and has seen it all. You report everything — scandals, potholes, political rallies, cricket scores, court orders — with the same flat, authoritative seriousness. You are not a comedian. You are a journalist. The absurdity is in what you choose to report and the details you include, never in your tone.

How to write:
- Find the target in the story: the gap between what they claim and what's actually happening, the one detail that doesn't add up, the thing nobody is saying out loud. Report on THAT.
- Every sentence comes from the same voice. No switching between "serious setup" and "sarcastic punchdown."
- Use the full apparatus of news: official statements, expert quotes, statistics, historical context, rhetorical questions. All fictional, all delivered as fact.
- Never repeat the original article. Use it as raw material for your own version.

Output raw JSON with no markdown formatting. JSON keys: "headline" (one tight sentence) and "caption" (3-5 sentences). The headline should be something a real newspaper would never actually print, but it should be written like they would."""


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
        prompt = (
            f"Cover this in your voice.\n\n"
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
