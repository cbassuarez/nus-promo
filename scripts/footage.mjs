// What the reshoot has delivered, for the film to pick up:
//   public/footage/<name>.mp4         → src/footage.json   (clips beat stills)
//   public/footage/<name>.marks.json  → src/marks.json     (element positions)
// Stills in public/shots/ stand in for anything missing.
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
const dir = new URL('../public/footage/', import.meta.url);
const files = existsSync(dir) ? readdirSync(dir) : [];
const clips = files.filter((f) => f.endsWith('.mp4')).map((f) => f.slice(0, -4));
const marks = Object.fromEntries(files.filter((f) => f.endsWith('.marks.json')).map((f) => [f.slice(0, -'.marks.json'.length), JSON.parse(readFileSync(new URL(f, dir)))]));
writeFileSync(new URL('../src/footage.json', import.meta.url), JSON.stringify(Object.fromEntries(clips.map((n) => [n, true])), null, 1) + '\n');
writeFileSync(new URL('../src/marks.json', import.meta.url), JSON.stringify(marks, null, 1) + '\n');
console.log(`footage: ${clips.length ? clips.join(', ') : 'none yet — stills stand in'} · marks: ${Object.keys(marks).join(', ') || 'defaults'}`);
