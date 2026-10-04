import '@testing-library/jest-dom';
import { beforeEach } from 'vitest';

beforeEach(() => {
  if (typeof window !== 'undefined') {
    // Default to /firewall for legacy integration suites expecting the console shell
    window.history.replaceState(null, '', '/firewall');
  }
});
