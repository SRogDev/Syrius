import tailwindcss from '@tailwindcss/vite';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import viteReact from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// TanStack Start in SPA mode (verified against the official @tanstack/cli
// scaffold for @tanstack/react-start 1.169.5 and the Start docs):
// - `tanstackStart()` from '@tanstack/react-start/plugin/vite'
// - `spa.enabled: true` disables SSR for the whole app; the prerendered
//   shell is written to /index.html with no link crawling.
// - Plugin order: tailwindcss, tanStackStart, viteReact.
const config = defineConfig({
  resolve: { tsconfigPaths: true },
  plugins: [
    tailwindcss(),
    tanstackStart({
      spa: {
        enabled: true,
        prerender: {
          outputPath: '/index.html',
          crawlLinks: false,
        },
      },
    }),
    viteReact(),
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});

export default config;
