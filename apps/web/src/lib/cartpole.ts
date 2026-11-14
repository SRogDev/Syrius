/** Pure CartPole helpers for the Environment Studio.
 * A trace step's observation is the Gymnasium CartPole-v1 order:
 * [cart position x, cart velocity, pole angle theta, pole velocity].
 * Nothing here touches React or the DOM, so it is unit-testable. */

export interface CartPoleStep {
  step: number;
  observation: number[];
  action: number;
  reward: number;
  terminated: boolean;
  truncated: boolean;
  info: Record<string, string>;
}

/** CartPole-v1 failure limits (Gymnasium): |x| > 2.4 or |theta| > 12 deg. */
export const CARTPOLE_X_LIMIT = 2.4;
export const CARTPOLE_ANGLE_LIMIT_RAD = (12 * Math.PI) / 180;
/** A full-length CartPole episode is 500 steps. */
export const CARTPOLE_SUCCESS_LENGTH = 500;

export function cumulativeRewards(steps: CartPoleStep[]): number[] {
  const out: number[] = [];
  let total = 0;
  for (const s of steps) {
    total += s.reward;
    out.push(total);
  }
  return out;
}

export interface EpisodeStats {
  length: number;
  totalReward: number;
  success: boolean | null;
  maxAbsX: number;
  maxAbsTheta: number;
  terminatedAt: number | null;
  truncatedAt: number | null;
}

export function episodeStats(steps: CartPoleStep[]): EpisodeStats {
  let totalReward = 0;
  let maxAbsX = 0;
  let maxAbsTheta = 0;
  let terminatedAt: number | null = null;
  let truncatedAt: number | null = null;
  for (const s of steps) {
    totalReward += s.reward;
    const obs = s.observation;
    if (obs.length >= 3) {
      maxAbsX = Math.max(maxAbsX, Math.abs(obs[0]));
      maxAbsTheta = Math.max(maxAbsTheta, Math.abs(obs[2]));
    }
    if (s.terminated && terminatedAt === null) terminatedAt = s.step;
    if (s.truncated && truncatedAt === null) truncatedAt = s.step;
  }
  const length = steps.length;
  return {
    length,
    totalReward,
    success:
      length === 0
        ? null
        : length >= CARTPOLE_SUCCESS_LENGTH && truncatedAt !== null,
    maxAbsX,
    maxAbsTheta,
    terminatedAt,
    truncatedAt,
  };
}

/** Clamp a 0-based timestep index into the trace range. */
export function clampStep(index: number, length: number): number {
  if (length <= 0) return 0;
  return Math.min(Math.max(index, 0), length - 1);
}

/** Pole-tip position in canvas coordinates, relative to the cart centre.
 * theta = 0 is straight up; positive theta leans right. y grows down
 * in canvas space, so the tip's y is negative (above the cart). */
export function poleTip(
  cartCentreX: number,
  theta: number,
  poleLength: number,
): { x: number; y: number } {
  return {
    x: cartCentreX + Math.sin(theta) * poleLength,
    y: -Math.cos(theta) * poleLength,
  };
}
