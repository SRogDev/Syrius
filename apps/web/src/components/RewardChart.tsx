import ReactECharts from 'echarts-for-react';
import { buildRewardOption, type RewardPoint } from '#/lib/charts';

/** Training-progress line chart (ECharts). Shows only points the session
 * actually observed via SSE/metrics — never invented history. */

export default function RewardChart({
  points,
  title,
}: {
  points: RewardPoint[];
  title: string;
}) {
  if (points.length === 0) {
    return (
      <p
        className="font-mono text-sm text-muted"
        data-testid="reward-chart-empty"
      >
        No training points yet — start training (or wait for a run) and the
        curve appears here, from the persisted training history.
      </p>
    );
  }
  return (
    <div data-testid="reward-chart">
      <ReactECharts
        option={buildRewardOption(points, title)}
        style={{ height: 280, width: '100%' }}
        notMerge
        lazyUpdate
      />
    </div>
  );
}
