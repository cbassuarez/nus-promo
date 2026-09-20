# Reshoot, a prompt for Claude Code on the Mac

Paste everything below the line into Claude Code, run from the `nus`
checkout on the Mac that records. It produces every piece of software
footage the promo film needs. It also proves the macOS build: every
frame of the film's UI comes from nus running on macOS.

---

You're producing the software footage for nus's 30-second promo film. The
film is built in `~/nus-promo` (Remotion + Blender, cut to a 152 bpm grid;
read its `PLAN.md` first, sections 1 and 5). Everything physical (the
laptop, the light, the type, the transitions) is done there. Your job is
the one thing only nus can do: **nus itself, running on macOS, captured
perfectly.**

The copy the film puts beside your footage is decided and has to be true
of it. So if a shot can't show what its line says, stop and report back;
don't fake it.

## The capture standard

Treat the UI like a photographed product. Every clip is a choreographed
performance of **one idea**, not a recording of someone using the app.
The viewer never waits for the operator and never wonders where to look.

- **Real product only.** No mock UI, no faked behaviour. If nus can't do
  it on camera, it isn't in the shot, and you report back.
- **Every clip has a shape:**
  1. **hold**: the start state registers
  2. **intent**: one action begins
  3. **response**: the UI reacts
  4. **result**: hold until the change is understood
  5. **out**: a stable frame to cut or loop on

  One strong interaction in six seconds beats five weak ones.
- **The capture layer is nus's own recorder**, not screen capture:
  offscreen frames at a fixed 1/60 s clock. That gives, by construction:
  - no desktop or wallpaper
  - no OS cursor, notifications or menu bar
  - no dropped frames
  - no window shadow
  - constant geometry
  - accurate sRGB

  Screen capture (ScreenCaptureKit) is the fallback only for a surface
  the recorder can't draw, and it's reported as such.
- **No cursor in the master.** Where pointer position is the point (a
  hover, a click), record the pointer's path to a sidecar
  (`pointer.json`, logical px per frame) so a clean cursor can be added
  downstream, or not at all.
- **Keyboard first.** Typing is confident and readable: pause at
  syntactic boundaries, never type boilerplate on camera, and correct a
  mistake only if the correction shows product behaviour.
- **The UI stays calm.** Only the product's own animation plays. All
  camera motion, zooms, reframing, captions, callouts and cursors come
  later, never baked into a master.
- **Composition, checked before every take:**
  - a clear hierarchy
  - balanced panes
  - legible type at laptop-render and phone size
  - no noisy terminal history
  - no half-lines at pane edges
  - no scrollbar motion
  - no truncated labels
  - a safe margin (≥ 4 %) around anything that matters, because the
    frame gets perspective-mapped onto a 3D screen and cropped for 9:16
    and 4:5
- **Takes:**
  1. Reset to the start state.
  2. Rehearse and verify the end state.
  3. Reset again, then record.
  4. Step frame by frame around every transition.
  5. Retake on any of these:
     - a hitch or unexpected load
     - layout movement or a stray hover
     - rushed typing or a mistimed change
     - stale content

  Keep two clean takes of the important shots. Don't accept the first
  take that merely works.

## 0 · Build and measure

1. Build the release app on this Mac and run the test suite. Note
   anything macOS-specific that's broken; fixing parity blockers is in
   scope, since the film claims macOS.
2. **Latency.** The film's number card says *2.8 ms · key to screen*. That
   figure is the `vt-render` spike on Windows (`docs/SPIKES.md` §3, method
   in `spikes/vt-render/README.md`). Measure key → present **in the full
   app, release build, on this Mac**, using the same method. Report the
   median and p95, the display's refresh rate, and exactly what was
   measured. The film uses whatever this says.

## 1 · The recorder

Built on 2026-09-19 and in the nus tree (`spikes/composite/src/clock.rs`,
`shot.rs`). `NUS_SHOT=<script>` runs a step list on the app's own event
loop and writes PNGs from an offscreen render. What it does now:

- **One clock.** Everything that animates reads `clock::now()`. In a
  recording that clock advances exactly 1/60 s per written frame, however
  long the machine took to draw it, so a take lands on the same frames
  every time. Real time is still real where it should be: page-load
  timings, network deadlines, the event loop.
- **`record <name> <seconds>`** writes `<NUS_SHOT_OUT>/<name>/f00000.png`
  and on from there, at 60 fps.
- **`at <seconds> <step>`** lines follow the `record` line and are its
  schedule. Every other verb works inside a recording.
- **`type <text> <cps>`** types into whatever has the focus, a character
  at a time, on the clock. **`key <chord>`** sends a chord (`cmd+s`,
  `down`, `tab`, `enter`, `esc`) through the app's own key handling, not
  synthetic OS input, so a scripted key runs the code a finger runs.
- **`await-paint`** and **`await-lsp`** stop the clock. No frames are
  written and nothing animates until the page paints or the language
  server answers, which is how a page load or an HMR reload lands on an
  exact frame although Chromium is not on this clock. A hold that never
  comes gives up after 10 s and says so rather than hanging.
- **`settle`** holds the script until six frames in a row hash the same,
  so a take starts from the same still frame every time.
- **`NUS_SHOT_SIZE=1600x1000`** fixes the window at creation. On this Mac
  that captures at **3200×2000**, which is the standard.
- **`marks <file.json> all`** (or `key=label` pairs) writes the on-screen
  rectangles of named elements in logical px, read from the accessibility
  tree, so an overlay the film draws sits exactly where nus drew the thing.
- **`layers <dir>`** writes `compositor.png`, `native-ui.png` (the chrome
  with the panes cut out), `terminal.png`, `chromium.png` and
  `marks.json`. One frame masked four ways, not four renders, so the
  planes line up to the pixel.
- **`atlas_png <file>`** dumps nus-render's glyph atlas as it sits on the
  GPU, 2048 square.
- **`phone on` / `phonetab`** turn SYNC · THE PHONE on and open the page
  it serves. **`hunk stage|revert|unstage|apply <n>`** clicks a chip on a
  diff's `@@` line, at the chip's own rectangle.

Checked: two takes of the same script came back 59 of 60 frames
byte-identical, every step on its frame, at 3200×2000.

Still to build, if a shot needs it: a second window under `NUS_SHOT2` in a
recording, and pointer paths to `pointer.json`.

Encode each recording with
`ffmpeg -framerate 60 -i f%05d.png -c:v libx264 -preset slow -crf 10 -pix_fmt yuv420p <name>.mp4`
and keep the PNG sequences, which are the masters.

## 2 · Stage the machine

The footage has to look like a real developer's real day, with nothing
personal in it.

- **A clean nus profile**: no personal history, sessions or folders.
  - Window name `acme-web`.
  - Theme **ink**, signal **red**, default fonts, a steady cursor (no blink).
  - Profile name **seb**, face = the initial, device **this mac**.
  - Everything else default except where a shot below says otherwise.
- **Projects:**
  - `~/dev/acme-web` is a small Vite app with a good-looking, plain,
    typographic landing page on `localhost:5173`. It's a real git repo
    with a handful of plausible commits.
  - A second service from a second nus tab: a small API on
    `localhost:8787` (`node server.js`).
  - A third: `python3 -m http.server 8765` in `~/dev/acme-web/docs`.
  - **All three are started from nus shells**, so the ports board lists
    them as **Mine** and knows their shells. Nothing else should listen
    where the board shows it; if something must, film *Mine* only.
  - A small Rust crate at `~/dev/acme-web/tools/lint` with
    rust-analyzer working in the editor pane. Seed one real type error
    for the diagnostics shot.
- **The prompt**: zsh, with **no username or hostname**. The path reads
  `~/dev/acme-web`. Keep nus's shell integration (OSC 133) working, and
  check that blocks, lit tokens and history prediction survive the
  prompt change.
- **The prompt's language server**: install bash-language-server, set
  **TERMINAL · PROMPT LSP: MENU** for shot 1, and check that it actually
  answers for zsh. If it doesn't, stop and report; the film's
  *language-aware, even at the prompt* depends on it.
- **History** that predicts: run the shot-1 commands a few times first.
- **Sidebar**: tabs named `web`, `api`, `docs`, stacked sensibly.
- **Sync**: a throwaway demo key and a local-folder carrier, so shot 9
  joins a "second device" without touching any real account.
- **Agents**: shot 2 uses the real hands path (`hand …` steps).
  **ASSISTANTS · HANDS: ASK**, with no hosts pre-allowed.

## 3 · Record

The film runs at **152 bpm: one beat = 0.394737 s**. Each clip's time 0
lands on the film beat given; times below are clip seconds. Leave **1 s
of handle** at the end of every clip. Everything lands on a beat, where
the music hits. The styleframes in `nus-promo/out/design/` show the
intended frames; where they're marked MOCK, your footage replaces them.

### 1 · `shell-min`: time 0 = beat 4 · record 4.2 s
The laptop's screen wakes on this (0–1.58 s, seen in 3D). The camera
pushes in and it's the full frame 8–12. Film line: *even the prompt has a
language server.*
- before `record`: `fullscreen hidden`, one shell `web` in
  `~/dev/acme-web`, a few lines of `git log --oneline -3` above the prompt
- 1.579 (beat 8): `type` a prefix the prompt's language server completes
  with **four or more** real rows (find one, e.g. a `git` or `cargo`
  subcommand, and use what the server really returns), at 10 cps
- `await-lsp`, then the menu shows under the caret
- 2.763 (beat 11): `key down`, `key tab`, which accepts the second row
- hold to 4.2

### 2 · `agent-page`: time 0 = beat 44 · record 4.2 s, plus marks
Film line: *the agent works where you can watch it.*
- before `record`: a split, a shell running `claude` on the left, and on
  the right `https://github.com/cbassuarez/nus` (a real page, public, and
  ours), loaded and settled
- 0.000: `hand read` puts up the read chip
- 0.789 (beat 46): `hand scroll 0 600`
- 1.579 (beat 48): `hand click "Issues"` raises the ASK band: *claude wants
  to click Issues · ALLOW · DENY · ALLOW ON THIS HOST*
- 2.368 (beat 50): `hands allow`, then `await-paint`; the Issues tab loads
- hold to 4.2
- `mark agent-page.marks.json band=<the ASK band> chips=<the chip row> log=<the page's log, if visible>`

### 3 · `vite-split`: time 0 = beat 12 · record 2.6 s
Film line: *every server. its shell. its page.*
- before `record`: the editor pane on `src/App.tsx` (or wherever the
  headline lives) on the left, `localhost:5173` on the right
- 0.100: `type` a new headline over the old one (select it first), 14 cps
- 0.789 (beat 14): `key cmd+s`
- 1.184 (beat 15): `await-paint`; the HMR update lands on this frame
- hold to 2.6

### 5 · `ports-ink`: time 0 = beat 16 · record 2.6 s, plus marks
- before `record`: the ports board up over the window, *Mine* first
  (5173 vite, 8787 node, 8765 python)
- 0.395: the selection moves to 5173
- hold to 2.6
- `mark ports-ink.marks.json port=… process=… shell=<web's sidebar row> page=<localhost:5173's tab or URL field>`;
  the film traces port → process → shell → page, one a beat

### 6 · `held-a` + `held-b`: time 0 = beats 20 and 22 · record 1.8 s each
Film line: *quit it. update it. crash it. / the shells keep going.* Two
recordings, because the app really quits in between.
- **held-a**: `cargo watch -x test` running in a held shell, a test pass
  in progress; `key cmd+q` at 0.789 (the quit is the clip's last frame)
- **held-b**: relaunch; the same shell reattached, still watching, with
  the next test pass arriving. Also, **in another tab**, a non-held
  command a restart *did* kill, showing the cut-off seam and its resume
  chip. Hold to 1.8.

### 7 · `art-live`: time 0 = beat 52 · record 2.6 s
Film line: *every pixel of it is a file you can edit.*
An art behind the prompt is one Luau file. That is the whole argument for
this beat, and it plays better than a settings page.
- before `record`: the prompt on the left with `homelook art memphis`, the
  editor pane on that art's Luau file on the right, `settle`
- 0.000, 0.395: `homelook art sky`, then `homelook art pond`, a beat each,
  the prompt redrawing under the line
- 0.789: `homelook art memphis` again, back where it started
- 1.184: `type` a changed number into the Luau (a colour, a count), `key
  cmd+s` at 1.579; the prompt redraws on save, by 1.8
- hold to 2.6
- if a re-skin still earns its place, `studio` and one preset snap belong
  here too; otherwise it goes to the b-roll

### 8 · `editor-lsp`: time 0 = beat 38 · record 3.4 s
Film line (the second half of *it's an IDE underneath.*)
- before `record`: the editor pane on the seeded Rust file,
  rust-analyzer warm, the type error already underlined
- 0.395: the pointer moves onto the error, and the diagnostic card shows
- 1.184: the pointer moves onto a function name; `await-lsp`; the hover
  card shows its signature and doc
- hold to 3.4

### 4 · `home-profile`: time 0 = beat 56 · record 2.6 s
On the 3D laptop's screen as the outro starts. Film line: *your account is a
file on your machine.*
- before `record`: `home` (the prompt, centred, nothing else)
- 0.395: `me`, and the profile card rises from the footer's avatar: face,
  name, the DAY badge, NAME · FACE · DEVICE · SYNC · PRIVATE, MORE / CLOSE
- hold to 2.6

### 9 · `sync-join`: time 0 = beat 60 · record 2.6 s
On the laptop as the lid closes, as the b-side to the phone. Film line:
*no account. no server. nothing phones home.*
- before `record`: SETTINGS · SYNC
- 0.000: paste the demo key; 0.395: join; the device list shows **2
  devices** once the exchange reports (`await-paint`, or its own await if
  it isn't CEF)
- hold to 2.6

### 10 · `hero-idle`: no beat · record 10 s
A beautiful, stable nus state for the laptop's screen in the open and
outro, and for the website.
- The split: `web` shell idle at the prompt in `~/dev/acme-web` beside
  `localhost:5173`.
- The only motion allowed is the product's own: a watch lamp, a clock
  that really ticks. No caret blink.
- The first and last frames must match, so it loops.

### 11 · `loop`: no beat · record 6 s
For the website: a single interaction whose end state is its start state.
- The palette opens (`palette go`), `type git lo 10`, the selection moves
  twice, then it closes (`close`).
- The last frame equals the first.

### 12 · `news-away`: time 0 = beat 22 · record 2.2 s
The second half of the held-shell beat, and the reason the beat matters:
the shells kept going, and nus tells you what they did.
- before `record`: a relaunch with work behind it (a test run that failed,
  one still running, a hands request waiting), `home`, `settle`
- 0.000: `news <unix seconds>`, the rows coming up over the prompt: what
  failed, what ran long, what still runs, who is asking for hands
- 0.789 (beat 24): the selection moves down one row
- hold to 2.2
- `marks news-away.marks.json all`

### 13 · `diff-hunk`: time 0 = beat 48 · record 2.6 s, plus marks
The other half of *the agent works where you can watch it*. It is not only
that you see the patch, it is that you decide, one hunk at a time.
- before `record`: a shell in `~/dev/acme-web`, the agent's patch printed
  by `git --no-pager diff` (two hunks, one file, plausible), shell
  integration on so the output is a block, `settle`
- 0.395: the pointer onto the first `@@` line, its chips lit
- 0.789 (beat 50): `hunk stage 0`
- 1.184: the toast lands, the output beneath it unchanged
- hold to 2.6
- `marks diff-hunk.marks.json all`

### 14 · `phone-allow`: no beat (cut against 60–64) · record 3.0 s
The shot the film did not have. Two machines in one frame, and the laptop
is the one serving.
- before `record`: `phone on`, a hands request waiting on the laptop, the
  phone (a real one, in frame) on the served address
- the laptop side is the recording: the ASK band waiting, answered from
  the phone at 1.184, the band resolving on that frame
- the phone side is filmed with the 3D camera in the same light, or shot
  against the same black and comped
- hold to 3.0
- `marks phone-allow.marks.json all`
- nothing personal on the phone's screen, and the address and its token
  never legible in frame

### Stills and layers
- Every still in `docs/media/` again, at 2× (3200×2000), same names, in
  the new staging, `-ink` and `-paper`. They back up any clip.
- From `shell-min`'s end state: `layers internals/` and
  `atlas internals/atlas.png`.

## 4 · Deliver

**Names.** `NUS_<SHOT>_<NN>` (take number), e.g. `NUS_SHELL_MIN_01`,
`NUS_AGENT_PAGE_02`. For each approved take:

```
footage/NUS_<SHOT>_<NN>_MASTER.mov    ProRes 4444, 3200×2000, 60 fps, sRGB (from the PNG sequence)
footage/NUS_<SHOT>_<NN>/f00000.png …  the PNG sequence, the true master
footage/NUS_<SHOT>_<NN>_WEB.mp4       H.264 CRF 18, 1600×1000, for the web
footage/NUS_<SHOT>_<NN>_THUMB.png     one representative frame
footage/NUS_<SHOT>_<NN>.json          metadata (below)
footage/NUS_<SHOT>_<NN>.marks.json    element rectangles, where the shot asks for marks
footage/NUS_<SHOT>_<NN>.pointer.json  the pointer path, where the shot has one
```

Also `footage/<shot>.mp4` (H.264, CRF 10), a copy of each shot's chosen
take under the short name the film's pipeline reads (`npm run footage`).

**Metadata** (`.json`), one per take:

```json
{
  "shot": "shell-min", "take": 1, "film_beat": 4,
  "nus_commit": "<sha>", "macos": "<version>", "machine": "<model>",
  "window_logical": [1600, 1000], "capture": [3200, 2000], "fps": 60,
  "frames": 252, "duration_s": 4.2,
  "start_state": "…", "end_state": "…", "interaction": "…",
  "events": [{ "t": 1.579, "step": "type git ch 10" }],
  "cursor": false, "crop": null, "notes": "…"
}
```

**Also:** `shots/*.png` (2× stills), `internals/*` (layers, atlas,
marks), `LATENCY.md`, and a **`MANIFEST.md`**: one line per approved shot
saying what it communicates and where it's best used (film beat, website,
social). Before you finish, review every approved shot together and retake
any whose pacing, type, content or hierarchy is weaker than the rest.

One zip, `nus-promo-reshoot-mac-<yyyy-mm-dd>.zip`. Before zipping, check
that:
- every master is 3200×2000, 60 fps, the listed length, with its
  metadata
- every listed event lands on its frame (frame = seconds × 60)
- no username, hostname, email, token, private repo or unrelated process
  appears in any frame
- the Issues click in shot 2 went only to the public repo

On the Mac: unzip into `nus-promo/public/`, then run `npm run footage &&
npm run check`, and the rough pass picks the footage up.
