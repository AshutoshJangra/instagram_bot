import json
import logging
import random
import re

logger = logging.getLogger(__name__)


def _truncate(text, max_len):
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    last_space = truncated.rfind(" ")
    if last_space >= max_len * 0.5:
        truncated = truncated[:last_space]
    return truncated.rstrip(",. ;-") + "..."

SYSTEM_PROMPT = """You are a satirical Indian socio-political commentator. Your style blends the absurd headline energy of The Fauxy, the relatable desi humor of Nakul Dhull, and the deadpan delivery of The Onion.

THE VOICE:
- Write in Indian English with natural Hinglish — yaar, bhai, matlab, literally, basically
- Deadpan delivery of absolutely ridiculous situations, stated as if completely normal
- Roast ALL sides equally — politicians, corporates, babus, celebrities, everyone
- Connect big news to everyday Indian struggles: traffic, exams, rent, parents, WhatsApp forwards, chai, chappal
- Use Indian pop culture references naturally — Bollywood, cricket, TV serials, memes

FORMAT:
- Output ONLY valid JSON with two fields: "headline" and "caption"
- Headline: exactly 3-6 words, max 45 characters, must fit in 2-3 lines on an image
- Caption: 2-4 sentences. Start absurd, land the real point. Hinglish flows naturally.

RULES:
- No source attribution ("according to reports", "per sources")
- No hashtags in headline
- Don't mention brand name
- Refer to Indian politicians by popular names: Modi, Kejriwal, Rahul, Yogi, Mallikarjun, etc.
- Punch up, not down. Bold but not cruel.
- The satire should speak for itself — don't explain the joke

EXAMPLES:
Headline: PM names 3 new schemes after himself
Caption: 'Modi Health Yojana', 'Modi Education Yojana', and 'Modi Morning Walk Scheme' were unveiled today. Sources say the last one involves PM walking for 10 minutes while 50 cameras follow. Meanwhile, common man still needs 16 documents for a ration card. Matlab, kya bolti company?

Headline: Delhi smog worse than your WhatsApp forwards
Caption: AQI crossed 500 and government's solution is a 'Smog Eating Robot' that works only in Lutyens' Delhi. Kejriwal held a press conference, Gopal Rai tweeted 17 times, Supreme Court formed a committee. Meanwhile, Noida folks are selling 'Authentic Delhi Air' in jars for Rs 499. Joke hai bhai, pure desh ka joke.

Headline: Govt wants to regulate memes now
Caption: New bill requires every meme to start with a 15-second government warning. IT Minister says "we want accountability." WhatsApp University has already found 3 loopholes and is now operating in clay pot currency. Economy in shambles."""


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
        max_tokens=250,
    )
    return resp.choices[0].message.content.strip()


def _fallback_generation(title_text):
    templates = [
        f"Big news: {_truncate(title_text, 35)}.",
        f"So {_truncate(title_text, 40).lower()}.",
        f"Wait, {_truncate(title_text, 40).lower()}?",
        f"Brace yourselves: {_truncate(title_text, 40)}.",
    ]
    h = random.choice(templates)
    return {
        "headline": _truncate(h, 50),
        "caption": h + " India is the only country where the news writes itself, aur hum yahan baith ke hanste hai.",
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
        return {"headline": _truncate(headline, 50), "caption": caption}

    if not headline and not caption:
        try:
            result = json.loads(raw)
            return {
                "headline": _truncate(result.get("headline", article_title), 50),
                "caption": result.get("caption", raw),
            }
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def generate_post(article_title, article_description, api_key=""):
    if api_key:
        prompt = (
            f"Write a satirical post about this Indian news story.\n\n"
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

    return _fallback_generation(article_title)
