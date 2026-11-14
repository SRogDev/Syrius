import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getRouter } from '#/router';
import { Route as ProjectsRoute } from './projects';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function renderWithQuery(ui: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

describe('project creation', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('creates a project from the form and posts to the real API path', async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse([]));
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          id: 'p9',
          name: 'CartPole',
          description: 'Balance',
          status: 'active',
          workspace_id: null,
        },
        201,
      ),
    );
    fetchMock.mockResolvedValue(jsonResponse([]));

    const Component = ProjectsRoute.options.component as React.ComponentType;
    renderWithQuery(<Component />);

    await waitFor(() =>
      expect(screen.getByText(/No projects exist yet/)).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByLabelText('Project name'), {
      target: { value: 'CartPole' },
    });
    fireEvent.change(screen.getByLabelText('Project objective'), {
      target: { value: 'Balance' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }));

    await waitFor(() => {
      const calls = fetchMock.mock.calls as Array<
        [string, RequestInit | undefined]
      >;
      const post = calls.find(
        ([url, init]) => url === '/api/v1/projects' && init?.method === 'POST',
      );
      expect(post).toBeDefined();
      expect(JSON.parse(post?.[1]?.body as string)).toEqual({
        name: 'CartPole',
        description: 'Balance',
      });
    });
  });

  it('requires a name before posting', async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(jsonResponse([]));

    const Component = ProjectsRoute.options.component as React.ComponentType;
    renderWithQuery(<Component />);
    await waitFor(() =>
      expect(screen.getByText(/No projects exist yet/)).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'A project needs a name.',
    );
    expect(fetchMock).toHaveBeenCalledTimes(1); // only the initial list fetch
  });
});

describe('router navigation', () => {
  it('resolves the Four Studios routes in the route tree', async () => {
    const router = getRouter();
    await router.load();
    const paths = Object.keys(router.routesByPath);
    expect(paths).toContain('/projects/$projectId');
    expect(paths).toContain('/experiments/$experimentId');
    expect(paths).toContain('/episodes/$episodeId');
    expect(paths).toContain('/evaluations/$evaluationId');
  });

  it('navigates to /projects and renders the projects heading', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse([])));
    const router = getRouter();
    const history = createMemoryHistory({ initialEntries: ['/projects'] });
    router.history = history;
    await router.load();
    render(<RouterProvider router={router} />);
    await waitFor(() =>
      expect(
        screen.getByRole('heading', { name: 'PROJECTS' }),
      ).toBeInTheDocument(),
    );
    vi.unstubAllGlobals();
  });
});
