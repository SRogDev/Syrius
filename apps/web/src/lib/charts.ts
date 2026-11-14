/** ECharts option builders for the Experiment Studio.
 * The series are plain {step, reward} points accumulated from the live
 * SSE/metrics stream — the backend has no history endpoint, so the chart
 * shows what this session observed plus the latest metrics point. */

export interface RewardPoint {
  step: number;
  reward: number;
}

const HUD = {
  text: '#BFC5CE',
  muted: '#7D8593',
  line: '#2E333E',
  highlight: '#E7EBF2',
};

export function buildRewardOption(
  points: RewardPoint[],
  title: string,
): Record<string, unknown> {
  return {
    animation: false,
    title: {
      text: title,
      left: 'left',
      textStyle: { color: HUD.text, fontSize: 12 },
    },
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => v.toFixed(2) },
    grid: { left: 48, right: 16, top: 32, bottom: 28 },
    xAxis: {
      type: 'value',
      name: 'step',
      nameLocation: 'middle',
      nameGap: 24,
      axisLine: { lineStyle: { color: HUD.line } },
      axisLabel: { color: HUD.muted },
    },
    yAxis: {
      type: 'value',
      name: 'mean reward',
      axisLine: { lineStyle: { color: HUD.line } },
      axisLabel: { color: HUD.muted },
      splitLine: { lineStyle: { color: HUD.line } },
    },
    series: [
      {
        name: 'mean episode reward',
        type: 'line',
        showSymbol: false,
        lineStyle: { color: HUD.highlight, width: 2 },
        data: points.map((p) => [p.step, p.reward] as [number, number]),
      },
    ],
  };
}
