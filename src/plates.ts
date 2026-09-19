// The 3D plates (public/plates/, from blender/plates.sh): rendered once, at
// the slowest tempo the cut plays at, and looked up by beat — so the 30 s
// and the 45 s cut share them. The cut never asks for a frame outside the
// beats a shot was rendered for.
import { staticFile } from 'remotion';
import cut from './cut.json';

type Shot = keyof typeof cut.plates.ranges;
const FPB = 3600 / cut.plates.bpm;

export function plate(shot: Shot, beat: number) {
  const [a, b] = cut.plates.ranges[shot];
  const f = Math.round(Math.min(b, Math.max(a, beat)) * FPB);
  const lo = Math.round(a * FPB);
  const hi = Math.round(b * FPB);
  return staticFile(`plates/${shot}/f${String(Math.min(hi, Math.max(lo, f))).padStart(4, '0')}.png`);
}
