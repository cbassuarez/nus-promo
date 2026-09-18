# Reshoot — a prompt for Claude Code on the Windows machine

Paste everything below the line into Claude Code, run from the `nus`
checkout on the Windows machine. It produces every piece of software
footage the promo film needs; the Mac turns it into the final cut.

---

You're producing the software footage for nus's 30-second promo film. The
film is built on another machine (`nus-promo`: Remotion + Blender, cut to a
152 bpm grid). Everything physical — the laptop, the lighting, the
transitions — is done there. Your job is the one thing only this machine can
do: **nus itself, running, captured perfectly.**

Read `spikes/composite/src/shot.rs` first. nus already photographs itself:
`NUS_SHOT=<script>` runs a step list on the app's own event loop (the same
functions chords and clicks call — no synthetic input) and writes PNGs from
an offscreen render. You'll extend that into a recorder, then stage a demo
machine state, then run the scripts below. Commit the extensions and the
scripts (under `docs/promo/`); they're part of nus.

## 1 · Extend the shot system

1. **Scale.** `NUS_SHOT_SCALE=2` renders the offscreen capture at 2× the
   logical size, independent of the display's scale. The window's logical
   size for every shot is **1600×1000**, so every capture is **3200×2000**.
2. **A fixed clock.** `record <name> <seconds>` starts a recording: from
   then on, every time source the UI animates on (easing, the caret's
   springs, scrolling curves, bands, the palette rising, the loading bar)
   reads a virtual clock that advances **exactly 1/60 s per frame**. Each
   frame: advance the clock, run the step list's timed steps, update, draw
   offscreen, write `<NUS_SHOT_OUT>/<name>/f00000.png`… Route the app's
   `Instant::now()` reads through one clock shim to do this; don't fork
   the animation code. Things that aren't on the clock (PTY output,
   Chromium page loads) happen *before* `record` starts — pre-warm them.
3. **Timed steps.** Inside a recording, `at <seconds> <step>` runs a step at
   that clip time. Add `type <text> <chars-per-second>`, which types into
   the focused shell (or the palette, if up) character by character on the
   virtual clock. Existing verbs (`palette`, `board`, `theme`, `url`, …)
   should work under `at`.
4. **Marks.** `mark <file.json> <key>=<element> …` writes the on-screen
   rectangles of named UI elements, in logical px of the 1600×1000 window,
   as `{ "key": [x, y, w, h] }`. The chrome is already an AccessKit tree
   with a node per hit target — resolve elements from there. The film
   draws its overlays (a trace across the ports board, a box around the
   prompt's prediction) from these, so they must be exact.
5. **Layers.** `layers <dir>` writes, from one frame: `compositor.png` (the
   final composite), `native-ui.png` (header + sidebar only, transparent
   elsewhere), `terminal.png` (the terminal pane's texture, at its place in
   the window, transparent elsewhere), `chromium.png` (the CEF texture,
   likewise), and `marks.json` with `header`, `sidebar`, `terminal`,
   `chromium` as `[x0, y0, x1, y1]` logical px. All at 2×.
6. **Atlas.** `atlas <file.png>` dumps nus-render's glyph atlas texture as
   it sits on the GPU (coverage as white on black is fine).

Encode each recording with
`ffmpeg -framerate 60 -i f%05d.png -c:v libx264 -preset slow -crf 10 -pix_fmt yuv420p <name>.mp4`
and keep the PNG sequences too.

## 2 · Stage the machine

The footage must look like a real developer's real day, with nothing
personal in it.

- **A clean profile** for nus (no personal history, sessions, folders).
  Window name `acme-web`. Theme **ink**, signal **red**, default fonts,
  cursor steady (no blink), everything else default.
- **A project**: `~\dev\acme-web`, a small Vite app with a good-looking
  page on `localhost:5173` (a plain, typographic landing page is ideal).
  A second service from a second nus tab: a small API on `localhost:8787`
  (`node server.js` is fine). A third: `python -m http.server 8765` in
  `~\dev\acme-web\docs`. **All three started from nus shells**, so the ports
  board lists them as **Mine** and knows their shells. Nothing else
  listening where the board shows it (stop OneDrive's port, `jhi_service`,
  etc., or make sure the board's view shows *Mine* only).
- **The prompt**: PowerShell, but no username in it — the path should read
  `~\dev\acme-web`, not `C:\Users\<you>\…`. Keep nus's shell integration
  (OSC 133 marks) working; check that blocks, lit tokens and history
  prediction still work after changing the prompt.
- **History** that predicts well: run `git log --oneline -5` a few times in
  that shell beforehand so typing `git lo` ghosts `g --oneline -5`.
- **Sidebar**: the three service tabs, stacked sensibly, named `web`,
  `api`, `docs`. No GitHub folder unless it shows a public demo repo.
- **Git**: `acme-web` a real repo with a handful of plausible commits.

## 3 · Record

The film runs at **152 bpm: one beat = 0.394737 s**. Each clip's time 0
lands on a given film beat; the times below are clip times in seconds. Leave
**1 s of handle** at the end of every clip. Everything lands on a beat —
the film's music hits there.

### `window-ink` — time 0 = film beat 4 · record 4.2 s
The laptop's screen comes on with this (0–1.58 s, seen on the 3D laptop),
the camera flies into it, and it becomes the full frame at beat 8.
- 0.000 — one shell tab, `web`, full width, idle at the prompt in
  `~\dev\acme-web`. No split.
- 1.776 — `type localhost:5173 18` at the prompt; the ruled hint
  (`↵ opens in browser · Ctrl+↵ runs in shell`) shows as it's typed.
- 2.368 — Enter: the page opens in the split beside the shell, with the
  local-site hazard tape. (Pre-load it so it paints on this frame.)
- hold to 4.2.

### `ports-ink` — time 0 = film beat 12 · record 4.2 s, plus marks
- 0.000 — the ports board is already up over the window (open it before
  `record`), *Mine* first: 5173 vite, 8787 node, 8765 python.
- 0.395 — the selection moves to the 5173 row.
- hold to 4.2.
- `mark ports-ink.marks.json port=<5173's port cell> process=<its process
  cell> shell=<the web tab's row in the sidebar> page=<the page:
  localhost:5173's URL field or its tab row>` — whichever of these are
  visible with the board up. The film traces port → process → shell →
  page across them, one per beat.

### `prompt-ink` — time 0 = film beat 20 · record 2.6 s, crop + marks
A crop, not the whole window: the shell pane around its prompt, **646×420
logical (1292×840)**, with a few lines of `git log` output above.
- 0.100 — `type git lo 12`: tokens colour as they're typed.
- by 0.789 — the prediction ghosts `g --oneline -5` after the caret.
- hold to 2.6.
- `mark prompt-ink.marks.json ghost=<the ghosted text>` in the crop's
  coordinates.

### `palette-ink` — time 0 = film beat 24 · record 3.0 s
Seen first on the 3D laptop's screen during a macro shot of Ctrl+Shift+K
being pressed, then full frame.
- 0.000 — the window as in `window-ink`'s end state (shell + page split).
- 0.099 — the palette opens (*go* mode), empty.
- 0.395 — `type git lo 8`: tab rows first, then actions, then search.
- hold to 3.0.

### `outro-screen` — time 0 = film beat 52 · record 5.0 s
On the 3D laptop as its lid closes. The window from `window-ink`'s end
state; the theme changes **exactly on these frames**:
- 0.000 catppuccin · 0.395 gruvbox · 0.789 nord · 1.184 rosé pine
- 1.579 paper (Broadsheet), and hold to 5.0.

### Stills and layers
- Every still in `docs/media/` again, at 2× (3200×2000), same names, in
  the new staging, `-ink` and `-paper` — they back up any clip.
- From the `window-ink` end state: `layers internals/` and
  `atlas internals/atlas.png`.

## 4 · Deliver

One zip, `nus-promo-reshoot-<yyyy-mm-dd>.zip`:

```
footage/window-ink.mp4
footage/ports-ink.mp4          footage/ports-ink.marks.json
footage/prompt-ink.mp4         footage/prompt-ink.marks.json
footage/palette-ink.mp4
footage/outro-screen.mp4
footage/<name>/f00000.png …    (the PNG sequences, masters)
shots/*.png                    (2× stills, docs/media names)
internals/compositor.png  native-ui.png  terminal.png  chromium.png  atlas.png  marks.json
README.md                      (nus commit, the scripts used, anything off-spec)
```

Before zipping, check: every clip is 3200×2000 (prompt-ink 1292×840),
60 fps, the right length; the theme changes and the Enter land on the
listed frames (frame = seconds × 60); no username, email, token, private
repo or unrelated process appears in any frame.

On the Mac: unzip into `nus-promo/public/`, then
`npm run footage && sh blender/render.sh && npm run render`.
