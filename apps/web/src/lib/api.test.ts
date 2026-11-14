import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  ApiError,
  createProject,
  downloadArtifact,
  fetchHealth,
  getEpisodeTrace,
  getTrainingHistory,
  listEpisodes,
  listEvaluations,
  listExperiments,
  listProjects,
} from './api';

const PROJECTS = [
  {
    id: 'p1',
    name: 'CartPole',
    description: 'Balance the pole',
    status: 'active',
    workspace_id: null,
  },
];

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('api client', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('lists projects from GET /api/v1/projects', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse(PROJECTS),
    );
    await expect(listProjects()).resolves.toEqual(PROJECTS);
    expect(fetch).toHaveBeenCalledWith('/api/v1/projects', expect.anything());
  });

  it('creates a project with POST /api/v1/projects and the given body', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse({ ...PROJECTS[0] }, 201),
    );
    await expect(
      createProject({ name: 'CartPole', description: 'Balance the pole' }),
    ).resolves.toEqual(PROJECTS[0]);
    const [, init] = (fetch as unknown as ReturnType<typeof vi.fn>).mock
      .calls[0];
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body as string)).toEqual({
      name: 'CartPole',
      description: 'Balance the pole',
    });
  });

  it('throws ApiError with the server detail on a 404', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockImplementation(() =>
      Promise.resolve(jsonResponse({ detail: 'project not found' }, 404)),
    );
    await expect(listProjects()).rejects.toThrowError(ApiError);
    await expect(listProjects()).rejects.toThrowError('project not found');
  });

  it('throws a plain Error when the API is unreachable', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new TypeError('fetch failed'),
    );
    await expect(fetchHealth()).rejects.toThrowError('API unreachable');
  });

  it('fetches an episode trace by id', async () => {
    const trace = {
      episode_id: 'e1',
      gym_id: 'CartPole-v1',
      seed: 0,
      steps: [],
    };
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse(trace),
    );
    await expect(getEpisodeTrace('e1')).resolves.toEqual(trace);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/episodes/e1/trace',
      expect.anything(),
    );
  });

  it('lists experiments, filtered by project when given', async () => {
    const experiments = [{ id: 'x1', name: 'ppo-1' }];
    (fetch as unknown as ReturnType<typeof vi.fn>).mockImplementation(() =>
      Promise.resolve(jsonResponse(experiments)),
    );
    await expect(listExperiments('p1')).resolves.toEqual(experiments);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/experiments?project_id=p1',
      expect.anything(),
    );
    await expect(listExperiments()).resolves.toEqual(experiments);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/experiments',
      expect.anything(),
    );
  });

  it('lists evaluations filtered by experiment', async () => {
    const runs = [{ id: 'ev1', status: 'completed' }];
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse(runs),
    );
    await expect(listEvaluations('x1')).resolves.toEqual(runs);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/evaluations?experiment_id=x1',
      expect.anything(),
    );
  });

  it('lists episodes filtered by environment', async () => {
    const episodes = [{ id: 'ep1', length: 22 }];
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse(episodes),
    );
    await expect(listEpisodes('env1')).resolves.toEqual(episodes);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/episodes?environment_id=env1',
      expect.anything(),
    );
  });

  it('fetches training history points', async () => {
    const history = {
      experiment_id: 'x1',
      training_run_id: 'r1',
      status: 'completed',
      points: [{ timestep: 512, mean_episode_reward: 21.5 }],
    };
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse(history),
    );
    await expect(getTrainingHistory('x1')).resolves.toEqual(history);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/experiments/x1/history',
      expect.anything(),
    );
  });

  it('downloads artifact bytes as a Blob', async () => {
    const blob = new Blob(['fake-zip'], { type: 'application/octet-stream' });
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(blob, { status: 200 }),
    );
    const result = await downloadArtifact('a1');
    expect(result).toBeInstanceOf(Blob);
    expect(fetch).toHaveBeenCalledWith('/api/v1/artifacts/a1/download');
  });
});
