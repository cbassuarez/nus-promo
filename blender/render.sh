#!/bin/sh
# Render every 3D shot with Cycles on the GPU, one Blender at a time.
#   sh blender/render.sh [samples]    (default 32)
set -e
cd "$(dirname "$0")/.."
BL=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
for shot in open macro internals outro; do
  rm -rf "public/renders/$shot"
  "$BL" -b --factory-startup -P blender/nus.py -- --shot "$shot" --engine cycles --samples "${1:-32}" 2>&1 | grep -E "^Saved|Error|Traceback" | tail -1
done
