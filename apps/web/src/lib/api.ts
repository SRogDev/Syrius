/** Minimal API client for Phase 0: only the health endpoint exists. */

export interface HealthResponse {
  service: string;
  version: string;
  environment: string;
  status: 'ok' | 'degraded';
  db: 'ok' | 'unavailable';
}

function apiBase(): string {
  // In dev, Vite proxies /api to the FastAPI server on :8000. In a built
  // deployment, point VITE_API_URL at the API origin.
  return import.meta.env.VITE_API_URL ?? '';
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBase()}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`API health check failed: ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}
