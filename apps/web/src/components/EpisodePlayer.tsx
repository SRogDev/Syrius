import { Pause, Play, RotateCcw, StepBack, StepForward } from 'lucide-react';
import {
  type CartPoleStep,
  cumulativeRewards,
  episodeStats,
} from '#/lib/cartpole';
import { useEpisodePlayer } from '#/lib/useEpisodePlayer';
import CartPoleCanvas from './CartPoleCanvas';
import { ApiErrorBox, Loading, Panel, SectionTitle, Stat } from './ui';

/** Environment Studio episode player: canvas renderer + simulation
 * controls + timeline + Agent/Environment inspectors + analytics.
 * All values come from the recorded trace; nothing is invented. */

const SPEEDS = [1, 10, 30, 60];

function fmt(n: number, digits = 3): string {
  return Number.isFinite(n) ? n.toFixed(digits) : '—';
}

export default function EpisodePlayer({ steps }: { steps: CartPoleStep[] }) {
  const player = useEpisodePlayer(steps);
  const cum = cumulativeRewards(steps);
  const stats = episodeStats(steps);
  const obs = player.step?.observation ?? [0, 0, 0, 0];

  if (steps.length === 0) {
    return <Loading label="No steps in this trace." />;
  }

  const events: string[] = [];
  if (stats.terminatedAt !== null)
    events.push(`terminated at step ${stats.terminatedAt}`);
  if (stats.truncatedAt !== null)
    events.push(`truncated at step ${stats.truncatedAt}`);
  if (stats.maxAbsTheta > (12 * Math.PI) / 180)
    events.push('pole angle exceeded 12°');
  if (stats.maxAbsX > 2.4) events.push('cart left the track (|x| > 2.4)');

  return (
    <div className="space-y-4">
      <Panel>
        <SectionTitle>Episode playback</SectionTitle>
        <CartPoleCanvas observation={obs} />
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={player.playing ? player.pause : player.play}
            className="flex h-9 cursor-pointer items-center gap-2 border border-highlight bg-highlight px-4 font-mono text-xs uppercase tracking-widest text-bg transition-colors duration-150 hover:bg-platinum"
          >
            {player.playing ? (
              <Pause className="h-4 w-4" aria-hidden />
            ) : (
              <Play className="h-4 w-4" aria-hidden />
            )}
            {player.playing ? 'Pause' : 'Play'}
          </button>
          <button
            type="button"
            onClick={player.reset}
            className="flex h-9 cursor-pointer items-center gap-2 border border-line px-4 font-mono text-xs uppercase tracking-widest text-highlight transition-colors duration-150 hover:border-platinum"
          >
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reset
          </button>
          <button
            type="button"
            onClick={player.stepBack}
            aria-label="Previous timestep"
            className="flex h-9 cursor-pointer items-center gap-1 border border-line px-3 font-mono text-xs text-highlight transition-colors duration-150 hover:border-platinum"
          >
            <StepBack className="h-4 w-4" aria-hidden />1 step
          </button>
          <button
            type="button"
            onClick={player.stepForward}
            aria-label="Next timestep"
            className="flex h-9 cursor-pointer items-center gap-1 border border-line px-3 font-mono text-xs text-highlight transition-colors duration-150 hover:border-platinum"
          >
            1 step
            <StepForward className="h-4 w-4" aria-hidden />
          </button>
          <label className="ml-2 flex items-center gap-2 font-mono text-xs text-platinum">
            Speed
            <select
              value={player.speed}
              onChange={(e) => player.setSpeed(Number(e.target.value))}
              aria-label="Playback speed in steps per second"
              className="h-9 cursor-pointer border border-line bg-surface px-2 text-highlight"
            >
              {SPEEDS.map((s) => (
                <option key={s} value={s}>
                  {s}× steps/s
                </option>
              ))}
            </select>
          </label>
          <span
            className="ml-auto font-mono text-sm text-highlight"
            data-testid="timestep-label"
          >
            Step {player.step?.step ?? 0} / {steps.length}
          </span>
        </div>
        <div className="mt-4">
          <label
            htmlFor="timestep-seek"
            className="mb-1 block font-mono text-[11px] uppercase tracking-widest text-muted"
          >
            Timestep seek
          </label>
          <input
            id="timestep-seek"
            type="range"
            min={0}
            max={steps.length - 1}
            value={player.index}
            onChange={(e) => player.seek(Number(e.target.value))}
            className="w-full cursor-pointer accent-[#E7EBF2]"
          />
        </div>
        {/* Reward timeline: cumulative reward per step, as text (the
            canvas above is the visual; this list is the seekable data). */}
        <p
          className="mt-2 font-mono text-xs text-muted"
          data-testid="cumulative-reward"
        >
          Cumulative reward at this step:{' '}
          {cum.length > 0 ? cum[player.index]?.toFixed(1) : '—'} · total{' '}
          {stats.totalReward.toFixed(1)}
        </p>
        <p
          className="mt-1 font-mono text-xs text-muted"
          data-testid="episode-events"
        >
          Events: {events.length > 0 ? events.join(' · ') : 'none recorded'}
        </p>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel>
          <SectionTitle>Agent inspector — selected timestep</SectionTitle>
          {player.step ? (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm">
              <Stat
                label="Observation [x, ẋ, θ, θ̇]"
                value={`[${obs.map((v) => fmt(v)).join(', ')}]`}
              />
              <Stat
                label="Action"
                value={
                  player.step.action === 0 ? '0 — push left' : '1 — push right'
                }
              />
              <Stat
                label="Reward (this step)"
                value={fmt(player.step.reward, 1)}
              />
              <Stat
                label="Terminated"
                value={player.step.terminated ? 'yes' : 'no'}
              />
              <Stat
                label="Truncated"
                value={player.step.truncated ? 'yes' : 'no'}
              />
              <Stat
                label="Info keys"
                value={Object.keys(player.step.info).join(', ') || 'none'}
              />
            </dl>
          ) : (
            <Loading label="No step selected." />
          )}
        </Panel>
        <Panel>
          <SectionTitle>Environment inspector — state</SectionTitle>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm">
            <Stat label="Cart position x" value={fmt(obs[0] ?? 0)} />
            <Stat label="Cart velocity ẋ" value={fmt(obs[1] ?? 0)} />
            <Stat label="Pole angle θ (rad)" value={fmt(obs[2] ?? 0)} />
            <Stat label="Pole velocity θ̇" value={fmt(obs[3] ?? 0)} />
            <Stat label="|x| limit" value="2.4" tone="muted" />
            <Stat label="|θ| limit" value="12° (0.209 rad)" tone="muted" />
            <Stat
              label="Max |x| in episode"
              value={fmt(stats.maxAbsX)}
              tone={stats.maxAbsX > 2.4 ? 'warn' : 'ok'}
            />
            <Stat
              label="Max |θ| in episode"
              value={`${fmt(stats.maxAbsTheta)} rad`}
              tone={stats.maxAbsTheta > 0.209 ? 'warn' : 'ok'}
            />
          </dl>
          <p className="mt-3 text-sm text-platinum">
            CartPole-v1: Box(4) observation, Discrete(2) action. Scenario and
            constraint config are not exposed by the API — see the environment
            detail for the stored config JSON.
          </p>
        </Panel>
      </div>

      <Panel>
        <SectionTitle>Episode analytics</SectionTitle>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
          <Stat label="Total reward" value={stats.totalReward.toFixed(1)} />
          <Stat label="Length (steps)" value={stats.length} />
          <Stat
            label="Success (500 steps)"
            value={stats.success === null ? '—' : stats.success ? 'yes' : 'no'}
            tone={stats.success ? 'ok' : 'warn'}
          />
          <Stat
            label="Outcome"
            value={
              stats.truncatedAt !== null
                ? 'truncated (time limit)'
                : stats.terminatedAt !== null
                  ? 'terminated (failure)'
                  : 'ongoing'
            }
          />
          <Stat
            label="Violations"
            value={events.length}
            tone={events.length > 0 ? 'warn' : 'ok'}
          />
          <Stat
            label="Final cumulative reward"
            value={cum.length > 0 ? (cum[cum.length - 1] ?? 0).toFixed(1) : '—'}
          />
        </dl>
      </Panel>
    </div>
  );
}

export function EpisodePlayerError({ error }: { error: unknown }) {
  return <ApiErrorBox error={error} />;
}
