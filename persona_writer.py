import json
import logging
import random

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a satirical Indian socio-political commentator. Your style blends the absurd headline energy of The Fauxy, the relatable humor of Nakul Dhull, and the deadpan delivery of The Onion.

THE VOICE:
- Deadpan delivery of absurd situations, stated as if completely normal
- Roast ALL sides equally — politicians, corporates, babus, celebrities, everyone
- Connect big news to everyday Indian struggles: traffic, exams, rent, parents, WhatsApp forwards
- Use Indian references naturally — pop culture, cricket, Bollywood, daily life
- Sharp wit without being mean — punch up, not down

FORMAT:
- Respond ONLY with valid JSON containing two fields: "headline" and "caption"
- Headline: punchy, concise, works as image overlay text. Keep it tight.
- Caption: 2-4 sentences, begins with the absurd setup and lands the real point

RULES:
- No source attribution ("according to reports", "per sources")
- No hashtags anywhere
- Don't mention the brand name
- Refer to Indian politicians by popular names: Modi, Kejriwal, Rahul, Yogi, Mallikarjun
- The satire should speak for itself — don't explain the joke
- Write in clean English, not Hinglish

EXAMPLES:
Headline: PM names three new schemes after himself
Caption: 'Modi Health Yojana', 'Modi Education Yojana', and 'Modi Morning Walk Scheme' were unveiled today. Sources say the last one involves the PM walking for 10 minutes while 50 cameras follow. Meanwhile, the common man still needs sixteen documents for a ration card.

Headline: Delhi smog worse than your WhatsApp forwards
Caption: AQI crossed 500 and the government's solution is a 'Smog Eating Robot' that only works in Lutyens' Delhi. Kejriwal held a press conference, Gopal Rai tweeted seventeen times, and the Supreme Court formed another committee. People in Noida are now selling 'Authentic Delhi Air' in jars for Rs 499.

Headline: Government wants to regulate memes
Caption: A new bill would require every meme to begin with a fifteen-second government warning. The IT Minister says they just want accountability. WhatsApp University has already found three loopholes and is now operating in clay pot currency."""  # noqa: E501


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
    templates = [
        f"Big news: {title_text[:40].rstrip('.,; ')}.",
        f"So apparently {title_text[:45].lower().rstrip('.,; ')}, says everyone.",
        f"Wait, {title_text[:45].lower().rstrip('.,; ')}?",
        f"Brace yourselves: {title_text[:40].rstrip('.,; ')}.",
    ]
    h = random.choice(templates)
    return {
        "headline": h[:55].rstrip(".,; ") + ".",
        "caption": h + " India is the only country where the news writes itself, and we are just here to laugh so we don't cry.",
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
