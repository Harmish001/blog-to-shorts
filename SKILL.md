---
name: blog-to-shorts
description: >-
  Turn one blog URL into one 9:16 YouTube Short told as a short story, with a
  neural voice, captions locked to that voice, slow moves on photos, and a
  catchy intro and a fade-out ending written for that post. Generate frames
  when the blog has too few photos. About 1 minute for a short post, about 2
  minutes for a long guide. Use when the user invokes /blog-to-shorts or asks
  to turn a blog URL into a YouTube Short.
disable-model-invocation: true
---

# Blog to Shorts

Make one YouTube Short from one blog URL. The viewer should feel they were walked through the article, not read a list.

## Rules

- One URL in. One short out. Ask for the URL if it is missing.
- Tell a story in full sentences. Contractions are fine. Connect ideas with when, so, and if. Do not speak labels, colons, or "point one".
- Say only what the article says. No extra facts.
- English only. If the article is not English, stop and ask. Do not translate unless the user asks.
- Use the article only when the user has rights to it. If the page blocks access, stop.
- Length:
  - A short post (one idea, a few sections) aims at about 1 minute. Hard cap 70 seconds.
  - A long guide (many sections, several cases) aims at about 2 minutes. Hard cap 120 seconds.
  - Do not pad a short post out to 2 minutes. Do not shrink a guide into a bullet readout to hit 60 seconds.
- Set `"size": "short"` or `"size": "long"` in `beats.json`. The renderer enforces the cap.

## Steps

```
Task Progress:
- [ ] Fetch the URL
- [ ] Decide short or long
- [ ] Write the story beats
- [ ] Render
- [ ] Confirm it sounds like a story and the length matches the size
```

### 1. Fetch

Use WebFetch. Keep the title and article body. Drop nav, footer, related posts, comments, and newsletter blocks.

If the fetch is empty, a cookie wall, or only a JS shell, stop.

### 2. Shape

Open on a catchy line that only this article could start with. Walk through the advice as choices a person makes. End so the picture fades out and the video feels finished.

A long guide gets two or three center cards. A short post gets one. Cards hold the lines worth remembering. Everything else is a photo scene.

Cover the arc: what it is about, the main advice, one concrete case, the close. Do not recite every bullet in the post.

The bottom line is a caption of the words being spoken, timed to the voice. The renderer builds that from the voice track. Do not write a second script for it.

### Intro and outro

First beat is `kind: intro`. Last beat is `kind: outro`. Write both from this article.

- `hook` is a short on-screen line, about 3–6 words. `voice` is the spoken version, one or two sentences.
- The intro hook is a catch. It is not "Let's begin", "In this video", or a title read aloud.
- The outro hook is the last thing on screen. The picture then fades to black. It is not "Thanks for watching", "Follow for more", or a line copied from another short.
- Read the hook back. If it would fit a different blog unchanged, rewrite it.

### 3. Beats

Save `shorts/<slug>/beats.json`.

```json
{
  "source": "https://example.com/post",
  "title": "Post title",
  "size": "long",
  "beats": [
    {
      "kind": "intro",
      "image": "images/open.jpg",
      "hook": "A line only this post would open on",
      "voice": "One or two sentences that earn the next scene."
    },
    {
      "kind": "scene",
      "image": "images/hero.jpg",
      "voice": "Two or three spoken sentences that move the story."
    },
    {
      "kind": "card",
      "caption": "Card title|Line to remember|Another line",
      "voice": "The same idea, spoken as sentences, not as the card text."
    },
    {
      "kind": "outro",
      "image": "images/close.jpg",
      "hook": "A last line only this post would end on",
      "voice": "One sentence that lands the story, then stop."
    }
  ]
}
```

- `kind`: `intro`, `scene`, `card`, or `outro`.
- `scene` uses a photo. The picture slowly zooms or pans. The bottom caption follows the voice. Do not add a separate lower-third title.
- `card` puts the important lines in the center. Split lines with `|`. The voice explains them. The bottom caption still follows the voice.
- `intro` and `outro` use `hook` plus `voice`. Outro holds the hook, then fades to black.
- First beat is the intro. Last beat is the outro.

### Pictures

Use photos from the article, not logos, icons, or nav. One picture should not repeat for every scene.

If the article has no usable photo, or fewer photos than picture beats, generate the missing frames. Ask for a 9:16 image, no words in the picture, and a subject that matches that beat. Save each file under `images/` next to `beats.json`. The renderer animates those frames the same way it animates article photos.

### 4. Render

Run the render script from the skill directory (e.g. `<skill-path>/scripts/render_short.py` depending on where the skill was installed, such as `.agents/skills/blog-to-shorts/scripts/render_short.py` or `.cursor/skills/blog-to-shorts/scripts/render_short.py`):

```bash
python <skill-path>/scripts/render_short.py shorts/<slug>/beats.json -o shorts/<slug>/short.mp4
```

Needs `ffmpeg`, `ffprobe`, and `edge-tts` (`pip install edge-tts`). Voice defaults to `en-US-AndrewNeural` at a slightly calm rate. Falls back to system speech if neural voice is unavailable.

Prints `OK <path> <seconds>`.

If it prints `OVER_CAP`, shorten the story and render again. Keep the arc. Do not turn it back into a list.

### 5. Reply

Report the mp4 path, duration, and the story in a few lines. Do not upload the file.

## Failure

- Missing URL: ask.
- Fetch blocked or empty: stop.
- Not English: stop and ask.
- `ffmpeg` missing: stop and name it.
- Over the cap after one tighten: stop and say what would not fit.
