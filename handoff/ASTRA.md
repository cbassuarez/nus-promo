# Astra — final execution

*A brief, ready for GPT Pro to tighten into Astra's prompt. Everything
below is true of the repo on 2026-09-18.*

---

You're finishing a 30-second launch film for **nus** (read
`handoff/CONTEXT.md`, then `PLAN.md`). The film is directed, cut and
roughed. **Your job is the final picture:** 4K renders, the look pushed
as far as it will go within the locks, three formats, and a clean package
for the finish in DaVinci Resolve. You're the last hands on the picture
before Seb grades it, so polish is the point. The locks aren't
negotiable.

## Where you run

Run on **Seb's Mac** (M4 Pro, 48 GB). Only it has everything, and none
of this is in the public repo:

- Blender 4.5.3 LTS (`/Applications/Blender.app`), Cycles on Metal
  (MetalRT)
- the Apple MacBook Pro USDZ stand-in (`assets/models/`) — **never
  commit or upload it, or any render of it, anywhere public**
- the Poly Haven HDRIs (`assets/hdri/`; `npm run hdri` refetches)
- Seb's rig workfiles (`blender/rigs/<shot>.blend`), where he's hand-lit a shot; the others are lit by the script (`DESIGNS`)
- the recordings from the Mac reshoot (`public/footage/`,
  `public/internals/`)
- the score, `ableton/bounce.wav` (Seb's Live set export)
- Node 20+ and Remotion 4.0.526 (`npm install`), and ffmpeg

## Locked: don't change these

- **Copy, claims, and the beat table** (`PLAN.md` §1). The film is
  picture-locked at G4. If something reads wrong, say so in your report.
  Don't fix it.
- **The score and every hit.** Picture cuts on beats (152 bpm, `src/grid.ts`).
- **Type:** IBM Plex Mono for copy, Newsreader Italic only for the
  wordmark (via the font cycle). **The Memphis kit and its rules**
  (`PLAN.md` §3).
- **The grounds:** pure #ffffff and #000000.
- **The screens are display-true.** The UI on the 3D screen must come
  out as the capture's own sRGB pixels at the hand-off frames (`display_inverse` in
  `blender/nus.py`).
- **Seb's rig files:** never overwrite them. Propose changes as
  `blender/rigs/<shot>.astra-<n>.blend` beside the original.

## Yours to push

- **Light and lens** within stage 2 (`PLAN.md` §4):
  - every `LOOK` value (`NUS_<KEY>`)
  - the per-shot highlight designs (`DESIGNS` in `nus.py`: `highlight()`
    places a softbox by reflection so its highlight lands on a named point,
    re-aimed per frame)
  - the rigs
  - camera paths and lenses, DOF, the lens pass

  Aim for a photographed product, not a render.
- **Composites in Remotion:**
  - transitions within their beat windows
  - motion polish on the Memphis pops and captions (the timings stay;
    easing, overshoot and stagger are yours)
  - the 3D-to-flat hand-offs
- **The 3D shots' animation** inside their beat ranges: camera moves, the
  lid, the sweeps and glints.
- **The formats:** re-lay 9:16 and 4:5 where the automatic layout falls
  short.
- Anything better you can do and show on a still first.

## The procedure

1. **Read, then run the rough pass.**
   - Read `handoff/CONTEXT.md`, `PLAN.md`, `src/Cut.tsx`,
     `blender/nus.py` (`LOOK`, `stage`, `display_inverse`, `lens`) and
     `RESHOOT.md`.
   - Render `npx remotion render Cut out/astra/cut-check.mp4` and watch it
     against `out/rough/nus-rough-v0.mp4`.
2. **Look-dev on stills. Nothing long renders until Seb approves one
   still per shot.**
   - For each shot (`open`, `macro`, `internals`, `outro`), render its
     key frame at 4K.
   - Use `blender -b --factory-startup -P blender/nus.py -- --shot <s> --frames <f>:<f> --scale 200`.
     The rig is picked up automatically.
   - Where a rig exists, run `sh blender/rig.sh check <shot>` (add-ons off, rig vs scripted).
   - Present them as a contact sheet (`tools/contact.py`) with the
     settings used.
3. **Final 3D:** `sh blender/render.sh 128 200`, or per shot with your
   approved `NUS_*` values. The 4K frames go to `public/renders/<shot>/`.
   Also write the EXR passes (`--exr 1`) for Resolve.
4. **Picture:** render `Cut`, `CutVertical` and `CutFeed` as in
   `handoff/RESOLVE.md` (4K for 16:9, `--scale 2`).
5. **Check:** `npm run check:final` must pass: no licensed
   files tracked, every frame present at size, no missing-texture frames,
   durations and frame counts exact, audio sync.
6. **Package** for Resolve exactly as `handoff/RESOLVE.md` lays out.

## Acceptance (what Seb checks)

- The hand-off frames: 3D → flat at beat 8 (and anywhere else a screen
  becomes the frame) have no visible jump in position, size or colour.
- The grounds measure pure: 255 on white, 0 on black.
- Captions are legible in all three formats at phone size, and nothing
  covers UI or type.
- No missing-texture magenta and no fireflies; the motion blur reads.
- `npm run check:final` passes.

## Report back

A short `out/astra/REPORT.md` covering:
- what you changed and why, with before/after stills
- every `NUS_*` value and rig version used per shot
- render times
- anything in copy, timing or the product you think is wrong (flag it,
  don't change it)
- what you'd do with one more day
