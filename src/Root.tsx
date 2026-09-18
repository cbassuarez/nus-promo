import { Composition } from 'remotion';
import { Film } from './Film';
import { DURATION, FPS } from './grid';
import './fonts';

export const Root = () => (
  <Composition id="Object" component={Film} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
);
