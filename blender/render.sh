#!/bin/sh
# Render every 3D shot — the 3840×2160 master, Cycles on the GPU (Metal,
# MetalRT), one Blender at a time.   sh blender/render.sh [samples] [scale]
set -e
cd "$(dirname "$0")/.."
BL=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
for shot in open macro internals outro; do
  rm -rf "public/renders/$shot"
  "$BL" -b --factory-startup -P blender/nus.py -- --shot "$shot" --engine cycles --samples "${1:-64}" --scale "${2:-200}" 2>&1 | grep -E "^Saved|Error|Traceback" | tail -1
done
