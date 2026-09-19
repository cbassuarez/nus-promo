// The 3D plates (public/plates/, from blender/plates.sh): rendered once, at
// the slowest tempo the cut plays at, and looked up by beat — so the 30 s
// and the 45 s cut share them. The cut never asks for a frame outside the
// beats a shot was rendered for.
import { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
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

// Labels that ride a plate (blender exports their anchors per frame, beside
// the frames): x, y 0–1 of the 16:9 render from its top left.
export type Tag = { text: string; x: number; y: number; on: number; off: number };
type Labels = { labels: { text: string; on: number; off: number }[]; frames: Record<string, [number, number][]> };

export function useLabels(shot: Shot) {
  const [data, setData] = useState<Labels | null>(null);
  const [handle] = useState(() => delayRender(`labels for ${shot}`));
  useEffect(() => {
    fetch(staticFile(`plates/${shot}/labels.json`))
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setData(d))
      .catch(() => setData(null))
      .finally(() => continueRender(handle));
  }, [handle, shot]);
  return data;
}

export function tagsAt(data: Labels | null, shot: Shot, beat: number): Tag[] {
  if (!data) return [];
  const [a, b] = cut.plates.ranges[shot];
  const f = Math.round(Math.min(b, Math.max(a, beat)) * FPB);
  const pts = data.frames[String(f)];
  if (!pts) return [];
  return data.labels.map((l, i) => ({ ...l, x: pts[i][0], y: pts[i][1] }));
}
