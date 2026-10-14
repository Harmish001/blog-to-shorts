---
name: blog-to-shorts
version: 2.0.0
description: Turn one blog URL into a YouTube Short that is designed around that specific post. First finds the post's most shareable angle, then picks a format (myth-buster, stat-drop, post-mortem story, code reveal, tips countdown, explainer, contrarian take, showdown, tutorial, quote reel) based on content signals, writes and scores multiple hooks, builds a retention-mapped script with pattern interrupts, art-directs unique per-beat visuals, self-critiques before rendering, and reviews real frames after rendering. Voice starts at 0.0s, captions stay in safe zones, ends on a loop.
disable-model-invocation: true
---

# Blog to Shorts v2: Angle-First Engine

Turn one blog or article URL into a vertical 9:16 Short that a stranger would stop scrolling for, watch to the end, and send to a friend.

**The v1 mistake this version fixes:** v1 picked a template and then poured the blog into it, so every video felt alike. v2 works in the opposite order: **blog -> angle -> format -> script -> visuals -> self-critique -> render -> frame review.**

## Core Rules

- **One URL in, one Short package out**: `short.mp4` + `meta.md`. Ask for the URL if missing.
- **Content decides the video.** Never choose a format, palette, or voice before the Shareability Brief (Step 1) is written.
- **Factual fidelity.** Every claim, number, and quote must come from the article. If you can't point to the sentence that backs it, cut it.
- **English by default.** If the article isn't English, stop and ask before translating.
- **Voice starts at 0.0s.** No title card, logo, or "Hey guys".
- **Spoken language, not written language.** Contractions, short sentences, concrete nouns. Never read bullets, colons, or labels aloud.
- **Safe zone.** Keep critical text inside the central 80%, captions around `y~1340px`, clear of YouTube's top bar, right-side buttons, and bottom channel/title area.
- **Length.** `short` = 30-45s (hard cap 60s). `long` = 55-75s (hard cap 90s). If a guide needs more than 90s, split it into Part 1 / Part 2 and end Part 1 on a cliffhanger.
- **Variety comes from content, not from rotation.** `shorts/.history.json` is only a tie-breaker (see Step 3), never a reason to pick a worse fit.

---

## Step 0: Is this post Short-worthy?

Read the full article first. If it has no surprising fact, no tension, no concrete outcome, and no clear takeaway, **do not render a weak video.** Tell the user in two lines what's missing and propose 2 candidate angles that might work (or a different post).

---

## Step 1: Shareability Brief (write this before anything else)

Save as `shorts/<slug>/brief.md`. Keep it under 15 lines.

```
CORE TENSION:    the conflict, mistake, surprise, or cost at the heart of the post (1 sentence)
BEST FACT:       the single most surprising/specific claim in the article + the sentence that backs it
VIEWER:          who stops for this (e.g. junior dev, founder, student) and what they fear or want
EMOTION:         pick one -> curiosity | fear-of-missing-out | vindication | awe | humor | urgency | calm
PROOF ASSETS:    which of these the post actually contains -> number | before/after | code | quote | story | steps | comparison | metaphor
VISUAL NATURE:   abstract concept | physical/real-world | UI/software | people | data
ONE-LINE PROMISE: what the viewer will know after 40 seconds
```

If you can't fill `BEST FACT` and `CORE TENSION` with specifics, go back to Step 0.

---

## Step 2: Pick the Format from Content Signals

Scan the brief's `PROOF ASSETS` and `EMOTION`. Pick the **first row that fits strongly**. Each format maps to renderer settings and a beat blueprint. Blueprints are starting points: add, drop, or reorder beats to serve the story, but keep at least **4 different beat kinds** and a **pattern interrupt** (Step 5).

| # | Format | Choose when the post... | Renderer `archetype` | Suggested `palette` | Beat blueprint |
| :-- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Myth Buster** | corrects a common belief or practice | `myth-vs-fact` | `ember` | intro (mistake callout) -> split -> scene (why it happens) -> stat (proof) -> card (the fix) -> outro |
| 2 | **Number Shock** | is led by a striking metric or benchmark | `stat-drop` | `sunset-gold` | intro (number first) -> stat -> scene (what it means) -> stat or split -> card (what to do) -> outro |
| 3 | **Post-mortem Story** | tells what happened, failure, or case study | `story-arc` | `clean-dark` | intro (mid-story drop) -> scene -> scene -> stat (the damage) -> scene (turning point) -> card (lesson) -> outro |
| 4 | **Code Reveal** | contains a code before/after or a surprising snippet | `explainer-stack` | `ocean-slate` | intro (bold claim) -> code (bad) -> split or code (good) -> stat (impact) -> outro |
| 5 | **Tips Countdown** | lists 3-5 tips, tools, or rules | `listicle-punch` | `neon-cyber` | intro (promise + count) -> card per tip (1 tip per beat, different image each) -> outro |
| 6 | **How It Really Works** | explains a mechanism or architecture | `explainer-stack` | `ocean-slate` | intro (question gap) -> scene (metaphor) -> card (3 steps) -> scene (where it breaks) -> outro |
| 7 | **Contrarian Take** | argues against the mainstream view | `quote-reel` or `story-arc` | `forest-emerald` / `clean-dark` | intro (bold claim) -> quote (author's strongest line) -> scene (evidence) -> split (old vs new) -> outro |
| 8 | **Showdown** | compares two tools, approaches, or options | `myth-vs-fact` | `neon-cyber` | intro (A vs B) -> split -> stat -> split -> verdict card -> outro |
| 9 | **Tutorial in 60s** | walks through a how-to | `explainer-stack` | `ocean-slate` | intro (before/after outcome) -> card (numbered steps) -> code or scene -> scene (common mistake) -> outro |
| 10 | **Principle Reel** | is philosophy, interview, or principles | `quote-reel` | `forest-emerald` | intro (question gap) -> quote -> scene -> quote or card -> outro |

**Palette override rule:** the renderer accepts any `palette` with any `archetype`. Choose palette by the post's **mood** (urgent/hot -> `ember`; trustworthy/technical -> `ocean-slate`; serious/reflective -> `clean-dark`; hype/new -> `neon-cyber`; money/results -> `sunset-gold`; calm/growth -> `forest-emerald`), not by what the format table suggests, if they disagree.

Write the chosen format and a one-sentence reason into `brief.md`.

---

## Step 3: Anti-Repetition (tie-breaker only)

Read `shorts/.history.json` if present.
- If two formats fit equally well, pick the one **not** used in the last 3 shorts.
- Never reuse the same **hook formula + palette** combination as the previous short.
- Never sacrifice fit for novelty: a Number Shock post stays a Number Shock even if the last one was too.

---

## Step 4: Hooks. Write 5, Score, Pick 1

The first 3 seconds decide everything. Write **5 candidate spoken hooks** (<= 12 words each), one per different formula where possible, all built from the article's real content:

| Formula | Pattern | Example |
| :--- | :--- | :--- |
| Bold Claim | surprising statement the post proves | "Your cache is quietly lying to you." |
| Number Shock | striking metric first | "One 0.1 second delay cost 7% of revenue." |
| Mistake Callout | what most people do wrong | "Most developers handle errors completely backwards." |
| Question Gap | a question the viewer can't answer yet | "What actually happens inside a JWT?" |
| Before / After | old pain vs new fix | "Stop writing 50 lines for one API call." |
| Mid-Story Drop | start at the dramatic moment | "At 3 AM, every primary database went dark." |
| Stakes First | what the viewer stands to lose | "This one setting can leak your users' data." |

**Score each hook 1-5 on:** (a) would I stop scrolling? (b) is it specific (names a number, thing, or moment)? (c) does it open a gap the video closes? Pick the highest total. Reject any hook that:
- starts with "In this video", "Today", "Let's talk about", or "Did you know"
- uses vague words (amazing, powerful, game-changing) without a concrete detail
- gives away the full answer

**On-screen hook text** is a punchier compression of the spoken hook, **<= 6 words** where possible, not a duplicate transcript.

---

## Step 5: Script to a Retention Map

Write the voiceover as spoken script, then split into beats. One idea per beat. **6-14 spoken words per beat** (~2.5 words/sec), so beats land at ~2.5-6 seconds. Total beats: 6-10 for `short`, 9-13 for `long`.

| Time | Job | How |
| :--- | :--- | :--- |
| 0-3s | **Hook** | The chosen hook, nothing before it |
| 3-8s | **Stakes + open loop** | Why it matters to the viewer, and a promise ("here's the part nobody checks") |
| ~40% mark | **Pattern interrupt** | A re-hook line ("But here's the catch.") **and** a change in beat kind, motion, and image. Re-grabs viewers about to swipe. |
| Middle | **Delivery** | One new fact or visual every <= 5s. Never two beats of the same kind back-to-back unless it's a Tips Countdown |
| Last 5-8s | **Payoff + loop** | Land the takeaway, then end on a line that flows naturally back into the hook (grammatically if possible), so the replay feels seamless |

Script rules:
- Use "you" often. Address one person.
- Prefer verbs over adjectives. Cut every sentence that doesn't add a fact, feeling, or turn.
- Numbers spoken naturally ("eighty percent", "two hundred milliseconds").
- Read the script aloud in your head. If you'd stumble, rewrite.
- Never invent urgency or stats the article doesn't contain.

---

## Step 6: Art Direction (each Short looks different because each post is different)

**Style bible (one line, decided per Short):** from `VISUAL NATURE` and `EMOTION`, write one sentence defining the visual language, e.g. *"macro photography of server hardware, cold blue light, shallow depth of field"* or *"warm film-grain street scenes at night"*. Every image in this Short follows it. Next Short, with a different post, gets a different bible.

**Per-beat image prompt template:**
`<specific subject that illustrates THIS beat's idea>, <concrete metaphor or setting>, <style bible>, vertical 9:16 composition, quiet dark area in upper third for text, no text, no logos, no watermarks, no UI screenshots with readable text`

Image rules:
- **Every beat gets its own image.** Reuse at most one: the outro may reuse the intro image to support the loop.
- Images must illustrate the beat's meaning (a stat about outages -> a dark server room, not a generic laptop).
- Avoid generic AI-looking stock: no glowing brains, floating cubes, or handshake silhouettes unless the post is literally about them.
- If the blog's author is the user and the post has its own diagrams or screenshots, they may be used for `scene` beats where they genuinely clarify.
- Store in `shorts/<slug>/images/`, named by beat (`01_intro.jpg`, `02_split.jpg`, ...).

**Motion:** match the emotion. Urgent -> `punch-zoom`, `handheld-left/right`. Reflective -> `push-in`, `pull-out`, `handheld-drift`. Reveal -> `tilt-up`. Never repeat the same motion back-to-back.

**Overlay text discipline:** `card` <= 3 lines of <= 5 words. `stat` value <= 6 characters. `split` sides <= 8 words each. Text on screen supports the voice; it never duplicates it word-for-word.

---

## Step 7: Voice and Pace

Choose by `EMOTION` and topic. Set `voice.rate` for energy.

| Topic / Tone | Voice | Rate |
| :--- | :--- | :--- |
| Architecture, outages, deep dives | `en-US-ChristopherNeural` | `-2%` to `+2%` |
| AI news, startups, bold tech | `en-US-GuyNeural` | `+6%` to `+10%` |
| Tutorials, how-tos, onboarding | `en-US-JennyNeural` | `+2%` to `+5%` |
| Data, benchmarks, clean code | `en-US-EricNeural` | `+2%` to `+4%` |
| Tips, listicles, hacks | `en-US-RogerNeural` | `+8%` to `+12%` |
| Product announcements, news | `en-US-AriaNeural` | `+4%` to `+8%` |
| British English | `en-GB-RyanNeural` / `en-GB-SoniaNeural` | `+0%` to `+4%` |
| India dev community | `en-IN-PrabhatNeural` / `en-IN-NeerjaNeural` | `+2%` to `+6%` |

`"name": "auto"` is allowed. Pick explicitly when you can; unsupported names are normalized by the renderer.

---

## Step 8: Write `beats.json`

Same schema as v1 (renderer-compatible). Add `angle` and `format` for your own tracking; the renderer ignores unknown top-level keys.

```json
{
  "source": "https://example.com/post-slug",
  "title": "Clean Code Rules That Actually Matter",
  "angle": "80% of bugs come from just two mistakes",
  "format": "number-shock",
  "size": "short",
  "archetype": "stat-drop",
  "palette": "sunset-gold",
  "seed": 48213,
  "voice": { "name": "en-US-EricNeural", "rate": "+4%", "pitch": "+0Hz" },
  "music": { "mood": "tech-pulse", "duck_db": -14 },
  "cta": "none",
  "beats": [
    { "kind": "intro", "hook_pattern": "number-shock", "hook": "80% of bugs. Two mistakes.",
      "image": "images/01_intro.jpg",
      "voice": "Eighty percent of software bugs come from just two mistakes.",
      "motion": "punch-zoom", "sfx": "whoosh" },
    { "kind": "stat", "value": "80%", "label": "of bugs are preventable",
      "image": "images/02_stat.jpg",
      "voice": "And you're probably making both of them right now.",
      "motion": "push-in" }
  ]
}
```

Beat kinds and motions are unchanged from v1 (`intro`, `scene`, `card`, `stat`, `split`, `code`, `quote`, `outro`; every beat needs `image`, `voice`, `motion`).

### New in v2 (renderer 2.0 supports these)

| Field | Level | Type | What it does |
| :--- | :--- | :--- | :--- |
| `transition` | beat | string | How this beat is joined to the **previous** one: `cut`, `fade`, `fadeblack`, `dissolve`, `slideleft`, `slideright`, `slideup`, `slidedown`, `wipeleft`, `wiperight`, `zoomin`, `circleopen`, `smoothleft`, `smoothright`, `radial`, `pixelize`. Default = archetype transition. |
| `transition_dur` | beat / top | number | Seconds (0.08-0.6, default 0.22). |
| `transition` | top | string | Default transition for the whole Short, overriding the archetype's. |
| `tail` | beat | number | Silence after the voice, in seconds (default 0.35, outro-loop 0.08). Use `0.05-0.15` on fast beats for punchier pacing. |
| `emphasis` | beat | string[] | Words in the captions drawn in the palette highlight color. Numbers, `%`, and `$` are emphasized automatically. Pick 1-2 words per beat, never more. |
| `palette` | beat | string | Overrides the palette for this beat only, e.g. an `ember` beat inside a `clean-dark` short to mark the turning point. Use sparingly (at most 1-2 beats). |
| `progress_bar` | top | `"none"` / `"top"` / `"bottom"` | Thin bar that fills over the whole video. Good for Tips Countdown and Tutorials. Default `none`. |

**Transition craft:** use `cut` for fast rhythmic beats and for the pattern interrupt (a hard cut feels like a jolt), and a soft transition (`fade`, `dissolve`) for emotional or story beats. Don't use a different fancy transition on every join; one default plus 1-2 deliberate overrides looks intentional.

---

## Step 9: Pre-Render Self-Critique (mandatory)

Score the draft 1-5 on each, silently. **Revise until total >= 24/30 and Hook >= 4 and Specificity >= 4.**

| Criterion | Question |
| :--- | :--- |
| Hook | Would a stranger stop scrolling in 3 seconds? |
| Specificity | Does every beat contain a concrete fact, number, or image from the post? |
| One idea | Can the whole video be summarized in one sentence? |
| Pacing | Does something new happen every <= 5 seconds, with a re-hook near 40%? |
| Payoff | Does the ending deliver what the hook promised, and loop back? |
| Shareability | Would someone send this to a friend or save it? Why? |

If a criterion scores low, fix the script, not the styling.

---

## Step 10: Render

```bash
python <skill-path>/scripts/render_short.py shorts/<slug>/beats.json -o shorts/<slug>/short.mp4
```

The renderer synthesizes voice with word timestamps, composites overlays over the photos, applies camera motion, adds captions in the safe zone (emphasized words in the highlight color), joins beats with per-beat transitions or hard cuts, optionally adds a progress bar, ducks ambient music under voice (-14 LUFS), writes `meta.md`, and logs to `shorts/.history.json`.

> **v1 bug fixed in renderer 2.0:** v1 applied xfade transitions only when a Short had exactly 2 beats. With 3 or more beats it silently fell back to plain hard cuts, so the archetype transitions described in v1 never appeared. Transitions now work for any number of beats.

## Step 11: Post-Render Frame Review (mandatory)

Do not trust the render blindly. Extract one frame per beat and look at them:

```bash
mkdir -p shorts/<slug>/qa
ffmpeg -i shorts/<slug>/short.mp4 -vf "fps=1/3,scale=360:-1" shorts/<slug>/qa/f_%02d.jpg
```

View the frames and check:
- Text is readable, not clipped, not covered by a busy part of the photo.
- Consecutive frames don't look alike (variety of image, kind, composition).
- First frame already shows the hook (not black or blank).
- Nothing important sits in the YouTube UI zones.
- Duration is within the cap.

If any check fails, fix `beats.json` (shorter text, new image, different kind) and re-render. Do this at most twice, then report what remains.

---

## Step 12: `meta.md` Package

Besides what the renderer writes, make sure `meta.md` contains:
- **3 title options** (<= 70 chars): curiosity, number-led, and direct-benefit styles; recommend one.
- **Description**: first line is the hook plus a link to the blog; then 3-5 hashtags.
- **Pinned comment**: a question that invites an answer or a debate (e.g. "Which of these mistakes have you made?").
- **Cover frame timestamp**: the frame with the strongest visual plus readable hook text.
- **Angle** and **format** used, so future runs can learn from what performed.

---

## Final QA Checklist

- [ ] `brief.md` exists and the chosen format is justified by content signals
- [ ] Hook picked from 5 scored candidates, <= 12 spoken words, specific, voice at 0.0s
- [ ] Pattern interrupt near 40% (re-hook line + kind/motion/image change)
- [ ] Every beat has its own relevant image (outro may reuse intro)
- [ ] >= 4 different beat kinds; no repeated motion back-to-back
- [ ] Every claim traceable to the article
- [ ] Self-critique score >= 24/30
- [ ] Frame review done, no clipping or look-alike frames
- [ ] Ending loops back into the hook
- [ ] Duration within cap; `meta.md` complete with 3 titles and a pinned comment
- [ ] Transitions deliberate: one default plus 1-2 overrides (usually `cut` at the pattern interrupt); 1-2 `emphasis` words per beat at most
