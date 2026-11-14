import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import RewardChart from './RewardChart';

// echarts-for-react needs a real layout engine (clientWidth/height,
// canvas 2d) that jsdom does not provide; the chart option itself is
// unit-tested in lib/charts.test.ts, so the component test stubs the
// React wrapper.
vi.mock('echarts-for-react', () => ({
  default: ({ option }: { option: Record<string, unknown> }) => (
    <div data-testid="echarts-stub">{JSON.stringify((option.series as unknown[])[0])}</div>
  ),
}));

describe('RewardChart', () => {
  it('states honestly that no points exist yet instead of drawing a fake curve', () => {
    render(<RewardChart points={[]} title="Training reward" />);
    expect(screen.getByTestId('reward-chart-empty')).toHaveTextContent('No training points yet');
  });

  it('renders the chart container once points exist', () => {
    render(
      <RewardChart
        points={[
          { step: 0, reward: 21 },
          { step: 20000, reward: 134 },
        ]}
        title="Training reward"
      />,
    );
    expect(screen.getByTestId('reward-chart')).toBeInTheDocument();
  });
});
