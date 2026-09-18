# nus-promo

The promo film for [nus](https://nus.dev). 30 seconds at 152 bpm, scored on
Ableton's Perc Kitchen Kit, on pure white and pure black.

```
npm install
npm run studio          # scrub it in Remotion Studio
npm run blender         # the 3D shots (Cycles, ~1 h) → public/renders/
npm run render          # picture → out/nus-promo.mp4, scored with ableton/bounce.wav
npm run mux             # re-lay audio only (ableton/bounce.wav, else the preview mix)
npm run render:prores   # ProRes 4444 master for Resolve
```

**The next cut is planned in [`PLAN.md`](PLAN.md)**: the copy, the beat
table, the type and Memphis systems, the 3D shots and the Mac reshoot
([`RESHOOT.md`](RESHOOT.md)). The table below is the cut that's built now.

## Design files

- `src/design/`: the system the next cut is built from.
  - `tokens.ts`: colours, the six signals and the section map, the type scale, the grid
  - `layout.ts`: one layout for 16:9, 9:16 and 4:5
  - `Caption.tsx`: typed captions with nus's caret
  - `Memphis.tsx`: the kit (squiggle, stripes, dots, solids, stickers, zigzag)
  - `Wordmark.tsx`: the end card with the font-cycle wordmark
  - `Mocks.tsx`: ink-theme stand-ins for UI the reshoot hasn't recorded yet, marked MOCK
- `src/Styleframes.tsx`: the `Styleframe`, `StyleframeVertical` and
  `StyleframeFeed` compositions, one still per section:
  ```
  npx remotion still Styleframe out/design/sf-agents.png --props='{"id":"agents"}'
  ```
- `blender/mocks.py`: 3D look-dev stills on the real sets:
  - `memphis`: props on the cove, a hard sun, Freestyle outlines
  - `cards`: floating UI cards
  - `first-light`: a spot through a blind, in haze
  - `dolly-35` / `dolly-85`: a dolly-zoom pair
  - `glint`

  It runs without factory startup, so Photographer and Light Wrangler load:
  ```
  blender -b -P blender/mocks.py -- --mock all
  ```
- `tools/contact.py`: labelled contact sheets (needs Pillow).

Renders land in `out/design/` and `out/mocks/`, which are local, like all renders.

## The cut

Everything is placed in beats (`src/grid.ts`); 76 beats = 19 bars = 30.000 s.
The claims follow the positioning: the running local loop first, then how
it's built, then how it's driven — no firsts, no speed, no AI headline.

| beats | ground | shot | made in |
|---|---|---|---|
| 0–8 | white | the lid lifts, the screen comes on, the camera flies into it | Blender |
| 8–12 | white | *Type a URL at the prompt.* It opens beside the shell. | capture |
| 11.5–12.5 | — | hazard shutter | Remotion |
| 12–20 | white | the ports board, traced port → process → (shell →) page. *Every port. Its process. Its page.* | capture |
| 19.5–20.5 | — | band wipe | Remotion |
| 20–24 | white | *Lit as you type. Predicted from history.* | capture |
| 24–25 | white | macro: Ctrl+Shift, then K, at f/2.8 | Blender |
| 25–28 | white | *Tabs, actions, the web.* ⌘K · Ctrl+Shift+K | capture |
| 28–29 | — | cell resolve | Remotion |
| 28–44 | black | the software's parts as machined slabs, parting in haze. *One native compositor.* | Blender |
| 43–44 | — | band wipe | Remotion |
| 44–52 | white | *One action model.* `nus open`, `nus launch`, `nus ls`, `nus block last` | type |
| 52–53 | — | cell resolve | Remotion |
| 52–64 | black | rim light, a theme a beat, paper; the lid shuts | Blender |
| 64–76 | white | the icon draws in; **nus** / *From the shell to the page it serves.* | nus-render |

Captures are stand-ins until the reshoot lands (see `RESHOOT.md`): clips in
`public/footage/` replace stills automatically, on screen in Blender and flat
in Remotion, and `*.marks.json` re-register the overlays to the new layout.

## Sound — your Live set is the master

`ableton/nus-object Project/nus-object Project/nus-object.als` is the score:
the Perc Kitchen Kit across three tracks (0–52, 52–60, 60–76) with Auto Pan,
Redux, Compressor, Channel EQ and Erosion, Beat Repeat on the Reverb return,
and cuelume's *arrival* once at bar 17. Nothing here writes to it.

- **Export** (File → Export Audio/Video): Main, from 1.1.1, length 19.0.0,
  48 kHz, 24-bit WAV → `ableton/bounce.wav`. Then `npm run mux` (seconds);
  a full `npm run render` also picks it up.
- **`ableton/film-sync.mid`** — the picture-sync hits the new cut added after
  your save (band wipes, cell resolves, Ctrl+Shift, the K press, the palette
  cut). Drag it onto a kit track at 1.1.1. Three older hits no longer sit on
  picture: kettle at beat 24 (the K now lands at 24.25), water at 27.5 and
  spoons at 43.5 — yours to keep or drop.
- `src/score.json` (from `scripts/pattern.mjs`) is still what the picture
  cuts to; `npm run score` renders a rough preview mix from it, used only
  until `bounce.wav` exists. `npm run als` writes a fresh generated set,
  `nus-object (generated).als`, never yours.

## The laptop and the 3D shots — `blender/nus.py`

Four shots, keyed from `src/score.json`'s beat grid with cubic ease-out
(nus's curve), rendered in Cycles on the GPU (Metal, MetalRT) with depth
of field and motion blur: `open`, `macro`, `internals`, `outro` →
`public/renders/<shot>/f####.png`, numbered by film frame, 3840×2160 by
default.

- **The machine.** `--laptop apple` uses Apple's MacBook Pro 14" USDZ as a
  stand-in until the licensed model arrives: the logo insert hidden and its
  hole filled, the hinge axis solved so the lid shuts flush, our captures
  on a copy of the screen surface. It lives in `assets/models/` and is
  **never committed**. `--laptop ours` is the original handmade body.
- **The sets** are real cycloramas (floor, cove, wall) lit by Poly Haven
  studio HDRIs (`npm run hdri` → `assets/hdri/`). Camera rays see the flat
  #fff or #000. Cycles light linking keeps the rims and sweeps on the
  product. `LOOK` in `nus.py` holds the measured exposure, and every value
  can be overridden with `NUS_<KEY>`.
- **The internals** use the compositor's own layer dumps and glyph atlas
  when the reshoot sends them (`public/internals/`), else crops of the
  window capture and an atlas drawn from Plex Mono (`tools/atlas.py`).

## Assets

- `public/shots/` — captures from `nus/docs/media`, 1600×1000 at 1×. Drop in
  3200×2000 captures under the same names and re-render.
- `public/icon/` — 121 frames of `nus_render::icon::app_icon_at` (`npm run icon`).
- `public/fonts/`: IBM Plex Mono and Newsreader Italic, plus Silkscreen, Bungee and Rubik Mono One for the wordmark's font cycle (all OFL).
- `public/icons/`: Phosphor icons (MIT) for the Memphis stickers.
- `public/icon/ink/`: the icon frames in paper, for black grounds.

## Sync

Remotion's own AAC track runs ~42 ms late, so `render` writes picture only
and `scripts/mux.sh` lays the audio with ffmpeg. Measured: hits within ±4 ms.

## Licences

Remotion: free for individuals and teams up to three. Fonts OFL; Phosphor icons MIT; cuelume MIT;
Perc Kitchen Kit samples are Ableton Core Library content, licensed with Live.
