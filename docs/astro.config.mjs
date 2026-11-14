// @ts-check

import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';

// Docs for Syrius v0.1 (Phase 0: repository foundation only).
export default defineConfig({
  integrations: [
    starlight({
      title: 'Syrius',
      description:
        'Syrius is an open-source RL Engineering Factory: departments, studios and reproducible reinforcement-learning pipelines.',
      logo: {
        src: './src/assets/syrius-logo.webp',
        alt: 'Syrius logo — the star Sirius',
      },
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/SRogDev/Syrius',
        },
      ],
      sidebar: [
        { label: 'Getting started', link: '/getting-started/' },
        { label: 'Operations', link: '/operations/' },
        {
          label: 'Architecture',
          items: [
            { label: 'Overview', link: '/architecture/' },
            { label: 'Versions', link: '/architecture/versions/' },
          ],
        },
        { label: 'Development', link: '/development/' },
      ],
    }),
  ],
});
