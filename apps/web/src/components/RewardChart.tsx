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
      <p className="font-mono text-sm text-muted" data-testid="reward-chart-empty">
        No training points yet — start training (or wait for a run) and the
        live curve appears here. The backend has no training-history
        endpoint, so past runs show only their latest metrics point.
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
