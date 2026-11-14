import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, createProject, fetchHealth, getEpisodeTrace, listProjects } from './api';

const PROJECTS = [
  { id: 'p1', name: 'CartPole', description: 'Balance the pole', status: 'active', workspace_id: null },
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
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(jsonResponse(PROJECTS));
    await expect(listProjects()).resolves.toEqual(PROJECTS);
    expect(fetch).toHaveBeenCalledWith('/api/v1/projects', expect.anything());
  });

  it('creates a project with POST /api/v1/projects and the given body', async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      jsonResponse({ ...PROJECTS[0] }, 201),
    );
    await expect(createProject({ name: 'CartPole', description: 'Balance the pole' })).resolves.toEqual(
      PROJECTS[0],
    );
    const [, init] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
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
    (fetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new TypeError('fetch failed'));
    await expect(fetchHealth()).rejects.toThrowError('API unreachable');
  });

  it('fetches an episode trace by id', async () => {
    const trace = { episode_id: 'e1', gym_id: 'CartPole-v1', seed: 0, steps: [] };
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(jsonResponse(trace));
    await expect(getEpisodeTrace('e1')).resolves.toEqual(trace);
    expect(fetch).toHaveBeenCalledWith('/api/v1/episodes/e1/trace', expect.anything());
  });
});
