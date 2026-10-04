/**
 * Frontend Environment Configuration (Phase 14.1)
 *
 * Centralizes environment variables accessed via Vite's `import.meta.env`.
 * Safe defaults for development and strict environment overrides for production.
 * NO secrets or private tokens are EVER placed in frontend code.
 */

export interface FrontendConfig {
  apiBaseUrl: string;
  appName: string;
  appVersion: string;
  mode: string;
  isProduction: boolean;
}

const isProduction = typeof import.meta !== 'undefined' && Boolean(import.meta.env && import.meta.env.PROD);
const envApiUrl =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '';

export const config: FrontendConfig = {
  apiBaseUrl: (
    envApiUrl ||
    (isProduction ? '' : 'http://localhost:8000')
  ).replace(/\/+$/, ''),
  appName: (
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_APP_NAME) ||
    'Nivesh Firewall'
  ),
  appVersion: (
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_APP_VERSION) ||
    '1.0.0'
  ),
  mode: (
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.MODE) ||
    'development'
  ),
  isProduction,
};
