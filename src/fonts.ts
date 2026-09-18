import { continueRender, delayRender, staticFile } from 'remotion';

// The app's own faces, bundled OFL: IBM Plex Mono and Newsreader Italic.
const faces: [string, string, FontFaceDescriptors][] = [
  ['Plex', 'IBMPlexMono-Regular.ttf', { weight: '400' }],
  ['Plex', 'IBMPlexMono-Medium.ttf', { weight: '500' }],
  ['Plex', 'IBMPlexMono-SemiBold.ttf', { weight: '600' }],
  ['Plex', 'IBMPlexMono-Italic.ttf', { weight: '400', style: 'italic' }],
  ['Newsreader', 'Newsreader-Italic.ttf', { style: 'italic', weight: '200 800' }],
  // The wordmark's font cycle only: a pixel face and two chunky displays (OFL).
  ['Silkscreen', 'Silkscreen-Regular.ttf', { weight: '400' }],
  ['Bungee', 'Bungee-Regular.ttf', { weight: '400' }],
  ['RubikMono', 'RubikMonoOne-Regular.ttf', { weight: '400' }],
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
