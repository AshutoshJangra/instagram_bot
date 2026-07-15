import logging
from pathlib import Path

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoClip,
)

import config

logger = logging.getLogger(__name__)

REEL_SIZE = (1080, 1920)
FONT_BOLD = str(config.ASSETS_DIR / "Inter-Bold.ttf")
FONT_REGULAR = str(config.ASSETS_DIR / "Inter-Regular.ttf")
BG_COLOR = (0, 0, 0)
TEXT_COLOR = "white"
ACCENT = "#00BCD4"
LINE_DELAY = 2
LINE_ANIM_DURATION = 0.6
FADE_DURATION = 0.5


def _make_text_clip(text, font_size, color=TEXT_COLOR, font=FONT_BOLD, method="label"):
    return TextClip(
        text=text,
        font_size=font_size,
        color=color,
        font=font,
        method=method,
    )


def _fade_in_slide(clip, start_time, duration, pos_func):
    clip = clip.with_start(start_time).with_position(pos_func)
    clip = clip.with_effects([vfx.CrossFadeIn(LINE_ANIM_DURATION)])
    return clip


from moviepy import vfx


def generate_reel(
    image_path,
    headline,
    source,
    output_path,
    brand_name=None,
    duration=15,
):
    if brand_name is None:
        brand_name = config.BRAND_NAME

    # Background
    bg = ColorClip(size=REEL_SIZE, color=BG_COLOR).with_duration(duration)

    # Post image — scale to fit width, position at top
    post_img = (
        ImageClip(str(image_path))
        .with_duration(duration)
        .resized(width=1080)
        .with_position(("center", 0))
        .with_effects([vfx.FadeIn(FADE_DURATION)])
    )

    # Gradient overlay at bottom of image area (subtle fade to black)
    # We'll skip the gradient for POC simplicity

    # Calculate text area: below the image
    # Image is 1080 wide, square, so height = 1080
    # Text starts around y=1100
    text_start_y = 1120

    # Split headline into 3 display lines
    words = headline.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if len(test) <= 32:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    # Pad to at least 1 line, at most 3
    lines = lines[:3]
    if not lines:
        lines = [headline[:32]]

    # Brand label
    brand_clip = (
        _make_text_clip(
            brand_name.upper(),
            font_size=16,
            color="#888888",
            font=FONT_REGULAR,
        )
        .with_duration(duration)
        .with_position((40, 20))
        .with_effects([vfx.FadeIn(FADE_DURATION)])
    )

    # Create animated text lines
    text_clips = []
    line_height = 80
    for i, line in enumerate(lines):
        t_start = LINE_DELAY + i * LINE_ANIM_DURATION + i * 0.5
        clip = _make_text_clip(line, font_size=64, color=TEXT_COLOR, font=FONT_BOLD)
        y_pos = text_start_y + i * line_height
        clip = (
            clip.with_start(t_start)
            .with_duration(duration - t_start)
            .with_position((40, y_pos))
            .with_effects([vfx.CrossFadeIn(LINE_ANIM_DURATION)])
        )
        text_clips.append(clip)

    # Source line
    source_start = LINE_DELAY + len(lines) * (LINE_ANIM_DURATION + 0.5) + 0.5
    source_text = f"Source: {source}"
    source_clip = _make_text_clip(source_text, font_size=22, color="#AAAAAA", font=FONT_REGULAR)
    source_clip = (
        source_clip.with_start(source_start)
        .with_duration(duration - source_start)
        .with_position((40, text_start_y + len(lines) * line_height + 20))
        .with_effects([vfx.CrossFadeIn(LINE_ANIM_DURATION)])
    )
    text_clips.append(source_clip)

    # Tagline at bottom
    tagline = (
        _make_text_clip(
            "Follow @dispatch for more",
            font_size=18,
            color="#666666",
            font=FONT_REGULAR,
        )
        .with_duration(duration)
        .with_position(("center", 1860))
        .with_effects([vfx.FadeIn(FADE_DURATION * 3)])
    )

    all_clips = [bg, post_img, brand_clip, *text_clips, tagline]

    final = CompositeVideoClip(all_clips, size=REEL_SIZE)

    output_path = Path(output_path)
    logger.info("Rendering reel: %s", output_path.name)
    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio=False,
        preset="medium",
        threads=2,
        logger=None,
    )
    final.close()
    logger.info("Reel saved: %s", output_path)
    return str(output_path)
