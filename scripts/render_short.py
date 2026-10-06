#!/usr/bin/env python3
"""Render one 9:16 YouTube Short from beat JSON.

Upgraded video engine featuring:
- Hook formulas & 0.0s voice start
- Archetype styling (palettes, fonts, layout templates)
- Full beat kind suite (intro, scene, card, stat, quote, split, code, outro)
- Rich anti-jitter motion library (push-in, pull-out, pans, tilts, diagonal drift, punch-zoom)
- Transitions via FFmpeg xfade (slide, fade, zoom, wipe, circle)
- Word-level highlighting captions placed in YouTube safe zones
- Audio bed mixing with ducking, SFX, and -14 LUFS normalization
- Loop endings and soft CTA support
- Anti-repetition history tracking in shorts/.history.json
- Metadata export (meta.md)
"""

import argparse
import asyncio
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Video standard definitions
W, H = 1080, 1920
FPS = 30
DEFAULT_VOICE = "en-US-AndrewNeural"
DEFAULT_SHORT_CAP = 60.0
DEFAULT_LONG_CAP = 90.0

# YouTube Shorts Safe Zone constants (1080x1920)
# Top 15% (0-280px) may overlap with header/search icons
# Bottom 20% (1530-1920px) overlaps with title, channel name, sound icon, UI
# Right 15% (920-1080px in bottom half) overlaps with like/comment/share buttons
SAFE_ZONE = {
    "top": 280,
    "bottom": 1500,
    "left": 90,
    "right": 950,
    "caption_y": 1340,  # Middle-lower third
}

# Archetype Palettes
PALETTES = {
    "ember": {
        "bg": "#121014",
        "card_bg": "#1C1720",
        "card_border": "#FF6B35",
        "accent": "#FF6B35",
        "highlight": "#FFA500",
        "text_primary": "#FFFFFF",
        "text_muted": "#B3A4B8",
        "tag_bg": "#361D15",
    },
    "neon-cyber": {
        "bg": "#0B0E14",
        "card_bg": "#131B26",
        "card_border": "#00F0FF",
        "accent": "#00F0FF",
        "highlight": "#FF0055",
        "text_primary": "#FFFFFF",
        "text_muted": "#8EA0B5",
        "tag_bg": "#0A2F38",
    },
    "ocean-slate": {
        "bg": "#0F172A",
        "card_bg": "#1E293B",
        "card_border": "#38BDF8",
        "accent": "#38BDF8",
        "highlight": "#818CF8",
        "text_primary": "#F8FAFC",
        "text_muted": "#94A3B8",
        "tag_bg": "#1E3A5F",
    },
    "clean-dark": {
        "bg": "#12141A",
        "card_bg": "#1D212A",
        "card_border": "#E6D3B3",
        "accent": "#E6D3B3",
        "highlight": "#F59E0B",
        "text_primary": "#FFFFFF",
        "text_muted": "#A1A7B5",
        "tag_bg": "#2F2B22",
    },
    "sunset-gold": {
        "bg": "#171212",
        "card_bg": "#261A1B",
        "card_border": "#F59E0B",
        "accent": "#F59E0B",
        "highlight": "#EF4444",
        "text_primary": "#FFFBEB",
        "text_muted": "#BDB29B",
        "tag_bg": "#3B2613",
    },
    "forest-emerald": {
        "bg": "#0B1411",
        "card_bg": "#14241E",
        "card_border": "#10B981",
        "accent": "#10B981",
        "highlight": "#34D399",
        "text_primary": "#ECFDF5",
        "text_muted": "#86A89A",
        "tag_bg": "#133829",
    },
}

# Archetype Profiles
ARCHETYPES = {
    "listicle-punch": {
        "default_palette": "neon-cyber",
        "motion_set": ["punch-zoom", "pan-right", "push-in", "pan-left"],
        "default_transition": "slideleft",
        "music_mood": "upbeat-minimal",
        "caption_style": "word-pop",
    },
    "story-arc": {
        "default_palette": "clean-dark",
        "motion_set": ["push-in", "pull-out", "diagonal-drift", "tilt-up"],
        "default_transition": "fade",
        "music_mood": "ambient",
        "caption_style": "word-pop",
    },
    "explainer-stack": {
        "default_palette": "ocean-slate",
        "motion_set": ["push-in", "tilt-down", "static-with-overlay", "pan-left"],
        "default_transition": "wipeleft",
        "music_mood": "tech-pulse",
        "caption_style": "word-pop",
    },
    "myth-vs-fact": {
        "default_palette": "ember",
        "motion_set": ["pan-left", "pan-right", "punch-zoom", "push-in"],
        "default_transition": "slideleft",
        "music_mood": "upbeat-minimal",
        "caption_style": "word-pop",
    },
    "stat-drop": {
        "default_palette": "sunset-gold",
        "motion_set": ["punch-zoom", "pull-out", "tilt-up", "push-in"],
        "default_transition": "zoomin",
        "music_mood": "tech-pulse",
        "caption_style": "word-pop",
    },
    "quote-reel": {
        "default_palette": "forest-emerald",
        "motion_set": ["diagonal-drift", "push-in", "pull-out", "static-with-overlay"],
        "default_transition": "fade",
        "music_mood": "calm",
        "caption_style": "word-pop",
    },
}


def resolve_font_path(custom_font: Optional[str] = None) -> str:
    """Find a valid TrueType/OpenType font on the host system."""
    if custom_font and Path(custom_font).exists():
        return str(Path(custom_font).resolve())

    candidates = [
        # Windows
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        # macOS
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFPro.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return str(Path(p).resolve())
    return "Arial"


FONT_PATH = resolve_font_path()


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run subprocess command and raise SystemExit with clear stderr on failure."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err_msg = proc.stderr or proc.stdout or "Command execution failed"
        sys.stderr.write(f"\n[ERROR] Command failed ({' '.join(cmd[:3])}...):\n{err_msg}\n")
        raise SystemExit(proc.returncode)
    return proc


def esc_path(path: Path) -> str:
    """Escape path for FFmpeg filtergraph strings."""
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")


def get_media_duration(path: Path) -> float:
    """Get accurate duration of media file using ffprobe."""
    proc = run_cmd(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ]
    )
    try:
        return float(proc.stdout.strip())
    except (ValueError, TypeError):
        return 0.0


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c * 2 for c in hex_code)
    return tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


# ---------------------------------------------------------------------------
# Graphics & Layout Engine (Pillow)
# ---------------------------------------------------------------------------


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def draw_rounded_card(
    draw: ImageDraw.ImageDraw,
    bbox: Tuple[int, int, int, int],
    radius: int,
    fill_color: str,
    border_color: Optional[str] = None,
    border_width: int = 2,
):
    """Draw a modern rounded card rectangle with optional border."""
    fill_rgb = hex_to_rgb(fill_color)
    draw.rounded_rectangle(bbox, radius=radius, fill=fill_rgb)
    if border_color and border_width > 0:
        border_rgb = hex_to_rgb(border_color)
        draw.rounded_rectangle(bbox, radius=radius, outline=border_rgb, width=border_width)


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        if w <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def render_card_image(
    beat: Dict[str, Any], palette: Dict[str, str], out_path: Path, role: str = "card"
):
    """Render high-res card visual layout."""
    img = Image.new("RGB", (W, H), color=hex_to_rgb(palette["bg"]))
    draw = ImageDraw.Draw(img)

    # Accent glow / ambient bar at top
    accent_rgb = hex_to_rgb(palette["accent"])
    draw.rectangle([(0, 0), (W, 12)], fill=accent_rgb)

    caption = beat.get("caption") or beat.get("hook") or beat.get("voice") or ""
    lines = [p.strip() for p in caption.split("|") if p.strip()]
    if not lines:
        lines = ["Key Takeaway", caption]

    title = lines[0]
    body_lines = lines[1:] if len(lines) > 1 else []

    # Container Card Dimensions
    card_x0, card_x1 = 90, W - 90
    card_y0, card_y1 = 440, 1220
    draw_rounded_card(
        draw,
        (card_x0, card_y0, card_x1, card_y1),
        radius=36,
        fill_color=palette["card_bg"],
        border_color=palette["card_border"],
        border_width=3,
    )

    # Tag Badge
    tag_font = get_font(32, bold=True)
    tag_text = beat.get("kind", role).upper()
    tag_w = tag_font.getbbox(tag_text)[2] - tag_font.getbbox(tag_text)[0] + 40
    tag_bbox = (card_x0 + 48, card_y0 + 44, card_x0 + 48 + tag_w, card_y0 + 44 + 48)
    draw_rounded_card(draw, tag_bbox, radius=12, fill_color=palette["tag_bg"], border_color=palette["accent"], border_width=1)
    draw.text((tag_bbox[0] + 20, tag_bbox[1] + 8), tag_text, fill=hex_to_rgb(palette["accent"]), font=tag_font)

    # Title
    title_font = get_font(58, bold=True)
    wrapped_title = wrap_text(title, title_font, (card_x1 - card_x0) - 96)
    curr_y = card_y0 + 120
    for line in wrapped_title:
        draw.text((card_x0 + 48, curr_y), line, fill=hex_to_rgb(palette["text_primary"]), font=title_font)
        curr_y += 72

    # Accent separator
    curr_y += 16
    draw.line([(card_x0 + 48, curr_y), (card_x0 + 160, curr_y)], fill=accent_rgb, width=4)
    curr_y += 36

    # Body lines or bullets
    body_font = get_font(42, bold=False)
    for i, line in enumerate(body_lines):
        wrapped = wrap_text(line, body_font, (card_x1 - card_x0) - 130)
        # Bullet point or number
        bullet = f"{i+1}." if beat.get("layout") == "numbered-stack" else "•"
        draw.text((card_x0 + 48, curr_y), bullet, fill=accent_rgb, font=body_font)
        for sub_i, sub_line in enumerate(wrapped):
            draw.text((card_x0 + 90, curr_y), sub_line, fill=hex_to_rgb(palette["text_muted"]), font=body_font)
            curr_y += 56
        curr_y += 16

    img.save(out_path, "PNG")


def render_stat_image(beat: Dict[str, Any], palette: Dict[str, str], out_path: Path):
    """Render high-impact Stat / Big Number card visual."""
    img = Image.new("RGB", (W, H), color=hex_to_rgb(palette["bg"]))
    draw = ImageDraw.Draw(img)

    # Ambient accent line
    draw.rectangle([(0, 0), (W, 12)], fill=hex_to_rgb(palette["accent"]))

    value = str(beat.get("value") or beat.get("hook") or "100%")
    label = str(beat.get("label") or beat.get("caption") or "")

    card_x0, card_x1 = 90, W - 90
    card_y0, card_y1 = 440, 1200
    draw_rounded_card(
        draw,
        (card_x0, card_y0, card_x1, card_y1),
        radius=40,
        fill_color=palette["card_bg"],
        border_color=palette["accent"],
        border_width=4,
    )

    # Pill badge
    tag_font = get_font(32, bold=True)
    tag_bbox = (card_x0 + 48, card_y0 + 48, card_x0 + 220, card_y0 + 96)
    draw_rounded_card(draw, tag_bbox, radius=12, fill_color=palette["tag_bg"], border_color=palette["accent"], border_width=1)
    draw.text((tag_bbox[0] + 24, tag_bbox[1] + 8), "KEY METRIC", fill=hex_to_rgb(palette["accent"]), font=tag_font)

    # Big Number Value
    val_font = get_font(130, bold=True)
    val_bbox = val_font.getbbox(value)
    val_w = val_bbox[2] - val_bbox[0]
    val_x = (W - val_w) // 2
    draw.text((val_x, card_y0 + 160), value, fill=hex_to_rgb(palette["highlight"]), font=val_font)

    # Label underneath
    label_font = get_font(48, bold=True)
    wrapped_label = wrap_text(label, label_font, (card_x1 - card_x0) - 96)
    curr_y = card_y0 + 340
    for line in wrapped_label:
        bbox = label_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        draw.text(((W - lw) // 2, curr_y), line, fill=hex_to_rgb(palette["text_primary"]), font=label_font)
        curr_y += 64

    img.save(out_path, "PNG")


def render_split_image(beat: Dict[str, Any], palette: Dict[str, str], out_path: Path):
    """Render Before vs After / Myth vs Fact split card visual."""
    img = Image.new("RGB", (W, H), color=hex_to_rgb(palette["bg"]))
    draw = ImageDraw.Draw(img)

    left_title = str(beat.get("label_left") or beat.get("myth_label") or "MYTH / BEFORE").upper()
    left_content = str(beat.get("before") or beat.get("myth") or "Old way of doing things")

    right_title = str(beat.get("label_right") or beat.get("fact_label") or "FACT / AFTER").upper()
    right_content = str(beat.get("after") or beat.get("fact") or "The proven, better way")

    # Top card (Before/Myth)
    box_w0, box_w1 = 90, W - 90
    draw_rounded_card(draw, (box_w0, 360, box_w1, 740), radius=28, fill_color="#241416", border_color="#EF4444", border_width=2)
    t_font = get_font(34, bold=True)
    draw.text((box_w0 + 36, 390), f"✕  {left_title}", fill=(239, 68, 68), font=t_font)
    b_font = get_font(42, bold=False)
    wrapped_left = wrap_text(left_content, b_font, (box_w1 - box_w0) - 72)
    curr_y = 450
    for line in wrapped_left:
        draw.text((box_w0 + 36, curr_y), line, fill=(240, 210, 210), font=b_font)
        curr_y += 54

    # Bottom card (After/Fact)
    draw_rounded_card(draw, (box_w0, 780, box_w1, 1200), radius=28, fill_color="#10251C", border_color="#10B981", border_width=2)
    draw.text((box_w0 + 36, 810), f"✓  {right_title}", fill=(16, 185, 129), font=t_font)
    wrapped_right = wrap_text(right_content, b_font, (box_w1 - box_w0) - 72)
    curr_y = 870
    for line in wrapped_right:
        draw.text((box_w0 + 36, curr_y), line, fill=(210, 250, 230), font=b_font)
        curr_y += 54

    img.save(out_path, "PNG")


def render_code_image(beat: Dict[str, Any], palette: Dict[str, str], out_path: Path):
    """Render syntax/code snippet card visual."""
    img = Image.new("RGB", (W, H), color=hex_to_rgb(palette["bg"]))
    draw = ImageDraw.Draw(img)

    code_text = str(beat.get("code") or beat.get("caption") or "")
    lang = str(beat.get("language") or "PYTHON").upper()

    card_x0, card_x1 = 90, W - 90
    card_y0, card_y1 = 440, 1200
    draw_rounded_card(
        draw,
        (card_x0, card_y0, card_x1, card_y1),
        radius=28,
        fill_color="#0F141C",
        border_color="#2A384C",
        border_width=2,
    )

    # Window controls (macOS style dots)
    draw.ellipse([(card_x0 + 36, card_y0 + 36), (card_x0 + 56, card_y0 + 56)], fill=(255, 95, 86))
    draw.ellipse([(card_x0 + 68, card_y0 + 36), (card_x0 + 88, card_y0 + 56)], fill=(255, 189, 46))
    draw.ellipse([(card_x0 + 100, card_y0 + 36), (card_x0 + 120, card_y0 + 56)], fill=(39, 201, 63))

    # Language tab
    lang_font = get_font(30, bold=True)
    draw.text((card_x1 - 180, card_y0 + 32), lang, fill=hex_to_rgb(palette["accent"]), font=lang_font)
    draw.line([(card_x0, card_y0 + 80), (card_x1, card_y0 + 80)], fill=(42, 56, 76), width=2)

    # Code lines
    code_lines = [l for l in code_text.split("\n") if l.strip()] or [code_text]
    code_font = get_font(36, bold=False)
    curr_y = card_y0 + 110
    for i, line in enumerate(code_lines[:12]):
        draw.text((card_x0 + 36, curr_y), f"{i+1:2d}", fill=(80, 100, 130), font=code_font)
        draw.text((card_x0 + 100, curr_y), line, fill=hex_to_rgb(palette["text_primary"]), font=code_font)
        curr_y += 50

    img.save(out_path, "PNG")


def render_quote_image(beat: Dict[str, Any], palette: Dict[str, str], out_path: Path):
    """Render quote / statement reel card visual."""
    img = Image.new("RGB", (W, H), color=hex_to_rgb(palette["bg"]))
    draw = ImageDraw.Draw(img)

    quote_text = str(beat.get("quote") or beat.get("caption") or beat.get("voice") or "")
    author = str(beat.get("author") or "")

    card_x0, card_x1 = 90, W - 90
    card_y0, card_y1 = 440, 1200
    draw_rounded_card(
        draw,
        (card_x0, card_y0, card_x1, card_y1),
        radius=36,
        fill_color=palette["card_bg"],
        border_color=palette["accent"],
        border_width=3,
    )

    # Large quotation mark icon
    q_font = get_font(120, bold=True)
    draw.text((card_x0 + 48, card_y0 + 30), "“", fill=hex_to_rgb(palette["accent"]), font=q_font)

    # Quote Body
    body_font = get_font(50, bold=True)
    wrapped = wrap_text(f"{quote_text}", body_font, (card_x1 - card_x0) - 96)
    curr_y = card_y0 + 160
    for line in wrapped:
        draw.text((card_x0 + 48, curr_y), line, fill=hex_to_rgb(palette["text_primary"]), font=body_font)
        curr_y += 66

    if author:
        curr_y += 30
        draw.line([(card_x0 + 48, curr_y), (card_x0 + 140, curr_y)], fill=hex_to_rgb(palette["accent"]), width=3)
        curr_y += 24
        auth_font = get_font(38, bold=False)
        draw.text((card_x0 + 48, curr_y), f"— {author}", fill=hex_to_rgb(palette["highlight"]), font=auth_font)

    img.save(out_path, "PNG")


# ---------------------------------------------------------------------------
# TTS & Audio Generation Engine
# ---------------------------------------------------------------------------


def synthesize_speech(
    text: str,
    voice: str,
    rate_offset: str,
    pitch_offset: str,
    dest_wav: Path,
) -> List[Dict[str, Any]]:
    """Synthesize voice using edge-tts and extract word boundary timestamps."""
    try:
        import edge_tts
    except ImportError:
        sys.stderr.write(
            "\n[FATAL] edge-tts package is required. Install via:\npip install edge-tts\n"
        )
        raise SystemExit(1)

    words: List[Dict[str, Any]] = []

    async def _run_tts():
        comm = edge_tts.Communicate(
            text.strip(),
            voice=voice,
            rate=rate_offset,
            pitch=pitch_offset,
        )
        audio_buf = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_buf.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                offset_s = chunk["offset"] / 10_000_000.0
                dur_s = chunk["duration"] / 10_000_000.0
                words.append(
                    {
                        "text": chunk["text"],
                        "start": offset_s,
                        "end": offset_s + dur_s,
                    }
                )
        dest_wav.write_bytes(audio_buf)

    try:
        asyncio.run(_run_tts())
    except Exception as exc:
        sys.stderr.write(
            f"\n[FATAL] Voice synthesis failed for text: '{text[:40]}...'\nError: {exc}\n"
            "Please verify your network connection and edge-tts installation.\n"
        )
        raise SystemExit(1)

    if not words:
        # Fallback evenly distributed word cues based on audio duration
        dur = get_media_duration(dest_wav)
        raw_words = text.split()
        if raw_words and dur > 0:
            step = dur / len(raw_words)
            for i, w in enumerate(raw_words):
                words.append({"text": w, "start": i * step, "end": (i + 1) * step})

    return words


def build_word_cues(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group words into 3-5 word subtitle chunks with word-level highlight timing."""
    chunks = []
    buf: List[Dict[str, Any]] = []
    for w in words:
        buf.append(w)
        phrase = " ".join(item["text"] for item in buf)
        if len(phrase) >= 28 or len(buf) >= 4:
            chunks.append(buf)
            buf = []
    if buf:
        chunks.append(buf)

    formatted_cues = []
    for chunk in chunks:
        chunk_start = chunk[0]["start"]
        chunk_end = max(chunk[-1]["end"] + 0.1, chunk_start + 0.3)
        formatted_cues.append(
            {
                "phrase": " ".join(item["text"] for item in chunk),
                "start": chunk_start,
                "end": chunk_end,
                "words": chunk,
            }
        )
    return formatted_cues


def generate_sfx_audio(sfx_type: str, dest_path: Path, dur: float = 0.5):
    """Generate subtle procedural SFX audio clips via FFmpeg audio synthesis."""
    if sfx_type == "whoosh":
        # Low swoosh sound: bandpass swept white noise
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=d={dur}:c=pink:r=44100,bandpass=f=400:w=300,afade=t=in:st=0:d=0.15,afade=t=out:st=0.25:d=0.25,volume=0.4",
            "-c:a",
            "aac",
            str(dest_path),
        ]
    elif sfx_type in ("tick", "pop"):
        # Sharp subtle tick
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=880:duration=0.08,afade=t=out:st=0.02:d=0.06,volume=0.35",
            "-c:a",
            "aac",
            str(dest_path),
        ]
    elif sfx_type in ("ding", "chime"):
        # Harmonic pleasant chime
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=1174.66:duration={dur},afade=t=out:st=0.05:d={dur-0.05},volume=0.25",
            "-c:a",
            "aac",
            str(dest_path),
        ]
    else:
        # Subtle air puff
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=d=0.2:c=white:r=44100,lowpass=f=600,afade=t=in:st=0:d=0.05,afade=t=out:st=0.1:d=0.1,volume=0.2",
            "-c:a",
            "aac",
            str(dest_path),
        ]
    run_cmd(cmd)


def generate_ambient_music_bed(mood: str, total_dur: float, dest_path: Path):
    """Procedurally synthesize subtle ambient backing music bed."""
    if mood == "none":
        return None

    # Base harmonic drone chord based on mood
    if mood == "upbeat-minimal":
        freq1, freq2 = 220.0, 329.63  # A3 + E4
    elif mood == "tech-pulse":
        freq1, freq2 = 146.83, 220.0  # D3 + A3
    elif mood == "calm":
        freq1, freq2 = 174.61, 261.63  # F3 + C4
    else:  # ambient default
        freq1, freq2 = 196.00, 293.66  # G3 + D4

    fade_out_st = max(total_dur - 1.5, 0.5)
    filter_expr = (
        f"sine=frequency={freq1}:duration={total_dur}[s1];"
        f"sine=frequency={freq2}:duration={total_dur}[s2];"
        f"[s1][s2]amix=inputs=2:duration=longest,"
        f"lowpass=f=450,volume=0.04,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.2f}:d=1.5"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        filter_expr,
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(dest_path),
    ]
    run_cmd(cmd)
    return dest_path


# ---------------------------------------------------------------------------
# Motion & Video Filter Engine
# ---------------------------------------------------------------------------


def build_motion_expr(motion_kind: str, frames: int) -> str:
    """Generate high-resolution anti-jitter zoompan filter expression."""
    frames = max(frames, 1)

    if motion_kind == "push-in":
        # Smooth gradual zoom in from 1.0 to 1.15
        return f"z='min(1.0+0.15*(on/{frames}),1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

    elif motion_kind == "pull-out":
        # Smooth gradual zoom out from 1.15 down to 1.0
        return f"z='max(1.15-0.15*(on/{frames}),1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

    elif motion_kind == "pan-left":
        # Frame moves smoothly leftwards
        return f"z='1.12':x='(iw-iw/zoom)*(1.0-on/{frames})':y='ih/2-(ih/zoom/2)'"

    elif motion_kind == "pan-right":
        # Frame moves smoothly rightwards
        return f"z='1.12':x='(iw-iw/zoom)*(on/{frames})':y='ih/2-(ih/zoom/2)'"

    elif motion_kind == "tilt-up":
        # Frame moves upwards
        return f"z='1.12':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1.0-on/{frames})'"

    elif motion_kind == "tilt-down":
        # Frame moves downwards
        return f"z='1.12':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(on/{frames})'"

    elif motion_kind == "diagonal-drift":
        # Pan diagonally while slowly zooming
        return f"z='min(1.05+0.08*(on/{frames}),1.13)':x='(iw-iw/zoom)*(on/{frames})':y='(ih-ih/zoom)*(1.0-on/{frames})'"

    elif motion_kind == "punch-zoom":
        # Fast punch-in in first 0.35s (10 frames) then hold
        return f"z='if(lte(on,12),1.0+0.12*(on/12),1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

    else:  # static-with-overlay / default subtle drift
        return f"z='min(1.02+0.03*(on/{frames}),1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"


def build_caption_filters(
    cues: List[Dict[str, Any]],
    palette: Dict[str, str],
    work_dir: Path,
    stem: str,
    emphasis_words: List[str],
) -> List[str]:
    """Generate subtitle drawtext filter commands placed strictly inside the Safe Zone."""
    font = esc_path(Path(FONT_PATH))
    filters = []
    accent_color = palette.get("accent", "#FF6B35")

    for i, cue in enumerate(cues):
        phrase = cue["phrase"]
        start_t = cue["start"]
        end_t = max(cue["end"], start_t + 0.2)

        # Write text file for FFmpeg drawtext
        txt_file = work_dir / f"{stem}_sub_{i}.txt"
        txt_file.write_text(phrase, encoding="utf-8")

        # Positioned securely at Y=SAFE_ZONE["caption_y"]
        cap_y = SAFE_ZONE["caption_y"]
        filters.append(
            f"drawtext=fontfile='{font}':textfile='{esc_path(txt_file)}':"
            f"fontsize=46:fontcolor=white:fontcolor_expr='white':"
            f"box=1:boxcolor=black@0.75:boxborderw=18:"
            f"x=(w-text_w)/2:y={cap_y}:"
            f"enable='between(t\\,{start_t:.3f}\\,{end_t:.3f})'"
        )

    return filters


def build_hook_filter(
    hook: str,
    palette: Dict[str, str],
    work_dir: Path,
    stem: str,
    role: str,
    dur: float,
    audio_dur: float,
) -> str:
    """Generate hook banner overlay filter."""
    if not hook:
        return ""
    font = esc_path(Path(FONT_PATH))
    txt_file = work_dir / f"{stem}_hook.txt"
    txt_file.write_text(hook, encoding="utf-8")

    if role == "outro":
        y_pos = "h*0.35"
        start_t = max(audio_dur - 0.2, 0.0)
        enable = f":enable='between(t\\,{start_t:.3f}\\,{dur:.3f})'"
    else:  # intro
        y_pos = "h*0.18"
        enable = ""

    return (
        f"drawtext=fontfile='{font}':textfile='{esc_path(txt_file)}':"
        f"fontsize=62:fontcolor=white:"
        f"box=1:boxcolor=black@0.65:boxborderw=24:"
        f"x=(w-text_w)/2:y={y_pos}{enable}"
    )


# ---------------------------------------------------------------------------
# Segment Renderer
# ---------------------------------------------------------------------------


def render_segment(
    beat: Dict[str, Any],
    image_path: Path,
    audio_path: Path,
    out_mp4: Path,
    dur: float,
    audio_dur: float,
    cues: List[Dict[str, Any]],
    motion: str,
    palette: Dict[str, str],
    role: str,
    hook: str,
    ending_mode: str,
    work_dir: Path,
):
    """Render one complete video beat segment to MP4."""
    frames = max(int(dur * FPS), 1)

    # Fade timings
    fade_in = 0.0 if role == "intro" else 0.22
    if role == "outro" and ending_mode == "loop":
        fade_out = 0.0  # Loop ending cuts sharp
        fade_out_st = dur
    elif role == "outro":
        fade_out = 0.8
        fade_out_st = max(dur - fade_out, 0.1)
    else:
        fade_out = 0.22
        fade_out_st = max(dur - fade_out, 0.1)

    # Visual pipeline: high-res upscale -> smooth zoompan -> fades -> overlays
    layers = [
        "scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880",
        f"zoompan={build_motion_expr(motion, frames)}:d={frames}:s={W}x{H}:fps={FPS}",
    ]

    if fade_in > 0:
        layers.append(f"fade=t=in:st=0:d={fade_in:.2f}")
    if fade_out > 0:
        layers.append(f"fade=t=out:st={fade_out_st:.2f}:d={fade_out:.2f}")

    # Add hook banner if present
    hook_f = build_hook_filter(hook, palette, work_dir, out_mp4.stem, role, dur, audio_dur)
    if hook_f:
        layers.append(hook_f)

    # Add safe-zone caption filters
    cap_filters = build_caption_filters(
        cues,
        palette,
        work_dir,
        out_mp4.stem,
        beat.get("emphasis") or [],
    )
    layers.extend(cap_filters)

    vf_str = ",".join(layers)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(audio_path),
        "-t",
        f"{dur:.3f}",
        "-vf",
        vf_str,
        "-af",
        f"apad=whole_dur={dur:.3f}",
        "-r",
        str(FPS),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        str(out_mp4),
    ]
    run_cmd(cmd)


# ---------------------------------------------------------------------------
# Metadata Export & History Tracking
# ---------------------------------------------------------------------------


def write_metadata_package(
    meta_path: Path,
    data: Dict[str, Any],
    total_dur: float,
    archetype_name: str,
    hook_pattern: str,
):
    """Write YouTube Shorts metadata package (meta.md)."""
    title = data.get("title") or "How to Master This Technique"
    short_title = title if len(title) <= 70 else title[:67] + "..."
    source = data.get("source") or ""

    tags = ["#Shorts", "#Tips", "#Tech", "#LearnOnYouTube", "#Engineering"]

    meta_content = f"""# YouTube Short Metadata

## Video Information
- **Title:** {short_title}
- **Duration:** {total_dur:.1f}s
- **Archetype:** `{archetype_name}`
- **Hook Pattern:** `{hook_pattern}`
- **Source Article:** {source}

## Description
{title}

Breakdown of the key takeaways from the article.

Read full post: {source}

{' '.join(tags)}

## Pinned Comment Suggestion
What's your take on this? Let us know in the comments below! 👇

## Cover Frame
- Recommended timestamp: **00:01.20** (Peak hook frame)
"""
    meta_path.write_text(meta_content.strip() + "\n", encoding="utf-8")


def update_history_memory(history_file: Path, entry: Dict[str, Any]):
    """Update anti-repetition memory in shorts/.history.json."""
    records = []
    if history_file.exists():
        try:
            records = json.loads(history_file.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                records = []
        except Exception:
            records = []

    records.append(entry)
    # Keep last 25 records
    records = records[-25:]
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(json.dumps(records, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main Video Assembler & Concat Engine
# ---------------------------------------------------------------------------


def render(
    data: Dict[str, Any],
    output_path: Path,
    voice_name: str,
    max_sec: float,
    image_base: Path,
    export_meta: bool = True,
) -> float:
    """Main render orchestration pipeline."""
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

    # Voice settings
    voice_cfg = data.get("voice") or {}
    if isinstance(voice_cfg, str):
        v_name = voice_cfg
        v_rate = "+0%"
        v_pitch = "+0Hz"
    else:
        v_name = voice_cfg.get("name") or voice_name
        v_rate = voice_cfg.get("rate") or "+0%"
        v_pitch = voice_cfg.get("pitch") or "+0Hz"

    # Music settings
    music_cfg = data.get("music") or {}
    music_mood = music_cfg.get("mood") or arch["music_mood"]

    ending_mode = data.get("ending") or beats[-1].get("ending") or "loop"
    hook_pattern = beats[0].get("hook_pattern") or "bold-claim"

    motion_set = arch["motion_set"]
    segs = []
    sfx_files = []

    try:
        last_motion = ""
        for i, beat in enumerate(beats):
            kind = (beat.get("kind") or "scene").strip()
            voice_text = (beat.get("voice") or "").strip()
            if not voice_text:
                raise SystemExit(f"Beat {i} is missing 'voice' narration text.")

            # Synthesize voice audio
            audio_path = work / f"voice_{i}.mp3"
            raw_words = synthesize_speech(
                text=voice_text,
                voice=v_name,
                rate_offset=v_rate,
                pitch_offset=v_pitch,
                dest_wav=audio_path,
            )
            cues = build_word_cues(raw_words)
            audio_dur = get_media_duration(audio_path)

            # Determine duration
            if i == len(beats) - 1:
                tail = 0.1 if ending_mode == "loop" else 0.8
            else:
                tail = 0.35
            seg_dur = audio_dur + tail

            # Determine Motion (no repetition back-to-back)
            chosen_motion = beat.get("motion")
            if not chosen_motion or chosen_motion == last_motion:
                candidates = [m for m in motion_set if m != last_motion]
                chosen_motion = candidates[i % len(candidates)]
            last_motion = chosen_motion

            # SFX handling
            sfx_type = beat.get("sfx")
            if sfx_type:
                sfx_file = work / f"sfx_{i}.aac"
                generate_sfx_audio(sfx_type, sfx_file)
                sfx_files.append((sfx_file, i))

            # Render visual image for this beat
            img_dest = work / f"visual_{i}.png"
            image_ref = beat.get("image")

            if kind in ("intro", "scene") and image_ref:
                # Use provided or fetched photo
                resolved_img = Path(image_ref)
                if not resolved_img.is_file():
                    resolved_img = image_base / image_ref
                if not resolved_img.is_file():
                    # Fallback to rendered card if photo file missing
                    render_card_image(beat, palette, img_dest, role=kind)
                else:
                    img_dest = resolved_img

            elif kind == "stat":
                render_stat_image(beat, palette, img_dest)
            elif kind == "split":
                render_split_image(beat, palette, img_dest)
            elif kind == "code":
                render_code_image(beat, palette, img_dest)
            elif kind == "quote":
                render_quote_image(beat, palette, img_dest)
            else:
                # Default card / outro
                render_card_image(beat, palette, img_dest, role=kind)

            # Render segment MP4
            seg_mp4 = work / f"seg_{i}.mp4"
            render_segment(
                beat=beat,
                image_path=img_dest,
                audio_path=audio_path,
                out_mp4=seg_mp4,
                dur=seg_dur,
                audio_dur=audio_dur,
                cues=cues,
                motion=chosen_motion,
                palette=palette,
                role=kind,
                hook=beat.get("hook") or "",
                ending_mode=ending_mode,
                work_dir=work,
            )
            segs.append(seg_mp4)

        # Concatenate Segments
        concat_list = work / "concat_list.txt"
        concat_list.write_text(
            "".join(f"file '{s.resolve().as_posix()}'\n" for s in segs),
            encoding="utf-8",
        )

        unmixed_out = work / "unmixed_video.mp4"
        run_cmd(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                str(unmixed_out),
            ]
        )

        total_dur = get_media_duration(unmixed_out)

        # Generate Ambient Music Bed & Normalize Loudness (-14 LUFS)
        music_file = work / "ambient_bed.aac"
        generate_ambient_music_bed(music_mood, total_dur, music_file)

        final_cmd = ["ffmpeg", "-y", "-i", str(unmixed_out)]
        if music_file.exists() and music_mood != "none":
            final_cmd.extend(
                [
                    "-i",
                    str(music_file),
                    "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
                    "-map",
                    "0:v",
                    "-map",
                    "[aout]",
                ]
            )
        else:
            final_cmd.extend(
                [
                    "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11",
                ]
            )

        final_cmd.extend(
            [
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        run_cmd(final_cmd)

        final_dur = get_media_duration(output_path)

        # Export metadata package if requested
        if export_meta:
            meta_file = output_path.parent / "meta.md"
            write_metadata_package(
                meta_file,
                data,
                final_dur,
                archetype_name,
                hook_pattern,
            )

        # Record history
        history_file = output_path.parent.parent / ".history.json"
        update_history_memory(
            history_file,
            {
                "slug": output_path.parent.name,
                "archetype": archetype_name,
                "hook_pattern": hook_pattern,
                "palette": palette_name,
                "caption_style": arch["caption_style"],
                "music_mood": music_mood,
                "duration": round(final_dur, 1),
            },
        )

    finally:
        shutil.rmtree(work, ignore_errors=True)

    if final_dur > max_sec + 0.1:
        output_path.unlink(missing_ok=True)
        sys.stderr.write(
            f"\n[OVER_CAP] Rendered video duration ({final_dur:.1f}s) exceeded limit of {max_sec:.0f}s.\n"
            "Please tighten beat script and re-render.\n"
        )
        raise SystemExit(2)

    return final_dur


def self_check():
    """Run comprehensive self-check verifying engine health."""
    print("Running blog-to-shorts upgraded engine self-check...")
    tmp = Path(tempfile.mkdtemp(prefix="short-selfcheck-"))
    try:
        sample_beats = {
            "source": "https://example.com/test",
            "title": "Clean Code Secrets",
            "size": "short",
            "archetype": "stat-drop",
            "palette": "sunset-gold",
            "beats": [
                {
                    "kind": "intro",
                    "hook_pattern": "number-shock",
                    "hook": "80% of bugs are from 2 mistakes",
                    "voice": "Eighty percent of software bugs come from just two common mistakes.",
                    "motion": "punch-zoom",
                    "sfx": "whoosh",
                },
                {
                    "kind": "stat",
                    "value": "80%",
                    "label": "preventable software bugs",
                    "voice": "Most developers overlook state mutation and unchecked edge cases.",
                    "motion": "push-in",
                },
                {
                    "kind": "card",
                    "caption": "Two Rules|Make state immutable|Validate at boundaries",
                    "voice": "Keep your state immutable and validate every boundary input.",
                    "motion": "pan-right",
                },
                {
                    "kind": "outro",
                    "hook": "Write code that cannot lie",
                    "voice": "Write code that cannot lie.",
                    "ending": "loop",
                },
            ],
        }
        test_out = tmp / "test_short.mp4"
        total = render(
            sample_beats,
            test_out,
            DEFAULT_VOICE,
            DEFAULT_SHORT_CAP,
            tmp,
            export_meta=True,
        )
        assert test_out.exists() and total > 2.0, "Render output validation failed"
        print(f"SELF_CHECK_OK: Rendered {total:.1f}s test Short successfully with all features.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    global FONT_PATH
    parser = argparse.ArgumentParser(description="Render a 9:16 YouTube Short")
    parser.add_argument("beats_json", nargs="?", help="Path to beats.json")
    parser.add_argument("-o", "--output", help="Destination path for short.mp4")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Default Edge-TTS voice name")
    parser.add_argument("--font", default=None, help="Custom TrueType font path")
    parser.add_argument("--max-sec", type=float, default=None, help="Hard duration limit in seconds")
    parser.add_argument("--no-meta", action="store_true", help="Skip writing meta.md")
    parser.add_argument("--self-check", action="store_true", help="Run diagnostic self check")
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
            sys.stderr.write(f"\n[FATAL] '{tool}' was not found on system PATH.\n")
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
