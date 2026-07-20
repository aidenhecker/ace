# Hero asset + social preview specs

## Hero sparkline (shipped)

`docs/hero.svg` — grouped log-scale bars of `context_tokens` per strategy across
the three corpora, with ACE's flat ~450-token reference line. Static SVG so it
renders in the README on GitHub light **and** dark themes (white rounded panel,
fixed colors). Regenerate the numbers from `results/<date>.json` whenever the
benchmark is re-run.

Palette: raw `#d1495b` · claude-mem `#edae49` · ace `#00798c` · ink `#1b1b1f`.

## Hero GIF (storyboard)

A ~7-second terminal GIF for the social post / docs top. Three beats:

| t | frame | on screen |
|---|---|---|
| 0.0–2.5s | **the run** | type `uvx agent-memory-bench` → the three result tables stream in |
| 2.5–5.0s | **the catch** | cursor highlights the `context_tokens` column: `224,377` → `927` → **`446`**; caption fades in: *"503× smaller context"* |
| 5.0–7.0s | **the honesty** | cursor drops to `kernel_log` ACE row `recall@10 = 0.42`; caption: *"…and where it loses. Ship the loss."* |

### Render command

Record with [`asciinema`](https://asciinema.org) + [`agg`](https://github.com/asciinema/agg) (both `brew install`-able):

```bash
# 1. record the run (Ctrl-D to stop)
asciinema rec hero.cast -c "uvx agent-memory-bench"

# 2. render to GIF — terminal-grade, loops, ~760px wide
agg --theme monokai --font-size 22 --cols 92 --rows 30 hero.cast docs/hero.gif

# 3. (optional) trim + caption overlays in any editor; keep < 2 MB for GitHub
```

Then swap the README hero to the GIF: `<img src="docs/hero.gif" ...>`.

## OG / social-preview image — 1280×640 spec

For GitHub repo social preview (Settings → Social preview) and link unfurls on
X / Hacker News / Slack. Export at exactly **1280×640 PNG**, < 1 MB.

```
┌──────────────────────────────────────────────────────────────┐  1280×640
│  bg: #0d0d12  (near-black; high contrast for feed thumbnails)  │
│                                                                │
│  agent-memory-bench                          [teal mono badge] │  64px bold, #f4f1ea
│  ─────────────────────────────────────────────                │
│  Reproduce ACE's 195×-class agent-memory                       │  40px, #c9c9d4
│  compression — verify it with your own corpus.                 │
│                                                                │
│   raw  224,377 ─────────────────────████████████  $0.676      │  mono row, #d1495b bar
│   mem      927 ─█                                  $0.0058     │  #edae49
│   ace      446 ▏                                   $0.0043     │  #00798c, glowing
│                                                                │
│   503× smaller context · 3 public corpora · uvx-runnable       │  24px, #8a8a94
│                                              github.com/hmatrades │  20px, bottom-right
└──────────────────────────────────────────────────────────────┘
```

- Font: a geometric sans for headings (Space Grotesk / Inter), monospace for the
  data row (JetBrains Mono / SF Mono).
- The single visual hook is the **length contrast** of the three bars — raw runs
  off the edge, ace is a sliver. That contrast is the whole pitch.
- Build it in Figma/Canva, or render `docs/hero.svg` on a dark 1280×640 canvas
  and add the title band.
