import { Composition } from 'remotion';
import { Film } from './Film';
import { DURATION, FPS } from './grid';
import './fonts';

// One film, three frames. The master renders at --scale 2 (3840×2160).
export const Root = () => (
  <>
    <Composition id="Object" component={Film} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
    <Composition id="Vertical" component={Film} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
    <Composition id="Feed" component={Film} durationInFrames={DURATION} fps={FPS} width={1080} height={1350} />
  </>
);
