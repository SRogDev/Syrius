import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';

// With vitest `globals: false`, Testing Library's auto-cleanup is not
// registered — unmount after every test so renders never leak into the
// next test's queries.
afterEach(() => {
  cleanup();
});
