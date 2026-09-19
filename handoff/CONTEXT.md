# nus promo — the context pack

*Synced with `PLAN.md` on 2026-09-18 (commit after `8e07027`). If you
can read the repo, `PLAN.md` wins wherever this disagrees.*

## The product

**nus** is a terminal whose architecture is an IDE's. One native
compositor (wgpu) draws its own VT core (the terminal), real Chromium
(through CEF, a patched cef-rs; not a fork), an editor pane and its own
chrome as peers in one window. Rust, MIT, for macOS, Windows and Linux,
at nus.dev.

Visually it's Memphis-leaning. It's ink and paper, with a set of six
signal colours, 2 px ink outlines and hard 8×8 shadows. Its wordmark is
**nus** in Newsreader Italic, and its UI type is IBM Plex Mono.

## What the film sells: the pillars, and only what's true

| Pillar | The film may say | Backed by | Never say |
|---|---|---|---|
| Fast | **2.8 ms**, key to screen | the vt-render spike on Windows; **re-measured in the full app on the recording Mac**, and the card shows that number | "lightweight" |
| Language-aware | completions and hovers from real language servers, at the prompt and in the editor | prompt LSP (MENU mode), the editor pane | "AI autocomplete" |
| Dev tools | the ports board traces server → shell → page; held shells survive quit/update/crash; cut-off commands resume | ports, held, cut off | — |
| IDE architecture | one native compositor; real Chromium drawn beside your shells | the compositor | "Chromium fork" |
| Agents, visible | every agent action is a block you can read, stop or take over; ASK before it acts | hands, action chips, ASK band | any AI headline beyond that |
| Customizable | rules, layouts and looks in luau; every colour a token; the look studio | rules.luau, look studio | "Chrome extensions" |
| Private | no account, no server, no telemetry; sync sealed with a key you copy | profile = a file, sync | — |

**Tagline:** *Built like an IDE. Fast like a terminal.*

## The film

30 s at **152 bpm**: 1 beat = 0.394737 s, 76 beats, 1800 frames at
60 fps. It's laid on the score's fixed sections. Picture is Remotion;
3D is Blender Cycles; the UI is the real app, recorded by nus itself.

| Beats | Section · signal | Picture | Copy (typed, mono) |
|---|---|---|---|
| 0–8 | — | 3D: white cove, Memphis props, the lid opens, the screen wakes on 4, a dolly-zoom push-in to the screen | — |
| 8–12 | Language · teal | fullscreen minimal shell, the language server's menu under the caret | language-aware, even **at the prompt**. |
| 12–20 | Dev tools · gold | Vite preview: edit → reload; the ports board traced | every server. its **shell**. its page. |
| 20–24 | Dev tools · green | held shell: quit, relaunch, reattach; the cut-off chip | quit. update. crash. your shells **keep running**. |
| 24–28 | Fast · red | 3D macro on ⌘, then the number card | **2.8 ms** · key to screen, measured |
| 28–44 | Architecture · blue | 3D internals, layers parting (28–38); the editor with LSP (38–44) | built like an **IDE**. / an editor, with **its language server**. |
| 44–52 | Agents · violet | a real page; the agent reads, scrolls, asks; ASK band | agents, in **plain sight**. |
| 52–56 | Customizable · red | look studio presets on the beat; rules.luau live | yours, **all the way down**. |
| 56–60 | Home · red | 3D outro on black; home and the profile card on the screen | you, **on this machine**. |
| 60–64 | Private · red | the lid shuts; sync joining with a key; the glint | no account. no server. no **telemetry**. |
| 64–76 | End | the icon band draws; the wordmark font-cycles and settles on Newsreader; the tagline types | built like an IDE. fast like a **terminal**. |

Transitions sit on hits already in the score:
- a shutter at 11.5–12.5
- band wipes at 19.5–20.5 and 43–44
- cell resolves at 28–29 and 52–53

## Look and type (locked)

- **Copy:** IBM Plex Mono only (600 heads, 400 subs, 500 kickers).
  - Captions are typed with nus's block caret, never faded.
  - One key word takes the section's signal.
  - Captions backspace out before the cut.
- **The wordmark** is Newsreader Italic. It arrives through a font cycle
  (Plex → Silkscreen → Plex Italic → Bungee → Rubik Mono One), a 16th per
  step, letter by letter.
- **The Memphis kit** is built from what nus draws: the icon's orbit as a
  squiggle, hazard stripes, halftone dots, solids with 2 px outline and
  8×8 shadow, Phosphor stickers, a zigzag rule.
  - Shapes frame the UI; they never cover UI or type.
  - Only shapes overshoot; type never does.
- **Grounds are pure white and pure black.** Formats: 16:9 (4K master),
  9:16, 4:5.
- **3D, stage 2:**
  - view transform: Khronos PBR Neutral
  - screens: display-true glass (the view transform is inverted in the
    shader)
  - metal: anodised
  - light: feathered softboxes and black flags for the product; a set
    light for the cyc
  - lens: a light pass
  - Each shot's lighting can come from a hand-lit rig file.

## Non-negotiables

- The score is Seb's Live set; the film uses its export. Never write to
  the set. cuelume plays once only (beat 64).
- Nothing licensed in the public repo: no Apple model (a stand-in until
  a licensed GLB), no renders, footage, rigs, HDRIs or audio.
- No mock UI in final picture. Every UI frame is the real app.
- Every claim is true of the footage beside it.

## The repo (github.com/cbassuarez/nus-promo)

| Path | Is |
|---|---|
| `PLAN.md` | the decisions |
| `RESHOOT.md` | the capture standard and the ten recordings |
| `src/Cut.tsx` | the next cut (compositions `Cut`, `CutVertical`, `CutFeed`) |
| `src/Styleframes.tsx`, `src/design/` | the sections, type, Memphis kit, wordmark, mocks |
| `blender/nus.py` | the 3D shots and the stage-2 look (`LOOK`, every value overridable as `NUS_<KEY>`) |
| `blender/mocks.py` | 3D look-dev stills |
| `blender/rig.sh` | rig workfiles: `new`, `open`, `check` |
| `tools/contact.py`, `tools/check.py` | contact sheets; acceptance checks |
| `handoff/` | this roundtable |
