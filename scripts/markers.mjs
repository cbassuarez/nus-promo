// A marker per section of the cut, as an EDL Resolve imports onto its
// timeline (Timeline → Import → Timeline Markers from EDL).
//   node scripts/markers.mjs > out/resolve/markers.edl
import { readFileSync } from 'node:fs';

const cut = JSON.parse(readFileSync(new URL('../src/cut.json', import.meta.url)));
const FPS = 60;
const FPB = (FPS * 60) / 152;
const tc = (frame) => {
  const f = frame % FPS;
  const s = Math.floor(frame / FPS);
  return [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60, f].map((n) => String(n).padStart(2, '0')).join(':');
};
const colours = ['Blue', 'Cyan', 'Green', 'Yellow', 'Red', 'Pink', 'Purple', 'Fuchsia', 'Rose', 'Lavender', 'Sky', 'Mint', 'Lemon'];
const out = ['TITLE: nus-promo', 'FCM: NON-DROP FRAME', ''];
cut.sections.forEach((s, i) => {
  const at = Math.round(s.from * FPB);
  const n = String(i + 1).padStart(3, '0');
  out.push(`${n}  001      V     C        ${tc(at)} ${tc(at + 1)} ${tc(at)} ${tc(at + 1)}  `);
  out.push(` |C:ResolveColor${colours[i % colours.length]} |M:${s.label} (beat ${s.from}) |D:1`);
  out.push('');
});
process.stdout.write(out.join('\n'));
