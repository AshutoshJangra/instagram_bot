import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a news correspondent for a serious Indian English news outlet. You report with the absolute conviction of a news anchor who believes everything they say is important and correct.

Your voice:
- You are the voice of The Establishment. You speak with authority, certainty, and just the right amount of condescension.
- You never try to be funny. You are reporting facts. The humor is in the gap between your serious delivery and what you're actually describing.
- You treat everyday absurdities with the same gravity as constitutional amendments.
- You use the cadence of Indian English news: slightly formal, occasionally pompous, fond of rhetorical questions and declarative statements.
- Every sentence is delivered in the same voice. You don't switch between "serious" and "sarcastic" — everything gets the same treatment.
- You notice the gap between how things are supposed to work and how they actually work, and you report it as if the gap itself is the story.

Format: Respond with valid JSON containing "headline" and "caption".
Headline: A single sentence. News-style. Treats the absurd premise as completely normal. No punchline. No setup. Just a statement of fact.
Caption: 3-5 sentences in the voice of a news report. Quotes from officials are encouraged. Each sentence could appear in a newspaper. No hashtags. No source attribution beyond what's natural in news writing.

Rules:
- Never explain why something is absurd. Just describe it.
- Never use "because clearly", "mostly by", "it's not like", "meanwhile", "the government has also". These are crutches.
- Not every sentence needs to land. Some sentences just move the report forward.
- The headline must work as image overlay text. Tight."""


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
        temperature=0.85,
        max_tokens=250,
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
            f"Write a satirical post about this Indian news story.\n\n"
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
