# Blog to Shorts Skill

Turn any blog post or article URL into a high-retention, YouTube-ready 9:16 vertical Short or Reel with neural voiceovers, dynamic visual templates, synchronized word-level captions, safe-zone layouts, subtle audio beds, and metadata packaging.

---

## Key Features

- 🎯 **High-Retention Hook Formulas**: Bold claims, number shock, mistake callouts, question gaps, and mid-story drops with voice starting at 0.0s.
- 🎨 **Archetype System**: Choose between 6 distinct visual archetypes (`listicle-punch`, `story-arc`, `explainer-stack`, `myth-vs-fact`, `stat-drop`, `quote-reel`) with curated palettes and motion profiles.
- 📊 **Dynamic Visual Beat Kinds**: Crisp Pillow-rendered visuals for Stats, Split Comparisons (Before vs After), Code Windows, Quotes, and Numbered Cards.
- 🎥 **Anti-Jitter Motion Engine**: 9 smooth camera motion styles (`push-in`, `pull-out`, `pan-left`, `pan-right`, `tilt-up`, `tilt-down`, `diagonal-drift`, `punch-zoom`, `static-with-overlay`).
- 🛡️ **YouTube Safe Zone Compliance**: Subtitles and visual overlays stay out of YouTube's bottom overlay zone (channel name, title, audio tags, action buttons).
- 🎵 **Audio Engineering & Ducking**: Background music beds ducked under speech (-14dB), procedural SFX, and YouTube-standard -14 LUFS loudness normalization.
- 🔁 **Loop Endings**: Seamless cutoff transitions that hook back into the opening frame for maximum replay retention.
- 🧠 **Anti-Repetition Memory**: Tracks past renders in `shorts/.history.json` to guarantee consecutive shorts feel fresh and distinct.
- 📝 **Metadata Packaging**: Automatically exports `meta.md` containing YouTube Short titles (<=70 chars), descriptions, hashtags, pinned comment prompts, and recommended cover timestamps.

---

## Installation

Install via the open skills CLI into your AI coding assistant (Cursor, Antigravity, Claude Code, Windsurf, etc.):

```bash
npx skills add Harmish001/blog-to-shorts
```

Or install globally:

```bash
npx skills add Harmish001/blog-to-shorts -g
```

---

## Prerequisites

- **Python 3.8+**
- **FFmpeg & FFprobe** on your `PATH`:
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
  - Windows: `winget install Gyan.FFmpeg` or `choco install ffmpeg`
- **Python Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```
  *(Requires `edge-tts` and `Pillow`)*

---

## How It Works

1. Provide an article URL to your AI agent (or invoke `/blog-to-shorts`).
2. The agent reads `shorts/.history.json`, picks a fresh Archetype, Hook formula, and Palette, and writes `shorts/<slug>/beats.json`.
3. The renderer generates crisp card graphics, synchronizes speech word timestamps to subtitles, applies smooth motion filters, mixes background audio, and exports `shorts/<slug>/short.mp4` and `shorts/<slug>/meta.md`.

---

## Example Archetypes

Pre-built template configurations are available in the [`examples/`](./examples) directory:

- [`examples/listicle_punch.json`](./examples/listicle_punch.json) — Fast-paced tool/tip lists with neon cyber aesthetics.
- [`examples/story_arc.json`](./examples/story_arc.json) — Engaging case studies and outage post-mortems.
- [`examples/explainer_stack.json`](./examples/explainer_stack.json) — Step-by-step concept tutorials with code snippets.
- [`examples/stat_drop.json`](./examples/stat_drop.json) — High-impact data and benchmark metrics with big number callouts.
- [`examples/myth_vs_fact.json`](./examples/myth_vs_fact.json) — Side-by-side comparison cards and practice breakdowns.
- [`examples/quote_reel.json`](./examples/quote_reel.json) — Elegant typography statements and philosophy highlights.

---

## Manual Render & Self-Check

Verify your local rendering environment:

```bash
python scripts/render_short.py --self-check
```

Render an existing beat plan manually:

```bash
python scripts/render_short.py shorts/<slug>/beats.json -o shorts/<slug>/short.mp4
```

CLI Flags:
- `--voice <name>`: Custom Edge-TTS voice (default: `en-US-AndrewNeural`)
- `--font <path>`: Custom `.ttf` font path
- `--max-sec <float>`: Override duration limit cap
- `--no-meta`: Skip writing `meta.md`
- `--self-check`: Run end-to-end diagnostic test
