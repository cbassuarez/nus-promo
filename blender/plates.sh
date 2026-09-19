#!/bin/sh
# The 3D plates the cut uses, at a tempo: only the beat ranges on screen
# (open 0–8, macro 24–25, internals 28–38, outro 56–64), Apple stand-in,
# stage 2 designs. The cut maps its beats onto these frames, so one set of
# plates serves every tempo; render at the slowest one for smooth motion.
#   sh blender/plates.sh [bpm] [samples] [scale]    → public/plates/<shot>/f####.png, plates.json
#   SHOTS="internals" sh blender/plates.sh …        one shot only
set -e
cd "$(dirname "$0")/.."
BL=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
BPM=${1:-152}
SAMPLES=${2:-16}
SCALE=${3:-50}
mkdir -p public/plates
SHOTS=${SHOTS:-open macro internals outro}  # SHOTS="internals" re-renders just that one
for spec in open:0:8 macro:24:25 internals:28:38 outro:56:64; do
  shot=${spec%%:*}; rest=${spec#*:}; a=${rest%%:*}; b=${rest#*:}
  case " $SHOTS " in *" $shot "*) ;; *) continue ;; esac
  fa=$(python3 -c "print(round($a*3600/$BPM))"); fb=$(python3 -c "print(round($b*3600/$BPM))")
  rm -rf "public/plates/$shot"
  NUS_BPM=$BPM "$BL" -b --factory-startup -P blender/nus.py -- --shot "$shot" --frames "$fa:$fb" --samples "$SAMPLES" --scale "$SCALE" --out "public/plates/$shot" 2>&1 | grep -E "Traceback|Error: [^K]" || true
  echo "$shot $fa-$fb done"
done
printf '{ "bpm": %s }\n' "$BPM" > public/plates/plates.json
echo PLATES_DONE
