#!/bin/sh
# Lighting workfiles — blender/rigs/<shot>.blend (local only: they hold the
# Apple model). Light by hand in Blender (Light Wrangler, Photographer); keep
# every light, flag and reflector in the `Rig` collection; save in place.
#
#   sh blender/rig.sh new <shot>     write the workfile (refuses to overwrite yours)
#   sh blender/rig.sh open <shot>    open it in Blender, with your add-ons
#   sh blender/rig.sh check <shot>   render one frame with add-ons OFF, rig vs
#                                     scripted stage, side by side → out/rigcheck/
#
# shots: open macro internals outro. Rules the render applies to Rig objects:
# they light the product only, unless an object has the custom property
# nus_link = "set" (the cyc only) or "all", or its name starts "Set light".
set -e
cd "$(dirname "$0")/.."
BL=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
cmd=$1
shot=${2:-open}
case $cmd in
  new)
    "$BL" -b --factory-startup -P blender/nus.py -- --shot "$shot" --rig-out 1 --scale 50 --samples 32 2>&1 | grep -E "^RIG|exists|Traceback|Error: [^K]" ;;
  open)
    open -a Blender "blender/rigs/$shot.blend" ;;
  check)
    frame=${3:-$("$BL" -b "blender/rigs/$shot.blend" --python-expr "import bpy; print('FRAME', bpy.context.scene.frame_current)" 2>/dev/null | sed -n 's/^FRAME //p')}
    out=out/rigcheck/$shot
    rm -rf "$out"
    "$BL" -b --factory-startup -P blender/nus.py -- --shot "$shot" --frames "$frame:$frame" --samples 48 --scale 50 --out "$out/rig" 2>&1 | grep -E "^RIG|Traceback|Error: [^K]" || true
    "$BL" -b --factory-startup -P blender/nus.py -- --shot "$shot" --frames "$frame:$frame" --samples 48 --scale 50 --no-rig 1 --out "$out/scripted" 2>&1 | grep -E "Traceback|Error: [^K]" || true
    f=$(printf "f%04d.png" "$frame")
    ffmpeg -loglevel error -y -i "$out/rig/$f" -i "$out/scripted/$f" -filter_complex hstack "$out/rig-vs-scripted.png"
    python3 - "$out/rig/$f" <<'EOF'
import sys, struct, zlib
# No numpy here on purpose: count magenta (missing-texture) pixels in the rig render.
from subprocess import run
out = run(["ffmpeg", "-loglevel", "error", "-i", sys.argv[1], "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
px = [out[i:i + 3] for i in range(0, len(out), 3)]
bad = sum(1 for p in px if p[0] > 200 and p[1] < 80 and p[2] > 200)
print(f"magenta (missing texture) pixels: {bad}" + ("  ← something in Rig references a file that isn't there" if bad else "  ✓"))
EOF
    echo "→ $out/rig-vs-scripted.png (left: your rig, add-ons off · right: the scripted stage)" ;;
  *)
    sed -n '2,13p' "$0" ;;
esac
