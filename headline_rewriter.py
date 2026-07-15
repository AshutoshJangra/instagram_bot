import logging
import re

logger = logging.getLogger(__name__)

TEMPLATES = {
    "general": [
        "BREAKING: Just In — {short}",
        "This Is Why Everyone Is Talking About {topic} Right Now",
        "You Won't Believe What Just Happened — {short}",
        "The Moment Everyone Has Been Waiting For — {short}",
        "What {source} Just Confirmed Has Left The World Stunned",
    ],
    "technology": [
        "This New Tech Is So Advanced, Experts Are Speechless",
        "Silicon Valley Just Changed Everything With {topic}",
        "Your Devices Are About to Get A Whole Lot Smarter",
        "The Future Just Arrived — And It's More Impressive Than You Think",
    ],
    "sports": [
        "This Athlete Just Did The Impossible — Here's The Full Story",
        "The Sports World Is Still Recovering From What Just Happened",
        "Everyone Missed This Historic Moment — Until Now",
    ],
    "business": [
        "Wall Street Just Saw Something It Hasn't Seen In Years",
        "This Company Just Made a Move That Changes The Game",
        "The Economy Just Sent a Signal — Here's What Experts Say",
    ],
    "science": [
        "Scientists Just Made a Discovery That Rewrites Everything",
        "This Breakthrough Will Change How We See The World",
        "What Researchers Just Found Has Left Them Speechless",
    ],
    "health": [
        "Health Experts Just Issued a Warning Everyone Needs to Hear",
        "This Medical Breakthrough Could Change Millions of Lives",
    ],
    "entertainment": [
        "Hollywood Just Got Shaken By What Happened Last Night",
        "This Is Why Everyone Can't Stop Talking About It",
    ],
}

FALLBACK_TEMPLATES = [
    "The Story Everyone's Talking About — {short}",
    "This Just Landed: {short}",
    "Why {short} Matters More Than You Think",
    "The Headline That's Breaking The Internet Right Now",
    "Here's What You Need To Know About {topic}",
]


def _extract_topic(title, description):
    text = f"{title}. {description or ''}"
    words = re.findall(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*", text)
    long = [w for w in words if len(w) > 8]
    return long[0] if long else (title.split()[:3] or ["this"])


def _shorten(title, max_words=8):
    words = title.split()
    short = " ".join(words[:max_words])
    if len(words) > max_words:
        short += "…"
    return short


def rewrite(headline, category, source, description=None):
    try:
        topic = " ".join(_extract_topic(headline, description)[:3])
        short = _shorten(headline, 7)

        cat_templates = TEMPLATES.get(category, []) + FALLBACK_TEMPLATES

        import random
        random.seed(hash(headline) % (2 ** 31))
        template = random.choice(cat_templates)

        rewritten = template.format(
            short=short,
            topic=topic,
            source=source or "Reports",
            original=headline,
        )

        if len(rewritten) > 100:
            rewritten = short + " — Read More"

        if rewritten.lower() == headline.lower():
            rewritten = headline

        return rewritten
    except Exception as e:
        logger.warning("Headline rewrite failed: %s — using original", e)
        return headline
