/**
 * Extension Configuration (Phase 13.1 Section 13 & 14)
 *
 * Centralized configuration avoiding hardcoded URLs throughout the codebase.
 * Security: NO private keys, tokens, or backend secrets are ever placed in extension bundles.
 */

import type { ExtensionPersistentConfig } from '../types/state';

const envBackendUrl = typeof import.meta !== 'undefined' && import.meta.env
  ? (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL)
  : undefined;

const envWebAppUrl = typeof import.meta !== 'undefined' && import.meta.env
  ? import.meta.env.VITE_WEB_APP_URL
  : undefined;

export const DEFAULT_CONFIG: ExtensionPersistentConfig = {
  backendApiUrl: (envBackendUrl || 'http://localhost:8000').replace(/\/+$/, ''),
  webAppBaseUrl: (envWebAppUrl || 'http://localhost:5173').replace(/\/+$/, ''),
  autoConnectHealthCheck: true,
  theme: 'dark',
};

export const EXTENSION_METADATA = {
  name: 'Nivesh Firewall',
  version: '1.0.0',
  engineVersion: '8.0.0',
  defaultTimeoutMs: 8000,
} as const;

/**
 * Loads persistent extension configuration from chrome.storage.local
 * Falling back safely to defaults.
 */
export async function getExtensionConfig(): Promise<ExtensionPersistentConfig> {
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
    try {
      const stored = await chrome.storage.local.get(['config']);
      if (stored && stored.config) {
        return { ...DEFAULT_CONFIG, ...stored.config };
      }
    } catch {
      // Fallback silently if storage unavailable
    }
  }
  return { ...DEFAULT_CONFIG };
}

/**
 * Constructs a safe deep-link URL into the Nivesh Web Application (Phase 13.1 Section 14 & 15).
 * Only passes the analysis identifier (analysis_id). NEVER includes raw financial message text,
 * passwords, OTPs, or banking details in the URL.
 */
export function buildNiveshWebAppUrl(webAppBaseUrl: string, analysisId?: string): string {
  const base = webAppBaseUrl.replace(/\/+$/, '');
  if (analysisId && analysisId.trim()) {
    const cleanId = encodeURIComponent(analysisId.trim());
    return `${base}/#protect?id=${cleanId}`;
  }
  return `${base}/#protect`;
}
