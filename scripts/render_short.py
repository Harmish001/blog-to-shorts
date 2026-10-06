#!/usr/bin/env python3
"""Render one 9:16 YouTube Short from beat JSON.

Needs ffmpeg and edge-tts (neural voice). Falls back to Windows SAPI
if the neural voice cannot be reached.
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 1080, 1920
FONT = "C:/Windows/Fonts/segoeuib.ttf"
BG = "0x12141a"
ACCENT = "0xE6D3B3"
DEFAULT_VOICE = "en-US-AndrewNeural"
SHORT_CAP = 70.0
LONG_CAP = 120.0


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "command failed\n")
        raise SystemExit(proc.returncode)
    return proc


def esc_filter_path(path):
    return str(path).replace("\\", "/").replace(":", "\\:")


def duration(path):
    proc = run(
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
    return float(proc.stdout.strip())


def speak_sapi(text, wav):
    txt = wav.with_suffix(".voice.txt")
    ps1 = wav.with_suffix(".ps1")
    txt.write_bytes((text.strip() + "\n").encode("utf-8"))
    ps1.write_text(
        "\n".join(
            [
                "Add-Type -AssemblyName System.Speech",
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer",
                "$s.Rate = 0",
                "$s.SetOutputToWaveFile('%s')" % str(wav).replace("'", "''"),
                "$s.Speak((Get-Content -LiteralPath '%s' -Raw -Encoding UTF8))"
                % str(txt).replace("'", "''"),
                "$s.Dispose()",
            ]
        ),
        encoding="utf-8",
    )
    run(["powershell", "-NoProfile", "-File", str(ps1)])


def ticks_to_sec(value):
    value = float(value)
    if value > 1000:
        return value / 10000000.0
    return value


def group_cues(words):
    lines = []
    buf = []
    for word in words:
        buf.append(word)
        phrase = " ".join(item["text"] for item in buf)
        if len(phrase) >= 34 or len(buf) >= 5:
            lines.append(buf)
            buf = []
    if buf:
        lines.append(buf)
    cues = []
    for i, group in enumerate(lines):
        start = group[0]["start"]
        end = group[-1]["end"] + 0.05
        if i + 1 < len(lines):
            end = min(end, lines[i + 1][0]["start"])
        cues.append((" ".join(item["text"] for item in group), start, max(end, start + 0.2)))
    return cues


def even_cues(text, dur):
    words = text.split()
    if not words or dur <= 0:
        return []
    step = dur / len(words)
    raw = []
    for i, word in enumerate(words):
        raw.append({"text": word, "start": i * step, "end": (i + 1) * step})
    return group_cues(raw)


def speak(text, dest, voice):
    try:
        import edge_tts
    except ImportError:
        speak_sapi(text, dest)
        return even_cues(text, duration(dest))

    async def _save():
        comm = edge_tts.Communicate(text.strip(), voice, rate="-8%")
        audio = bytearray()
        words = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = ticks_to_sec(chunk["offset"])
                length = ticks_to_sec(chunk["duration"])
                words.append(
                    {"text": chunk["text"], "start": start, "end": start + length}
                )
        dest.write_bytes(audio)
        return words

    try:
        words = asyncio.run(_save())
    except Exception as exc:
        sys.stderr.write("neural voice failed (%s); using Windows voice\n" % exc)
        speak_sapi(text, dest.with_suffix(".wav"))
        if dest.suffix != ".wav" and dest.with_suffix(".wav").exists():
            dest.with_suffix(".wav").replace(dest)
        return even_cues(text, duration(dest))
    if not words:
        return even_cues(text, duration(dest))
    return group_cues(words)


def write_line(path, text):
    path.write_bytes(" ".join(text.split()).encode("utf-8"))


def fade(dur):
    tail = max(dur - 0.4, 0.1)
    return "fade=t=in:st=0:d=0.35,fade=t=out:st=%.3f:d=0.35" % tail


def move_expr(kind, frames):
    if kind == "out":
        z = "if(lte(on,1),1.15,max(zoom-0.0011,1.0))"
        return "z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" % z
    if kind == "left":
        return (
            "z='1.12':x='(iw-iw/zoom)*(1-on/%d)':y='ih/2-(ih/zoom/2)'" % frames
        )
    if kind == "right":
        return "z='1.12':x='(iw-iw/zoom)*on/%d':y='ih/2-(ih/zoom/2)'" % frames
    return "z='min(1.0+0.0011*on,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"


def caption_filters(cues, work, stem):
    font = esc_filter_path(FONT)
    parts = []
    for i, (text, start, end) in enumerate(cues):
        path = work / ("%s-sub%d.txt" % (stem, i))
        write_line(path, text)
        parts.append(
            "drawtext=fontfile='%s':textfile='%s':fontsize=40:fontcolor=white:"
            "box=1:boxcolor=black@0.62:boxborderw=16:x=(w-text_w)/2:y=h-text_h-110:"
            "enable='between(t\\,%.3f\\,%.3f)'"
            % (font, esc_filter_path(path), start, max(end, start + 0.15))
        )
    return parts


def hook_filter(hook, work, stem, role, style, dur, audio_dur):
    if not hook:
        return ""
    path = work / ("%s-hook.txt" % stem)
    write_line(path, hook)
    font = esc_filter_path(FONT)
    if role == "outro":
        y = ["(h/2)-80", "(h/2)-220", "(h/2)-40"][style % 3]
        start = max(audio_dur - 0.3, 0)
        enable = ":enable='between(t\\,%.3f\\,%.3f)'" % (start, dur)
    else:
        y = ["h*0.18", "h*0.32", "h*0.46"][style % 3]
        enable = ""
    return (
        "drawtext=fontfile='%s':textfile='%s':fontsize=62:fontcolor=white:"
        "box=1:boxcolor=black@0.35:boxborderw=22:x=(w-text_w)/2:y=%s%s"
        % (font, esc_filter_path(path), y, enable)
    )


def render_scene(image, audio, out_mp4, dur, move, cues, role, hook, style, audio_dur):
    frames = max(int(dur * 30), 1)
    work = out_mp4.parent
    fade_in = 0.8 if role == "intro" else 0.28
    fade_out = 1.15 if role == "outro" else 0.32
    fade_out_at = max(dur - fade_out, 0.1)
    layers = [
        "scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880",
        "zoompan=%s:d=%d:s=%dx%d:fps=30" % (move_expr(move, frames), frames, W, H),
        "fade=t=in:st=0:d=%.2f,fade=t=out:st=%.3f:d=%.2f" % (fade_in, fade_out_at, fade_out),
    ]
    hook_vf = hook_filter(hook, work, out_mp4.stem, role, style, dur, audio_dur)
    if hook_vf:
        layers.append(hook_vf)
    layers.extend(caption_filters(cues, work, out_mp4.stem))
    vf = ",".join(layers)
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-t",
            "%.3f" % dur,
            "-vf",
            vf,
            "-af",
            "apad=whole_dur=%.3f" % dur,
            "-r",
            "30",
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
    )


def render_card(caption, audio, out_mp4, dur, cues, role="card"):
    lines = [part.strip() for part in caption.split("|") if part.strip()]
    if not lines:
        raise SystemExit("card caption empty")
    work = out_mp4.parent
    title = lines[0]
    body = lines[1:]
    gap = 68
    stack = 80 + (gap * len(body) if body else 0)
    title_y = stack // 2
    if role == "outro":
        parts = [
            "fade=t=in:st=0:d=0.35,fade=t=out:st=%.3f:d=1.15" % max(dur - 1.15, 0.1)
        ]
    elif role == "intro":
        parts = ["fade=t=in:st=0:d=0.8,fade=t=out:st=%.3f:d=0.32" % max(dur - 0.32, 0.1)]
    else:
        parts = [fade(dur)]
    parts.append(
        "drawbox=x=(w-160)/2:y=(h/2)-%d:w=160:h=4:color=%s:t=fill"
        % (title_y + 28, ACCENT)
    )
    title_path = work / (out_mp4.stem + "-title.txt")
    write_line(title_path, title)
    parts.append(
        "drawtext=fontfile='%s':textfile='%s':fontsize=60:fontcolor=white:"
        "x=(w-text_w)/2:y=(h/2)-%d"
        % (esc_filter_path(FONT), esc_filter_path(title_path), title_y)
    )
    if body:
        font = esc_filter_path(FONT)
        for i, line in enumerate(body):
            path = work / ("%s-b%d.txt" % (out_mp4.stem, i))
            write_line(path, line)
            y = "(h/2)-%d+%d" % (title_y - 84, i * gap)
            parts.append(
                "drawtext=fontfile='%s':textfile='%s':fontsize=40:fontcolor=white:"
                "x=(w-text_w)/2:y=%s" % (font, esc_filter_path(path), y)
            )
    parts.extend(caption_filters(cues, work, out_mp4.stem))
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=%s:s=%dx%d:r=30:d=%.3f" % (BG, W, H, dur),
            "-i",
            str(audio),
            "-vf",
            ",".join(parts),
            "-af",
            "apad=whole_dur=%.3f" % dur,
            "-t",
            "%.3f" % dur,
            "-r",
            "30",
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
    )


def render(beats, output, voice, max_sec, image_base, title=""):
    if not beats:
        raise SystemExit("beats empty")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="short-"))
    moves = ["in", "out", "left", "right"]
    # Shift the move cycle from the title so two videos do not open the same way.
    style = sum(ord(ch) for ch in (title or "x")) % 3
    segs = []
    scene_i = style
    try:
        for i, beat in enumerate(beats):
            voice_text = (beat.get("voice") or "").strip()
            caption = (beat.get("caption") or "").strip()
            hook = (beat.get("hook") or "").strip()
            if not voice_text:
                raise SystemExit("beat %d missing voice" % i)
            audio = work / ("%d.mp3" % i)
            cues = speak(voice_text, audio, voice)
            audio_dur = duration(audio)
            kind = (beat.get("kind") or "scene").strip()
            tail = 1.25 if kind == "outro" else 0.4
            dur = audio_dur + tail
            seg = work / ("%d.mp4" % i)
            image = beat.get("image")
            if image and kind != "card":
                render_scene(
                    resolve_image(image, image_base),
                    audio,
                    seg,
                    dur,
                    moves[scene_i % len(moves)],
                    cues,
                    kind,
                    hook,
                    style,
                    audio_dur,
                )
                scene_i += 1
            else:
                render_card(
                    caption or hook or voice_text,
                    audio,
                    seg,
                    dur,
                    cues,
                    kind,
                )
            segs.append(seg)
        listing = work / "list.txt"
        listing.write_text(
            "".join("file '%s'\n" % seg.as_posix() for seg in segs),
            encoding="utf-8",
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(listing),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "30",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
        total = duration(output)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if total > max_sec + 0.05:
        output.unlink(missing_ok=True)
        sys.stderr.write("OVER_CAP %.1fs > %.0fs\n" % (total, max_sec))
        raise SystemExit(2)
    return total


def resolve_image(image, base):
    path = Path(image)
    if not path.is_file():
        path = base / image
    if not path.is_file():
        raise SystemExit("image missing: %s" % image)
    return path


def cap_for(data, override):
    if override is not None:
        return override
    return LONG_CAP if data.get("size") == "long" else SHORT_CAP


def self_check():
    tmp = Path(tempfile.mkdtemp(prefix="short-check-"))
    try:
        beats = [
            {
                "kind": "card",
                "caption": "The point|Said in a sentence",
                "voice": "The point is said in a sentence.",
            }
        ]
        out = tmp / "check.mp4"
        total = render(beats, out, DEFAULT_VOICE, LONG_CAP, tmp, "check")
        assert out.exists() and 0.5 < total < 20, total
        print("SELF_CHECK_OK %.1fs" % total)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Render a 9:16 YouTube Short")
    parser.add_argument("beats_json", nargs="?")
    parser.add_argument("-o", "--output")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--max-sec", type=float, default=None)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    if not args.beats_json or not args.output:
        raise SystemExit("usage: render_short.py beats.json -o out.mp4")
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit("%s not on PATH" % tool)
    src = Path(args.beats_json)
    data = json.loads(src.read_text(encoding="utf-8"))
    total = render(
        data["beats"],
        args.output,
        args.voice,
        cap_for(data, args.max_sec),
        src.parent,
        data.get("title") or "",
    )
    print("OK %s %.1fs" % (args.output, total))


if __name__ == "__main__":
    main()
