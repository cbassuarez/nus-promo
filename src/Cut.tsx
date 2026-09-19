// The next cut, rough pass (PLAN.md §1): the new copy on the music's own
// sections, built from the styleframe components running on the beat.
// Rough, by design: UI marked MOCK stands in until the Mac reshoot lands,
// and the 3D plates are low-quality stage-2 renders on the Apple stand-in
// (public/plates/, from blender/plates.sh). Timing, copy and the order of ideas are what this pass
// locks; the look is Astra's to finish.

import type { ReactNode } from 'react';
import { AbsoluteFill, Img, useCurrentFrame } from 'remotion';
import { EndCard } from './design/Wordmark';
import { FPS } from './grid';
import { plate } from './plates';
import { Agents, Editor, Held, IDE, Language, NumberCard, Ports, Private, Yours } from './Styleframes';
import cut from './cut.json';
import { BandWipe, CellResolve, Shutter } from './Transitions';

// The beat table lives in cut.json (the markers for Resolve read it too);
// here each section's name becomes its picture. `u` is where a caption
// must be gone: it backspaces out in the half-beat before.
// A 3D plate filling the frame (narrow formats crop its middle).
const Plate = ({ src, bg }: { src: string; bg: string }) => (
  <AbsoluteFill style={{ background: bg }}>
    <Img src={src} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
  </AbsoluteFill>
);

const PICTURE: Record<string, (beat: number, frame: number) => ReactNode> = {
  open: (b) => <Plate src={plate('open', b)} bg="#ffffff" />,
  language: (b) => <Language t={b} f={8} u={12} />,
  ports: (b) => <Ports t={b} f={12} u={20} />,
  held: (b) => <Held t={b} f={20} u={24} />,
  macro: (b) => <Plate src={plate('macro', b)} bg="#ffffff" />,
  number: (b) => <NumberCard t={b} f={25} />,
  ide: (b) => <IDE t={b} f={28.5} u={38} plate={plate('internals', b)} />,
  editor: (b) => <Editor t={b} f={38} u={44} />,
  agents: (b) => <Agents t={b} f={44} u={52} />,
  yours: (b) => <Yours t={b} f={52} u={56} />,
  home: (b) => <Private t={b} f={56} u={60} plate={plate('outro', b)} home />,
  private: (b) => <Private t={b} f={60} u={64} plate={plate('outro', b)} />,
  end: (b) => <EndCard beat={b} />,
};

export const CUT = cut.sections;
const TRANSITIONS = cut.transitions as { from: number; to: number; kind: 'shutter' | 'band' | 'cells'; a: string; b: string }[];
const at = (beat: number) => CUT.find((s) => beat >= s.from && beat < s.to) ?? CUT[CUT.length - 1];
const draw = (name: string, beat: number, frame: number) => PICTURE[name](beat, frame);

// `bpm`: the same cut at another tempo — 152 is the score as written;
// slower is the score varispeeded (the bounce, resampled), and everything on
// the beat grid stretches with it.
export const Cut = ({ bpm = 152 }: { bpm?: number }) => {
  const frame = useCurrentFrame();
  const beat = frame / ((FPS * 60) / bpm);
  const t = TRANSITIONS.find((x) => beat >= x.from && beat < x.to);
  let picture: ReactNode = draw(at(beat).name, beat, frame);
  if (t) {
    const p = (beat - t.from) / (t.to - t.from);
    const a = draw(t.a, beat, frame);
    const b = draw(t.b, beat, frame);
    picture = t.kind === 'shutter' ? <Shutter p={p} a={a} b={b} /> : t.kind === 'band' ? <BandWipe p={p} a={a} b={b} /> : <CellResolve p={p} frame={frame} a={a} b={b} />;
  }
  return <AbsoluteFill style={{ background: '#ffffff', overflow: 'hidden' }}>{picture}</AbsoluteFill>;
};
