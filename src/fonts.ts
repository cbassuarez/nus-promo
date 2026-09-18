import { continueRender, delayRender, staticFile } from 'remotion';

// The app's own faces, bundled OFL: IBM Plex Mono and Newsreader Italic.
const faces: [string, string, FontFaceDescriptors][] = [
  ['Plex', 'IBMPlexMono-Regular.ttf', { weight: '400' }],
  ['Plex', 'IBMPlexMono-SemiBold.ttf', { weight: '600' }],
  ['Newsreader', 'Newsreader-Italic.ttf', { style: 'italic', weight: '200 800' }],
];

const handle = delayRender('Loading fonts');
Promise.all(
  faces.map(async ([family, file, desc]) => {
    const face = new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, desc);
    await face.load();
    document.fonts.add(face);
  }),
).then(() => continueRender(handle));

export const MONO = "'Plex', 'IBM Plex Mono', monospace";
export const SERIF = "'Newsreader', Georgia, serif";
