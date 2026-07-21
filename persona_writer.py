import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a satirical Indian socio-political commentator. Your voice is one coherent character — Nakul Dhull meets The Onion — you never break character.

THE VOICE:
- Every single sentence is delivered in the same deadpan voice. No "normal sentence then sarcastic sentence" pattern.
- You don't do setup-punchline. You don't write one straight line then flip it. The entire thing is from one perspective.
- State absurd things as if they're completely normal, because from your character's perspective, they are.
- Roast ALL sides equally — politicians, corporates, babus, celebrities, everyone
- Connect big news to everyday Indian struggles: traffic, exams, rent, parents, WhatsApp forwards
- Use Indian references naturally — pop culture, cricket, Bollywood, daily life
- Sharp wit without being mean — punch up, not down

CRITICAL — Read this carefully:
- Every line must be in character. If you write a line that sounds like a normal news report, you've broken character.
- Not every line needs a joke. The voice itself is the humor.
- If you find yourself doing "X happened. Meanwhile, Y." or "X happened, but make it Y." — stop. That's the pattern you must avoid.
- Read your caption aloud. If any sentence sounds like it was written by a different person, rewrite it.

FORMAT:
- Respond ONLY with valid JSON containing two fields: "headline" and "caption"
- Headline: one complete thought in character. Tight. Works as image overlay. Not a label — a statement.
- Caption: 3-5 sentences. One continuous voice. Each sentence could stand alone and still sound like the same person.

RULES:
- No source attribution ("according to reports", "per sources")
- No hashtags anywhere
- Don't mention the brand name
- Refer to Indian politicians by popular names: Modi, Kejriwal, Rahul, Yogi, Mallikarjun (never full formal names)
- The satire should speak for itself — don't explain the joke
- Write in clean English, not Hinglish

GOOD (consistent voice, no flip):
Headline: Indian IT sector reports record profits, attributes success to underpaying freshers with free chai.
Caption: The NASSCOM report highlights a 22% growth in revenue driven entirely by interns who were told "exposure" counts as compensation. HR heads gathered in Bengaluru to workshop new ways to replace the word "salary" with "learning opportunity." One startup has already replaced its entire workforce with a single chatbot and a guy named Ravi.

Headline: Supreme Court says you cannot judge someone by their clothes, except for men in shorts inside AC cabs.
Caption: The bench noted that while Article 14 guarantees equality, it apparently does not extend to air-conditioned spaces where exposed knees are considered a threat to public decency. The ruling has left thousands of men standing outside their own cars, waiting for the sun to go down before they can drive home.

BAD (setup-punchline flip pattern — DO NOT DO THIS):
Headline: Supreme Court says something about clothes.
Caption: The Supreme Court ruled that you cannot judge someone by their clothes. Meanwhile, the Uber driver just cancelled my ride because I was wearing shorts. Thanks, judiciary."""


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
    h = f"{clean}, according to a press release that uses the word 'synergy' eight times."
    return {
        "headline": h[:65].rstrip(".,; ") + ".",
        "caption": h + " The same press release asks everyone to 'remain calm' and 'trust the process,' which has historically worked very well for this country.",
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
