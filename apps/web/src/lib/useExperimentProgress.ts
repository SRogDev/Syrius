import { useEffect, useRef, useState } from 'react';
import { getExperimentMetrics, type MetricsOut } from '#/lib/api';

/** Live training progress for one experiment.
 * Primary: SSE GET /api/v1/experiments/{id}/events (the backend polls
 * its DB rows for up to ~60 s and closes). Fallback: poll
 * GET /metrics every 2 s. The browser never trains — it only observes.
 * Each event's (step, last_mean_episode_reward) point is appended to
 * the caller-owned series so the chart accumulates what this session
 * actually saw. */

export interface LiveProgress {
  metrics: MetricsOut | null;
  connected: boolean;
  usingFallback: boolean;
}

export function useExperimentProgress(
  experimentId: string,
  onPoint: (step: number, reward: number) => void,
): LiveProgress {
  const [metrics, setMetrics] = useState<MetricsOut | null>(null);
  const [connected, setConnected] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);
  const onPointRef = useRef(onPoint);
  onPointRef.current = onPoint;

  useEffect(() => {
    let stopped = false;
    let es: EventSource | null = null;
    let timer: ReturnType<typeof setInterval> | null = null;

    const apply = (m: MetricsOut) => {
      if (stopped) return;
      setMetrics(m);
      const reward = (m.metrics as Record<string, unknown>)
        ?.last_mean_episode_reward;
      const step = m.current_step ?? 0;
      if (typeof reward === 'number' && Number.isFinite(reward)) {
        onPointRef.current(step, reward);
      }
    };

    const pollOnce = async () => {
      try {
        apply(await getExperimentMetrics(experimentId));
      } catch {
        // Keep the last known state; the UI shows the fetch error via
        // the regular metrics query, not by inventing progress.
      }
    };

    if (typeof EventSource !== 'undefined') {
      es = new EventSource(`/api/v1/experiments/${experimentId}/events`);
      es.onopen = () => {
        if (!stopped) setConnected(true);
      };
      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as MetricsOut;
          if (data.status !== 'no_run') apply(data);
        } catch {
          // Ignore malformed SSE lines.
        }
      };
      es.onerror = () => {
        if (stopped) return;
        es?.close();
        setConnected(false);
        setUsingFallback(true);
        void pollOnce();
        timer = setInterval(() => void pollOnce(), 2000);
      };
    } else {
      setUsingFallback(true);
      void pollOnce();
      timer = setInterval(() => void pollOnce(), 2000);
    }

    return () => {
      stopped = true;
      es?.close();
      if (timer) clearInterval(timer);
    };
  }, [experimentId]);

  return { metrics, connected, usingFallback };
}
