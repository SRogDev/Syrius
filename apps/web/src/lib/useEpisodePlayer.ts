import { useCallback, useEffect, useRef, useState } from 'react';
import { type CartPoleStep, clampStep } from '#/lib/cartpole';

/** Episode playback state. The step index is the single source of truth;
 * the canvas draws from it — React state changes only when the step
 * changes, never per animation frame. Honors prefers-reduced-motion by
 * never auto-playing. */

export interface PlayerState {
  index: number;
  playing: boolean;
  speed: number; // steps per second
  step: CartPoleStep | null;
  play: () => void;
  pause: () => void;
  reset: () => void;
  stepForward: () => void;
  stepBack: () => void;
  seek: (index: number) => void;
  setSpeed: (speed: number) => void;
}

export function useEpisodePlayer(steps: CartPoleStep[]): PlayerState {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(30);
  const rafRef = useRef<number>(0);
  const lastRef = useRef<number>(0);
  const accRef = useRef<number>(0);

  // A new episode resets the player. `steps` is a new array identity
  // per fetched trace, so it is the episode identity here.
  // biome-ignore lint/correctness/useExhaustiveDependencies: steps identity = episode identity
  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [steps]);

  useEffect(() => {
    if (!playing) return;
    const tick = (t: number) => {
      if (lastRef.current === 0) lastRef.current = t;
      const dt = t - lastRef.current;
      lastRef.current = t;
      accRef.current += dt;
      const interval = 1000 / speed;
      if (accRef.current >= interval) {
        const advance = Math.floor(accRef.current / interval);
        accRef.current %= interval;
        setIndex((prev) => {
          const next = clampStep(prev + advance, steps.length);
          if (next >= steps.length - 1) setPlaying(false);
          return next;
        });
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafRef.current);
      lastRef.current = 0;
      accRef.current = 0;
    };
  }, [playing, speed, steps.length]);

  const seek = useCallback(
    (i: number) => setIndex(clampStep(i, steps.length)),
    [steps.length],
  );

  return {
    index,
    playing,
    speed,
    step: steps.length > 0 ? steps[clampStep(index, steps.length)] : null,
    play: () => {
      if (steps.length === 0) return;
      if (index >= steps.length - 1) setIndex(0);
      setPlaying(true);
    },
    pause: () => setPlaying(false),
    reset: () => {
      setPlaying(false);
      setIndex(0);
    },
    stepForward: () => {
      setPlaying(false);
      seek(index + 1);
    },
    stepBack: () => {
      setPlaying(false);
      seek(index - 1);
    },
    seek,
    setSpeed,
  };
}
