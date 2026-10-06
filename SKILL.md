---
name: blog-to-shorts
description: >-
  Turn one blog URL into one polished, YouTube-ready 9:16 Short (30-45s for short posts,
  60-75s for guides) with archetype-driven styling, high-retention hook formulas, neural
  voiceover starting at 0.0s, word-level captions in YouTube safe zones, anti-jitter motion,
  dynamic visual cards (stats, split screens, code, quotes), subtle audio ducking, loop
  endings, and metadata generation.
disable-model-invocation: true
---

# Blog to Shorts

Turn one blog or article URL into an engaging, YouTube-ready 9:16 vertical Short that holds viewer retention and does not look like an auto-generated slideshow.

## Core Rules

- **One URL in, one Short package out**: Video (`short.mp4`) + metadata (`meta.md`). Ask for the URL if missing.
- **Narrative Storytelling**: Tell a story in full sentences. Contractions are welcome. Connect ideas with *when*, *so*, and *if*. Never read out bullet points, colons, or labels like "point one".
- **Factual Fidelity**: Say only what the article backs up. No hallucinations or invented claims.
- **English by Default**: If the article is not English, stop and ask the user before translating.
- **Length & Sizing**:
  - `size: "short"` (1 core idea / quick takeaway): **Target 30–45 seconds**. Hard cap **60 seconds**.
  - `size: "long"` (deep dive / tutorial / multi-step case): **Target 60–75 seconds**. Hard cap **90 seconds**.
  - If a comprehensive guide exceeds 90s, split it into a numbered multi-part series (Part 1, Part 2) instead of compressing it into a rushed readout.
- **Voice Starts at 0.0s**: The spoken voiceover must start immediately on the very first frame. No title slides, no intro logos, and no "Hey guys / In this video".
- **Safe Zone Placement**: All critical text and captions are kept in the central 80% safe zone (middle-lower third at ~`y=1340px`), away from YouTube's top search bar, right-side buttons, and bottom channel/title overlay.
- **Anti-Repetition**: Consult `shorts/.history.json` before writing. Never use the same archetype, hook formula, or palette as the preceding short.

---

## 1. Hook Formulas (Pick One per Short)

The first beat is always `kind: "intro"`. Pick one hook formula that best matches the article angle. The spoken hook must be **<= 12 words** and begin at 0.0s.

| Hook Formula | Structure | Example |
| :--- | :--- | :--- |
| **Bold Claim** | A surprising, contrarian statement proven in the post | *"Your database cache is quietly lying to you."* |
| **Number Shock** | An eye-opening metric or cost stated first | *"A 0.1 second delay just cost you 7% of your revenue."* |
| **Mistake Callout** | Highlights what the majority does wrong | *"Most developers write clean code completely wrong."* |
| **Question Gap** | A compelling question the viewer cannot yet answer | *"Do you know what actually happens inside a JWT token?"* |
| **Before / After** | Sharp contrast between old struggle and new fix | *"Stop writing 50 lines of boilerplate for one API call."* |
| **Mid-Story Drop** | Drops right into the most dramatic turning point | *"At 3 AM, every single primary database dropped offline."* |

---

## 2. Archetypes & Visual Styling

Select the archetype that fits the article type. Archetypes automatically determine color palettes, motion profiles, default transitions, and music mood:

| Archetype | Best For | Default Palette | Motion Profile | Music Mood |
| :--- | :--- | :--- | :--- | :--- |
| `listicle-punch` | Tip roundups, tool reviews | `neon-cyber` | Punch-zoom & fast horizontal pans | `upbeat-minimal` |
| `story-arc` | Case studies, post-mortems, essays | `clean-dark` | Smooth push-ins & pulls | `ambient` |
| `explainer-stack` | Concepts, how-tos, architectures | `ocean-slate` | Push-in, tilt-down, static overlay | `tech-pulse` |
| `myth-vs-fact` | Best practice debates, dos & don'ts | `ember` | Split pans & punch-zooms | `upbeat-minimal` |
| `stat-drop` | Data-heavy posts, benchmark tests | `sunset-gold` | Punch-zoom & count-up stat cards | `tech-pulse` |
| `quote-reel` | Philosophy, interviews, principles | `forest-emerald` | Diagonal drift & elegant typography | `calm` |

### Color Palettes Available
- `neon-cyber`: Cyan (`#00F0FF`) + Neon Pink (`#FF0055`) on Deep Slate (`#0B0E14`)
- `clean-dark`: Warm Cream (`#E6D3B3`) + Amber Gold (`#F59E0B`) on Charcoal (`#12141A`)
- `ocean-slate`: Sky Blue (`#38BDF8`) + Indigo (`#818CF8`) on Dark Navy (`#0F172A`)
- `ember`: Fire Orange (`#FF6B35`) + Amber (`#FFA500`) on Dark Violet (`#121014`)
- `sunset-gold`: Warm Amber (`#F59E0B`) + Coral Red (`#EF4444`) on Warm Black (`#171212`)
- `forest-emerald`: Emerald Green (`#10B981`) + Mint (`#34D399`) on Dark Pine (`#0B1411`)

---

## 3. Beat Kinds & Motion Library

To keep videos visually dynamic and prevent the "AI slideshow" look, **no more than 50% of beats should be photo stills**. Alternate with high-impact visual cards:

### Available Beat Kinds:
1. `intro`: Hook text banner + moving background/card. Spoken narration starts at 0.0s.
2. `scene`: Photo from article or AI generated 9:16 still with camera motion.
3. `card`: Clean UI card with title and body lines (e.g. `layout: "numbered-stack"`). Split lines with `|`.
4. `stat`: Big-number callout (`value: "10x"`, `label: "faster page loads"`).
5. `split`: Before vs After / Myth vs Fact two-panel comparison (`before: "..."`, `after: "..."`).
6. `code`: Code snippet window with syntax-styled lines (`language: "python"`, `code: "..."`).
7. `quote`: Large quotation statement with author attribution (`quote: "..."`, `author: "..."`).
8. `outro`: Resolution beat. Supports seamless `ending: "loop"` or `ending: "fade"`.

### Motion Types (Never repeat the same motion back-to-back):
- `push-in`: Smooth gradual zoom-in (1.0 -> 1.15)
- `pull-out`: Smooth zoom-out (1.15 -> 1.0)
- `pan-left` / `pan-right`: Smooth horizontal window tracking
- `tilt-up` / `tilt-down`: Smooth vertical window tracking
- `diagonal-drift`: Combined diagonal pan and subtle scale
- `punch-zoom`: Rapid 0.35s snap zoom for emphasis
- `static-with-overlay`: Subtle ambient float

---

## 4. Extended `beats.json` Schema

Save the beat plan to `shorts/<slug>/beats.json`:

```json
{
  "source": "https://example.com/post-slug",
  "title": "Clean Code Rules That Actually Matter",
  "size": "short",
  "archetype": "stat-drop",
  "palette": "sunset-gold",
  "seed": 48213,
  "voice": {
    "name": "en-US-AndrewNeural",
    "rate": "+4%",
    "pitch": "+0Hz"
  },
  "music": {
    "mood": "tech-pulse",
    "duck_db": -14
  },
  "cta": "none",
  "beats": [
    {
      "kind": "intro",
      "hook_pattern": "number-shock",
      "hook": "80% of bugs come from 2 mistakes",
      "voice": "Eighty percent of software bugs come from just two common mistakes.",
      "motion": "punch-zoom",
      "sfx": "whoosh"
    },
    {
      "kind": "stat",
      "value": "80%",
      "label": "preventable software bugs",
      "voice": "Most developers overlook state mutation and unhandled edge cases.",
      "motion": "push-in"
    },
    {
      "kind": "split",
      "label_left": "Common Mistake",
      "before": "Mutating shared global state across functions",
      "label_right": "Clean Fix",
      "after": "Return immutable copies or pure function results",
      "voice": "Stop mutating shared global state. Always return pure, immutable values.",
      "motion": "pan-left"
    },
    {
      "kind": "card",
      "layout": "numbered-stack",
      "caption": "Action Items|Enforce immutability|Validate input boundaries",
      "voice": "Enforce immutability in your models, and validate all input boundaries.",
      "motion": "pan-right"
    },
    {
      "kind": "outro",
      "hook": "Write code that cannot lie",
      "voice": "Write code that cannot lie.",
      "ending": "loop"
    }
  ]
}
```

---

## 5. Workflow Steps

```
Task Progress:
- [ ] Check shorts/.history.json for last archetype and hook
- [ ] Fetch the blog URL and extract core takeaways
- [ ] Pick fresh Archetype, Hook Formula, and Palette
- [ ] Write shorts/<slug>/beats.json with varied beat kinds
- [ ] Render video and generate shorts/<slug>/meta.md
- [ ] Verify QA checklist before replying
```

### Step 1: Anti-Repetition Check
Read `shorts/.history.json` (if present). Ensure your new Short uses a different archetype, hook formula, and palette than the previous 3 entries.

### Step 2: Extract & Structure
Read the article body. Determine whether `short` (30–45s) or `long` (60–75s) is best.

### Step 3: Write Beats
Assemble 4–7 beats. Ensure:
- Voice begins at 0.0s.
- Hook voice is <= 12 words.
- At least 3 different beat kinds are used.
- Motions vary across adjacent beats.

### Step 4: Render Video
Run the render script from the skill directory:

```bash
python <skill-path>/scripts/render_short.py shorts/<slug>/beats.json -o shorts/<slug>/short.mp4
```

The renderer automatically:
1. Synthesizes voiceover with WordBoundary timestamps via `edge-tts`.
2. Generates crisp, high-DPI Pillow visual cards for `stat`, `card`, `split`, `code`, `quote`.
3. Scales stills to 1620x2880 to guarantee zero-jitter smooth motion.
4. Places word-pop subtitles safely in the YouTube Safe Zone (`y=1340px`).
5. Ducks ambient backing audio by -14dB and normalizes audio to -14 LUFS standard.
6. Exports `shorts/<slug>/meta.md` with YouTube title, description, tags, and cover frame timestamp.
7. Logs execution into `shorts/.history.json`.

---

## 6. Pre-Flight QA Checklist

Before reporting completion to the user, verify:
- [x] Voice starts at 0.0s on the very first frame.
- [x] Spoken hook is <= 12 words and uses a recognized hook formula.
- [x] No motion type repeated consecutively.
- [x] Captions and cards are placed inside the YouTube Safe Zone (no bottom UI clipping).
- [x] No single image reused across multiple scenes.
- [x] Archetype differs from the previous entry in `shorts/.history.json`.
- [x] Final video duration is within the cap (<=60s for short, <=90s for long).
- [x] `shorts/<slug>/meta.md` is generated and formatted.
