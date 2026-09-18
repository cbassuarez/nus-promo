// Transitions made of the app's own vocabulary.
//
//   CellResolve  the frame breaks into terminal cells — each flips through a
//                glyph from the terminal's face — and settles into the next shot
//   BandWipe     the signal band tears across; a colour split on its leading
//                edge only
//   Shutter      hazard tape closes over the frame like a shutter and opens
//                on the next shot
//
// Each takes the outgoing and incoming shots and a progress 0 → 1.

import type { ReactNode } from 'react';
import { AbsoluteFill, useVideoConfig } from 'remotion';
import { MONO } from './fonts';
import { easeOut } from './grid';

const SIGNAL = '#c8102e';
const CELL = 40; // px at 1920×1080; the grid keeps its cell size in every frame
// Glyphs a terminal actually shows: prompt, paths, test output, box drawing.
const GLYPHS = 'PS>C:\\nus$~cargo test ok 0123456789abcdef{}[]()<>=+-*/#@%&|─│┌┐└┘├┤┬┴┼█▓▒░';

const hash = (i: number) => {
  const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

export function CellResolve({ p, frame, a, b }: { p: number; frame: number; a: ReactNode; b: ReactNode }) {
  const { width: W, height: H } = useVideoConfig();
  const COLS = Math.round(W / CELL);
  const ROWS = Math.round(H / CELL);
  const CW = W / COLS;
  const CH = H / ROWS;
  const rects: string[] = [];
  const glyphs: ReactNode[] = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const i = r * COLS + c;
      // Sweeps left to right, broken up by noise.
      const t = 0.08 + 0.72 * ((c / COLS) * 0.55 + hash(i) * 0.45);
      if (p >= t + 0.12) rects.push(`<rect x='${c * CW}' y='${r * CH}' width='${CW + 0.5}' height='${CH + 0.5}'/>`);
      else if (p >= t) {
        const g = GLYPHS[Math.floor(hash(i * 7 + Math.floor(frame / 2)) * GLYPHS.length)];
        const hot = hash(i * 3) > 0.86;
        glyphs.push(
          <div key={i} style={{ position: 'absolute', left: c * CW, top: r * CH, width: CW, height: CH, background: '#000', color: hot ? SIGNAL : '#ece7da', fontFamily: MONO, fontSize: CH * 0.75, lineHeight: `${CH}px`, textAlign: 'center' }}>
            {g}
          </div>,
        );
      }
    }
  }
  const mask = `url("data:image/svg+xml;utf8,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='${W}' height='${H}' fill='white'>${rects.join('')}</svg>`)}")`;
  return (
    <AbsoluteFill>
      <AbsoluteFill>{a}</AbsoluteFill>
      <AbsoluteFill style={{ maskImage: mask, WebkitMaskImage: mask, maskSize: '100% 100%', WebkitMaskSize: '100% 100%' }}>{b}</AbsoluteFill>
      <AbsoluteFill>{glyphs}</AbsoluteFill>
    </AbsoluteFill>
  );
}

export function BandWipe({ p, a, b }: { p: number; a: ReactNode; b: ReactNode }) {
  const { width: W } = useVideoConfig();
  const band = 44;
  const x = easeOut(p) * (W + band * 2) - band;
  return (
    <AbsoluteFill>
      <AbsoluteFill>{a}</AbsoluteFill>
      <AbsoluteFill style={{ clipPath: `inset(0 ${Math.max(0, W - x + band)}px 0 0)` }}>{b}</AbsoluteFill>
      <div style={{ position: 'absolute', top: 0, bottom: 0, left: x - band, width: band, background: SIGNAL }} />
      {/* The split: cyan and red slivers pulled apart on the leading edge. */}
      <div style={{ position: 'absolute', top: 0, bottom: 0, left: x + 3, width: 5, background: 'rgba(0, 210, 255, 0.85)', mixBlendMode: 'screen' }} />
      <div style={{ position: 'absolute', top: 0, bottom: 0, left: x - 1, width: 4, background: 'rgba(255, 40, 70, 0.9)', mixBlendMode: 'screen' }} />
    </AbsoluteFill>
  );
}

export function Shutter({ p, a, b }: { p: number; a: ReactNode; b: ReactNode }) {
  // Closes over the first half, opens over the second, on the app's curve.
  const { height: H } = useVideoConfig();
  const shut = p < 0.5 ? easeOut(p * 2) : 1 - easeOut((p - 0.5) * 2);
  const h = (H / 2) * shut;
  const tape = `repeating-linear-gradient(-45deg, ${SIGNAL} 0 30px, #ffffff 30px 60px)`;
  return (
    <AbsoluteFill>
      <AbsoluteFill>{p < 0.5 ? a : b}</AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: h, background: tape, borderBottom: h > 2 ? '3px solid #000' : 'none' }} />
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: h, background: tape, borderTop: h > 2 ? '3px solid #000' : 'none' }} />
    </AbsoluteFill>
  );
}
