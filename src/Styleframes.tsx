// Styleframes: one still per section of the new cut (PLAN.md), set with the
// real type system, the Memphis kit, the real captures where we have them
// and ink-theme mocks where the Mac reshoot will record the real thing.
//   npx remotion still Styleframe out/design/sf-<id>.png --props='{"id":"<id>"}'
// (Vertical and Feed compositions take the same props.)

import type { ReactNode } from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { Caption } from './design/Caption';
import { useFrame } from './design/layout';
import { Dots, Pop, Solid, Squiggle, Sticker, Stripes } from './design/Memphis';
import { ActionBlock, AskBand, Caret, CodeCard, Completion, EditorPane, Line, PresetCard, ProfileCard, Shell, T, Welcome } from './design/Mocks';
import { BLACK, DIM_ON_WHITE, INK, MONO, SECTIONS, SIGNAL, type Section, WHITE } from './design/tokens';
import { EndCard } from './design/Wordmark';

const BEAT = 99; // typing complete: styleframes show the settled state

// Every section runs on the beat: `t` the film's beat now, `f` the beat it
// starts, `u` the beat it must be gone by (captions backspace out before
// it). A styleframe is the same component at t = 99. `frame` puts a Blender
// render sequence behind the sections that sit on 3D.
export type Timing = { t?: number; f?: number; u?: number; frame?: number; home?: boolean };
const shot = (name: string) => staticFile(`shots/${name}.png`);

// A capture as a hard-shadowed card: beside the caption in 16:9, below it in
// the narrow frames.
function useCard() {
  const { W, H, wide, m, col } = useFrame();
  if (wide) {
    const x = col(5);
    const w = W - m - x;
    const h = w / 1.6;
    return { x, y: (H - h) / 2 + 30, w, h };
  }
  const w = W - 2 * m;
  const h = w / 1.6;
  return { x: m, y: H * (H > 1600 ? 0.44 : 0.47), w, h };
}

function Card({ children, shadow = INK }: { children: ReactNode; shadow?: string }) {
  const c = useCard();
  const { k } = useFrame();
  return (
    <div style={{ position: 'absolute', left: c.x, top: c.y, width: c.w, height: c.h, border: `${2 * Math.max(1, k)}px solid ${INK}`, boxShadow: `${10 * k}px ${10 * k}px 0 ${shadow}`, overflow: 'hidden', background: T.bg }}>
      {children}
    </div>
  );
}

function Ground({ section, children }: { section: Section; children: ReactNode }) {
  return <AbsoluteFill style={{ background: SECTIONS[section].ground === 'white' ? WHITE : BLACK, overflow: 'hidden' }}>{children}</AbsoluteFill>;
}

function captionFor(section: Section, text: { kicker: string; headline: string; sub?: string }, wide: boolean, W: number, m: number, col: (n: number) => number, tm: { t: number; f: number; u: number } = { t: BEAT, f: 0, u: Infinity }) {
  const s = SECTIONS[section];
  return <Caption beat={tm.t} from={tm.f + 0.25} until={tm.u} signal={s.signal} ground={s.ground} {...text} style={wide ? { width: col(5) - m - 40 } : { width: W - 2 * m }} />;
}

// ── The frames ──────────────────────────────────────────────────────────────

export function Agents({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { W, H, wide, k, m, col } = useFrame();
  const c = useCard();
  const v = SIGNAL.violet;
  return (
    <Ground section="agents">
      <Pop beat={t} at={f + 0.5} x={c.x + c.w - 260 * k} y={c.y - 170 * k}>
        <Dots width={420 * k} height={300 * k} colour={v} pitch={20 * k} from="bottom-right" />
      </Pop>
      <Pop beat={t} at={f + 0.5} x={c.x + c.w - 110 * k} y={c.y + c.h - 90 * k}>
        <Solid shape="quarter" size={170 * k} colour={v} />
      </Pop>
      <Card>
        <Img src={shot('window-ink')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        <div style={{ position: 'absolute', left: '59.5%', right: '1%', top: '9%' }}>
          <AskBand text='claude wants to click "Merge"' size={12 * k * (wide ? 1 : 1.1)} accent={v} />
        </div>
        <div style={{ position: 'absolute', left: '61%', top: '30%', display: 'flex', flexDirection: 'column', gap: 12 * k }}>
          <ActionBlock who="claude" what="read page" when="12:03" lamp={T.green} size={13 * k} />
          <ActionBlock who="claude" what='scroll to "Files changed"' when="12:04" lamp={T.green} size={13 * k} />
          <ActionBlock who="claude" what='click "Merge"' when="12:04" lamp={v} size={13 * k} />
        </div>
      </Card>
      <Pop beat={t} at={f + 0.5} x={c.x - 40 * k} y={c.y + c.h - 70 * k} rotate={-10}>
        <Sticker icon="cursor-click" size={96 * k} />
      </Pop>
      {captionFor('agents', { kicker: 'Agents · 05', headline: 'agents, in *plain sight*.', sub: 'every click is a block you can read, stop or take over.' }, wide, W, m, col, { t, f, u })}
      <Pop beat={t} at={f + 0.5} x={m} y={wide ? H * 0.12 + 420 * k : c.y + c.h + 90 * k} rotate={-2}>
        <Squiggle width={(wide ? 420 : 380) * k} height={40 * k} colour={v} weight={14 * k} />
      </Pop>
    </Ground>
  );
}

export function Ports({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { W, wide, k, m, col } = useFrame();
  const c = useCard();
  const g = SIGNAL.gold;
  const s = c.w / 1600;
  const boxes: [string, number, number, number, number][] = [
    ['PORT', 298, 284, 76, 34],
    ['PROCESS', 676, 284, 144, 34],
    ['PAGE', 1068, 54, 402, 34],
  ];
  return (
    <Ground section="ports">
      <Pop beat={t} at={f + 0.5} x={c.x + c.w - 180 * k} y={c.y - 70 * k} rotate={8}>
        <Stripes width={240 * k} height={46 * k} colour={g} />
      </Pop>
      <Card>
        <Img src={shot('ports-ink')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        {boxes.map(([label, x, y, w, h]) => (
          <div key={label}>
            <div style={{ position: 'absolute', left: x * s, top: y * s, width: w * s, height: h * s, border: `${3 * k}px solid ${g}`, boxSizing: 'border-box' }} />
            <div style={{ position: 'absolute', left: x * s, top: (y - 26) * s, background: g, color: INK, fontFamily: MONO, fontWeight: 600, fontSize: 13 * k, letterSpacing: '0.06em', padding: `${2 * k}px ${7 * k}px` }}>{label}</div>
          </div>
        ))}
        <div style={{ position: 'absolute', left: 374 * s, top: 299 * s, width: (676 - 374) * s, height: 3 * k, background: g }} />
        <div style={{ position: 'absolute', left: 746 * s, top: 70 * s, width: 3 * k, height: (284 - 70) * s, background: g }} />
        <div style={{ position: 'absolute', left: 746 * s, top: 69 * s, width: (1068 - 746) * s, height: 3 * k, background: g }} />
      </Card>
      <Pop beat={t} at={f + 0.5} x={c.x - 70 * k} y={c.y + c.h - 110 * k}>
        <Solid shape="circle" size={130 * k} colour={g} />
      </Pop>
      {captionFor('ports', { kicker: 'Dev tools · 02', headline: 'every server.\nits *shell*.\nits page.', sub: 'the ports board traces each service to the shell that started it.' }, wide, W, m, col, { t, f, u })}
    </Ground>
  );
}

export function Language({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { k, W, H, wide, m } = useFrame();
  const size = (wide ? 27 : 34) * k;
  const sig = SIGNAL.teal;
  return (
    <Ground section="language">
      <Shell
        size={size}
        pad={wide ? 120 * k : 72}
        lines={[
          [['~/dev/acme-web ', T.dim], ['main', T.magenta]],
          [['› ', T.green], ['git log --oneline -3', T.fg]],
          [['a1f9c2e ', T.yellow], ['ports: remember the shell that started it', T.fg]],
          [['7be0d14 ', T.yellow], ['editor: hover from the language server', T.fg]],
          [['03c55a8 ', T.yellow], ['home: the profile card', T.fg]],
          [[' ']],
        ]}
      >
        <Line runs={[['› ', T.green], ['git ', T.yellow], ['ch', T.fg]]} size={size} />
        <div style={{ position: 'relative', top: -size * 1.45, left: size * 0.6 * 8.2, display: 'inline-flex', alignItems: 'flex-start' }}>
          <Caret size={size} />
        </div>
        <div style={{ marginLeft: size * 0.6 * 6, marginTop: -size * 0.9 }}>
          <Completion
            size={size}
            accent={sig}
            items={[
              ['checkout', 'switch branches'],
              ['cherry-pick', 'apply commits'],
              ['check-ignore', 'debug .gitignore'],
              ['cherry', 'find unmerged'],
            ]}
          />
        </div>
      </Shell>
      <Pop beat={t} at={f + 0.5} x={wide ? W - m - 190 * k : W - m - 150 * k} y={wide ? H - m - 560 * k : H * 0.56}>
        <Solid shape="half" size={150 * k} colour={sig} />
      </Pop>
      <div style={{ position: 'absolute', right: m, bottom: wide ? m : H * 0.08, background: WHITE, border: `2px solid ${INK}`, boxShadow: `${8 * k}px ${8 * k}px 0 ${sig}`, padding: `${26 * k}px ${34 * k}px`, width: wide ? 880 * k : W - 2 * m, boxSizing: 'border-box' }}>
        <Caption beat={t} from={f + 0.25} until={u} signal="teal" ground="white" kicker="Language · 01" headline={'language-aware,\neven *at the prompt*.'} sub="the same language servers as your editor." style={{ position: 'relative', left: 0, top: 0, width: '100%' }} />
      </div>
    </Ground>
  );
}

export function Held({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { k, W, H, wide, m } = useFrame();
  const size = (wide ? 26 : 30) * k;
  const g = SIGNAL.green;
  return (
    <Ground section="held">
      <Shell
        size={size}
        pad={wide ? 120 * k : 72}
        lines={[
          [['~/dev/acme-web ', T.dim], ['main', T.magenta]],
          [['› ', T.green], ['cargo watch -x test', T.fg]],
          [['[Running cargo test]', T.dim]],
          [['test ports::remembers_the_shell ... ', T.fg], ['ok', T.green]],
          [['test held::reattaches_after_quit ... ', T.fg], ['ok', T.green]],
          [['test result: ', T.fg], ['ok', T.green], ['. 212 passed; 0 failed', T.fg]],
          [[' ']],
          [['── nus quit · 14:02 ── relaunched · 14:02 ── reattached ──', T.dim]],
          [['[Running cargo test]', T.dim]],
          [['test result: ', T.fg], ['ok', T.green], ['. 212 passed; 0 failed', T.fg]],
        ]}
      >
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 * k, marginTop: 16 * k, background: g, color: T.paper, fontFamily: MONO, fontWeight: 600, fontSize: size * 0.8, padding: `${4 * k}px ${12 * k}px`, border: `2px solid ${T.fg}` }}>● held · cargo watch running</div>
      </Shell>
      <Pop beat={t} at={f + 0.5} x={wide ? W - m - 250 * k : W - m - 220 * k} y={wide ? H - m - 545 * k : H * 0.6} rotate={-6}>
        <Stripes width={260 * k} height={44 * k} colour={g} />
      </Pop>
      <div style={{ position: 'absolute', right: m, bottom: wide ? m : H * 0.08, background: WHITE, border: `2px solid ${INK}`, boxShadow: `${8 * k}px ${8 * k}px 0 ${g}`, padding: `${26 * k}px ${34 * k}px`, width: wide ? 860 * k : W - 2 * m, boxSizing: 'border-box' }}>
        <Caption beat={t} from={f + 0.25} until={u} signal="green" ground="white" kicker="Dev tools · 03" headline={'quit. update. crash.\nyour shells *keep running*.'} style={{ position: 'relative', left: 0, top: 0, width: '100%' }} />
      </div>
    </Ground>
  );
}

export function IDE({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { W, H, wide, k, m, col } = useFrame();
  const b = SIGNAL.blue;
  return (
    <Ground section="ide">
      <Img src={staticFile(frame !== undefined ? `renders/internals/f${String(Math.min(1042, Math.max(664, frame))).padStart(4, '0')}.png` : 'lookdev/internals-0960.png')} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: '66% 50%' }} />
      {captionFor('ide', { kicker: 'Architecture · 04', headline: 'built like an *IDE*.', sub: 'one native compositor. real chromium, drawn beside your shells.' }, wide, W, m, col, { t, f, u })}
      <Pop beat={t} at={f + 0.5} x={m} y={(wide ? H * 0.12 : H * 0.08) + (wide ? 390 : 480) * k}>
        <Squiggle width={330 * k} height={36 * k} colour={b} weight={13 * k} />
      </Pop>
      <Pop beat={t} at={f + 0.5} x={W - 330 * k} y={H - 250 * k}>
        <Dots width={360 * k} height={280 * k} colour={b} pitch={20 * k} from="bottom-right" />
      </Pop>
    </Ground>
  );
}

export function Yours({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { W, H, wide, k, m, col } = useFrame();
  const c = useCard();
  const presets: [string, string[], string][] = [
    ['Broadsheet', ['#f4f1ea', '#e9e4d8'], SIGNAL.red],
    ['Midnight', ['#1f2a44', '#141414'], SIGNAL.blue],
    ['Ledger', ['#eef3e6', '#d7e4c7'], SIGNAL.green],
    ['Darkroom', ['#2b1a1a', '#141414'], SIGNAL.gold],
  ];
  const cs = (wide ? 44 : 43) * k;
  return (
    <Ground section="yours">
      <div style={{ position: 'absolute', left: c.x, top: wide ? H * 0.3 : c.y, width: c.w }}>
        <CodeCard
          title="rules.luau"
          size={(wide ? 19 : 22) * k}
          lines={[
            [['function ', T.magenta], ['new_tab', T.blue], ['(ctx)', T.fg]],
            [['  if ', T.magenta], ['ctx.kind == ', T.fg], ['"shell"', T.green], [' then', T.magenta]],
            [['    return ', T.magenta], ['{ signal = ', T.fg], ['hue', T.blue], ['(ctx.index * ', T.fg], ['47', T.yellow], [') }', T.fg]],
            [['  end', T.magenta]],
            [['end', T.magenta]],
          ]}
        />
        <div style={{ display: 'flex', gap: 22 * k, marginTop: 34 * k, flexWrap: 'wrap' }}>
          {presets.map(([n, r, s], i) => (
            <PresetCard key={n} name={n} ramp={r} signal={s} size={cs} ring={i === 0} />
          ))}
        </div>
      </div>
      {captionFor('yours', { kicker: 'Customizable · 06', headline: 'yours, *all the way down*.', sub: 'rules, layouts and looks in luau. every colour a token.' }, wide, W, m, col, { t, f, u })}
      {(['red', 'blue', 'gold', 'green', 'violet', 'teal'] as const).map((s, i) => (
        <Pop key={s} beat={t} at={f + 0.5} x={m + i * 58 * k} y={wide ? H - m - 60 * k : c.y - 110 * k}>
          <Solid shape={i % 2 ? 'circle' : 'square'} size={40 * k} colour={SIGNAL[s]} />
        </Pop>
      ))}
    </Ground>
  );
}

export function Private({ t = BEAT, f = 0, u = Infinity, frame, home }: Timing = {}) {
  const { W, H, wide, k, m, col } = useFrame();
  const r = SIGNAL.red;
  return (
    <Ground section="private">
      <Img src={staticFile(frame !== undefined ? `renders/outro/f${String(frame).padStart(4, '0')}.png` : 'lookdev/apple-outro-1240.png')} style={wide ? { position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: '62% 50%' } : { position: 'absolute', left: 0, right: 0, bottom: 0, width: '100%', height: '58%', objectFit: 'cover', objectPosition: '66% 50%' }} />
      {captionFor('private', home ? { kicker: 'Home · 07', headline: 'you, *on this machine*.', sub: 'your profile is a file. no server, nothing counted, nothing sent.' } : { kicker: 'Private · 08', headline: 'no account.\nno server.\nno *telemetry*.', sub: 'a file in a folder is the whole account. sync is sealed with a key you copy.' }, wide, W, m, col, { t, f, u })}
      <Pop beat={t} at={f + 0.5} x={m} y={wide ? H - 150 * k : H * 0.4} rotate={-3}>
        <Stripes width={280 * k} height={44 * k} colour={r} />
      </Pop>
    </Ground>
  );
}

export function Home({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { W, H, wide, k, m, col } = useFrame();
  const r = SIGNAL.red;
  const c = useCard();
  return (
    <Ground section="yours">
      <Pop beat={t} at={f + 0.5} x={c.x + c.w - 300 * k} y={c.y - 150 * k}>
        <Dots width={380 * k} height={240 * k} colour={r} pitch={20 * k} from="bottom-right" />
      </Pop>
      <Card>
        <Welcome size={(wide ? 19 : 17) * k} accent={r} />
      </Card>
      <div style={{ position: 'absolute', left: wide ? c.x + c.w - 470 * k : W - m - 440 * k, top: wide ? c.y + c.h * 0.36 : c.y + c.h * 0.42 }}>
        <ProfileCard size={(wide ? 22 : 21) * k} accent={r} />
      </div>
      <Pop beat={t} at={f + 0.5} x={c.x - 50 * k} y={c.y - 50 * k} rotate={-10}>
        <Sticker icon="house" size={100 * k} />
      </Pop>
      {captionFor('yours', { kicker: 'Home · 07', headline: 'you, *on this machine*.', sub: 'your profile is a file. no server, nothing counted, nothing sent.' }, wide, W, m, col, { t, f, u })}
    </Ground>
  );
}

export function NumberCard({ t = BEAT, f = 0, u = Infinity, frame }: Timing = {}) {
  const { W, H, wide, k, m } = useFrame();
  return (
    <AbsoluteFill style={{ background: WHITE }}>
      <Pop beat={t} at={f + 0.5} x={W - 520 * k} y={-40 * k}>
        <Dots width={560 * k} height={400 * k} colour={SIGNAL.red} pitch={22 * k} from="top-left" />
      </Pop>
      <div style={{ position: 'absolute', left: m, top: wide ? H * 0.22 : H * 0.3, fontFamily: MONO, color: INK }}>
        <div style={{ fontWeight: 500, fontSize: 18 * k * (wide ? 1 : 1.3), letterSpacing: '0.08em', color: DIM_ON_WHITE, marginBottom: 20 * k }}>Key to screen · measured</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 20 * k }}>
          <span style={{ fontWeight: 600, fontSize: 280 * k * (wide ? 1 : 1.25), letterSpacing: '-0.04em', lineHeight: 0.9 }}>2.8</span>
          <span style={{ fontSize: 110 * k * (wide ? 1 : 1.25), color: DIM_ON_WHITE }}>ms</span>
        </div>
        <div style={{ fontSize: 30 * k * (wide ? 1 : 1.2), color: DIM_ON_WHITE, marginTop: 24 * k }}>fast like a <span style={{ color: SIGNAL.red }}>terminal</span>. because it is one.</div>
      </div>
      <div style={{ position: 'absolute', left: m, bottom: wide ? 70 * k : H * 0.06, fontFamily: MONO, fontSize: 15 * k * (wide ? 1 : 1.3), letterSpacing: '0.04em', color: DIM_ON_WHITE }}>key → present · vt-render spike, release · TODO: the full app, on the recording Mac</div>
      <Pop beat={t} at={f + 0.5} x={wide ? W * 0.62 : W - m - 220 * k} y={wide ? H * 0.52 : H * 0.62}>
        <Solid shape="circle" size={220 * k} colour={SIGNAL.red} />
      </Pop>
      <Pop beat={t} at={f + 0.5} x={wide ? W * 0.72 : m} y={wide ? H * 0.7 : H * 0.78} rotate={-8}>
        <Squiggle width={300 * k} height={50 * k} colour={SIGNAL.gold} weight={16 * k} />
      </Pop>
    </AbsoluteFill>
  );
}

export function Editor({ t = BEAT, f = 0, u = Infinity }: Timing = {}) {
  const { W, H, wide, k, m, col } = useFrame();
  const c = useCard();
  const b = SIGNAL.blue;
  return (
    <Ground section="editor">
      <Pop beat={t} at={f + 0.5} x={c.x + c.w - 250 * k} y={c.y - 150 * k}>
        <Dots width={380 * k} height={260 * k} colour={b} pitch={20 * k} from="bottom-right" />
      </Pop>
      <Card>
        <EditorPane size={(wide ? 17 : 15) * k * (c.w / (1100 * k))} accent={SIGNAL.red} />
      </Card>
      <Pop beat={t} at={f + 0.5} x={c.x - 40 * k} y={c.y + c.h - 80 * k} rotate={-8}>
        <Sticker icon="code" size={96 * k} />
      </Pop>
      {captionFor('editor', { kicker: 'Architecture · 04', headline: 'an editor, with *its language server*.', sub: 'hover, diagnostics, go to definition — in a pane beside the shell.' }, wide, W, m, col, { t, f, u })}
    </Ground>
  );
}

// A sheet of the kit itself, for the design file.
function Kit() {
  const { k } = useFrame();
  const label = (t: string) => <div style={{ fontFamily: MONO, fontWeight: 500, fontSize: 16 * k, letterSpacing: '0.08em', color: DIM_ON_WHITE, marginTop: 14 * k }}>{t}</div>;
  const cell = (el: ReactNode, t: string) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
      {el}
      {label(t)}
    </div>
  );
  return (
    <AbsoluteFill style={{ background: WHITE, padding: 110 * k, boxSizing: 'border-box', fontFamily: MONO }}>
      <div style={{ fontWeight: 600, fontSize: 56 * k, letterSpacing: '-0.02em', color: INK }}>the kit</div>
      <div style={{ fontSize: 22 * k, color: DIM_ON_WHITE, marginBottom: 60 * k }}>memphis, made of what nus already draws. one signal per section; shapes frame, never cover.</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 60 * k, alignItems: 'end' }}>
        {cell(<Squiggle width={300 * k} height={50 * k} colour={SIGNAL.violet} weight={16 * k} />, 'Squiggle · the orbit band')}
        {cell(<Stripes width={260 * k} height={46 * k} colour={SIGNAL.gold} />, 'Stripes · hazard tape')}
        {cell(<Dots width={260 * k} height={150 * k} colour={SIGNAL.teal} pitch={18 * k} />, 'Dots · halftone')}
        {cell(<div style={{ display: 'flex', gap: 24 * k }}><Solid shape="circle" size={90 * k} colour={SIGNAL.red} /><Solid shape="quarter" size={90 * k} colour={SIGNAL.blue} /><Solid shape="half" size={90 * k} colour={SIGNAL.green} /></div>, 'Solids · lamps, the space square')}
        {cell(<div style={{ display: 'flex', gap: 20 * k }}><Sticker icon="cursor-click" size={90 * k} /><Sticker icon="lock-key" size={90 * k} /><Sticker icon="plugs-connected" size={90 * k} /></div>, 'Stickers · Phosphor')}
        {cell(<div style={{ display: 'flex', gap: 14 * k }}>{(['red', 'blue', 'gold', 'green', 'violet', 'teal'] as const).map((s) => <div key={s} style={{ width: 54 * k, height: 54 * k, background: SIGNAL[s], border: `2px solid ${INK}`, boxShadow: `4px 4px 0 ${INK}` }} />)}</div>, 'Signals · agents violet · ports gold · language teal · held green · ide blue · yours/private red')}
        {cell(<div style={{ fontSize: 88 * k * 0.6, fontWeight: 600, letterSpacing: '-0.02em', color: INK }}>plex mono <span style={{ color: SIGNAL.red }}>600</span></div>, 'Headline · 88 · −0.02em')}
        {cell(<div style={{ fontFamily: "'Newsreader'", fontStyle: 'italic', fontSize: 96 * k, color: INK, lineHeight: 1 }}>nus</div>, 'Wordmark only · Newsreader Italic')}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 56 * k, marginTop: 80 * k, color: INK, borderTop: `2px solid ${INK}`, paddingTop: 36 * k, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 18 * k, fontWeight: 500, letterSpacing: '0.08em', color: DIM_ON_WHITE }}>KICKER 18/500</span>
        <span style={{ fontSize: 30 * k, color: DIM_ON_WHITE }}>sub 30/400 · 42ch</span>
        <span style={{ fontSize: 30 * k, fontFamily: MONO, background: '#141414', color: '#ece7da', padding: `${2 * k}px ${10 * k}px` }}>code 30</span>
        <span style={{ fontSize: 88 * k * 0.7, fontWeight: 600, letterSpacing: '-0.02em' }}>headline 88</span>
        <span style={{ fontSize: 110 * k, fontWeight: 600, letterSpacing: '-0.04em' }}>2.8<span style={{ fontSize: 40 * k, color: DIM_ON_WHITE }}> number 240</span></span>
      </div>
    </AbsoluteFill>
  );
}

const FRAMES: Record<string, () => ReactNode> = {
  agents: Agents,
  ports: Ports,
  language: Language,
  held: Held,
  ide: IDE,
  yours: Yours,
  home: Home,
  private: Private,
  number: NumberCard,
  editor: Editor,
  kit: Kit,
  'end-a': () => <EndCard beat={65.4} />,
  'end-b': () => <EndCard beat={66.62} />,
  'end-c': () => <EndCard beat={72} />,
  'end-white': () => <EndCard beat={72} ground="white" />,
};

export const Styleframe = ({ id }: { id: string }) => {
  const F = FRAMES[id];
  return F ? <>{F()}</> : <AbsoluteFill style={{ background: WHITE }} />;
};
export const STYLEFRAMES = Object.keys(FRAMES);
