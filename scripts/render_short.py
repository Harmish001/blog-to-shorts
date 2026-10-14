#!/usr/bin/env python3
"""Render one 9:16 YouTube Short from beat JSON.

Cinema-grade rendering engine (Clean Typography Edition):
- EVERY beat has a real background photo (no solid-color cards)
- Direct-on-photo typography: NO ugly rectangular card boxes or outlined containers
- Wrapped text prevents left/right edge cutout/clipping
- Clean modern typography using Inter / Open Sans fonts
- Sequential bullet text reveal for list points
- Handheld camera simulation + organic camera motions (cubic easing)
- Motion blur, vignette, and audio bed ducking (-14 LUFS)
"""

import argparse
import asyncio
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from voices import validate_and_normalize_voice, recommend_voice, is_supported_voice
except ImportError:
    from scripts.voices import validate_and_normalize_voice, recommend_voice, is_supported_voice

W, H = 1080, 1920
FPS = 30
DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_SHORT_CAP = 60.0
DEFAULT_LONG_CAP = 90.0

# YouTube Safe Zone — text sits in central clear region of frame
SAFE_ZONE = {
    "top": 280,
    "bottom": 1500,
    "left": 90,
    "right": 950,
    "caption_y": 1320,
}

VALID_TRANSITIONS = {
    "cut", "fade", "fadeblack", "dissolve", "slideleft", "slideright", "slideup",
    "slidedown", "wipeleft", "wiperight", "zoomin", "circleopen", "smoothleft",
    "smoothright", "radial", "pixelize",
}
DEFAULT_XFADE_DUR = 0.22

PALETTES = {
    "ember": {
        "bg": "#121014", "card_bg": "#1C1720", "card_border": "#FF6B35",
        "accent": "#FF6B35", "highlight": "#FFA500",
        "text_primary": "#FFFFFF", "text_muted": "#B3A4B8", "tag_bg": "#361D15",
        "overlay_rgba": (18, 16, 20, 185),
    },
    "neon-cyber": {
        "bg": "#0B0E14", "card_bg": "#131B26", "card_border": "#00F0FF",
        "accent": "#00F0FF", "highlight": "#FF0055",
        "text_primary": "#FFFFFF", "text_muted": "#8EA0B5", "tag_bg": "#0A2F38",
        "overlay_rgba": (11, 14, 20, 180),
    },
    "ocean-slate": {
        "bg": "#0F172A", "card_bg": "#1E293B", "card_border": "#38BDF8",
        "accent": "#38BDF8", "highlight": "#818CF8",
        "text_primary": "#F8FAFC", "text_muted": "#94A3B8", "tag_bg": "#1E3A5F",
        "overlay_rgba": (15, 23, 42, 178),
    },
    "clean-dark": {
        "bg": "#12141A", "card_bg": "#1D212A", "card_border": "#E6D3B3",
        "accent": "#E6D3B3", "highlight": "#F59E0B",
        "text_primary": "#FFFFFF", "text_muted": "#A1A7B5", "tag_bg": "#2F2B22",
        "overlay_rgba": (18, 20, 26, 175),
    },
    "sunset-gold": {
        "bg": "#171212", "card_bg": "#261A1B", "card_border": "#F59E0B",
        "accent": "#F59E0B", "highlight": "#EF4444",
        "text_primary": "#FFFBEB", "text_muted": "#BDB29B", "tag_bg": "#3B2613",
        "overlay_rgba": (23, 18, 18, 182),
    },
    "forest-emerald": {
        "bg": "#0B1411", "card_bg": "#14241E", "card_border": "#10B981",
        "accent": "#10B981", "highlight": "#34D399",
        "text_primary": "#ECFDF5", "text_muted": "#86A89A", "tag_bg": "#133829",
        "overlay_rgba": (11, 20, 17, 178),
    },
}

ARCHETYPES = {
    "listicle-punch": {
        "default_palette": "neon-cyber",
        "motion_set": ["punch-zoom", "pan-right", "push-in", "handheld-left"],
        "default_transition": "slideleft",
        "music_mood": "upbeat-minimal",
        "caption_style": "word-pop",
    },
    "story-arc": {
        "default_palette": "clean-dark",
        "motion_set": ["push-in", "pull-out", "handheld-drift", "tilt-up"],
        "default_transition": "fade",
        "music_mood": "ambient",
        "caption_style": "word-pop",
    },
    "explainer-stack": {
        "default_palette": "ocean-slate",
        "motion_set": ["push-in", "tilt-down", "handheld-right", "pan-left"],
        "default_transition": "wipeleft",
        "music_mood": "tech-pulse",
        "caption_style": "word-pop",
    },
    "myth-vs-fact": {
        "default_palette": "ember",
        "motion_set": ["pan-left", "pan-right", "punch-zoom", "handheld-drift"],
        "default_transition": "slideleft",
        "music_mood": "upbeat-minimal",
        "caption_style": "word-pop",
    },
    "stat-drop": {
        "default_palette": "sunset-gold",
        "motion_set": ["punch-zoom", "pull-out", "tilt-up", "handheld-left"],
        "default_transition": "zoomin",
        "music_mood": "tech-pulse",
        "caption_style": "word-pop",
    },
    "quote-reel": {
        "default_palette": "forest-emerald",
        "motion_set": ["handheld-drift", "push-in", "pull-out", "diagonal-drift"],
        "default_transition": "fade",
        "music_mood": "calm",
        "caption_style": "word-pop",
    },
}


# ---------------------------------------------------------------------------
# Font Resolution — Prioritizes Inter font for clean typography
# ---------------------------------------------------------------------------

def resolve_font_path(custom_font: Optional[str] = None) -> str:
    if custom_font and Path(custom_font).exists():
        return str(Path(custom_font).resolve())

    # Check bundled Inter font first
    script_dir = Path(__file__).resolve().parent
    skill_font = script_dir.parent / "fonts" / "Inter-Bold.ttf"
    if skill_font.exists():
        return str(skill_font.resolve())

    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return str(Path(p).resolve())
    return "Arial"


FONT_PATH = resolve_font_path()


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = proc.stderr or proc.stdout or "Command failed"
        sys.stderr.write(f"\n[ERROR] {' '.join(cmd[:3])}...\n{err}\n")
        raise SystemExit(proc.returncode)
    return proc


def esc_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")


def get_media_duration(path: Path) -> float:
    proc = run_cmd([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ])
    try:
        return float(proc.stdout.strip())
    except (ValueError, TypeError):
        return 0.0


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        if bold:
            # Try Inter-Bold if available
            bold_font = Path(FONT_PATH).parent / "Inter-Bold.ttf"
            if bold_font.exists():
                return ImageFont.truetype(str(bold_font), size)
        else:
            reg_font = Path(FONT_PATH).parent / "Inter-Regular.ttf"
            if reg_font.exists():
                return ImageFont.truetype(str(reg_font), size)
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        w = (font.getbbox(test)[2] - font.getbbox(test)[0])
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def wrap_text_by_chars(text: str, max_chars: int = 22) -> List[str]:
    """Wrap text by character count to guarantee fitting on screen."""
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if len(test) <= max_chars or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


# ---------------------------------------------------------------------------
# Background Image Preparation
# ---------------------------------------------------------------------------

def prepare_background_image(
    image_path: Path,
    out_path: Path,
    blur_radius: float = 0.0,
    darken: float = 0.0,
    add_grain: bool = False,
) -> Path:
    """Scale and crop image to 1080x1920. Darkens slightly for crisp text readability."""
    img = Image.open(image_path).convert("RGB")

    iw, ih = img.size
    scale = max(W / iw, H / ih)
    nw, nh = int(iw * scale) + 2, int(ih * scale) + 2
    img = img.resize((nw, nh), Image.LANCZOS)

    left = (nw - W) // 2
    top = (nh - H) // 2
    img = img.crop((left, top, left + W, top + H))

    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    if darken > 0:
        overlay = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.blend(img, overlay, darken)

    img.save(out_path, "PNG")
    return out_path


def composite_overlay_on_photo(
    photo_path: Path,
    overlay_img: Image.Image,
    out_path: Path,
) -> Path:
    """Paste RGBA text overlay on top of a photo background."""
    bg = Image.open(photo_path).convert("RGBA")
    bg.paste(overlay_img, (0, 0), overlay_img)
    bg.convert("RGB").save(out_path, "PNG")
    return out_path


# ---------------------------------------------------------------------------
# Clean Overlay Compositor — DIRECT ON PHOTO (NO CARDS / CONTAINER BOXES)
# ---------------------------------------------------------------------------

def draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int, int] = (255, 255, 255, 255),
    shadow_fill: Tuple[int, int, int, int] = (0, 0, 0, 200),
    shadow_offset: int = 3,
):
    """Draw crisp text with a heavy drop shadow for legibility directly on photos."""
    x, y = xy
    # Drop shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=shadow_fill, font=font)
    draw.text((x - 1, y - 1), text, fill=shadow_fill, font=font)
    draw.text((x + 1, y + 1), text, fill=shadow_fill, font=font)
    # Main text
    draw.text((x, y), text, fill=fill, font=font)


def draw_dark_gradient_backdrop(overlay: Image.Image, y0: int = 500, y1: int = 1450, max_alpha: int = 180):
    """Draw subtle vertical dark gradient behind text zone for 100% legibility on any image."""
    draw = ImageDraw.Draw(overlay)
    h = y1 - y0
    for y in range(y0, y1):
        rel = (y - y0) / h
        # Smooth bell / sine gradient curve
        alpha = int(max_alpha * math.sin(rel * math.pi))
        draw.line([(0, y), (W, y)], fill=(10, 12, 18, alpha))


def build_card_overlay(
    beat: Dict[str, Any],
    palette: Dict[str, str],
    role: str,
) -> Image.Image:
    """Build clean text points overlay directly on photo — NO card box."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Apply dark gradient behind text area
    draw_dark_gradient_backdrop(overlay, y0=600, y1=1450, max_alpha=190)

    caption = beat.get("caption") or beat.get("hook") or beat.get("voice") or ""
    lines = [p.strip() for p in caption.split("|") if p.strip()]
    if not lines:
        lines = [caption]

    title = lines[0]
    body_lines = lines[1:] if len(lines) > 1 else []
    accent_rgba = hex_to_rgb(palette["accent"]) + (255,)

    # Safe text margin
    text_x = 120
    max_w = W - 240
    cy = 720

    # Title text — clean Inter Bold
    title_font = get_font(54, bold=True)
    wrapped_title = wrap_text(title, title_font, max_w)
    for tl in wrapped_title:
        draw_text_with_shadow(draw, (text_x, cy), tl, title_font, fill=(255, 255, 255, 255))
        cy += 66

    # Accent underline
    cy += 12
    draw.rectangle([(text_x, cy), (text_x + 120, cy + 5)], fill=accent_rgba)
    cy += 36

    # Body lines (points)
    body_font = get_font(42, bold=False)
    for i, bl in enumerate(body_lines):
        bullet = f"{i+1}." if beat.get("layout") == "numbered-stack" else ">"
        draw_text_with_shadow(draw, (text_x, cy), bullet, body_font, fill=accent_rgba)

        wrapped = wrap_text(bl, body_font, max_w - 50)
        for sub in wrapped:
            draw_text_with_shadow(draw, (text_x + 48, cy), sub, body_font, fill=(245, 245, 245, 255))
            cy += 54
        cy += 14

    return overlay


def build_stat_overlay(beat: Dict[str, Any], palette: Dict[str, str]) -> Image.Image:
    """Big-number stat overlay directly on photo — NO outlined box panel."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw_dark_gradient_backdrop(overlay, y0=650, y1=1350, max_alpha=190)

    value = str(beat.get("value") or "")
    label = str(beat.get("label") or beat.get("caption") or "")

    highlight_rgba = hex_to_rgb(palette["highlight"]) + (255,)

    # Big value (e.g., 200+ or 53%)
    val_font = get_font(140, bold=True)
    vb = val_font.getbbox(value)
    vw = vb[2] - vb[0]
    val_x = (W - vw) // 2
    val_y = 740

    draw_text_with_shadow(draw, (val_x, val_y), value, val_font, fill=highlight_rgba, shadow_offset=4)

    # Label text below stat
    lbl_font = get_font(46, bold=True)
    wrapped = wrap_text(label, lbl_font, W - 200)
    cy = val_y + 175
    for line in wrapped:
        lb = lbl_font.getbbox(line)
        lw = lb[2] - lb[0]
        draw_text_with_shadow(draw, ((W - lw) // 2, cy), line, lbl_font, fill=(255, 255, 255, 245))
        cy += 60

    return overlay


def build_split_overlay(beat: Dict[str, Any], palette: Dict[str, str]) -> Image.Image:
    """Before/After split comparison directly on photo — NO rounded container boxes."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw_dark_gradient_backdrop(overlay, y0=500, y1=1350, max_alpha=200)

    left_title = str(beat.get("label_left") or "INITIAL REPORT").upper()
    left_body = str(beat.get("before") or "")
    right_title = str(beat.get("label_right") or "REALITY").upper()
    right_body = str(beat.get("after") or "")

    badge_font = get_font(30, bold=True)
    body_font = get_font(40, bold=False)

    # --- Section 1 (Red / Myth / Initial) ---
    cy = 580
    # Small pill badge for tag only
    t1_txt = f"{left_title}"
    tb1 = badge_font.getbbox(t1_txt)
    tw1 = tb1[2] - tb1[0]
    draw.rounded_rectangle([(120, cy), (120 + tw1 + 36, cy + 44)], radius=12, fill=(220, 40, 40, 220))
    draw.text((138, cy + 6), t1_txt, fill=(255, 255, 255, 255), font=badge_font)

    cy += 64
    for line in wrap_text(left_body, body_font, W - 240):
        draw_text_with_shadow(draw, (120, cy), line, body_font, fill=(255, 230, 230, 255))
        cy += 52

    # --- Section 2 (Green / Fact / Reality) ---
    cy += 48
    t2_txt = f"{right_title}"
    tb2 = badge_font.getbbox(t2_txt)
    tw2 = tb2[2] - tb2[0]
    draw.rounded_rectangle([(120, cy), (120 + tw2 + 36, cy + 44)], radius=12, fill=(16, 185, 129, 220))
    draw.text((138, cy + 6), t2_txt, fill=(255, 255, 255, 255), font=badge_font)

    cy += 64
    for line in wrap_text(right_body, body_font, W - 240):
        draw_text_with_shadow(draw, (120, cy), line, body_font, fill=(230, 255, 240, 255))
        cy += 52

    return overlay


def build_code_overlay(beat: Dict[str, Any], palette: Dict[str, str]) -> Image.Image:
    """Code snippet overlay directly on photo — clean translucent backdrop."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    code_text = str(beat.get("code") or beat.get("caption") or "")
    lang = str(beat.get("language") or "CODE").upper()
    accent_rgba = hex_to_rgb(palette["accent"]) + (255,)

    panel_y0, panel_y1 = 620, 1280
    # Soft dark backdrop strip (no bright border)
    draw.rectangle([(60, panel_y0), (W - 60, panel_y1)], fill=(12, 16, 24, 215))

    # Window dots
    draw.ellipse([(90, panel_y0 + 20), (110, panel_y0 + 40)], fill=(255, 95, 86, 255))
    draw.ellipse([(120, panel_y0 + 20), (140, panel_y0 + 40)], fill=(255, 189, 46, 255))
    draw.ellipse([(150, panel_y0 + 20), (170, panel_y0 + 40)], fill=(39, 201, 63, 255))

    lang_font = get_font(28, bold=True)
    draw.text((W - 180, panel_y0 + 18), lang, fill=accent_rgba, font=lang_font)

    code_font = get_font(36, bold=False)
    cy = panel_y0 + 70
    for i, line in enumerate([l for l in code_text.split("\n")][:12]):
        lnum_font = get_font(28)
        draw.text((80, cy + 4), f"{i+1:2d}", fill=(80, 100, 130, 255), font=lnum_font)
        draw.text((130, cy), line, fill=(220, 235, 255, 255), font=code_font)
        cy += 48

    return overlay


def build_quote_overlay(beat: Dict[str, Any], palette: Dict[str, str]) -> Image.Image:
    """Quote statement overlay directly on photo — NO card box."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw_dark_gradient_backdrop(overlay, y0=550, y1=1350, max_alpha=190)

    quote_text = str(beat.get("quote") or beat.get("caption") or beat.get("voice") or "")
    author = str(beat.get("author") or "")
    accent_rgba = hex_to_rgb(palette["accent"]) + (255,)

    q_font = get_font(120, bold=True)
    draw_text_with_shadow(draw, (90, 640), "\u201c", q_font, fill=accent_rgba)

    body_font = get_font(48, bold=True)
    cy = 760
    for line in wrap_text(quote_text, body_font, W - 180):
        draw_text_with_shadow(draw, (90, cy), line, body_font, fill=(255, 255, 255, 255))
        cy += 64

    if author:
        cy += 20
        draw.line([(90, cy), (190, cy)], fill=accent_rgba, width=3)
        cy += 18
        auth_font = get_font(36)
        draw_text_with_shadow(draw, (90, cy), f"\u2014 {author}", auth_font, fill=hex_to_rgb(palette["highlight"]) + (255,))

    return overlay


def build_intro_hook_overlay(beat: Dict[str, Any], palette: Dict[str, str]) -> Image.Image:
    """Intro hook text overlay — clean wrapped typography with top gradient, NO cutout."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    hook = str(beat.get("hook") or "")
    if not hook:
        return overlay

    accent_rgba = hex_to_rgb(palette["accent"]) + (255,)

    # Top dark gradient
    grad = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    for y in range(400):
        alpha = int(210 * (1.0 - y / 400))
        for x in range(W):
            grad.putpixel((x, y), (8, 10, 15, alpha))
    overlay.paste(grad, (0, 0), grad)

    hook_font = get_font(60, bold=True)
    # Wrap cleanly to prevent ANY side clipping
    wrapped = wrap_text(hook, hook_font, W - 160)
    cy = 120
    for line in wrapped:
        lb = hook_font.getbbox(line)
        lw = lb[2] - lb[0]
        draw_text_with_shadow(draw, ((W - lw) // 2, cy), line, hook_font, fill=(255, 255, 255, 255))
        cy += 76

    # Accent underline
    draw.rectangle([(W // 2 - 80, cy + 10), (W // 2 + 80, cy + 16)], fill=accent_rgba)

    return overlay


def build_outro_overlay(beat: Dict[str, Any], palette: Dict[str, str]) -> Image.Image:
    """Cinematic outro overlay — centered hook text over photo, NO card box."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    hook = str(beat.get("hook") or "")
    accent_rgba = hex_to_rgb(palette["accent"]) + (255,)

    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for y in range(H):
        t = abs(y - H // 2) / (H // 2)
        alpha = int(160 * (t ** 1.5))
        for x in range(W):
            tx = abs(x - W // 2) / (W // 2)
            a = min(255, alpha + int(120 * (tx ** 2)))
            vignette.putpixel((x, y), (0, 0, 0, a))
    overlay.paste(vignette, (0, 0), vignette)

    if hook:
        hook_font = get_font(68, bold=True)
        wrapped = wrap_text(hook, hook_font, W - 160)
        total_h = len(wrapped) * 82
        cy = (H - total_h) // 2 - 40
        for line in wrapped:
            lb = hook_font.getbbox(line)
            lw = lb[2] - lb[0]
            draw_text_with_shadow(draw, ((W - lw) // 2, cy), line, hook_font, fill=(255, 255, 255, 255))
            cy += 82

        draw.rectangle([(W // 2 - 75, cy + 16), (W // 2 + 75, cy + 22)], fill=accent_rgba)

    return overlay


# ---------------------------------------------------------------------------
# Motion Expression Builder — cinematic camera motions
# ---------------------------------------------------------------------------

def build_motion_expr(motion_kind: str, frames: int, speed_factor: float = 1.0) -> str:
    """Generate smooth zoompan filter expression with easing and organic variation."""
    f = max(frames, 1)

    # Ease in-out cubic: t = on/frames, eased = t*t*(3-2*t)
    ease = "on/{f}*(on/{f}*(3-2*on/{f}))".replace("{f}", str(f))

    if motion_kind == "push-in":
        return f"z='min(1.0+0.18*{ease},1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    elif motion_kind == "pull-out":
        return f"z='max(1.18-0.18*{ease},1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    elif motion_kind == "pan-left":
        return f"z='1.14':x='(iw-iw/zoom)*(1.0-{ease})':y='ih/2-(ih/zoom/2)'"
    elif motion_kind == "pan-right":
        return f"z='1.14':x='(iw-iw/zoom)*{ease}':y='ih/2-(ih/zoom/2)'"
    elif motion_kind == "tilt-up":
        return f"z='1.14':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1.0-{ease})'"
    elif motion_kind == "tilt-down":
        return f"z='1.14':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*{ease}'"
    elif motion_kind == "diagonal-drift":
        return f"z='min(1.06+0.10*{ease},1.16)':x='(iw-iw/zoom)*{ease}':y='(ih-ih/zoom)*(1.0-{ease})'"
    elif motion_kind == "punch-zoom":
        return f"z='if(lte(on,14),1.0+0.16*(on/14),1.16)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    elif motion_kind == "handheld-left":
        return f"z='1.12':x='(iw-iw/zoom)*(0.6+0.4*{ease})+sin(on*0.15)*3':y='ih/2-(ih/zoom/2)+sin(on*0.09)*5'"
    elif motion_kind == "handheld-right":
        return f"z='1.12':x='(iw-iw/zoom)*(0.4-0.4*{ease})+sin(on*0.12)*3':y='ih/2-(ih/zoom/2)+sin(on*0.11)*4'"
    elif motion_kind == "handheld-drift":
        return f"z='1.10+0.04*sin(on*0.08)':x='iw/2-(iw/zoom/2)+sin(on*0.13)*6':y='ih/2-(ih/zoom/2)+cos(on*0.09)*5'"
    else:
        return f"z='1.04+0.02*sin(on*0.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"


# ---------------------------------------------------------------------------
# TTS Synthesis Engine
# ---------------------------------------------------------------------------

def synthesize_speech(
    text: str, voice: str, rate_offset: str, pitch_offset: str, dest_wav: Path
) -> List[Dict[str, Any]]:
    try:
        import edge_tts
    except ImportError:
        sys.stderr.write("\n[FATAL] edge-tts is required: pip install edge-tts\n")
        raise SystemExit(1)

    words: List[Dict[str, Any]] = []

    async def _run():
        try:
            comm = edge_tts.Communicate(
                text.strip(), voice=voice, rate=rate_offset, pitch=pitch_offset, boundary="WordBoundary"
            )
        except TypeError:
            comm = edge_tts.Communicate(text.strip(), voice=voice, rate=rate_offset, pitch=pitch_offset)
        buf = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buf.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                t0 = chunk["offset"] / 10_000_000.0
                dur = chunk["duration"] / 10_000_000.0
                words.append({"text": chunk["text"], "start": t0, "end": t0 + dur})
        dest_wav.write_bytes(buf)

    try:
        asyncio.run(_run())
    except Exception as exc:
        sys.stderr.write(f"\n[FATAL] TTS failed: {exc}\n")
        raise SystemExit(1)

    if not words:
        dur = get_media_duration(dest_wav)
        raw = text.split()
        if raw and dur > 0:
            step = dur / len(raw)
            for i, w in enumerate(raw):
                words.append({"text": w, "start": i * step, "end": (i + 1) * step})

    return words


def build_word_cues(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not words:
        return []

    chunks, buf = [], []
    for w in words:
        buf.append(w)
        txt = w["text"]
        ends_clause = any(txt.endswith(p) for p in (",", ".", "!", "?", ";", ":", "—", "-"))
        cur_phrase = " ".join(x["text"] for x in buf)
        if ends_clause or len(cur_phrase) >= 24 or len(buf) >= 4:
            chunks.append(buf)
            buf = []
    if buf:
        chunks.append(buf)

    cues = []
    for i, chunk in enumerate(chunks):
        start = max(0.0, chunk[0]["start"])
        last_word_end = chunk[-1]["end"]
        if i + 1 < len(chunks):
            next_start = max(0.0, chunks[i + 1][0]["start"])
            if next_start - last_word_end > 0.4:
                end = last_word_end + 0.25
            else:
                end = max(next_start - 0.02, start + 0.15)
        else:
            end = last_word_end + 0.35

        cues.append({
            "phrase": " ".join(x["text"] for x in chunk),
            "start": round(start, 3),
            "end": round(end, 3),
            "words": chunk,
        })
    return cues


# ---------------------------------------------------------------------------
# Safe Zone Subtitle Caption Builder
# ---------------------------------------------------------------------------

def _norm_word(text: str) -> str:
    return re.sub(r"[^\w%$]", "", text.lower())


def is_emphasis_word(text: str, extra: set) -> bool:
    """Numbers, money, percentages, and any word listed in beat['emphasis'] get the highlight color."""
    return bool(re.search(r"\d", text)) or "%" in text or "$" in text or _norm_word(text) in extra


def build_caption_filters(
    cues: List[Dict[str, Any]],
    work_dir: Path,
    stem: str,
    emphasis: Optional[set] = None,
    highlight_hex: str = "#FFFFFF",
) -> List[str]:
    """Build safe-zone drawtext subtitle filters. Emphasized words are drawn in the highlight color."""
    font = esc_path(Path(FONT_PATH))
    filters: List[str] = []
    cap_y = SAFE_ZONE["caption_y"]
    extra = emphasis or set()
    size = 46
    try:
        pil_font = ImageFont.truetype(FONT_PATH, size)
        asc, desc = pil_font.getmetrics()
        line_h = asc + desc
        space_w = pil_font.getlength(" ")
    except Exception:
        pil_font = None
        line_h = space_w = 0
    hl = highlight_hex.lstrip("#")
    # drawtext places each string by its own glyph extents, so words with/without ascenders drift.
    # "y=<const>-ascent" pins every word to one baseline (verified empirically on ffmpeg 6.1).
    baseline = cap_y + int(size * 0.78) + 2
    box_h = int(size * 1.8)

    for i, cue in enumerate(cues):
        phrase = cue["phrase"]
        s, e = cue["start"], max(cue["end"], cue["start"] + 0.2)
        en = f"enable='between(t\\,{s:.3f}\\,{e:.3f})'"
        words = [w["text"] for w in cue.get("words", [])] or phrase.split()
        has_emph = any(is_emphasis_word(w, extra) for w in words)

        if not has_emph or pil_font is None:
            txt = work_dir / f"{stem}_sub_{i}.txt"
            txt.write_text(phrase, encoding="utf-8")
            filters.append(
                f"drawtext=fontfile='{font}':textfile='{esc_path(txt)}':"
                f"fontsize={size}:fontcolor=white:"
                f"box=1:boxcolor=black@0.78:boxborderw=18:"
                f"x=(w-text_w)/2:y={cap_y}:{en}"
            )
            continue

        widths = [pil_font.getlength(w) for w in words]
        total = sum(widths) + space_w * (len(words) - 1)
        x = (W - total) / 2.0
        pad = 18
        filters.append(
            f"drawbox=x={x - pad:.0f}:y={cap_y - pad}:w={total + 2 * pad:.0f}:h={box_h}:"
            f"color=black@0.78:t=fill:{en}"
        )
        for j, (w, wd) in enumerate(zip(words, widths)):
            txt = work_dir / f"{stem}_sub_{i}_{j}.txt"
            txt.write_text(w, encoding="utf-8")
            color = f"0x{hl}" if is_emphasis_word(w, extra) else "white"
            filters.append(
                f"drawtext=fontfile='{font}':textfile='{esc_path(txt)}':"
                f"fontsize={size}:fontcolor={color}:"
                f"x={x:.1f}:y={baseline}-ascent:{en}"
            )
            x += wd + space_w
    return filters


# ---------------------------------------------------------------------------
# Sequential Bullet-Text Animation via FFmpeg drawtext
# ---------------------------------------------------------------------------

def build_animated_bullet_filters(
    lines: List[str],
    base_time: float,
    total_dur: float,
    work_dir: Path,
    stem: str,
    accent_hex: str,
    y_start: int = 880,
    font_size: int = 44,
    line_gap: int = 64,
) -> List[str]:
    """Animate bullet point lines appearing sequentially over clip duration."""
    if not lines:
        return []

    font = esc_path(Path(FONT_PATH))
    filters = []
    n = len(lines)
    interval = min(1.2, (total_dur - 0.5) / max(n, 1))

    for i, line in enumerate(lines):
        appear_t = base_time + 0.4 + i * interval
        txt = work_dir / f"{stem}_bullet_{i}.txt"
        txt.write_text(line, encoding="utf-8")
        cy = y_start + i * line_gap

        bullet_txt = work_dir / f"{stem}_bmarker_{i}.txt"
        bullet_txt.write_bytes(b">")

        filters.append(
            f"drawtext=fontfile='{font}':textfile='{esc_path(bullet_txt)}':"
            f"fontsize={font_size}:fontcolor=0xFF6B35@0.95:"
            f"x=90:y={cy}:"
            f"enable='between(t\\,{appear_t:.3f}\\,{total_dur:.3f})'"
        )
        filters.append(
            f"drawtext=fontfile='{font}':textfile='{esc_path(txt)}':"
            f"fontsize={font_size}:fontcolor=white@0.96:"
            f"box=0:x=138:y={cy}:"
            f"enable='between(t\\,{appear_t:.3f}\\,{total_dur:.3f})'"
        )

    return filters


def build_vignette_filter() -> str:
    """Add cinematic vignette using FFmpeg vignette filter."""
    return "vignette=PI/4:mode=backward"


# ---------------------------------------------------------------------------
# Segment Renderer — ALWAYS has a background image
# ---------------------------------------------------------------------------

def render_beat_segment(
    beat: Dict[str, Any],
    bg_image_path: Path,
    audio_path: Path,
    out_mp4: Path,
    dur: float,
    audio_dur: float,
    cues: List[Dict[str, Any]],
    motion: str,
    palette: Dict[str, str],
    role: str,
    work_dir: Path,
) -> None:
    """Render one beat segment with real background image and clean text overlays."""
    frames = max(int(dur * FPS), 1)

    blur_amt = 0.0
    darken_amt = 0.15 if role in ("card", "stat", "split", "code", "quote", "outro") else 0.08

    prepped_bg = work_dir / f"{out_mp4.stem}_bg.png"
    prepare_background_image(bg_image_path, prepped_bg, blur_radius=blur_amt, darken=darken_amt)

    use_overlay_png = role in ("intro", "card", "stat", "split", "code", "quote", "outro")
    ov = None

    if use_overlay_png:
        if role == "intro":
            ov = build_intro_hook_overlay(beat, palette)
        elif role == "card":
            ov = build_card_overlay(beat, palette, role)
        elif role == "stat":
            ov = build_stat_overlay(beat, palette)
        elif role == "split":
            ov = build_split_overlay(beat, palette)
        elif role == "code":
            ov = build_code_overlay(beat, palette)
        elif role == "quote":
            ov = build_quote_overlay(beat, palette)
        elif role == "outro":
            ov = build_outro_overlay(beat, palette)

    fade_in = 0.0 if role == "intro" else 0.20
    fade_out = 0.0 if role == "outro" else 0.22
    fade_out_st = max(dur - fade_out, 0.1)

    emph = {_norm_word(str(x)) for x in (beat.get("emphasis") or [])}
    cap_filters = build_caption_filters(
        cues, work_dir, out_mp4.stem, emphasis=emph, highlight_hex=palette.get("highlight", "#FFFFFF")
    )

    if ov:
        ov_path = work_dir / f"{out_mp4.stem}_ov.png"
        ov.save(ov_path, "PNG")

        bg_chain = [
            "scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880",
            f"zoompan={build_motion_expr(motion, frames)}:d={frames}:s={W}x{H}:fps={FPS}",
            build_vignette_filter(),
        ]

        post_chain = []
        if fade_in > 0:
            post_chain.append(f"fade=t=in:st=0:d={fade_in:.2f}")
        if fade_out > 0:
            post_chain.append(f"fade=t=out:st={fade_out_st:.2f}:d={fade_out:.2f}")
        post_chain.extend(cap_filters)

        post_str = ("," + ",".join(post_chain)) if post_chain else ""
        filter_complex = f"[0:v]{','.join(bg_chain)}[bg]; [bg][1:v]overlay=0:0{post_str}[v]"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(prepped_bg),
            "-loop", "1", "-i", str(ov_path),
            "-i", str(audio_path),
            "-t", f"{dur:.3f}",
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "2:a",
            "-af", f"apad=whole_dur={dur:.3f}",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            str(out_mp4),
        ]
    else:
        layers = [
            "scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880",
            f"zoompan={build_motion_expr(motion, frames)}:d={frames}:s={W}x{H}:fps={FPS}",
        ]
        if fade_in > 0:
            layers.append(f"fade=t=in:st=0:d={fade_in:.2f}")
        if fade_out > 0:
            layers.append(f"fade=t=out:st={fade_out_st:.2f}:d={fade_out:.2f}")
        layers.append(build_vignette_filter())
        layers.extend(cap_filters)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(prepped_bg),
            "-i", str(audio_path),
            "-t", f"{dur:.3f}",
            "-vf", ",".join(layers),
            "-af", f"apad=whole_dur={dur:.3f}",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            str(out_mp4),
        ]

    run_cmd(cmd)


# ---------------------------------------------------------------------------
# SFX & Music
# ---------------------------------------------------------------------------

def generate_sfx_audio(sfx_type: str, dest: Path, dur: float = 0.5):
    if sfx_type == "whoosh":
        expr = f"anoisesrc=d={dur}:c=pink:r=44100,bandpass=f=400:w=300,afade=t=in:st=0:d=0.15,afade=t=out:st={max(dur-0.25,0.05):.2f}:d=0.25,volume=0.4"
    elif sfx_type in ("tick", "pop"):
        expr = "sine=frequency=880:duration=0.08,afade=t=out:st=0.02:d=0.06,volume=0.35"
    elif sfx_type in ("ding", "chime"):
        expr = f"sine=frequency=1174.66:duration={dur},afade=t=out:st=0.05:d={max(dur-0.05,0.05):.2f},volume=0.25"
    else:
        expr = "anoisesrc=d=0.2:c=white:r=44100,lowpass=f=600,afade=t=in:st=0:d=0.05,afade=t=out:st=0.1:d=0.1,volume=0.2"

    run_cmd(["ffmpeg", "-y", "-f", "lavfi", "-i", expr, "-c:a", "aac", str(dest)])


def generate_ambient_music(mood: str, total_dur: float, dest: Path) -> Optional[Path]:
    if mood == "none":
        return None

    mood_map = {
        "upbeat-minimal": (220.0, 329.63),
        "tech-pulse": (146.83, 220.0),
        "calm": (174.61, 261.63),
        "ambient": (196.00, 293.66),
    }
    f1, f2 = mood_map.get(mood, (196.00, 293.66))
    fade_st = max(total_dur - 1.5, 0.5)

    fexpr = (
        f"sine=frequency={f1}:duration={total_dur}[s1];"
        f"sine=frequency={f2}:duration={total_dur}[s2];"
        f"[s1][s2]amix=inputs=2:duration=longest,"
        f"lowpass=f=450,volume=0.045,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_st:.2f}:d=1.5"
    )
    run_cmd(["ffmpeg", "-y", "-f", "lavfi", "-i", fexpr, "-c:a", "aac", "-b:a", "128k", str(dest)])
    return dest


# ---------------------------------------------------------------------------
# Metadata & History
# ---------------------------------------------------------------------------

def write_meta(meta_path: Path, data: Dict, dur: float, archetype: str, hook_pattern: str):
    title = data.get("title") or "Key Insights"
    short_title = title[:70] if len(title) <= 70 else title[:67] + "..."
    source = data.get("source") or ""
    tags = ["#Shorts", "#Tips", "#Tech", "#LearnOnYouTube", "#Engineering"]
    meta_path.write_text(
        f"# YouTube Short Metadata\n\n"
        f"- **Title:** {short_title}\n"
        f"- **Duration:** {dur:.1f}s\n"
        f"- **Archetype:** `{archetype}`\n"
        f"- **Hook Pattern:** `{hook_pattern}`\n"
        f"- **Source:** {source}\n\n"
        f"## Description\n{title}\n\nRead full post: {source}\n\n"
        f"{' '.join(tags)}\n\n"
        f"## Pinned Comment\nWhat do you think? Drop a comment below! 👇\n\n"
        f"## Cover Frame\n- Recommended: **00:01.20**\n",
        encoding="utf-8",
    )


def update_history(history_file: Path, entry: Dict):
    records = []
    if history_file.exists():
        try:
            records = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            records = []
    records.append(entry)
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(json.dumps(records[-25:], indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Image Resolution — every beat MUST resolve to a background photo
# ---------------------------------------------------------------------------

def resolve_beat_image(
    beat: Dict[str, Any],
    image_base: Path,
    fallback_pool: List[Path],
    beat_index: int,
) -> Optional[Path]:
    """Return a real image for any beat kind. Falls back to nearest scene image."""
    img_ref = beat.get("image")
    if img_ref:
        p = Path(img_ref)
        if not p.is_file():
            p = image_base / img_ref
        if p.is_file():
            return p

    if fallback_pool:
        return fallback_pool[beat_index % len(fallback_pool)]

    return None


def collect_image_pool(beats: List[Dict], image_base: Path) -> List[Path]:
    """Collect all valid images referenced in beats."""
    pool = []
    for beat in beats:
        img_ref = beat.get("image")
        if img_ref:
            p = Path(img_ref)
            if not p.is_file():
                p = image_base / img_ref
            if p.is_file() and p not in pool:
                pool.append(p)
    return pool


# ---------------------------------------------------------------------------
# Main Render Orchestrator
# ---------------------------------------------------------------------------

def render(
    data: Dict[str, Any],
    output_path: Path,
    voice_name: str,
    max_sec: float,
    image_base: Path,
    export_meta: bool = True,
) -> float:
    beats = data.get("beats") or []
    if not beats:
        raise SystemExit("Error: 'beats' list is empty in beats.json")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="short-render-"))

    archetype_name = data.get("archetype") or "story-arc"
    arch = ARCHETYPES.get(archetype_name, ARCHETYPES["story-arc"])
    palette_name = data.get("palette") or arch["default_palette"]
    palette = PALETTES.get(palette_name, PALETTES["clean-dark"])

    voice_cfg = data.get("voice") or {}
    if isinstance(voice_cfg, str):
        v_raw, v_rate, v_pitch = voice_cfg, "+0%", "+0Hz"
    else:
        v_raw = voice_cfg.get("name") or voice_name
        v_rate = voice_cfg.get("rate") or "+0%"
        v_pitch = voice_cfg.get("pitch") or "+0Hz"

    topic_hint = data.get("title") or (beats[0].get("hook") if beats else "")
    if not v_raw or v_raw.lower() in ("auto", "dynamic"):
        v_name = recommend_voice(topic=topic_hint, archetype=archetype_name)
    else:
        v_name = validate_and_normalize_voice(v_raw, default=DEFAULT_VOICE, topic=topic_hint)

    music_cfg = data.get("music") or {}
    music_mood = music_cfg.get("mood") or arch["music_mood"]
    ending_mode = data.get("ending") or beats[-1].get("ending") or "loop"
    hook_pattern = beats[0].get("hook_pattern") or "bold-claim"
    motion_set = arch["motion_set"]

    image_pool = collect_image_pool(beats, image_base)

    segs = []
    last_motion = ""

    try:
        for i, beat in enumerate(beats):
            kind = (beat.get("kind") or "scene").strip()
            voice_text = (beat.get("voice") or "").strip()
            if not voice_text:
                raise SystemExit(f"Beat {i} missing 'voice' text.")

            audio_path = work / f"voice_{i}.mp3"
            raw_words = synthesize_speech(voice_text, v_name, v_rate, v_pitch, audio_path)
            cues = build_word_cues(raw_words)
            audio_dur = get_media_duration(audio_path)

            tail = 0.08 if (kind == "outro" and ending_mode == "loop") else 0.35
            if beat.get("tail") is not None:
                tail = max(0.0, min(float(beat["tail"]), 1.5))
            beat_palette = PALETTES.get(beat.get("palette") or "", palette)
            seg_dur = audio_dur + tail

            chosen_motion = beat.get("motion")
            if not chosen_motion or chosen_motion == last_motion:
                candidates = [m for m in motion_set if m != last_motion]
                chosen_motion = candidates[i % len(candidates)]
            last_motion = chosen_motion

            sfx_type = beat.get("sfx")
            if sfx_type:
                sfx_path = work / f"sfx_{i}.aac"
                generate_sfx_audio(sfx_type, sfx_path)

            bg_img = resolve_beat_image(beat, image_base, image_pool, i)

            if bg_img is None:
                placeholder = work / f"placeholder_{i}.png"
                bg = Image.new("RGB", (W, H))
                from PIL import ImageDraw as ID2
                d = ID2.Draw(bg)
                accent_rgb = hex_to_rgb(palette["accent"])
                for y in range(H):
                    t = y / H
                    bg_rgb = tuple(int(c * (1 - t) + 5 * t) for c in accent_rgb)
                    d.line([(0, y), (W, y)], fill=bg_rgb)
                bg.save(placeholder, "PNG")
                bg_img = placeholder

            seg_mp4 = work / f"seg_{i}.mp4"
            render_beat_segment(
                beat=beat,
                bg_image_path=bg_img,
                audio_path=audio_path,
                out_mp4=seg_mp4,
                dur=seg_dur,
                audio_dur=audio_dur,
                cues=cues,
                motion=chosen_motion,
                palette=beat_palette,
                role=kind,
                work_dir=work,
            )
            segs.append(seg_mp4)

        arch_transition = data.get("transition") or arch.get("default_transition", "fade")
        if arch_transition not in VALID_TRANSITIONS:
            arch_transition = arch.get("default_transition", "fade")
        top_dur = float(data.get("transition_dur") or DEFAULT_XFADE_DUR)

        # transitions[i] describes the join between segment i-1 and segment i
        transitions: List[Tuple[str, float]] = [("cut", 0.0)]
        for i in range(1, len(beats)):
            t_name = beats[i].get("transition") or arch_transition
            if t_name not in VALID_TRANSITIONS:
                t_name = arch_transition
            t_dur = float(beats[i].get("transition_dur") or top_dur)
            transitions.append((t_name, max(0.08, min(t_dur, 0.6))))

        concat_out = work / "concat_video.mp4"
        if len(segs) == 1:
            run_cmd([
                "ffmpeg", "-y", "-i", str(segs[0]),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "160k",
                str(concat_out),
            ])
        else:
            _chain_segments(segs, concat_out, transitions)

        bar_mode = str(data.get("progress_bar") or "none").lower()
        if bar_mode in ("top", "bottom"):
            concat_out = _add_progress_bar(concat_out, work, palette["accent"], bar_mode)

        total_dur = get_media_duration(concat_out)

        music_file = work / "ambient.aac"
        generate_ambient_music(music_mood, total_dur, music_file)

        final_cmd = ["ffmpeg", "-y", "-i", str(concat_out)]
        if music_file.exists() and music_mood != "none":
            final_cmd += [
                "-i", str(music_file),
                "-filter_complex",
                "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
                "-map", "0:v", "-map", "[aout]",
            ]
        else:
            final_cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]

        final_cmd += [
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            str(output_path),
        ]
        run_cmd(final_cmd)

        final_dur = get_media_duration(output_path)

        if export_meta:
            meta_file = output_path.parent / "meta.md"
            write_meta(meta_file, data, final_dur, archetype_name, hook_pattern)

        history_file = output_path.parent.parent / ".history.json"
        update_history(history_file, {
            "slug": output_path.parent.name,
            "archetype": archetype_name,
            "hook_pattern": hook_pattern,
            "palette": palette_name,
            "music_mood": music_mood,
            "duration": round(final_dur, 1),
        })

    finally:
        shutil.rmtree(work, ignore_errors=True)

    if final_dur > max_sec + 0.1:
        output_path.unlink(missing_ok=True)
        sys.stderr.write(f"\n[OVER_CAP] {final_dur:.1f}s > {max_sec:.0f}s limit.\n")
        raise SystemExit(2)

    return final_dur


def _chain_segments(
    segs: List[Path],
    out: Path,
    transitions: List[Tuple[str, float]],
) -> None:
    """Join segments in one filter graph. Each join is either a hard cut or a real xfade.

    v1 only applied xfade for exactly 2 segments; with 3+ it silently fell back to plain concat.
    """
    durations = [get_media_duration(s) for s in segs]
    cmd = ["ffmpeg", "-y"]
    for s in segs:
        cmd += ["-i", str(s)]

    parts: List[str] = []
    # Normalize every video input to the same fps/timebase; xfade and concat both require it.
    for i in range(len(segs)):
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS},settb=1/{FPS},format=yuv420p[n{i}]")
    vlab, alab = "[n0]", "[0:a]"
    acc = durations[0]
    for i in range(1, len(segs)):
        name, xd = transitions[i]
        xd = min(xd, durations[i] * 0.5, acc * 0.5)
        vout, aout = f"[v{i}]", f"[a{i}]"
        if name == "cut" or xd < 0.05:
            parts.append(f"{vlab}[n{i}]concat=n=2:v=1:a=0,fps={FPS},settb=1/{FPS}{vout}")
            parts.append(f"{alab}[{i}:a]concat=n=2:v=0:a=1{aout}")
            acc += durations[i]
        else:
            offset = max(acc - xd, 0.05)
            parts.append(f"{vlab}[n{i}]xfade=transition={name}:duration={xd:.3f}:offset={offset:.3f},fps={FPS},settb=1/{FPS}{vout}")
            parts.append(f"{alab}[{i}:a]acrossfade=d={xd:.3f}{aout}")
            acc += durations[i] - xd
        vlab, alab = vout, aout

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", vlab, "-map", alab,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k",
        str(out),
    ]
    run_cmd(cmd)


def _add_progress_bar(video: Path, work: Path, accent_hex: str, mode: str) -> Path:
    """Overlay a thin progress bar that fills across the full video (retention cue)."""
    total = max(get_media_duration(video), 0.5)
    y = 120 if mode == "top" else H - 400
    out = work / "concat_bar.mp4"
    run_cmd([
        "ffmpeg", "-y", "-i", str(video),
        "-f", "lavfi", "-i", f"color=c=0x{accent_hex.lstrip('#')}:s={W}x8:r={FPS}:d={total:.3f}",
        "-filter_complex", f"[0:v][1:v]overlay=x='-w+w*t/{total:.3f}':y={y}:shortest=1[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out),
    ])
    return out


# ---------------------------------------------------------------------------
# Self Check
# ---------------------------------------------------------------------------

def self_check():
    print("Running blog-to-shorts cinema engine self-check (Clean Typography Edition)...")
    tmp = Path(tempfile.mkdtemp(prefix="short-selfcheck-"))
    try:
        test_img = tmp / "images" / "test.jpg"
        test_img.parent.mkdir(parents=True)
        bg = Image.new("RGB", (400, 711), color=(30, 45, 80))
        from PIL import ImageDraw as ID2
        d = ID2.Draw(bg)
        for y in range(711):
            r = int(20 + 40 * (y / 711))
            g = int(30 + 60 * (y / 711))
            b = int(80 + 80 * (1 - y / 711))
            d.line([(0, y), (400, y)], fill=(r, g, b))
        bg.save(test_img, "JPEG")

        beats_data = {
            "source": "https://example.com/self-check",
            "title": "Clean Typography Engine Self Check",
            "size": "short",
            "archetype": "stat-drop",
            "palette": "sunset-gold",
            "beats": [
                {
                    "kind": "intro",
                    "hook_pattern": "bold-claim",
                    "hook": "A laboratory technician dead and 200 people isolated immediately",
                    "image": "images/test.jpg",
                    "voice": "This is an automated self-check of the clean typography engine without card boxes.",
                    "motion": "punch-zoom",
                    "sfx": "whoosh",
                },
                {
                    "kind": "stat",
                    "value": "200+",
                    "label": "people under observation",
                    "image": "images/test.jpg",
                    "voice": "Over two hundred people placed under strict medical observation.",
                    "motion": "push-in",
                },
                {
                    "kind": "split",
                    "label_left": "INITIAL REPORT",
                    "before": "A simple case of unknown pneumonia",
                    "label_right": "REALITY",
                    "after": "A broken test tube with live samples",
                    "image": "images/test.jpg",
                    "voice": "Initial reports claimed pneumonia, but the reality was a broken vial.",
                    "motion": "pan-left",
                },
                {
                    "kind": "outro",
                    "hook": "Truth behind closed doors",
                    "image": "images/test.jpg",
                    "voice": "The truth behind closed doors.",
                    "ending": "loop",
                },
            ],
        }
        test_out = tmp / "test_short.mp4"
        total = render(beats_data, test_out, DEFAULT_VOICE, DEFAULT_SHORT_CAP, tmp, export_meta=False)
        assert test_out.exists() and total > 2.0, "Output validation failed"
        print(f"SELF_CHECK_OK: Rendered {total:.1f}s clean typography test Short.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    global FONT_PATH
    parser = argparse.ArgumentParser(description="Render a 9:16 YouTube Short — Cinema Engine (No Cards Edition)")
    parser.add_argument("beats_json", nargs="?")
    parser.add_argument("-o", "--output")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--font", default=None)
    parser.add_argument("--max-sec", type=float, default=None)
    parser.add_argument("--no-meta", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.font:
        FONT_PATH = resolve_font_path(args.font)

    if args.self_check:
        self_check()
        return

    if not args.beats_json or not args.output:
        parser.print_help()
        raise SystemExit(1)

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            sys.stderr.write(f"\n[FATAL] '{tool}' not found on PATH.\n")
            raise SystemExit(1)

    src = Path(args.beats_json).resolve()
    if not src.is_file():
        raise SystemExit(f"File not found: {src}")

    data = json.loads(src.read_text(encoding="utf-8"))
    size_cap = DEFAULT_LONG_CAP if data.get("size") == "long" else DEFAULT_SHORT_CAP
    effective_cap = args.max_sec if args.max_sec is not None else size_cap

    total = render(
        data=data,
        output_path=Path(args.output),
        voice_name=args.voice,
        max_sec=effective_cap,
        image_base=src.parent,
        export_meta=not args.no_meta,
    )
    print(f"OK {args.output} {total:.1f}s")


if __name__ == "__main__":
    main()
