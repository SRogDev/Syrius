import { describe, expect, it } from 'vitest';
import {
  CARTPOLE_ANGLE_LIMIT_RAD,
  CARTPOLE_X_LIMIT,
  clampStep,
  cumulativeRewards,
  episodeStats,
  poleTip,
  type CartPoleStep,
} from './cartpole';

function step(partial: Partial<CartPoleStep>): CartPoleStep {
  return {
    step: 1,
    observation: [0, 0, 0, 0],
    action: 0,
    reward: 1,
    terminated: false,
    truncated: false,
    info: {},
    ...partial,
  };
}

describe('cumulativeRewards', () => {
  it('accumulates per-step rewards', () => {
    const steps = [step({ reward: 1 }), step({ reward: 1 }), step({ reward: 0.5 })];
    expect(cumulativeRewards(steps)).toEqual([1, 2, 2.5]);
  });

  it('returns an empty series for an empty trace', () => {
    expect(cumulativeRewards([])).toEqual([]);
  });
});

describe('episodeStats', () => {
  it('totals reward and length and marks a 500-step CartPole run a success', () => {
    const steps = Array.from({ length: 500 }, (_, i) =>
      step({ step: i + 1, truncated: i === 499 }),
    );
    const stats = episodeStats(steps);
    expect(stats.length).toBe(500);
    expect(stats.totalReward).toBe(500);
    expect(stats.success).toBe(true);
    expect(stats.terminatedAt).toBeNull();
    expect(stats.truncatedAt).toBe(500);
  });

  it('reports a failure when the pole angle exceeds the CartPole limit', () => {
    const steps = [
      step({}),
      step({ step: 2, observation: [0, 0, CARTPOLE_ANGLE_LIMIT_RAD + 0.01, 0], terminated: true }),
    ];
    const stats = episodeStats(steps);
    expect(stats.maxAbsTheta).toBeGreaterThan(CARTPOLE_ANGLE_LIMIT_RAD);
    expect(stats.maxAbsX).toBeLessThanOrEqual(CARTPOLE_X_LIMIT);
    expect(stats.terminatedAt).toBe(2);
  });
});

describe('clampStep', () => {
  it('clamps a timestep into the trace range', () => {
    expect(clampStep(0, 10)).toBe(0);
    expect(clampStep(99, 10)).toBe(9);
    expect(clampStep(4, 10)).toBe(4);
    expect(clampStep(3, 0)).toBe(0);
  });
});

describe('poleTip', () => {
  it('places the pole tip straight up when theta is zero', () => {
    const tip = poleTip(100, 0, 80);
    expect(tip.x).toBeCloseTo(100);
    expect(tip.y).toBeCloseTo(-80);
  });

  it('leans the pole tip in the direction of theta', () => {
    const tip = poleTip(100, 0.2, 80);
    expect(tip.x).toBeGreaterThan(100);
  });
});
