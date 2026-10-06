# Blog to Shorts Skill

Turn any blog post or article URL into a polished 9:16 YouTube Short or Reel with neural voiceover, synchronized captions, subtle photo animations, and catchy hook/fadeout.

## Installation

Install via the open skills CLI into your AI coding assistant (Cursor, Antigravity, Claude Code, Windsurf, etc.):

```bash
npx skills add Harmish001/blog-to-shorts
```

Or install globally:

```bash
npx skills add Harmish001/blog-to-shorts -g
```

## Prerequisites

- **Python 3.8+**
- **FFmpeg & FFprobe** on your `PATH`:
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
  - Windows: `winget install Gyan.FFmpeg` or `choco install ffmpeg`
- **edge-tts** for neural text-to-speech:
  ```bash
  pip install -r requirements.txt
  ```

## How It Works

1. Provide an article URL to your AI agent (or invoke `/blog-to-shorts`).
2. The agent extracts key takeaways, writes a story arc into `shorts/<slug>/beats.json`, and places relevant images.
3. The renderer generates animated video clips, synchronizes speech word timestamps to subtitles, and concats into a vertical 9:16 `.mp4` video.

## Manual Render / Self-Check

You can verify your environment anytime:

```bash
python scripts/render_short.py --self-check
```

Or render manually:

```bash
python scripts/render_short.py shorts/<slug>/beats.json -o shorts/<slug>/short.mp4
```
