import { describe, it, expect } from 'vitest';
import manifest from '../manifest.json';

describe('Manifest V3 Architecture & Permission Model (Phase 13.1 Sections 3, 18, 21, 26)', () => {
  it('specifies Manifest Version 3 with valid metadata', () => {
    expect(manifest.manifest_version).toBe(3);
    expect(manifest.name).toBe('Nivesh Firewall');
    expect(manifest.version).toBe('1.0.0');
    expect(manifest.description).toBeDefined();
    expect(manifest.minimum_chrome_version).toBe('100');
  });

  it('implements strict Permission Minimization (Principle of Least Privilege)', () => {
    // Only permitted permissions
    const allowedPermissions = ['activeTab', 'storage', 'scripting'];
    expect(manifest.permissions).toEqual(expect.arrayContaining(allowedPermissions));
    expect(manifest.permissions.length).toBe(allowedPermissions.length);

    // Strictly forbidden broad permissions
    const forbiddenPermissions = [
      '<all_urls>',
      'history',
      'bookmarks',
      'downloads',
      'passwords',
      'clipboardRead',
      'clipboardWrite',
      'webRequest',
      'webRequestBlocking',
      'management',
      'cookies',
      'topSites',
    ];

    for (const forbidden of forbiddenPermissions) {
      expect(manifest.permissions).not.toContain(forbidden);
    }
  });

  it('restricts host permissions exclusively to local backend API without wildcard internet access', () => {
    expect(manifest.host_permissions).toBeDefined();
    expect(manifest.host_permissions).toContain('http://localhost:8000/*');
    expect(manifest.host_permissions).toContain('http://127.0.0.1:8000/*');

    // Forbidden wildcard host access
    expect(manifest.host_permissions).not.toContain('<all_urls>');
    expect(manifest.host_permissions).not.toContain('*://*/*');
    expect(manifest.host_permissions).not.toContain('https://*/*');
  });

  it('declares background service worker as ES module', () => {
    expect(manifest.background).toBeDefined();
    expect(manifest.background.service_worker).toBe('background.js');
    expect(manifest.background.type).toBe('module');
  });

  it('declares popup UI action', () => {
    expect(manifest.action).toBeDefined();
    expect(manifest.action.default_popup).toBe('popup/index.html');
    expect(manifest.action.default_title).toBe('Nivesh Firewall Protection');
  });

  it('declares content script executing at document_idle', () => {
    expect(manifest.content_scripts).toBeDefined();
    expect(manifest.content_scripts.length).toBeGreaterThan(0);
    const contentScript = manifest.content_scripts[0];
    expect(contentScript.js).toContain('content.js');
    expect(contentScript.run_at).toBe('document_idle');
  });
});
