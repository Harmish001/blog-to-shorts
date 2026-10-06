---
name: blog-to-shorts
description: >-
  Turn one blog URL into one polished, YouTube-ready 9:16 Short (30-45s for short posts,
  60-75s for guides) with archetype-driven styling, high-retention hook formulas, neural
  voiceover starting at 0.0s, word-level captions in YouTube safe zones, cinema-grade
  camera motions, glass-morphism text overlays always over a real background photo,
  animated sequential bullet reveals, dynamic voice selection, ambient audio ducking,
  loop endings, and metadata generation.
disable-model-invocation: true
---

# Blog to Shorts — Cinema Engine

Turn one blog or article URL into an engaging, YouTube-ready 9:16 vertical Short that holds viewer retention and does **not** look like an auto-generated AI slideshow.

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

## 3. Dynamic Voice Selection (Edge-TTS Models)

The agent dynamically selects the voiceover model based on the article's topic, tone, and archetype. Only valid voices from the official Edge-TTS catalog are supported (see `scripts/voices.py`).

| Topic / Tone Category | Recommended Voice | Gender | Voice Personality | Best Fit For |
| :--- | :--- | :--- | :--- | :--- |
| **Tech Architecture / Deep Dives / Outages** | `en-US-ChristopherNeural` | Male | Reliable, Authority | Backend post-mortems, systems, databases, cloud architecture |
| **AI Breakthroughs / Bold Tech / Startups** | `en-US-GuyNeural` | Male | Passion, High Energy | Exciting releases, AI benchmarks, startup launches, speed tips |
| **Tutorials / How-To / Guides / SaaS** | `en-US-JennyNeural` | Female | Friendly, Considerate | Developer onboarding, how-tos, step-by-step explainer stacks |
| **Data / Metrics / Benchmarks / Clean Code** | `en-US-EricNeural` | Male | Rational, Analytical | Stats drops, refactoring, algorithms, math, benchmarks |
| **Listicles / Tips / Quick Hacks** | `en-US-RogerNeural` | Male | Lively, Engaging | Fast-paced listicles, top 5 tools, productivity shortcuts |
| **Product Announcements / News** | `en-US-AriaNeural` | Female | Positive, Confident | Official feature updates, product reveals, overview shorts |
| **Global / British English** | `en-GB-RyanNeural` / `en-GB-SoniaNeural` | Male/Female | Friendly, Professional | International engineering and design topics |
| **India Developer Community** | `en-IN-PrabhatNeural` / `en-IN-NeerjaNeural` | Male/Female | Friendly, Positive | India-focused tech ecosystem content |

*Rule:* You can set `"name": "auto"` or an explicit voice in `beats.json`. If an unsupported voice name is provided, the renderer automatically normalizes to the closest supported match.

---

## 4. Beat Kinds, Motion Library & Cinema Rules

> **Cinema Rule**: Every single beat MUST have an `"image"` field pointing to a real background photo. The renderer places all text overlays (points, stat, split, code, quote, outro) directly over the photo using clean Inter typography and dark gradient backdrops — **NO ugly rectangular card boxes or outlined containers**. If a beat omits its `image` key, the renderer automatically pools images from other beats as a fallback.

### Available Beat Kinds

1. **`intro`**: Hook text fades in over a background photo with a gradient darkening strip at the top. Text is wrapped to max 22 characters per line to eliminate edge clipping.
2. **`scene`**: Full-bleed background photo with camera motion only. Voice narrates over it.
3. **`card`**: Clean text points composited directly over the background photo (NO card box container). Title + bullet lines with **sequential animated reveal** (each line appears one by one with timed delay). Split caption fields with `|`.
4. **`stat`**: Big-number callout (`value: "200+"`, `label: "people under observation"`) rendered directly over the background photo. Value renders in the palette highlight color with drop shadow.
5. **`split`**: Before vs After / Myth vs Fact comparison rendered directly over the background photo. Compact pill tags for category labels (`✕ INITIAL REPORT` / `✓ REALITY`) with body text underneath.
6. **`code`**: Terminal window overlay with macOS-style window dots composited over the background photo. Up to 12 lines of monospace code.
7. **`quote`**: Typographic quote with large opening `"` mark and author attribution, composited over background photo.
8. **`outro`**: Cinematic final beat — **NO card box**. Hook text rendered large and centered over background photo with vignette. Accent separator line below.

### Motion Library (Never repeat back-to-back)

| Motion | Effect | When to Use |
| :--- | :--- | :--- |
| `push-in` | Smooth ease-in zoom 1.0→1.18 | Opening emphasis, stat reveals |
| `pull-out` | Smooth ease-out zoom 1.18→1.0 | Resolution, outro pulls |
| `pan-left` | Horizontal track across frame | Mid-story scene changes |
| `pan-right` | Horizontal track opposite | Alternating scene beats |
| `tilt-up` | Vertical track upward | Reveal / ascent moments |
| `tilt-down` | Vertical track downward | Code reveals, descent |
| `diagonal-drift` | Combined diagonal pan + scale | Quote reels, cinematic scenes |
| `punch-zoom` | Rapid 14-frame snap zoom in | Hook punch, big stat reveals |
| `handheld-left` | Slow rightward drift + vertical sine wobble | Authentic handheld feel |
| `handheld-right` | Slow leftward drift + vertical sine wobble | Varied handheld continuity |
| `handheld-drift` | Organic 2D float with no clear direction | Story narration, subtle presence |

### Transition Types

Transitions between segments are automatically set per archetype:
- `listicle-punch`, `myth-vs-fact`: `slideleft`
- `story-arc`, `quote-reel`: `fade`
- `explainer-stack`: `wipeleft`
- `stat-drop`: `zoomin`

---

## 5. Beat JSON Schema — Complete Reference

> **Image Rule**: The `image` field is **required** on every beat. Use a relative path from the `beats.json` directory. The renderer resolves all image paths relative to the directory containing `beats.json`.

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
      "image": "images/code_bug.jpg",
      "voice": "Eighty percent of software bugs come from just two common mistakes.",
      "motion": "punch-zoom",
      "sfx": "whoosh"
    },
    {
      "kind": "stat",
      "value": "80%",
      "label": "preventable software bugs",
      "image": "images/code_bug.jpg",
      "voice": "Most developers overlook state mutation and unhandled edge cases.",
      "motion": "push-in"
    },
    {
      "kind": "split",
      "label_left": "Common Mistake",
      "before": "Mutating shared global state across functions",
      "label_right": "Clean Fix",
      "after": "Return immutable copies or pure function results",
      "image": "images/refactor.jpg",
      "voice": "Stop mutating shared global state. Always return pure, immutable values.",
      "motion": "pan-left"
    },
    {
      "kind": "card",
      "layout": "numbered-stack",
      "caption": "Action Items|Enforce immutability|Validate input boundaries",
      "image": "images/code_bug.jpg",
      "voice": "Enforce immutability in your models, and validate all input boundaries.",
      "motion": "handheld-drift"
    },
    {
      "kind": "outro",
      "hook": "Write code that cannot lie",
      "image": "images/code_bug.jpg",
      "voice": "Write code that cannot lie.",
      "ending": "loop"
    }
  ]
}
```

### Beat Field Reference

| Field | Required | Type | Description |
| :--- | :--- | :--- | :--- |
| `kind` | ✅ | string | Beat type: `intro`, `scene`, `card`, `stat`, `split`, `code`, `quote`, `outro` |
| `image` | ✅ | string | **Relative path to background photo.** Used as a persistent background for the entire beat. |
| `voice` | ✅ | string | Spoken narration text. Full sentences, no bullet labels. |
| `motion` | ✅ | string | Camera motion type (see motion library above). Never repeat back-to-back. |
| `hook` | Intro/Outro | string | Displayed hook text (≤ 12 words for intro). |
| `caption` | Card | string | Card title + body lines split by `\|`. First segment = title. |
| `layout` | Card | string | `"numbered-stack"` for numbered items (default: bullet `▸`). |
| `value` | Stat | string | Large stat value e.g. `"53%"`, `"10x"`, `"$4B"`. |
| `label` | Stat | string | Stat explanation label text. |
| `before` / `after` | Split | string | Left (red) and right (green) panel content. |
| `label_left` / `label_right` | Split | string | Panel header labels e.g. `"MYTH"` / `"FACT"`. |
| `code` | Code | string | Code snippet text (newlines as `\n`). Up to 12 lines. |
| `language` | Code | string | Language badge shown in terminal chrome e.g. `"Python"`. |
| `quote` | Quote | string | Full quotation text. |
| `author` | Quote | string | Attribution name shown after `—`. |
| `sfx` | Optional | string | Sound effect: `"whoosh"`, `"tick"`, `"chime"`, `"ding"`. |
| `ending` | Outro | string | `"loop"` (tight cut for looping) or `"fade"`. |
| `hook_pattern` | Intro | string | Hook formula name for QA tracking. |

---

## 6. Workflow Steps

```
Task Progress:
- [ ] Check shorts/.history.json for last archetype and hook
- [ ] Fetch the blog URL and extract core takeaways
- [ ] Pick fresh Archetype, Hook Formula, and Palette
- [ ] Source or generate background images for each beat
- [ ] Write shorts/<slug>/beats.json with varied beat kinds and image fields
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
- **Every beat has an `image` field** pointing to a real photo.

### Step 4: Source Background Images
Before rendering, ensure every beat's image path resolves:
- Use the `generate_image` tool to create cinematic 9:16 background photos if none are available.
- Store generated images in `shorts/<slug>/images/`.
- Use descriptive, relevant images — not generic stock photos.

### Step 5: Render Video

```bash
python <skill-path>/scripts/render_short.py shorts/<slug>/beats.json -o shorts/<slug>/short.mp4
```

The cinema renderer automatically:
1. Synthesizes voiceover with WordBoundary timestamps via `edge-tts`.
2. Prepares background photo for every beat (scale, crop, optional blur for readability).
3. Composites glass-morphism overlays (card/stat/split/code/quote/outro) as RGBA PNGs on top of the photo.
4. Applies organic camera motion (push-in, handheld-drift, punch-zoom, etc.) with cubic easing.
5. Adds cinematic vignette filter to every segment.
6. Renders sequential bullet reveals for `card` beats via timed FFmpeg `drawtext` filters.
7. Places word-pop captions in the YouTube Safe Zone (`y≈1320px`).
8. Chains segments with xfade transitions (slideleft, fade, wipeleft, zoomin).
9. Mixes ambient backing audio ducked under voice and normalizes to -14 LUFS.
10. Exports `shorts/<slug>/meta.md` with YouTube title, description, tags, and cover frame timestamp.
11. Logs execution into `shorts/.history.json`.

---

## 7. Pre-Flight QA Checklist

Before reporting completion to the user, verify:
- [x] Voice starts at 0.0s on the very first frame.
- [x] Spoken hook is <= 12 words and uses a recognized hook formula.
- [x] No motion type repeated consecutively.
- [x] **Every beat has an `image` field** with a valid file path.
- [x] Captions and cards are placed inside the YouTube Safe Zone (no bottom UI clipping).
- [x] Outro renders as hook text over photo — NOT as a card box.
- [x] Archetype differs from the previous entry in `shorts/.history.json`.
- [x] Final video duration is within the cap (<=60s for short, <=90s for long).
- [x] `shorts/<slug>/meta.md` is generated and formatted.
