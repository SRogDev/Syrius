import { describe, expect, it } from 'vitest';
import { buildRewardOption, type RewardPoint } from './charts';

const POINTS: RewardPoint[] = [
  { step: 0, reward: 21.1 },
  { step: 10240, reward: 80.4 },
  { step: 20000, reward: 134.4 },
];

describe('buildRewardOption', () => {
  it('builds a line series from training points', () => {
    const option = buildRewardOption(POINTS, 'Training reward');
    const series = option.series as unknown as Array<{
      type: string;
      data: Array<[number, number]>;
    }>;
    expect(series).toHaveLength(1);
    expect(series[0].type).toBe('line');
    expect(series[0].data).toEqual([
      [0, 21.1],
      [10240, 80.4],
      [20000, 134.4],
    ]);
  });

  it('marks the x axis as a value axis so sparse live points still plot', () => {
    const option = buildRewardOption(POINTS, 'Training reward');
    const xAxis = option.xAxis as unknown as { type: string };
    expect(xAxis.type).toBe('value');
  });

  it('is empty-series-safe so the chart can render before any point arrives', () => {
    const option = buildRewardOption([], 'Training reward');
    const series = option.series as unknown as Array<{ data: unknown[] }>;
    expect(series[0].data).toEqual([]);
  });
});
