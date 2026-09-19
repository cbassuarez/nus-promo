"""Acceptance checks — the gate Astra's final (and every commit) goes through.

  python3 tools/check.py            hygiene and what exists: warnings, fails only on a leak
  python3 tools/check.py --final    the G5 bar: every frame, every size, every duration

Needs ffprobe; Pillow for the image checks (skipped, with a warning, without it).
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINAL = "--final" in sys.argv
FPS = 60
FPB = FPS * 60 / 152
# The shots' beat ranges, read from blender/nus.py so the two never drift.
import ast
import re

RANGES = ast.literal_eval(re.search(r"^RANGES = (\{.*\})", (ROOT / "blender" / "nus.py").read_text(), re.M).group(1))
fails, warns, oks = [], [], []


def fail(msg):
    fails.append(msg)


def warn(msg):
    (fails if FINAL else warns).append(msg)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate,nb_frames",
                          "-of", "json", str(path)], capture_output=True, text=True).stdout
    return json.loads(out or "{}")


# ── 1 · Nothing licensed in the public repo ───────────────────────────────────
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
LEAKS = (".usdz", ".glb", ".exr", ".hdr", ".blend", ".wav", ".aif", ".mp3", ".mov", ".mp4")
LEAK_DIRS = ("assets/models/", "assets/hdri/", "public/renders/", "public/footage/", "public/lookdev/", "blender/rigs/", "out/", "ableton/bounce")
# Versioned on purpose: the Live set (Seb's master, samples referenced from
# Ableton's library, not bundled), cuelume's arrival (MIT, ours), the preview mix.
ALLOWED = ("ableton/nus-object Project/", "public/score.wav", "ableton/film-sync.mid")
leaks = [f for f in tracked if (f.endswith(LEAKS) or f.startswith(LEAK_DIRS)) and not f.startswith(ALLOWED)]
if leaks:
    fail(f"licensed or generated files are tracked by git: {leaks[:8]}{' …' if len(leaks) > 8 else ''}")
else:
    oks.append("git: no model, render, footage, rig, HDRI or audio tracked")

# ── 2 · The 3D frames ─────────────────────────────────────────────────────────
try:
    from PIL import Image
except ImportError:
    Image = None
    warn("Pillow missing: image checks skipped (python3 -m venv .venv && .venv/bin/pip install pillow)")

for shot, (a, b) in RANGES.items():
    d = ROOT / "public" / "renders" / shot
    want = range(round(a * FPB), round(b * FPB) + 1)
    have = {p.name for p in d.glob("f*.png")} if d.exists() else set()
    missing = [f for f in want if f"f{f:04d}.png" not in have]
    if len(missing) > 2:  # the first/last frame of a range may round either way
        warn(f"renders/{shot}: {len(missing)} of {len(want)} frames missing (first f{missing[0]:04d})")
        continue
    if Image is None or not have:
        continue
    sample = sorted(have)[:: max(1, len(have) // 12)]
    sizes, bad = set(), []
    for name in sample:
        im = Image.open(d / name).convert("RGB")
        sizes.add(im.size)
        small = im.resize((192, 108))
        raw = small.tobytes()
        magenta = sum(1 for i in range(0, len(raw), 3) if raw[i] > 200 and raw[i + 1] < 80 and raw[i + 2] > 200)
        if magenta > 40:
            bad.append(f"{name} (missing texture)")
    if FINAL and sizes != {(3840, 2160)}:
        fail(f"renders/{shot}: sizes {sorted(sizes)} — the master is 3840×2160")
    if bad:
        fail(f"renders/{shot}: {bad}")
    if not bad and (not FINAL or sizes == {(3840, 2160)}):
        oks.append(f"renders/{shot}: {len(have)} frames, {sorted(sizes)[0][0]}×{sorted(sizes)[0][1]}, no missing textures")

# ── 3 · The score ─────────────────────────────────────────────────────────────
wav = ROOT / "ableton" / "bounce.wav"
if wav.exists():
    dur = float(probe(wav).get("format", {}).get("duration", 0))
    (oks.append(f"bounce.wav: {dur:.3f} s") if dur >= 30.0 else fail(f"bounce.wav is {dur:.3f} s — the film is 30.000"))
else:
    warn("ableton/bounce.wav missing — export it from the Live set")

# ── 4 · The reshoot ───────────────────────────────────────────────────────────
footage = sorted((ROOT / "public" / "footage").glob("*.mp4")) + sorted((ROOT / "public" / "footage").glob("*.mov"))
if not footage:
    warn("public/footage/: empty — the Mac reshoot hasn't landed (the cut runs on stills and MOCKs)")
for f in footage:
    v = next((s for s in probe(f).get("streams", []) if s.get("codec_type") == "video"), {})
    fps = v.get("r_frame_rate", "0/1")
    if (v.get("width"), v.get("height")) != (3200, 2000) or fps != "60/1":
        warn(f"footage/{f.name}: {v.get('width')}×{v.get('height')} @ {fps} — the standard is 3200×2000 @ 60")
    if not f.with_suffix(".json").exists() and not (f.parent / (f.stem + ".marks.json")).exists():
        warn(f"footage/{f.name}: no metadata .json beside it (RESHOOT.md §4)")

# ── 5 · The masters ───────────────────────────────────────────────────────────
masters = {"NUS_16x9_PICTURE.mov": (3840, 2160), "NUS_9x16_PICTURE.mov": (1080, 1920), "NUS_4x5_PICTURE.mov": (1080, 1350)}
for name, size in masters.items():
    p = ROOT / "out" / "resolve" / "picture" / name
    if not p.exists():
        if FINAL:
            fail(f"out/resolve/picture/{name} missing")
        continue
    info = probe(p)
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    frames = int(v.get("nb_frames") or 0)
    got = (v.get("width"), v.get("height"))
    if got != size or v.get("r_frame_rate") != "60/1" or frames != 1800:
        fail(f"{name}: {got[0]}×{got[1]} @ {v.get('r_frame_rate')}, {frames} frames — want {size[0]}×{size[1]} @ 60, 1800")
    else:
        oks.append(f"{name}: {size[0]}×{size[1]} @ 60, 1800 frames")

# ── Report ────────────────────────────────────────────────────────────────────
for m in oks:
    print(f"  ok    {m}")
for m in warns:
    print(f"  warn  {m}")
for m in fails:
    print(f"  FAIL  {m}")
print(f"\n{'FINAL' if FINAL else 'check'}: {len(fails)} failing, {len(warns)} warnings, {len(oks)} ok")
sys.exit(1 if fails else 0)
