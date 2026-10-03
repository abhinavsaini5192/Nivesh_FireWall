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

export const config: FrontendConfig = {
  apiBaseUrl: (
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
    'http://localhost:8000'
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
  isProduction: (
    typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.PROD === true
  ),
};
