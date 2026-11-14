import { QueryClientProvider } from '@tanstack/react-query';
import { createRootRoute, HeadContent, Scripts } from '@tanstack/react-router';
import Header from '../components/Header';
import { queryClient } from '../lib/query-client';

import appCss from '../styles.css?url';

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'Syrius — RL Engineering Factory' },
      {
        name: 'description',
        content:
          'Syrius is an open-source RL Engineering Factory: departments, studios and reproducible reinforcement-learning pipelines.',
      },
    ],
    links: [{ rel: 'stylesheet', href: appCss }],
  }),
  // shellComponent renders the full HTML document (Start v1 root-route
  // convention, as in the official @tanstack/cli scaffold).
  shellComponent: RootDocument,
});

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-screen bg-bg font-sans text-highlight antialiased">
        <Header />
        <main className="mx-auto max-w-6xl px-4 pb-16 pt-8">
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        </main>
        <footer className="border-t border-line py-6">
          <p className="mx-auto max-w-6xl px-4 font-mono text-xs tracking-wider text-muted">
            SYRIUS v0.1 — PHASE 5 · FOUR STUDIOS · BACKEND VERTICAL SLICE
            MEASURED 2026-11-14
          </p>
        </footer>
        <Scripts />
      </body>
    </html>
  );
}
