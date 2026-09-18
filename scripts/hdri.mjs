// Studio HDRIs from Poly Haven (CC0) → assets/hdri/<id>.<exr|hdr>, at 8K,
// whichever of EXR or HDR is smaller. Lighting and reflections only; the
// camera never sees them (white shots sit on #fff, black on #000).
//   cyclorama_hard_light   white shots — a lit infinity cove
//   monochrome_studio_02   black shots — white lamps, a dark ceiling
//   studio_small_09        spare — softbox and umbrella, long highlights
import { createWriteStream, existsSync, mkdirSync } from 'node:fs';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';

export const HDRIS = ['cyclorama_hard_light', 'monochrome_studio_02', 'studio_small_09'];
const dir = new URL('../assets/hdri/', import.meta.url);
mkdirSync(dir, { recursive: true });
for (const id of HDRIS) {
  const files = await (await fetch(`https://api.polyhaven.com/files/${id}`)).json();
  const [ext, file] = Object.entries(files.hdri['8k']).sort((a, b) => a[1].size - b[1].size)[0];
  const out = new URL(`${id}.${ext}`, dir);
  if (existsSync(out)) {
    console.log(`${id}.${ext} · already here`);
    continue;
  }
  const res = await fetch(file.url);
  await pipeline(Readable.fromWeb(res.body), createWriteStream(out));
  console.log(`${id}.${ext} · ${Math.round(file.size / 1e6)} MB`);
}
