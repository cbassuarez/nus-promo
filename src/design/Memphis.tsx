// The Memphis kit, made of what nus already draws: the icon's orbit as a
// tapered squiggle, hazard tape as stripes, the halftone and stipple
// textures as dot fields, the lamps and the Space square as solids with a
// 2 px ink outline and the app's hard 8×8 shadow, the stitch as a zigzag, and
// Phosphor icons as stickers. Shapes pop on the beat (the only thing that may
// overshoot); type never does.

import type { CSSProperties, ReactNode } from 'react';
import { Img, staticFile } from 'remotion';
import { INK, PAPER, WHITE } from './tokens';

// Entry: a quick pop with a little overshoot, over a quarter-beat.
export function pop(beat: number, at: number, dur = 0.35) {
  const t = Math.max(0, Math.min(1, (beat - at) / dur));
  if (t <= 0) return 0;
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

type Place = { x: number; y: number; rotate?: number; scale?: number; style?: CSSProperties };
function Placed({ x, y, rotate = 0, scale = 1, style, children }: Place & { children: ReactNode }) {
  return <div style={{ position: 'absolute', left: x, top: y, transform: `rotate(${rotate}deg) scale(${scale})`, transformOrigin: 'center', ...style }}>{children}</div>;
}

// The icon's band, opened out: a stroke that swells in the middle and tapers
// at both ends, drawn on by `progress`.
export function Squiggle({ width, height, colour, weight, waves = 1.5, progress = 1, shadow = true }: { width: number; height: number; colour: string; weight: number; waves?: number; progress?: number; shadow?: boolean }) {
  const n = 96;
  const top: string[] = [];
  const bottom: string[] = [];
  const upto = Math.max(2, Math.round(n * progress));
  for (let i = 0; i <= upto; i++) {
    const t = i / n;
    const x = t * width;
    const y = height / 2 + (height / 2 - weight / 2) * Math.sin(Math.PI * 2 * waves * t);
    const dy = (height / 2 - weight / 2) * Math.cos(Math.PI * 2 * waves * t) * Math.PI * 2 * waves / width;
    const len = Math.hypot(1, dy);
    const w = (weight / 2) * (0.25 + 0.75 * Math.sin(Math.PI * t));
    const nx = -dy / len;
    const ny = 1 / len;
    top.push(`${(x + nx * w).toFixed(1)},${(y + ny * w).toFixed(1)}`);
    bottom.unshift(`${(x - nx * w).toFixed(1)},${(y - ny * w).toFixed(1)}`);
  }
  const d = `M${top.join(' L')} L${bottom.join(' L')} Z`;
  return (
    <svg width={width + 12} height={height + 12} style={{ overflow: 'visible' }}>
      {shadow && <path d={d} fill={INK} transform="translate(6 6)" />}
      <path d={d} fill={colour} stroke={INK} strokeWidth={2} strokeLinejoin="round" />
    </svg>
  );
}

export function Zigzag({ width, height, colour, stroke }: { width: number; height: number; colour: string; stroke: number }) {
  const teeth = Math.max(3, Math.round(width / (height * 1.2)));
  const pts = Array.from({ length: teeth * 2 + 1 }, (_, i) => `${(i / (teeth * 2)) * width},${i % 2 ? stroke / 2 : height - stroke / 2}`).join(' ');
  return (
    <svg width={width} height={height} style={{ overflow: 'visible', flexShrink: 0 }}>
      <polyline points={pts} fill="none" stroke={colour} strokeWidth={stroke} strokeLinejoin="miter" strokeLinecap="square" />
    </svg>
  );
}

export function Stripes({ width, height, colour }: { width: number; height: number; colour: string }) {
  return (
    <div
      style={{
        width,
        height,
        background: `repeating-linear-gradient(-45deg, ${colour} 0 ${height * 0.45}px, ${PAPER} ${height * 0.45}px ${height * 0.9}px)`,
        border: `2px solid ${INK}`,
        boxShadow: `8px 8px 0 ${INK}`,
      }}
    />
  );
}

// Halftone: a grid of dots whose radius falls off from one corner.
export function Dots({ width, height, colour, pitch = 18, from = 'top-left' as 'top-left' | 'bottom-right' | 'centre' }: { width: number; height: number; colour: string; pitch?: number; from?: 'top-left' | 'bottom-right' | 'centre' }) {
  const dots: ReactNode[] = [];
  const cols = Math.floor(width / pitch);
  const rows = Math.floor(height / pitch);
  for (let r = 0; r <= rows; r++) {
    for (let c = 0; c <= cols; c++) {
      const u = c / cols;
      const v = r / rows;
      const d = from === 'top-left' ? (u + v) / 2 : from === 'bottom-right' ? 1 - (u + v) / 2 : Math.hypot(u - 0.5, v - 0.5) * 1.4;
      const rad = (pitch / 2) * 0.85 * (1 - d);
      if (rad > 0.6) dots.push(<circle key={`${r}-${c}`} cx={c * pitch} cy={r * pitch} r={rad} fill={colour} />);
    }
  }
  return <svg width={width} height={height} style={{ overflow: 'visible' }}>{dots}</svg>;
}

export function Solid({ shape, size, colour }: { shape: 'circle' | 'square' | 'quarter' | 'half'; size: number; colour: string }) {
  const s = size;
  const d =
    shape === 'circle'
      ? `M${s / 2},0 A${s / 2},${s / 2} 0 1 1 ${s / 2 - 0.01},0 Z`
      : shape === 'square'
        ? `M0,0 H${s} V${s} H0 Z`
        : shape === 'quarter'
          ? `M0,${s} V0 A${s},${s} 0 0 1 ${s},${s} Z`
          : `M0,${s / 2} A${s / 2},${s / 2} 0 0 1 ${s},${s / 2} Z`;
  return (
    <svg width={s + 10} height={s + 10} style={{ overflow: 'visible' }}>
      <path d={d} fill={INK} transform="translate(8 8)" />
      <path d={d} fill={colour} stroke={INK} strokeWidth={2} />
    </svg>
  );
}

export function Sticker({ icon, size }: { icon: string; size: number }) {
  return (
    <div style={{ width: size, height: size, borderRadius: '50%', background: WHITE, border: `2px solid ${INK}`, boxShadow: `6px 6px 0 ${INK}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Img src={staticFile(`icons/${icon}.svg`)} style={{ width: size * 0.56, height: size * 0.56 }} />
    </div>
  );
}

// A shape that pops in on its beat.
export function Pop({ beat, at, children, ...place }: Place & { beat: number; at: number; children: ReactNode }) {
  const s = pop(beat, at);
  if (s <= 0) return null;
  return (
    <Placed {...place} scale={(place.scale ?? 1) * s}>
      {children}
    </Placed>
  );
}
