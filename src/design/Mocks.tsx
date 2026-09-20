// Stand-ins for UI the Mac reshoot will record for real (RESHOOT.md): drawn
// from nus's own ink-theme tokens so the styleframes read true, and marked
// MOCK in a corner so nobody mistakes one for a capture.

import type { CSSProperties, ReactNode } from 'react';
import { MONO, SERIF, SIGNAL } from './tokens';

export const T = {
  bg: '#141414',
  fg: '#ece7da',
  dim: '#8a857a',
  rule: '#3a3a3a',
  red: '#e0574c',
  green: '#7ac77f',
  yellow: '#e5b94a',
  blue: '#6ea3ef',
  magenta: '#d086d0',
  cyan: '#6fd0da',
  paper: '#f4f1ea',
  ink: '#141414',
};

export const Mock = ({ style }: { style?: CSSProperties }) => (
  <div style={{ position: 'absolute', right: 12, bottom: 10, fontFamily: MONO, fontSize: 12, letterSpacing: '0.1em', color: T.dim, opacity: 0.8, ...style }}>MOCK</div>
);

type Run = [string, string?];
export const Line = ({ runs, size }: { runs: Run[]; size: number }) => (
  <div style={{ fontFamily: MONO, fontSize: size, lineHeight: 1.45, whiteSpace: 'pre' }}>
    {runs.map(([t, c], i) => (
      <span key={i} style={{ color: c ?? T.fg }}>
        {t}
      </span>
    ))}
  </div>
);

// A full-window shell, chromeless: the minimal mode.
export function Shell({ lines, size, children, pad = 64 }: { lines: Run[][]; size: number; children?: ReactNode; pad?: number }) {
  return (
    <div style={{ position: 'absolute', inset: 0, background: T.bg, padding: pad, boxSizing: 'border-box' }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 6, background: SIGNAL.red }} />
      {lines.map((l, i) => (
        <Line key={i} runs={l} size={size} />
      ))}
      {children}
      <Mock />
    </div>
  );
}

export const Caret = ({ size, colour = T.fg }: { size: number; colour?: string }) => (
  <span style={{ display: 'inline-block', width: size * 0.6, height: size * 1.05, background: colour, verticalAlign: '-0.2em' }} />
);

// The prompt line's language server: a completion list under the caret.
export function Completion({ items, size, accent }: { items: [string, string][]; size: number; accent: string }) {
  return (
    <div style={{ display: 'inline-block', background: '#1d1d1d', border: `2px solid ${T.fg}`, boxShadow: `8px 8px 0 #000`, fontFamily: MONO, fontSize: size * 0.8, minWidth: size * 22 }}>
      {items.map(([name, doc], i) => (
        <div key={name} style={{ display: 'flex', justifyContent: 'space-between', gap: size, padding: `${size * 0.25}px ${size * 0.6}px`, background: i === 0 ? accent : 'transparent', color: i === 0 ? T.paper : T.fg }}>
          <span>{name}</span>
          <span style={{ color: i === 0 ? T.paper : T.dim }}>{doc}</span>
        </div>
      ))}
    </div>
  );
}

// An agent's action, as a block in the page's tab: lamp, verb, time.
export function ActionBlock({ who, what, when, lamp, size }: { who: string; what: string; when: string; lamp: string; size: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size * 0.6, background: T.bg, border: `2px solid ${T.fg}`, boxShadow: `6px 6px 0 #000`, padding: `${size * 0.5}px ${size * 0.8}px`, fontFamily: MONO, fontSize: size, color: T.fg, whiteSpace: 'nowrap' }}>
      <span style={{ width: size * 0.6, height: size * 0.6, borderRadius: '50%', background: lamp, flexShrink: 0 }} />
      <span style={{ color: T.dim }}>{who}</span>
      <span>·</span>
      <span>{what}</span>
      <span style={{ color: T.dim }}>· {when}</span>
    </div>
  );
}

// ASK: the band an agent raises before it acts.
export function AskBand({ text, size, accent }: { text: string; size: number; accent: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size, background: T.paper, color: T.ink, borderTop: `4px solid ${accent}`, borderBottom: `2px solid ${T.ink}`, padding: `${size * 0.55}px ${size}px`, fontFamily: MONO, fontSize: size, whiteSpace: 'nowrap' }}>
      <span style={{ flex: 1 }}>{text}</span>
      {['ALLOW', 'DENY', 'ALLOW ON THIS HOST'].map((b, i) => (
        <span key={b} style={{ fontWeight: 600, letterSpacing: '0.06em', padding: `${size * 0.2}px ${size * 0.5}px`, border: `2px solid ${T.ink}`, background: i === 0 ? accent : 'transparent', color: i === 0 ? T.paper : T.ink }}>
          {b}
        </span>
      ))}
    </div>
  );
}

// A look preset card: its ramp, its signal chip, its name in Newsreader.
export function PresetCard({ name, ramp, signal, size, ring }: { name: string; ramp: string[]; signal: string; size: number; ring?: boolean }) {
  return (
    <div style={{ width: size * 5, height: size * 3.4, border: `2px solid ${T.ink}`, boxShadow: `8px 8px 0 ${T.ink}`, background: `linear-gradient(135deg, ${ramp.join(', ')})`, position: 'relative', outline: ring ? `4px solid ${signal}` : 'none', outlineOffset: 6 }}>
      <div style={{ position: 'absolute', left: size * 0.4, top: size * 0.4, width: size * 0.7, height: size * 0.7, background: signal, border: `2px solid ${T.ink}` }} />
      <div style={{ position: 'absolute', left: size * 0.4, bottom: size * 0.35, fontFamily: SERIF, fontStyle: 'italic', fontWeight: 500, fontSize: size * 0.72, color: T.ink, background: T.paper, padding: `0 ${size * 0.25}px` }}>{name}</div>
    </div>
  );
}

// A code card: a file, syntax-coloured the way nus colours it.
export function CodeCard({ title, lines, size }: { title: string; lines: Run[][]; size: number }) {
  return (
    <div style={{ background: T.bg, border: `2px solid ${T.ink}`, boxShadow: `10px 10px 0 ${T.ink}`, position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: size * 0.5, borderBottom: `1.5px solid ${T.rule}`, padding: `${size * 0.4}px ${size * 0.7}px`, fontFamily: MONO, fontSize: size * 0.7, fontWeight: 600, letterSpacing: '0.06em', color: T.fg }}>
        <span style={{ width: size * 0.45, height: size * 0.45, background: SIGNAL.red }} />
        {title}
      </div>
      <div style={{ padding: `${size * 0.7}px ${size * 0.9}px` }}>
        {lines.map((l, i) => (
          <Line key={i} runs={l} size={size} />
        ))}
      </div>
      <Mock />
    </div>
  );
}

// The profile card (spikes/composite/src/me.rs): face, name, the day badge,
// rows that edit in place, MORE and CLOSE. A file in a folder is the account.
export function ProfileCard({ size, accent, name = 'seb', day = 1 }: { size: number; accent: string; name?: string; day?: number }) {
  const rows: [string, string][] = [
    ['NAME', name],
    ['FACE', 'initial'],
    ['DEVICE', 'this mac'],
    ['SYNC', 'off · set up with a key'],
    ['PRIVATE', 'no account · no server · no telemetry'],
  ];
  const btn = (t: string, on: boolean) => (
    <span style={{ fontWeight: 600, letterSpacing: '0.06em', fontSize: size * 0.62, padding: `${size * 0.2}px ${size * 0.5}px`, border: `2px solid ${T.ink}`, background: on ? accent : 'transparent', color: on ? T.paper : T.ink }}>{t}</span>
  );
  return (
    <div style={{ width: size * 21, background: T.paper, color: T.ink, border: `2px solid ${T.ink}`, boxShadow: `10px 10px 0 ${T.ink}`, padding: size, fontFamily: MONO, fontSize: size * 0.72, position: 'relative', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: size * 0.8 }}>
        <div style={{ width: size * 2.6, height: size * 2.6, borderRadius: '50%', background: accent, border: `2px solid ${T.ink}`, color: T.paper, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: SERIF, fontStyle: 'italic', fontSize: size * 1.6 }}>{name[0]}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: size * 1.2, fontWeight: 600 }}>{name}</div>
          <div style={{ color: '#6b665c' }}>you, on this machine</div>
        </div>
        <div style={{ border: `2px solid ${T.ink}`, textAlign: 'center', minWidth: size * 2.4 }}>
          <div style={{ background: accent, color: T.paper, fontSize: size * 0.5, fontWeight: 600, letterSpacing: '0.08em', padding: `${size * 0.08}px 0` }}>DAY</div>
          <div style={{ fontSize: size * 1.1, fontWeight: 600, padding: `${size * 0.05}px 0` }}>{day}</div>
        </div>
      </div>
      <div style={{ marginTop: size * 0.8 }}>
        {rows.map(([k, v]) => (
          <div key={k} style={{ display: 'flex', gap: size * 0.6, borderTop: `1.5px solid ${T.ink}`, padding: `${size * 0.32}px 0` }}>
            <span style={{ width: size * 4.4, fontWeight: 600, fontSize: size * 0.58, letterSpacing: '0.08em', color: '#6b665c', paddingTop: size * 0.08 }}>{k}</span>
            <span>{v}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: size * 0.4, borderTop: `1.5px solid ${T.ink}`, paddingTop: size * 0.6 }}>
        {btn('MORE', true)}
        <span style={{ flex: 1 }} />
        {btn('CLOSE', false)}
      </div>
      <Mock style={{ color: '#6b665c', bottom: -22, right: 0 }} />
    </div>
  );
}

// The welcome page (welcome.rs): a ruled document you can act from: chord,
// title, what it does, and TRY where it makes sense. Profile first.
export function Welcome({ size, accent }: { size: number; accent: string }) {
  const rows: [string, string, string, boolean][] = [
    ['', 'you', 'the profile card: a file, not an account', true],
    ['⌘⇧P', 'palette', 'every command, by name', true],
    ['⌘D', 'split', 'a shell and a page, side by side', true],
    ['⌘⇧O', 'ports', 'every server, its shell, its page', true],
    ['⌘,', 'look studio', 'fonts, ramps, signals, live', true],
    ['⌘⇧H', 'hints', 'label every link and act on it', false],
  ];
  return (
    <div style={{ position: 'absolute', inset: 0, background: T.bg, color: T.fg, fontFamily: MONO, padding: `${size * 1.6}px ${size * 2}px`, boxSizing: 'border-box' }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 6, background: accent }} />
      <div style={{ fontFamily: SERIF, fontStyle: 'italic', fontSize: size * 2.6, lineHeight: 1 }}>welcome</div>
      <div style={{ color: T.dim, fontSize: size * 0.8, marginTop: size * 0.4, marginBottom: size * 1.2 }}>the whole of nus, laid out. every row does the thing.</div>
      <div style={{ fontSize: size * 0.6, fontWeight: 600, letterSpacing: '0.1em', color: T.dim, marginBottom: size * 0.3 }}>FIRST</div>
      {rows.map(([chord, title, what, tr], i) => (
        <div key={title} style={{ display: 'flex', alignItems: 'center', gap: size * 0.8, borderTop: `1.5px solid ${T.rule}`, padding: `${size * 0.5}px 0`, fontSize: size * 0.85 }}>
          <span style={{ width: size * 3.4, color: T.dim, fontSize: size * 0.7 }}>{chord}</span>
          <span style={{ width: size * 7, color: i === 0 ? accent : T.fg, fontWeight: 600 }}>{title}</span>
          <span style={{ flex: 1, color: T.dim }}>{what}</span>
          {tr && <span style={{ fontSize: size * 0.6, fontWeight: 600, letterSpacing: '0.08em', border: `1.5px solid ${T.fg}`, padding: `${size * 0.12}px ${size * 0.4}px` }}>TRY</span>}
        </div>
      ))}
      <Mock />
    </div>
  );
}

// The editor pane (editor.rs): a file in the terminal's monospace, ruled,
// tree-sitter colour, a diagnostic from the language server under the
// offending expression and its hover card.
export function EditorPane({ size, accent }: { size: number; accent: string }) {
  const code: [string, string?][][] = [
    [['use', T.magenta], [' std::path::{Path, PathBuf};', T.fg]],
    [['']],
    [['/// Every file under `root` the rules apply to.', T.dim]],
    [['pub fn ', T.magenta], ['targets', T.blue], ['(root: &Path) -> Vec<PathBuf> {', T.fg]],
    [['    walk(root).filter(|p| ', T.fg], ['matches', T.blue], ['(p)).collect()', T.fg]],
    [['}', T.fg]],
    [['']],
    [['fn ', T.magenta], ['matches', T.blue], ['(p: &Path) -> bool {', T.fg]],
    [['    p.extension() == ', T.fg], ['SQUIGGLE', T.fg]],
    [['}', T.fg]],
  ];
  const line = (runs: [string, string?][], i: number) => (
    <div key={i} style={{ display: 'flex', fontFamily: MONO, fontSize: size, lineHeight: 1.6, whiteSpace: 'pre' }}>
      <span style={{ width: size * 2.4, color: T.rule, textAlign: 'right', paddingRight: size * 1.1, flexShrink: 0 }}>{i + 1}</span>
      {runs.map(([t, c], j) =>
        t === 'SQUIGGLE' ? (
          <span key={j} style={{ color: T.fg, textDecoration: `underline wavy ${T.red}`, textUnderlineOffset: size * 0.28, textDecorationThickness: Math.max(1.5, size * 0.08) }}>
            Some(<span style={{ color: T.green }}>"rs"</span>)
          </span>
        ) : (
          <span key={j} style={{ color: c ?? T.fg }}>{t}</span>
        ),
      )}
    </div>
  );
  return (
    <div style={{ position: 'absolute', inset: 0, background: T.bg, color: T.fg, fontFamily: MONO }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 5, background: accent }} />
      <div style={{ display: 'flex', gap: size * 1.2, alignItems: 'center', borderBottom: `1.5px solid ${T.rule}`, padding: `${size * 0.9}px ${size * 1.2}px ${size * 0.6}px`, fontSize: size * 0.8 }}>
        <span style={{ fontWeight: 600 }}>lint/src/main.rs</span>
        <span style={{ color: T.dim }}>lib.rs</span>
        <span style={{ color: T.dim }}>rules.rs</span>
        <span style={{ flex: 1 }} />
        <span style={{ color: T.dim }}>rust-analyzer ● 1 error</span>
      </div>
      <div style={{ padding: `${size * 0.8}px ${size}px` }}>{code.map(line)}</div>
      <div style={{ position: 'absolute', left: size * 9.5, top: size * 18.4, background: '#1d1d1d', border: `2px solid ${T.fg}`, boxShadow: '8px 8px 0 #000', padding: `${size * 0.6}px ${size * 0.9}px`, fontSize: size * 0.82, lineHeight: 1.5, maxWidth: size * 30 }}>
        <div><span style={{ color: T.red, fontWeight: 600 }}>error[E0308]</span>: mismatched types</div>
        <div style={{ color: T.dim }}>expected <span style={{ color: T.fg }}>Option&lt;&amp;OsStr&gt;</span>, found <span style={{ color: T.fg }}>Option&lt;&amp;str&gt;</span></div>
      </div>
      <Mock />
    </div>
  );
}
