# What Resolve gets

The finish (grade, grain, halation, final polish and the sound designer's
mix) happens in DaVinci Resolve. Masters leave Remotion and Blender
**clean**, so all of that stays a choice in the grade, not something
baked in.

## The package: `out/resolve/`

```
out/resolve/
  picture/
    NUS_16x9_PICTURE.mov        3840×2160  ProRes 4444  60 fps  no audio   the whole film
    NUS_9x16_PICTURE.mov        1080×1920  ProRes 4444
    NUS_4x5_PICTURE.mov         1080×1350  ProRes 4444
  plates/
    <shot>/f####.exr            multilayer EXR (half, DWAA): Combined, Cryptomatte (object, material)
                                — the 3D shots, for power windows and mattes
  footage/
    NUS_<SHOT>_<NN>_MASTER.mov  the Mac reshoot masters (ProRes 4444), with their .json
  audio/
    bounce.wav                  the score, 48 kHz 24-bit, from 0:00:00:00
    film-sync.mid               picture-sync hits
  markers.edl                   one marker per section, named, at 60 fps (import onto the timeline)
  README.txt                    the commit, the NUS_* values, what's in each file
```

## Colour

- The picture is **display-referred sRGB**. Blender renders through
  Khronos PBR Neutral to sRGB, and Remotion composites in sRGB. The
  screens are display-true, so the UI is its own pixels.
- In Resolve, use DaVinci YRGB with the timeline in Rec.709 (Scene), and
  interpret the ProRes as Rec.709, sRGB transfer. Deliver web files
  tagged **Rec.709-A** so browsers on macOS don't lift the blacks.
- **The grounds are pure** (#fff and #000). Keep them pure through the
  grade: qualify them out, or grade only inside the plates' Cryptomatte
  mattes. Grain on a pure ground is a choice, not a default.

## Commands

The package is Astra's at G5. These write it:

```sh
npx remotion render Cut        out/resolve/picture/NUS_16x9_PICTURE.mov --codec prores --prores-profile 4444 --scale 2 --muted
npx remotion render CutVertical out/resolve/picture/NUS_9x16_PICTURE.mov --codec prores --prores-profile 4444 --muted
npx remotion render CutFeed    out/resolve/picture/NUS_4x5_PICTURE.mov  --codec prores --prores-profile 4444 --muted
blender -b --factory-startup -P blender/nus.py -- --shot <shot> --exr 1 --out out/resolve/plates/<shot>
node scripts/markers.mjs > out/resolve/markers.edl
cp ableton/bounce.wav ableton/film-sync.mid out/resolve/audio/
npm run check:final
```

## Later, not now

- **A graphics-only layer** (captions, Memphis shapes, the end card on
  alpha), so type can be protected from the grade. The sections draw
  picture and graphics together today; splitting them is a `layer` prop
  on `Cut`, and it's Astra's call whether it's worth it.
- **A sound-designer package:** stems from the Live set (Seb exports),
  this beat table, `film-sync.mid`, and a picture-locked
  `NUS_16x9_PICTURE.mov`.
