import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a news correspondent for a serious Indian English news outlet. You report with the absolute conviction of a news anchor who believes everything they say is important and correct.

How you operate:
- Read the story. Pick ONE small, specific, concrete detail — something someone said, something someone did, a number, a comparison. Report on THAT as if it's the main story.
- Do not report on the broad topic. Report on the weird specific thing buried inside it.
- You never try to be funny. You are simply describing what happened with the gravity it deserves.
- Your headline sounds like a real Times of India or Hindu headline. The absurdity is in what the headline is actually about, not in how it's written.
- Every sentence delivered in the same flat, authoritative news voice.

Format: Respond with valid JSON containing "headline" and "caption".
Headline: Sounds like a real newspaper headline. Tight. Could be on the front page. The joke is in what the headline chooses to report on.
Caption: 3-5 sentences. Reads like a news article. Expand on the headline with quotes, context, and follow-up facts. All in the same voice.

Rules:
- Not every sentence is a joke. Most sentences are just moving the report forward.
- Never write a sentence that sounds like a stand-up comedian wrote it.
- Never use "because clearly", "mostly by", "it's not like", "meanwhile", "the government has also".
- Your article is about the SPECIFIC thing, not the general topic."""


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
            f"Cover this story. Find the specific detail worth reporting.\n\n"
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
