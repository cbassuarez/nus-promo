// A caption: typed, not faded. The headline types in a few characters per
// 16th with nus's block caret riding the last character; one key word
// (marked *like this*) takes the section's signal; the sub types after it,
// faster; on the way out it backspaces right to left in the half-beat before
// the cut. A zigzag rule — the stitch texture — opens it.

import type { CSSProperties } from 'react';
import { useFrame } from './layout';
import { Zigzag } from './Memphis';
import { DIM_ON_BLACK, DIM_ON_WHITE, INK, MONO, SIGNAL, type Signal, TYPE, WHITE } from './tokens';

export type CaptionProps = {
  beat: number;
  from: number; // the beat typing starts
  until?: number; // the beat it must be gone by
  kicker?: string;
  headline: string; // *word* marks the key word
  sub?: string;
  signal: Signal;
  ground: 'white' | 'black';
  rate?: number; // headline characters per beat
  style?: CSSProperties;
};

function parse(text: string) {
  const out: { ch: string; key: boolean }[] = [];
  let key = false;
  for (const ch of text) {
    if (ch === '*') key = !key;
    else out.push({ ch, key });
  }
  return out;
}

export function Caption({ beat, from, until = Infinity, kicker, headline, sub, signal, ground, rate: base, style }: CaptionProps) {
  const { k, m, captionTop, W } = useFrame();
  if (beat < from) return null;
  const ink = ground === 'white' ? INK : WHITE;
  const dim = ground === 'white' ? DIM_ON_WHITE : DIM_ON_BLACK;
  const colour = SIGNAL[signal];
  const head = parse(headline);
  // Typing is the entrance, reading is the point: the headline lands within
  // ¾ of a beat however long it is, the sub right behind it, and the whole
  // caption then holds until a quick erase in the last third of a beat.
  const rate = base ?? Math.max(20, head.length / 0.75);
  const subChars = sub ? [...sub] : [];
  const headDone = from + head.length / rate;
  const subRate = Math.max(rate * 1.6, subChars.length / 0.6);
  // Out: the last third of a beat before `until`, a quick backspace.
  const erase = Math.max(0, Math.min(1, (beat - (until - 0.35)) / 0.35));
  const shownHead = Math.floor(Math.min(head.length, (beat - from) * rate) * (1 - erase));
  const shownSub = Math.floor(Math.min(subChars.length, Math.max(0, (beat - headDone - 0.1) * subRate)) * (1 - erase));
  const typing = beat < headDone + (sub ? subChars.length / subRate + 0.1 : 0);
  // After typing, the caret blinks on the beat (visible in the first half).
  const caretOn = typing || (beat % 1) < 0.5;
  const caretOnSub = sub && beat >= headDone + 0.1;
  const size = TYPE.headline.size * k;
  const caret = (h: number, colour: string) => (
    <span style={{ display: 'inline-block', width: h * 0.6, height: h * 0.92, background: colour, verticalAlign: '-0.12em', marginLeft: h * 0.04, opacity: caretOn ? 1 : 0 }} />
  );
  return (
    <div style={{ position: 'absolute', left: m, top: captionTop, width: W - 2 * m, fontFamily: MONO, color: ink, ...style }}>
      {kicker && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 * k, fontSize: TYPE.kicker.size * k, fontWeight: 500, letterSpacing: TYPE.kicker.tracking, color: dim, marginBottom: 22 * k }}>
          <Zigzag width={96 * k} height={14 * k} colour={colour} stroke={4 * k} />
          {kicker}
        </div>
      )}
      <div style={{ fontSize: size, fontWeight: 600, letterSpacing: TYPE.headline.tracking, lineHeight: TYPE.headline.leading, maxWidth: 20 * size, whiteSpace: 'pre-wrap' }}>
        {head.slice(0, shownHead).map((c, i) => (
          <span key={i} style={{ color: c.key ? colour : ink }}>
            {c.ch}
          </span>
        ))}
        {!caretOnSub && erase < 1 && caret(size, ink)}
      </div>
      {sub && (
        <div style={{ fontSize: TYPE.sub.size * k, fontWeight: 400, lineHeight: TYPE.sub.leading, color: dim, marginTop: 26 * k, maxWidth: `${TYPE.sub.measure}ch`, minHeight: TYPE.sub.size * k * 1.4 }}>
          {subChars.slice(0, shownSub).join('')}
          {caretOnSub && erase < 1 && caret(TYPE.sub.size * k, dim)}
        </div>
      )}
    </div>
  );
}
