import type { ReactNode } from 'react';
import { cn } from '#/lib/utils';

/** Small shared HUD primitives for the Studios. Flat surfaces, hairline
 * borders, square corners — the Syrius design system (no neon). */

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cn('hud-panel p-5', className)}>{children}</section>;
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 font-mono text-xs uppercase tracking-[0.25em] text-platinum">
      {children}
    </h2>
  );
}

export function Stat({ label, value, tone }: { label: string; value: ReactNode; tone?: 'ok' | 'warn' | 'muted' }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-widest text-muted">{label}</dt>
      <dd
        className={cn(
          'font-mono text-sm',
          tone === 'warn' ? 'text-amber-300' : tone === 'muted' ? 'text-muted' : 'text-highlight',
        )}
      >
        {value}
      </dd>
    </div>
  );
}

export function Loading({ label }: { label: string }) {
  return <p className="font-mono text-sm text-muted">{label}</p>;
}

/** Honest error state: shows the real API error, never a fake empty state. */
export function ApiErrorBox({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : 'Unknown error';
  return (
    <div role="alert" className="hud-panel border-amber-300/50 p-5">
      <p className="font-mono text-sm text-highlight">Could not load live data from the API.</p>
      <p className="mt-1 font-mono text-xs text-muted">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 cursor-pointer font-mono text-xs uppercase tracking-widest text-highlight underline-offset-4 transition-colors duration-150 hover:underline"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

/** Used where the backend honestly lacks a feature: states it and links
 * to the status doc. Never fakes the number or the feature. */
export function NotImplemented({ what, reason }: { what: string; reason: string }) {
  return (
    <div className="hud-panel p-4">
      <p className="font-mono text-sm text-highlight">{what}: not yet implemented</p>
      <p className="mt-1 text-sm text-platinum">{reason}</p>
      <p className="mt-2 font-mono text-xs text-muted">
        See IMPLEMENTATION_STATUS.md — Phase 5 table for the exact backend gap.
      </p>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const warn = ['failed', 'cancelled', 'invalid', 'degraded'].includes(status);
  const ok = ['ok', 'completed', 'validated', 'reviewed', 'active'].includes(status);
  return (
    <span
      className={cn(
        'inline-block border px-2 py-0.5 font-mono text-[11px] uppercase tracking-widest',
        warn
          ? 'border-amber-300/60 text-amber-300'
          : ok
            ? 'border-highlight/60 text-highlight'
            : 'border-line text-platinum',
      )}
    >
      {status}
    </span>
  );
}
