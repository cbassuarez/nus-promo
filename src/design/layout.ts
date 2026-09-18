import { useVideoConfig } from 'remotion';
import { GRID } from './tokens';

// One film, three frames. `k` scales type, `m` is the margin; the narrow
// frames keep captions in the top third, clear of the platforms' own UI.
export function useFrame() {
  const { width: W, height: H } = useVideoConfig();
  const wide = W / H > 1.2;
  const k = wide ? W / 1920 : (W / 1080) * 0.88;
  const m = wide ? GRID.margin * k : 72;
  const col = (n: number) => (wide ? m + n * ((W - 2 * m + GRID.gutter * k) / GRID.columns) : m);
  return { W, H, wide, k, m, col, captionTop: wide ? H * 0.12 : H * 0.08 };
}
