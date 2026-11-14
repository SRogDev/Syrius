import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { CartPoleStep } from '#/lib/cartpole';
import EpisodePlayer from './EpisodePlayer';

const STEPS: CartPoleStep[] = Array.from({ length: 5 }, (_, i) => ({
  step: i + 1,
  observation: [0.1 * i, 0.01 * i, 0.02 * i, 0.001 * i],
  action: i % 2,
  reward: 1,
  terminated: false,
  truncated: i === 4,
  info: {},
}));

describe('EpisodePlayer', () => {
  it('shows the first timestep and its observation on mount', () => {
    render(<EpisodePlayer steps={STEPS} />);
    expect(screen.getByTestId('timestep-label')).toHaveTextContent(
      'Step 1 / 5',
    );
    expect(
      screen.getByText(/Cumulative reward at this step: 1\.0/),
    ).toBeInTheDocument();
  });

  it('steps forward and back one timestep at a time and updates the inspector', () => {
    render(<EpisodePlayer steps={STEPS} />);
    fireEvent.click(screen.getByRole('button', { name: 'Next timestep' }));
    expect(screen.getByTestId('timestep-label')).toHaveTextContent(
      'Step 2 / 5',
    );
    expect(
      screen.getByText(/Cumulative reward at this step: 2\.0/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Previous timestep' }));
    expect(screen.getByTestId('timestep-label')).toHaveTextContent(
      'Step 1 / 5',
    );
  });

  it('seeks to an arbitrary timestep via the slider', () => {
    render(<EpisodePlayer steps={STEPS} />);
    const slider = screen.getByLabelText('Timestep seek');
    fireEvent.change(slider, { target: { value: '4' } });
    expect(screen.getByTestId('timestep-label')).toHaveTextContent(
      'Step 5 / 5',
    );
    expect(screen.getByText(/truncated at step 5/)).toBeInTheDocument();
  });

  it('reports truncation as the episode outcome in analytics', () => {
    render(<EpisodePlayer steps={STEPS} />);
    expect(screen.getByText('truncated (time limit)')).toBeInTheDocument();
  });
});
