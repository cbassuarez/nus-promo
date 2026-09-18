// The beat grid. Everything in the film is placed in beats, never frames.
import sheet from './score.json';

export const BPM = sheet.bpm; // 152
export const BEATS = sheet.beats; // 76 = 19 bars = 30.000 s
export const FPS = 60;
export const FPB = (FPS * 60) / BPM; // 23.684 frames a beat
export const DURATION = Math.round(BEATS * FPB); // 1800

export const clamp01 = (t: number) => Math.min(1, Math.max(0, t));
// nus has one easing, ease-out cubic; so does the film.
export const easeOut = (t: number) => 1 - Math.pow(1 - clamp01(t), 3);
// Eased 0→1 between two beats.
export const ramp = (beat: number, from: number, to: number) => easeOut((beat - from) / (to - from));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
