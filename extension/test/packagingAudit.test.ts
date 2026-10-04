/**
 * Phase 17.3: Extension Packaging, Manifest V3 & Permission Audit Tests
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import manifest from '../manifest.json';
import { auditDist } from '../scripts/audit-dist.js';
import { inspectZipBuffer } from '../scripts/zip-util.js';

describe('Phase 17.3: Extension Packaging & Permission Audit Suite', () => {
  const extensionDir = path.resolve(import.meta.dirname, '..');
  const distDir = path.join(extensionDir, 'dist');
  const zipPath = path.join(extensionDir, 'nivesh-firewall-v1.0.0.zip');

  // ===========================================================================
  // 1. Manifest V3 Production Compliance
  // ===========================================================================
  describe('1. Manifest V3 Production Compliance', () => {
    it('declares exact manifest_version 3 with valid metadata', () => {
      expect(manifest.manifest_version).toBe(3);
      expect(manifest.name).toBe('Nivesh Firewall');
      expect(manifest.version).toBe('1.0.0');
      expect(manifest.minimum_chrome_version).toBe('100');
    });

    it('has concise, factual description under Chrome Web Store 132 char limit', () => {
      expect(manifest.description).toBeDefined();
      expect(manifest.description.length).toBeLessThanOrEqual(132);
      expect(manifest.description.length).toBeGreaterThan(20);

      // Must not make broker/advisor or guaranteed fraud detection claims
      expect(manifest.description.toLowerCase()).not.toContain('broker');
      expect(manifest.description.toLowerCase()).not.toContain('investment advisor');
      expect(manifest.description.toLowerCase()).not.toContain('guaranteed');
    });

    it('declares icons in both manifest root and default_action', () => {
      expect(manifest.icons).toBeDefined();
      expect(manifest.icons['16']).toBe('icons/icon16.png');
      expect(manifest.icons['48']).toBe('icons/icon48.png');
      expect(manifest.icons['128']).toBe('icons/icon128.png');

      expect(manifest.action.default_icon).toBeDefined();
      expect(manifest.action.default_icon['16']).toBe('icons/icon16.png');
      expect(manifest.action.default_icon['48']).toBe('icons/icon48.png');
      expect(manifest.action.default_icon['128']).toBe('icons/icon128.png');
    });
  });

  // ===========================================================================
  // 2. Permission Minimization Audit
  // ===========================================================================
  describe('2. Permission Minimization Audit', () => {
    it('contains strictly minimal required permissions: activeTab, storage, scripting', () => {
      expect(manifest.permissions).toEqual(['activeTab', 'storage', 'scripting']);
    });

    it('forbids all broad, invasive, and background monitoring permissions', () => {
      const forbidden = [
        '<all_urls>',
        'tabs',
        'history',
        'passwords',
        'clipboardRead',
        'clipboardWrite',
        'webRequest',
        'webRequestBlocking',
        'cookies',
        'downloads',
        'notifications',
        'geolocation',
        'management',
        'topSites',
      ];

      for (const perm of forbidden) {
        expect(manifest.permissions).not.toContain(perm);
      }
    });

    it('strictly forbids wildcard external access in host_permissions', () => {
      expect(manifest.host_permissions).not.toContain('<all_urls>');
      expect(manifest.host_permissions).not.toContain('*://*/*');
      expect(manifest.host_permissions).not.toContain('https://*/*');
    });
  });

  // ===========================================================================
  // 3. Physical Icon Files Audit
  // ===========================================================================
  describe('3. Physical Icon Files Audit', () => {
    for (const size of [16, 48, 128]) {
      it(`verifies icon${size}.png exists as valid PNG with exact dimensions`, () => {
        const iconPath = path.join(extensionDir, `icons/icon${size}.png`);
        expect(fs.existsSync(iconPath)).toBe(true);

        const buf = fs.readFileSync(iconPath);
        // PNG magic signature: 89 50 4E 47 0D 0A 1A 0A
        expect(buf.subarray(0, 8).toString('hex')).toBe('89504e470d0a1a0a');

        const width = buf.readUInt32BE(16);
        const height = buf.readUInt32BE(20);
        expect(width).toBe(size);
        expect(height).toBe(size);
      });
    }
  });

  // ===========================================================================
  // 4. Production Build Artifact & Security Audit
  // ===========================================================================
  describe('4. Production Build Artifact & Security Audit', () => {
    it('successfully audits production dist/ artifact using auditDist', () => {
      if (fs.existsSync(distDir)) {
        const result = auditDist(distDir);
        expect(result.success).toBe(true);
        expect(result.fileCount).toBeGreaterThanOrEqual(10);
      }
    });
  });

  // ===========================================================================
  // 5. ZIP Package Verification
  // ===========================================================================
  describe('5. ZIP Package Verification', () => {
    it('verifies generated nivesh-firewall-v1.0.0.zip archive integrity', () => {
      if (fs.existsSync(zipPath)) {
        const zipBuf = fs.readFileSync(zipPath);
        expect(zipBuf.length).toBeGreaterThan(1000);

        const entries = inspectZipBuffer(zipBuf);
        expect(entries.length).toBeGreaterThanOrEqual(10);

        const names = entries.map((e: { name: string }) => e.name);
        expect(names).toContain('manifest.json');
        expect(names).toContain('background.js');
        expect(names).toContain('content.js');
        expect(names).toContain('popup/index.html');
        expect(names).toContain('popup/popup.js');
        expect(names).toContain('popup/popup.css');
        expect(names).toContain('icons/icon16.png');
        expect(names).toContain('icons/icon48.png');
        expect(names).toContain('icons/icon128.png');

        // Check that no forbidden files exist inside the ZIP
        for (const name of names) {
          expect(name).not.toMatch(/\.ts$/i);
          expect(name).not.toMatch(/\.test\./i);
          expect(name).not.toMatch(/\.env/i);
          expect(name).not.toMatch(/\.map$/i);
        }
      }
    });
  });
});
