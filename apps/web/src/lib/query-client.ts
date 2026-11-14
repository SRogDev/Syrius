import { QueryClient } from '@tanstack/react-query';

// SPA-only app, so a single module-level client is correct (no per-request
// state to isolate as there would be with SSR).
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10_000,
    },
  },
});
