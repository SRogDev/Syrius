import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '@/lib/api';

/**
 * Live API health panel. Shows real state from `GET /api/v1/health`:
 * loading, unreachable, or the service/database status. No mock data.
 */
export default function ApiHealth() {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['api-health'],
    queryFn: fetchHealth,
  });

  return (
    <section
      aria-label="API health"
      className="hud-panel rounded-none p-5"
      data-testid="api-health"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-mono text-xs uppercase tracking-[0.25em] text-platinum">
          API · Health
        </h2>
        <button
          type="button"
          onClick={() => void refetch()}
          className="cursor-pointer font-mono text-xs uppercase tracking-widest text-highlight underline-offset-4 hover:underline"
        >
          Recheck
        </button>
      </div>

      {isPending ? (
        <p className="font-mono text-sm text-muted">Probing API…</p>
      ) : isError ? (
        <div>
          <p className="font-mono text-sm text-highlight">
            API unreachable — is the API running on :8000?
          </p>
          <p className="mt-1 font-mono text-xs text-muted">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      ) : data ? (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm sm:grid-cols-4">
          <div>
            <dt className="text-[11px] uppercase tracking-widest text-muted">
              Service
            </dt>
            <dd className="text-highlight">{data.service}</dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-widest text-muted">
              Version
            </dt>
            <dd className="text-highlight">{data.version}</dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-widest text-muted">
              Status
            </dt>
            <dd
              className={
                data.status === 'ok' ? 'text-highlight' : 'text-amber-300'
              }
            >
              {data.status}
            </dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-widest text-muted">
              Database
            </dt>
            <dd
              className={data.db === 'ok' ? 'text-highlight' : 'text-amber-300'}
            >
              {data.db}
            </dd>
          </div>
        </dl>
      ) : null}
    </section>
  );
}
