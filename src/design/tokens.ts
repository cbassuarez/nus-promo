// The film's design tokens. One face for type (IBM Plex Mono — the app's),
// Newsreader Italic for the wordmark only, the app's six signals as the
// Memphis palette, one signal per section, the way each Space has one.

export const INK = '#141414';
export const PAPER = '#f4f1ea';
export const WHITE = '#ffffff';
export const BLACK = '#000000';
export const DIM_ON_WHITE = '#6b665c';
export const DIM_ON_BLACK = '#8a857a';

export const SIGNAL = {
  red: '#c8102e',
  blue: '#1f5fbf',
  gold: '#d9a400',
  green: '#2e7d32',
  violet: '#6b3fa0',
  teal: '#1a7f8a',
} as const;
export type Signal = keyof typeof SIGNAL;

// A section, its signal, and its ground.
export const SECTIONS = {
  agents: { signal: 'violet', ground: 'white' },
  ports: { signal: 'gold', ground: 'white' },
  language: { signal: 'teal', ground: 'white' },
  held: { signal: 'green', ground: 'white' },
  ide: { signal: 'blue', ground: 'black' },
  editor: { signal: 'blue', ground: 'white' },
  yours: { signal: 'red', ground: 'white' },
  private: { signal: 'red', ground: 'black' },
  end: { signal: 'red', ground: 'black' },
} as const satisfies Record<string, { signal: Signal; ground: 'white' | 'black' }>;
export type Section = keyof typeof SECTIONS;

export const MONO = "'Plex', 'IBM Plex Mono', monospace";
export const SERIF = "'Newsreader', Georgia, serif";

// Type scale at 1920×1080; multiply by the layout's k.
export const TYPE = {
  kicker: { size: 18, weight: 500, tracking: '0.08em' },
  headline: { size: 88, weight: 600, tracking: '-0.02em', leading: 1.05 },
  sub: { size: 30, weight: 400, leading: 1.4, measure: 42 },
  number: { size: 240, weight: 600, tracking: '-0.04em' },
  code: { size: 30, weight: 400 },
} as const;

// The grid: 12 columns, 128 px margins, 32 px gutters, 8 px baseline (16:9).
export const GRID = { columns: 12, margin: 128, gutter: 32, baseline: 8 } as const;
