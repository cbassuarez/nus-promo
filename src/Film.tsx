// nus — the promo. 30 s, 152 bpm, Perc Kitchen Kit.
//
// Pure white and pure black grounds; the app's own ease-out cubic; hard
// shadows, nothing blurs. Every capture is a real one from nus/docs/media.
// The claims follow the positioning: the running local loop first (a port,
// its process, its page), then how it's built, then how it's driven — no
// firsts, no speed, no AI headline.
//
//  beats   ground  section                                          made in
//   0–8    white   the lid lifts, the screen comes on, fly into it   Blender
//   8–12   white   a URL at the prompt, the page beside the shell    capture
//  12      —       hazard shutter
//  12–20   white   ports: port → process → page, traced              capture
//  20      —       band wipe
//  20–24   white   the prompt, lit and predicted                      capture
//  24–25   white   Ctrl+Shift, K — macro                              Blender
//  25–28   white   the palette                                        capture
//  28–29   —       cell resolve
//  28–44   black   the software's parts as machined slabs             Blender
//  43–44   —       band wipe
//  44–52   white   one action model: the CLI                          type
//  52–53   —       cell resolve
//  52–64   black   rim light, a theme a beat, the lid shuts           Blender
//  64–76   white   nus                                                icon renderer
//
// The 3D shots are frames from blender/nus.py (public/renders/<shot>/f####.png,
// numbered by film frame). Captures become footage when the reshoot lands:
// public/footage/<name>.mp4 wins over public/shots/<name>.png (npm run footage).

import { Fragment, type CSSProperties, type ReactNode } from 'react';
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { MONO, SERIF } from './fonts';
import { FPB, easeOut, lerp, ramp } from './grid';
import footage from './footage.json';
import marks from './marks.json';
import { BandWipe, CellResolve, Shutter } from './Transitions';

const WHITE = '#ffffff';
const BLACK = '#000000';
const INK = '#141414';
const SIGNAL = '#c8102e';
const shot = (name: string) => staticFile(`shots/${name}.png`);

// ── Layout: one film, three frames ──────────────────────────────────────────
// 16:9 (the master, 1920×1080 at --scale 2 → 3840×2160), 9:16 (1080×1920)
// and 4:5 (1080×1350). Type is re-set for the frame, never cropped; `k`
// scales it, `m` is the margin, `wide` picks the landscape arrangement.
function useLayout() {
  const { width: W, height: H } = useVideoConfig();
  const wide = W / H > 1.2;
  const k = wide ? W / 1920 : (W / 1080) * 0.78;
  const m = wide ? 110 * k : 64;
  return { W, H, wide, k, m };
}

// ── Type ────────────────────────────────────────────────────────────────────
// Words set on their beat, instantly, like type. A signal rule draws above.
type Line = [text: string, beat: number][];
function Words({ beat, lines, from, style, size: base = 112, color = BLACK, rule = true }: { beat: number; lines: Line[]; from: number; style?: CSSProperties; size?: number; color?: string; rule?: boolean }) {
  const { k, m } = useLayout();
  const size = base * k;
  return (
    <div style={{ position: 'absolute', left: m, top: m, display: 'flex', flexDirection: 'column', gap: size * 0.12, ...style }}>
      {rule && <div style={{ height: 6 * k, width: 220 * k * ramp(beat, from, from + 1), background: SIGNAL, marginBottom: 18 * k }} />}
      {lines.map((line, i) => (
        <div key={i} style={{ fontFamily: SERIF, fontStyle: 'italic', fontWeight: 500, fontSize: size, lineHeight: 1.02, color, whiteSpace: 'nowrap' }}>
          {line.map(([text, b], j) => (
            <span key={j} style={{ visibility: beat >= b ? 'visible' : 'hidden' }}>
              {j > 0 ? ' ' : ''}
              {text}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}

// A caption box over a capture: white, a 2 px edge, the app's hard 8×8 shadow.
function Plate({ beat, from, title, sub, subAt }: { beat: number; from: number; title: Line; sub?: string; subAt?: number }) {
  const { W, k, m, wide } = useLayout();
  if (beat < from) return null;
  return (
    <div style={{ position: 'absolute', left: m, bottom: wide ? 96 * k : m * 1.5, maxWidth: W - 2 * m, boxSizing: 'border-box', background: WHITE, border: `2px solid ${BLACK}`, boxShadow: `${8 * k}px ${8 * k}px 0 ${BLACK}`, padding: `${24 * k}px ${36 * k}px ${28 * k}px`, display: 'flex', flexDirection: 'column', gap: 12 * k }}>
      <div style={{ height: 6 * k, width: 140 * k * ramp(beat, from, from + 1), background: SIGNAL }} />
      <div style={{ fontFamily: SERIF, fontStyle: 'italic', fontWeight: 500, fontSize: 76 * k, lineHeight: 1.04, color: BLACK, whiteSpace: wide ? 'nowrap' : 'normal' }}>
        {title.map(([t, b], j) => (
          <span key={j} style={{ visibility: beat >= b ? 'visible' : 'hidden' }}>
            {j > 0 ? ' ' : ''}
            {t}
          </span>
        ))}
      </div>
      {sub && <div style={{ fontFamily: MONO, fontSize: 28 * k, color: BLACK, visibility: beat >= (subAt ?? from) ? 'visible' : 'hidden' }}>{sub}</div>}
    </div>
  );
}

// ── A capture, full frame, with a push toward a point ───────────────────────
// Children draw in capture pixels (1600×1000), so overlays stay registered.
// Where each reshoot clip's time zero falls in the film (see RESHOOT.md).
export const CLIP_START: Record<string, number> = { 'window-ink': 4, 'ports-ink': 12, 'prompt-ink': 20, 'palette-ink': 24 };

// A capture: the reshoot's clip if it has landed, else the still.
function Media({ name, w = 1600, h = 1000 }: { name: string; w?: number | string; h?: number | string }) {
  const style = { width: w, height: h, display: 'block' } as const;
  if ((footage as Record<string, unknown>)[name]) {
    return (
      <Sequence from={Math.round((CLIP_START[name] ?? 0) * FPB)} layout="none">
        <OffthreadVideo src={staticFile(`footage/${name}.mp4`)} style={style} muted />
      </Sequence>
    );
  }
  return <Img src={shot(name)} style={style} />;
}

// Element positions, in the capture's logical px (1600×1000). The reshoot
// writes them next to its clips; these defaults are registered to the stills.
type Rect = [number, number, number, number];
const MARKS = marks as Record<string, Record<string, Rect>>;
const PORT_TRACE: [string, Rect][] = (() => {
  const m = MARKS['ports-ink'];
  const order = ['port', 'process', 'shell', 'page'];
  if (m) return order.filter((k) => m[k]).map((k) => [k.toUpperCase(), m[k]] as [string, Rect]);
  return [
    ['PORT', [298, 284, 76, 34]],
    ['PROCESS', [676, 284, 144, 34]],
    ['PAGE', [1068, 54, 402, 34]],
  ];
})();
const GHOST: Rect = MARKS['prompt-ink']?.ghost ?? [386, 328, 186, 30];

// The scale is set for 16:9; other frames keep the same visible height of
// the capture, so the fly-in's hand-off still lines up in 9:16 and 4:5.
function Flat({ name, beat, from, to, s0, s1, focus, children }: { name: string; beat: number; from: number; to: number; s0: number; s1: number; focus: [number, number]; children?: ReactNode }) {
  const { W, H } = useLayout();
  const s = Math.max(lerp(s0, s1, ramp(beat, from, to)) * (H / 1080), W / 1600);
  const tx = Math.min(0, Math.max(W - 1600 * s, W / 2 - focus[0] * s));
  const ty = Math.min(0, Math.max(H - 1000 * s, H / 2 - focus[1] * s));
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 1600, height: 1000, transformOrigin: '0 0', transform: `translate(${tx}px, ${ty}px) scale(${s})` }}>
      <Media name={name} />
      {children}
    </div>
  );
}

// ── The 3D shots ────────────────────────────────────────────────────────────
// Where each render is cropped for the narrow frames: the horizontal centre
// of the crop (0–1 of the 16:9 render), keyed in beats. 16:9 shows it all.
const CROP: Record<string, [number, number][]> = {
  open: [[0, 0.44], [4, 0.47], [8, 0.5]],
  macro: [[24, 0.55]],
  internals: [[28, 0.66], [44, 0.64]],
  outro: [[52, 0.66], [64, 0.6]],
};
function cropAt(name: string, beat: number) {
  const keys = CROP[name];
  if (beat <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (beat < keys[i][0]) return lerp(keys[i - 1][1], keys[i][1], (beat - keys[i - 1][0]) / (keys[i][0] - keys[i - 1][0]));
  return keys[keys.length - 1][1];
}
export function Render({ name, frame, bg }: { name: string; frame: number; bg: string }) {
  const x = cropAt(name, frame / FPB);
  return (
    <AbsoluteFill style={{ background: bg }}>
      <Img src={staticFile(`renders/${name}/f${String(frame).padStart(4, '0')}.png`)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${x * 100}% 50%` }} />
    </AbsoluteFill>
  );
}

function OutroShot({ beat, frame }: { beat: number; frame: number }) {
  return (
    <AbsoluteFill>
      <Render name="outro" frame={frame} bg={BLACK} />
      {beat < 60 && <Words beat={beat} from={53} color={WHITE} lines={[[['Paper,', 53], ['ink,', 54]], [['or yours.', 55]]]} />}
    </AbsoluteFill>
  );
}

function InternalsShot({ beat, frame }: { beat: number; frame: number }) {
  return (
    <AbsoluteFill>
      <Render name="internals" frame={frame} bg={BLACK} />
      <Words beat={beat} from={36} color={WHITE} size={84} lines={[[['One native compositor.', 36]], [['Chromium and the terminal,', 38]], [['drawn as peers.', 39]]]} />
    </AbsoluteFill>
  );
}

// ── 8–11 · a URL at the prompt ──────────────────────────────────────────────
function UrlShot({ beat }: { beat: number }) {
  return (
    <AbsoluteFill style={{ background: WHITE, overflow: 'hidden' }}>
      <Flat name="window-ink" beat={beat} from={8} to={12} s0={1.2} s1={1.34} focus={[800, 500]} />
      <Plate beat={beat} from={9} title={[['Type a URL at the prompt.', 9]]} sub="It opens beside the shell." subAt={10} />
    </AbsoluteFill>
  );
}

// ── 12–19 · ports: port → process → page ────────────────────────────────────
// Registered to ports-ink.png: the 8000 row, its process, and the page it
// serves, open in the browser pane (the URL field above the board).
function Box({ x, y, w, h, on }: { x: number; y: number; w: number; h: number; on: boolean }) {
  return on ? <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, border: `3px solid ${SIGNAL}`, boxSizing: 'border-box' }} /> : null;
}
function Tag({ x, y, on, children }: { x: number; y: number; on: boolean; children: ReactNode }) {
  return on ? (
    <div style={{ position: 'absolute', left: x, top: y, background: SIGNAL, color: WHITE, fontFamily: MONO, fontWeight: 600, fontSize: 17, letterSpacing: '0.06em', padding: '3px 9px', whiteSpace: 'nowrap' }}>{children}</div>
  ) : null;
}
// The trace: each element boxed on its beat, an elbow drawn to the next
// over the beat before it — port → process → (its shell →) the page.
function PortsShot({ beat }: { beat: number }) {
  const centre = (r: Rect) => [r[0] + r[2] / 2, r[1] + r[3] / 2];
  return (
    <AbsoluteFill style={{ background: WHITE, overflow: 'hidden' }}>
      <Flat name="ports-ink" beat={beat} from={12} to={20} s0={1.2} s1={1.28} focus={[800, 330]}>
        {PORT_TRACE.map(([label, r], i) => {
          const at = 13 + i;
          const prev = i > 0 ? PORT_TRACE[i - 1][1] : null;
          let lines: ReactNode = null;
          if (prev && beat >= at - 1) {
            const [ax, ay] = centre(prev);
            const [bx, by] = centre(r);
            const across = ramp(beat, at - 1, at - 0.5);
            const along = ramp(beat, at - 0.5, at);
            lines = (
              <>
                <div style={{ position: 'absolute', left: Math.min(ax, ax + (bx - ax) * across), top: ay - 1.5, width: Math.abs(bx - ax) * across, height: 3, background: SIGNAL }} />
                {beat >= at - 0.5 && <div style={{ position: 'absolute', left: bx - 1.5, top: Math.min(ay, ay + (by - ay) * along), width: 3, height: Math.abs(by - ay) * along, background: SIGNAL }} />}
              </>
            );
          }
          return (
            <Fragment key={label}>
              {lines}
              <Box x={r[0]} y={r[1]} w={r[2]} h={r[3]} on={beat >= at} />
              <Tag x={r[0]} y={r[1] - 34} on={beat >= at}>
                {label}
              </Tag>
            </Fragment>
          );
        })}
      </Flat>
      <Plate beat={beat} from={16} title={[['Every port.', 16], ['Its process.', 17], ['Its page.', 18]]} />
    </AbsoluteFill>
  );
}

// ── 20–23 · the prompt, lit and predicted ───────────────────────────────────
function PromptShot({ beat }: { beat: number }) {
  const { W, H, wide, k, m } = useLayout();
  // The card: right of the words in 16:9, below them in the narrow frames.
  const S = wide ? 1.55 * k : (W - 2 * m) / 646;
  const left = wide ? 790 * k : m;
  const top = (wide ? 214 * k : H * 0.44) + 40 * k * (1 - ramp(beat, 20, 20.5));
  return (
    <AbsoluteFill style={{ background: WHITE }}>
      <div style={{ position: 'absolute', left, top, width: 646 * S, height: 420 * S, border: `2px solid ${BLACK}`, boxShadow: `${10 * k}px ${10 * k}px 0 ${BLACK}` }}>
        <Media name="prompt-ink" w="100%" h="100%" />
        {/* The ghost: history continuing the line past the caret. */}
        {beat >= 22 && <div style={{ position: 'absolute', left: GHOST[0] * S, top: GHOST[1] * S, width: GHOST[2] * S, height: GHOST[3] * S, border: `3px solid ${SIGNAL}`, boxSizing: 'border-box' }} />}
      </div>
      <Words beat={beat} from={20} style={wide ? { top: 290 * k } : { top: H * 0.1 }} size={84} lines={[[['Lit as you type.', 20]], [['Predicted', 22]], [['from history.', 22]]]} />
    </AbsoluteFill>
  );
}

// ── 25–28 · the palette (after the Ctrl+Shift+K macro) ──────────────────────
function PaletteShot({ beat }: { beat: number }) {
  return (
    <AbsoluteFill style={{ background: WHITE, overflow: 'hidden' }}>
      <Flat name="palette-ink" beat={beat} from={25} to={29} s0={1.3} s1={1.5} focus={[805, 330]} />
      <Plate beat={beat} from={25} title={[['Tabs, actions, the web.', 25]]} sub="⌘K · Ctrl+Shift+K" subAt={25.5} />
    </AbsoluteFill>
  );
}

// ── 44–51 · one action model ────────────────────────────────────────────────
// Real verbs of the nus CLI (crates/cli); lit the way the prompt lights them.
const COMMANDS: { beat: number; parts: [string, string][] }[] = [
  { beat: 46, parts: [['nus', '#e5b94a'], [' open ', '#ece7da'], ['localhost:5173', '#6fd0da'], [' --split', '#8a857a']] },
  { beat: 47, parts: [['nus', '#e5b94a'], [' launch ', '#ece7da'], ['--run', '#8a857a'], [" 'cargo watch'", '#7ac77f']] },
  { beat: 48, parts: [['nus', '#e5b94a'], [' ls', '#ece7da']] },
  { beat: 49, parts: [['nus', '#e5b94a'], [' block last', '#ece7da']] },
];
function ActionShot({ beat }: { beat: number }) {
  const { W, H, wide, k, m } = useLayout();
  const card = wide ? { left: 960 * k, top: 250 * k, width: 850 * k } : { left: m, top: H * 0.5, width: W - 2 * m };
  const fs = wide ? 30 * k : Math.min(30 * k, (card.width - 56 * k) / 21);
  return (
    <AbsoluteFill style={{ background: WHITE }}>
      <Words beat={beat} from={44} style={{ top: wide ? 250 * k : H * 0.12 }} size={104} lines={[[['One action model.', 44]]]} />
      <div style={{ position: 'absolute', left: m, top: wide ? 470 * k : H * 0.12 + 230 * k, width: wide ? 700 * k : W - 2 * m, fontFamily: MONO, fontSize: 30 * k, lineHeight: 1.5, color: BLACK, visibility: beat >= 45 ? 'visible' : 'hidden' }}>
        The nus CLI, your rules and the palette drive the same actions.
      </div>
      <div style={{ position: 'absolute', ...card, height: 350 * k, background: INK, border: `2px solid ${BLACK}`, boxShadow: `${10 * k}px ${10 * k}px 0 ${BLACK}`, fontFamily: MONO }}>
        <div style={{ height: 48 * k, borderBottom: '1.5px solid #3a3a3a', display: 'flex', alignItems: 'center', gap: 14 * k, padding: `0 ${22 * k}px`, color: '#ece7da', fontSize: 18 * k, fontWeight: 600, letterSpacing: '0.06em' }}>
          <div style={{ width: 12 * k, height: 12 * k, background: SIGNAL }} />
          Shell · ~/app
        </div>
        <div style={{ padding: `${26 * k}px ${28 * k}px`, display: 'flex', flexDirection: 'column', gap: 22 * k, fontSize: fs }}>
          {COMMANDS.map((c, i) => (
            <div key={i} style={{ visibility: beat >= c.beat ? 'visible' : 'hidden', whiteSpace: 'nowrap' }}>
              <span style={{ color: '#5a564e' }}>$ </span>
              {c.parts.map(([t, col], j) => (
                <span key={j} style={{ color: col }}>
                  {t}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
}

// ── 64–75 · nus ─────────────────────────────────────────────────────────────
export const TAGLINE = 'From the shell to the page it serves.';
function EndCard({ beat }: { beat: number }) {
  // The icon's band draws in: nus-render's own app_icon_at, frame by frame.
  const band = Math.round(120 * ramp(beat, 64, 66.5));
  const { W, m } = useLayout();
  // The lockup is drawn at 16:9 size (about 1250 wide) and scaled to fit.
  const fit = Math.min(W / 1920, (W - 2 * m) / 1250);
  return (
    <AbsoluteFill style={{ background: WHITE }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 44, transform: `scale(${fit})` }}>
        <Img src={staticFile(`icon/icon-${String(band).padStart(3, '0')}.png`)} style={{ width: 400, height: 400, display: 'block' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontFamily: SERIF, fontStyle: 'italic', fontWeight: 500, fontSize: 190, lineHeight: 0.9, color: INK, visibility: beat >= 66 ? 'visible' : 'hidden' }}>nus</div>
          <div style={{ height: 1.5, width: 800 * ramp(beat, 66, 67), background: INK, margin: '18px 0 14px' }} />
          <div style={{ fontFamily: MONO, fontSize: 36, color: INK, whiteSpace: 'nowrap', visibility: beat >= 68 ? 'visible' : 'hidden' }}>{TAGLINE}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// ── The film ────────────────────────────────────────────────────────────────
function shotAt(beat: number, frame: number): ReactNode {
  if (beat < 8) return <Render name="open" frame={frame} bg={WHITE} />;
  if (beat < 12) return <UrlShot beat={beat} />;
  if (beat < 20) return <PortsShot beat={beat} />;
  if (beat < 24) return <PromptShot beat={beat} />;
  if (beat < 25) return <Render name="macro" frame={frame} bg={WHITE} />;
  if (beat < 28) return <PaletteShot beat={beat} />;
  if (beat < 44) return <InternalsShot beat={beat} frame={frame} />;
  if (beat < 52) return <ActionShot beat={beat} />;
  if (beat < 64) return <OutroShot beat={beat} frame={frame} />;
  return <EndCard beat={beat} />;
}

// Each window sits where both sides have picture: a Blender shot only
// exists inside its own beats, so its side of the cut is the one that waits.
const TRANSITIONS: { from: number; to: number; kind: 'shutter' | 'band' | 'cells'; a: (b: number, f: number) => ReactNode; b: (b: number, f: number) => ReactNode }[] = [
  { from: 11.5, to: 12.5, kind: 'shutter', a: (b) => <UrlShot beat={b} />, b: (b) => <PortsShot beat={b} /> },
  { from: 19.5, to: 20.5, kind: 'band', a: (b) => <PortsShot beat={b} />, b: (b) => <PromptShot beat={b} /> },
  { from: 28, to: 29, kind: 'cells', a: (b) => <PaletteShot beat={b} />, b: (b, f) => <InternalsShot beat={b} frame={f} /> },
  { from: 43, to: 44, kind: 'band', a: (b, f) => <InternalsShot beat={b} frame={f} />, b: (b) => <ActionShot beat={b} /> },
  { from: 52, to: 53, kind: 'cells', a: (b) => <ActionShot beat={b} />, b: (b, f) => <OutroShot beat={b} frame={f} /> },
];

export const Film = () => {
  const frame = useCurrentFrame();
  const beat = frame / FPB;
  const t = TRANSITIONS.find((x) => beat >= x.from && beat < x.to);
  let picture: ReactNode = shotAt(beat, frame);
  if (t) {
    const p = (beat - t.from) / (t.to - t.from);
    const a = t.a(beat, frame);
    const b = t.b(beat, frame);
    picture = t.kind === 'shutter' ? <Shutter p={p} a={a} b={b} /> : t.kind === 'band' ? <BandWipe p={p} a={a} b={b} /> : <CellResolve p={p} frame={frame} a={a} b={b} />;
  }
  return (
    <AbsoluteFill style={{ background: WHITE, overflow: 'hidden' }}>
      <Audio src={staticFile('score.wav')} />
      {picture}
    </AbsoluteFill>
  );
};
