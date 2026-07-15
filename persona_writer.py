import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a satirical news writer with a deadpan, authoritative delivery. You write like a serious news anchor reporting facts — except the facts are spun through a sarcastic, self-aware filter.

Your style:
- Deadpan delivery: state absurd things as if they're completely normal
- Sarcasm with meaning: make people laugh, then think, then laugh harder
- Unfiltered but smart: observations that land because there's truth beneath
- Mundane + profound: connect big news to everyday human experiences

Rules:
- Output ONLY valid JSON with two fields: "headline" and "caption"
- Headline: max 100 characters, punchy enough to work as image text overlay
- Caption: 2-4 sentences expanding the joke with dry humor
- No source attribution ("according to reports", "per sources", etc.)
- No hashtags in the headline
- The caption should feel like a person talking, not a press release
- Don't mention the brand name or use sign-offs

Examples of the tone:
Headline: ChatGPT's new memory feature remembers everything you said since 2024
Caption: Tragically, this includes the time you asked it to write a poem about your Neighbour's cat. The feature cannot be turned off, much like your neighbour's inability to stop bringing up their kid's SAT scores.

Headline: Scientists confirm the universe is expanding, but so is my stomach
Caption: In breaking news that nobody asked for, researchers have discovered that the cosmos keeps getting bigger. Meanwhile, I just ate an entire pizza and feel like I'm containing a small galaxy. We are all stardust, but some of us are more dense than others.

Headline: Tech CEO announces plan to colonize Mars by 2030, Earth not informed
Caption: The announcement came during a livestream that glitched three times. Followers of the CEO say they are "excited to die on another planet." NASA has declined to comment, presumably because they're too busy laughing."""


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
        temperature=0.85,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def _fallback_generation(topic_type, title_text):
    fallbacks_ai = [
        f"AI experts are very excited about {title_text[:50].lower()}. The experts are always excited. It's honestly exhausting.",
        f"{title_text[:60]} — and nobody knows what that means, including the person who announced it.",
        f"Breaking: {title_text[:60]}. Stocks either went up or down. Experts are available for comment on TV.",
    ]
    fallbacks_history = [
        f"On this day, {title_text[:80].lower()} — which historians agree was 'a thing that happened'.",
        f"History reminds us that in {title_text[:70]}. We have learned nothing, but at least we have a funny story.",
        f"On this day in history, {title_text[:80].lower()}. The parties involved are no longer with us, so feel free to make jokes.",
    ]

    templates = fallbacks_ai if topic_type == "tech" else fallbacks_history
    h = random.choice(templates)
    return {
        "headline": h[:100],
        "caption": h + " History is just one thing after another, and we're here to make fun of all of it.",
    }


def _parse_response(raw, article_title):
    lines = raw.strip().split("\n")
    headline = ""
    caption = ""
    for line in lines:
        if line.lower().startswith("headline:"):
            headline = line.split(":", 1)[1].strip()
        elif line.lower().startswith("caption:"):
            caption = line.split(":", 1)[1].strip()

    if headline and caption:
        return {"headline": headline[:100], "caption": caption}

    if not headline and not caption:
        try:
            result = json.loads(raw)
            return {
                "headline": result.get("headline", article_title)[:100],
                "caption": result.get("caption", raw),
            }
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def generate_post(topic_type, article_title, article_description, api_key=""):
    if api_key:
        prompt = (
            f"Write a satirical post about this {'tech/AI news' if topic_type == 'tech' else 'historical event'}.\n\n"
            f"Title: {article_title}\n"
            f"Description: {article_description or 'No description available'}\n"
        )
        try:
            raw = _call_groq(prompt, api_key)
            result = _parse_response(raw, article_title)
            if result:
                return result
        except Exception as e:
            logger.warning("Groq generation failed: %s — using fallback", e)

    return _fallback_generation(topic_type, article_title)
