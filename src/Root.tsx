import { Composition } from 'remotion';
import { Cut } from './Cut';
import { Film } from './Film';
import { Styleframe } from './Styleframes';
import { DURATION, FPS } from './grid';
import './fonts';

// One film, three frames. The master renders at --scale 2 (3840×2160).
export const Root = () => (
  <>
    <Composition id="Object" component={Film} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
    <Composition id="Vertical" component={Film} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
    <Composition id="Feed" component={Film} durationInFrames={DURATION} fps={FPS} width={1080} height={1350} />
    {/* The next cut, rough pass (PLAN.md §1) — the one Astra finishes. */}
    <Composition id="Cut" component={Cut} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
    <Composition id="CutVertical" component={Cut} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
    <Composition id="CutFeed" component={Cut} durationInFrames={DURATION} fps={FPS} width={1080} height={1350} />
    {/* Styleframes: stills of the new cut's sections — see PLAN.md. */}
    <Composition id="Styleframe" component={Styleframe} durationInFrames={1} fps={FPS} width={1920} height={1080} defaultProps={{ id: 'agents' }} />
    <Composition id="StyleframeVertical" component={Styleframe} durationInFrames={1} fps={FPS} width={1080} height={1920} defaultProps={{ id: 'agents' }} />
    <Composition id="StyleframeFeed" component={Styleframe} durationInFrames={1} fps={FPS} width={1080} height={1350} defaultProps={{ id: 'agents' }} />
  </>
);
