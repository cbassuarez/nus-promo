// The end card. The icon's band draws its orbit (nus-render's own
// app_icon_at, frame by frame); then the wordmark types itself as a font
// cycle — each letter flips through faces on the 16ths (the terminal's mono,
// the glyph atlas's pixels, a chunky Memphis display…) and settles on the
// real wordmark, Newsreader Italic, left to right. nus lets you choose your
// fonts; the logo says so. Then the tagline types, mono, with the caret.

import { AbsoluteFill, Img, staticFile } from 'remotion';
import { useFrame } from './layout';
import { Pop, Squiggle, Dots } from './Memphis';
import { BLACK, DIM_ON_BLACK, DIM_ON_WHITE, INK, MONO, PAPER, SERIF, SIGNAL, WHITE } from './tokens';

// Each face, with a size factor so every stop lands at the same visual height.
const FACES: { family: string; weight: number; style: 'normal' | 'italic'; scale: number; upper?: boolean }[] = [
  { family: "'Plex'", weight: 600, style: 'normal', scale: 0.86 },
  { family: "'Silkscreen'", weight: 400, style: 'normal', scale: 0.84 },
  { family: "'Plex'", weight: 400, style: 'italic', scale: 0.86 },
  { family: "'Bungee'", weight: 400, style: 'normal', scale: 0.7 },
  { family: "'RubikMono'", weight: 400, style: 'normal', scale: 0.7 },
];
const FINAL = { family: SERIF, weight: 500, style: 'italic' as const, scale: 1 };
const STEP = 0.25; // a 16th at 152 bpm

export const WORDMARK_START = 66;
export const settleBeat = (i: number) => WORDMARK_START + (FACES.length + i) * STEP;

function faceAt(beat: number, i: number) {
  const k = Math.floor((beat - WORDMARK_START) / STEP) - i; // letter i starts a 16th late
  if (k < 0) return null; // not typed yet
  if (k >= FACES.length) return FINAL;
  return FACES[(k + i) % FACES.length];
}

export function EndCard({ beat, ground = 'black' }: { beat: number; ground?: 'white' | 'black' }) {
  const { W, H, k, wide } = useFrame();
  const ink = ground === 'white' ? INK : PAPER;
  const dim = ground === 'white' ? DIM_ON_WHITE : DIM_ON_BLACK;
  const band = Math.round(120 * Math.max(0, Math.min(1, (beat - 64) / 2.5)) ** 0.6);
  const icon = ground === 'white' ? `icon/icon-${String(band).padStart(3, '0')}.png` : `icon/ink/icon-${String(band).padStart(3, '0')}.png`;
  const size = 190;
  const settled = beat >= settleBeat(2);
  const letters = 'nus'.split('');
  const tag1 = "a *terminal* with an IDE's bones.";
  const tag2 = 'nothing leaves this machine.';
  const typed = (s: string, at: number, rate = 16) => {
    const plain = s.replace(/\*/g, '');
    const n = Math.max(0, Math.min(plain.length, Math.floor((beat - at) * rate)));
    let i = 0;
    let key = false;
    const out: { ch: string; key: boolean }[] = [];
    for (const ch of s) {
      if (ch === '*') {
        key = !key;
        continue;
      }
      if (i++ < n) out.push({ ch, key });
    }
    return out;
  };
  const caretBlink = beat % 1 < 0.5;
  const fit = Math.min(W / 1920, (W - 144) / 1250) * (wide ? 1 : 1.18);
  return (
    <AbsoluteFill style={{ background: ground === 'white' ? WHITE : BLACK }}>
      {/* Memphis: a dot field bleeding off the top-right, a squiggle under the tagline. */}
      <Pop beat={beat} at={67.25} x={W - 520 * k} y={-60 * k}>
        <Dots width={560 * k} height={420 * k} colour={SIGNAL.red} pitch={22 * k} from="top-left" />
      </Pop>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${fit})` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
          <Img src={staticFile(icon)} style={{ width: 380, height: 380 }} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ height: size * 1.05, display: 'flex', alignItems: 'flex-end', color: ink }}>
              {settled ? (
                <span style={{ fontFamily: SERIF, fontStyle: 'italic', fontWeight: 500, fontSize: size, lineHeight: 1 }}>nus</span>
              ) : (
                letters.map((ch, i) => {
                  const f = faceAt(beat, i);
                  return (
                    <span key={i} style={{ display: 'inline-block', width: size * 0.5, textAlign: 'center', fontFamily: f?.family, fontWeight: f?.weight, fontStyle: f?.style, fontSize: size * (f?.scale ?? 1), lineHeight: 1, visibility: f ? 'visible' : 'hidden' }}>
                      {ch}
                    </span>
                  );
                })
              )}
              {!settled && beat >= 65 && <span style={{ display: 'inline-block', width: size * 0.3, height: size * 0.62, background: ink, marginLeft: 8, marginBottom: size * 0.1, opacity: beat < WORDMARK_START || caretBlink ? 1 : 0.9 }} />}
            </div>
            <div style={{ height: 2, width: 780 * Math.max(0, Math.min(1, beat - settleBeat(2))), background: ink, margin: '22px 0 20px' }} />
            <div style={{ fontFamily: MONO, fontSize: 36, color: dim, minHeight: 50 * 2, lineHeight: 1.4 }}>
              <div>
                {typed(tag1, 68).map((c, i) => (
                  <span key={i}>{c.ch}</span>
                ))}
              </div>
              <div>
                {typed(tag2, 69).map((c, i) => (
                  <span key={i} style={{ color: c.key ? SIGNAL.red : dim }}>
                    {c.ch}
                  </span>
                ))}
                {beat >= 68 && <span style={{ display: 'inline-block', width: 20, height: 34, background: dim, verticalAlign: '-6px', marginLeft: 4, opacity: caretBlink ? 1 : 0 }} />}
              </div>
            </div>
            {beat >= 71 && (
              <div style={{ fontFamily: MONO, fontWeight: 500, fontSize: 18, letterSpacing: '0.08em', color: dim, marginTop: 28 }}>nus.dev · MIT · macOS · Windows · Linux</div>
            )}
          </div>
        </div>
      </div>
      <Pop beat={beat} at={69} x={(W / 2) + 120 * k} y={H / 2 + 250 * k * (wide ? 1 : 1.6)} rotate={-4}>
        <Squiggle width={260 * k} height={46 * k} colour={SIGNAL.red} weight={16 * k} waves={1.5} />
      </Pop>
    </AbsoluteFill>
  );
}
