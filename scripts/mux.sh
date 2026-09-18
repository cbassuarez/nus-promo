#!/bin/sh
# Lay the score under the picture. Your Live export wins if it's there
# (ableton/bounce.wav: Main, 1.1.1, 19 bars, 48 kHz); otherwise the preview
# mix. −1.5 dB keeps the true peak under the AAC encode's ceiling; nothing
# else touches the mix. ffmpeg's AAC compensates encoder priming, so hits
# land on the frame (Remotion's own track runs ~42 ms late).
set -e
cd "$(dirname "$0")/.."
AUDIO=public/score.wav
GAIN=0dB
[ -f ableton/bounce.wav ] && AUDIO=ableton/bounce.wav && GAIN=-1.5dB
echo "mux: $AUDIO ($GAIN)"
ffmpeg -loglevel error -y -i out/picture.mp4 -i "$AUDIO" -map 0:v -map 1:a -c:v copy -af "volume=$GAIN,apad" -c:a aac -b:a 320k -t 30.0 -movflags +faststart out/nus-promo.mp4
