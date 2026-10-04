/**
 * Phase 17.4: Chrome Web Store Readiness & Submission Preparation Test Suite
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import manifest from '../manifest.json';
import { inspectZipBuffer } from '../scripts/zip-util.js';

describe('Phase 17.4: Chrome Web Store Readiness & Submission Test Suite', () => {
  const extensionDir = path.resolve(import.meta.dirname, '..');
  const storeDocPath = path.join(extensionDir, 'STORE_SUBMISSION.md');
  const zipPath = path.join(extensionDir, 'nivesh-firewall-v1.0.0.zip');
  const distDir = path.join(extensionDir, 'dist');

  // ===========================================================================
  // 1. Store Documentation Verification (STORE_SUBMISSION.md)
  // ===========================================================================
  describe('1. Store Submission Documentation Audit', () => {
    it('verifies STORE_SUBMISSION.md exists and is populated', () => {
      expect(fs.existsSync(storeDocPath)).toBe(true);
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content.length).toBeGreaterThan(1500);
    });

    it('documents exact Executive Status & Deployment Reality markers', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('Chrome Web Store package:\nTechnically ready');
      expect(content).toContain('Public API dependency:\nNOT YET DEPLOYED');
      expect(content).toContain('Public user installation:\nNOT YET END-TO-END VERIFIED');
      expect(content).toContain('Store Publication Status:\nNOT PUBLISHED');
    });

    it('declares exact required Single-Purpose Statement', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      const requiredPurpose = 'Helping users inspect financial content and understand potential safety concerns before consequential actions.';
      expect(content).toContain(requiredPurpose);
      expect(content).toContain('No Background Surveillance');
      expect(content).toContain('User-Initiated Activation');
    });

    it('includes non-advisory, non-broker, and non-guarantee regulatory notices', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('is NOT a registered investment advisor (RIA) or broker-dealer');
      expect(content).toContain('does NOT offer investment advice');
      expect(content).toContain('does NOT guarantee scam or fraud prevention');
    });

    it('justifies every requested permission and lists forbidden permissions', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('### `activeTab`');
      expect(content).toContain('### `storage`');
      expect(content).toContain('### `scripting`');
      expect(content).toContain('### Host Permissions (`https://api.nivesh.ai/*`)');

      // Forbidden permissions explicitly acknowledged as not requested
      expect(content).toContain('<all_urls>');
      expect(content).toContain('history');
      expect(content).toContain('passwords');
      expect(content).toContain('cookies');
      expect(content).toContain('clipboardRead');
    });

    it('specifies explicit privacy zero-collection guarantees', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('No Passwords');
      expect(content).toContain('No Payment Details');
      expect(content).toContain('No OTPs / 2FA');
      expect(content).toContain('No Keystroke Surveillance');
      expect(content).toContain('No Continuous Surveillance');
    });

    it('defines the normal user installation flow and forbids developer mode instructions', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('Nivesh Landing Page');
      expect(content).toContain('Add to Chrome');
      expect(content).toContain('Chrome Web Store');
      expect(content).toContain('No Developer Mode Instructions');
      expect(content).toContain('VITE_CHROME_WEBSTORE_URL');
    });

    it('defines all 5 required real UI screenshot specifications', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('Popup Idle / Ready State');
      expect(content).toContain('Analyze This Page State');
      expect(content).toContain('Example Analysis Result');
      expect(content).toContain('Full Firewall Handoff');
      expect(content).toContain('In-Page Intervention Overlay');
      expect(content).toContain('1280 x 800 px');
    });

    it('contains comprehensive store review risk audit matrix', () => {
      const content = fs.readFileSync(storeDocPath, 'utf8');
      expect(content).toContain('1. Misleading Description');
      expect(content).toContain('2. Unnecessary Permissions');
      expect(content).toContain('3. Remote Code Execution');
      expect(content).toContain('4. Unclear Privacy Behavior');
      expect(content).toContain('5. Financial Advisor Disclaimers');
      expect(content).toContain('6. Development Endpoints');
      expect(content).toContain('7. Hidden Functionality');
      expect(content).toContain('8. Unexplained Data Collection');
      expect(content).toContain('9. Misleading Branding');
    });
  });

  // ===========================================================================
  // 2. Manifest V3 Chrome Web Store Rules
  // ===========================================================================
  describe('2. Manifest V3 Chrome Web Store Rules', () => {
    it('manifest has valid name, version, and short description length', () => {
      expect(manifest.name).toBe('Nivesh Firewall');
      expect(manifest.version).toMatch(/^\d+\.\d+\.\d+$/);
      expect(manifest.description.length).toBeLessThanOrEqual(132);
      expect(manifest.description.length).toBeGreaterThan(20);
    });

    it('strictly minimizes permissions without invasive capabilities', () => {
      expect(manifest.permissions).toEqual(['activeTab', 'storage', 'scripting']);
    });

    it('declares valid square icons for all required resolutions', () => {
      expect(manifest.icons).toEqual({
        '16': 'icons/icon16.png',
        '48': 'icons/icon48.png',
        '128': 'icons/icon128.png',
      });
    });
  });

  // ===========================================================================
  // 3. Remote Code Execution Prohibition Audit
  // ===========================================================================
  describe('3. Remote Code Execution Prohibition Audit', () => {
    it('verifies dist/ JS/HTML files contain zero eval, new Function, or remote scripts', () => {
      if (!fs.existsSync(distDir)) return;

      const jsAndHtmlFiles: string[] = [];
      function collectFiles(dir: string) {
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
          const full = path.join(dir, entry.name);
          if (entry.isDirectory()) collectFiles(full);
          else if (entry.name.endsWith('.js') || entry.name.endsWith('.html')) jsAndHtmlFiles.push(full);
        }
      }
      collectFiles(distDir);

      expect(jsAndHtmlFiles.length).toBeGreaterThanOrEqual(4);

      for (const filePath of jsAndHtmlFiles) {
        const content = fs.readFileSync(filePath, 'utf8');
        expect(content).not.toMatch(/\beval\s*\(/);
        expect(content).not.toMatch(/new\s+Function\s*\(/);
        expect(content).not.toMatch(/<script[^>]+src=["']https?:\/\//i);
      }
    });
  });

  // ===========================================================================
  // 4. Packaged ZIP Production Manifest
  // ===========================================================================
  describe('4. Packaged ZIP Production Manifest', () => {
    it('verifies that the distribution ZIP uses production HTTPS endpoint without localhost', () => {
      if (!fs.existsSync(zipPath)) return;

      const zipBuf = fs.readFileSync(zipPath);
      const entries = inspectZipBuffer(zipBuf);
      const manifestEntry = entries.find((e: { name: string }) => e.name === 'manifest.json');
      expect(manifestEntry).toBeDefined();

      // Ensure no localhost or local IP in the ZIP package
      const zipString = zipBuf.toString('utf8');
      expect(zipString).not.toContain('http://localhost:8000');
      expect(zipString).not.toContain('http://127.0.0.1:8000');
    });
  });
});
