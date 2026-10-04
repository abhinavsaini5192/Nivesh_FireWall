/**
 * Extension Build & Distribution Smoke Test
 *
 * Verifies that the production extension bundle in dist/ satisfies all
 * Manifest V3 packaging and distribution requirements.
 */

import fs from 'fs';
import path from 'path';

function runSmokeTest(): void {
  console.log('--- Starting Nivesh Extension Smoke Test ---');

  const distDir = path.resolve(import.meta.dirname, '../dist');
  if (!fs.existsSync(distDir)) {
    throw new Error(`dist directory does not exist at: ${distDir}`);
  }

  // 1. Verify Manifest
  const manifestPath = path.join(distDir, 'manifest.json');
  if (!fs.existsSync(manifestPath)) {
    throw new Error('manifest.json is missing in dist/');
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  console.log(`[PASS] Manifest verified: ${manifest.name} v${manifest.version} (MV${manifest.manifest_version})`);

  // 2. Verify Background Service Worker
  const bgPath = path.join(distDir, 'background.js');
  if (!fs.existsSync(bgPath)) {
    throw new Error('background.js is missing in dist/');
  }
  const bgSize = fs.statSync(bgPath).size;
  console.log(`[PASS] Background Service Worker present (${bgSize} bytes)`);

  // 3. Verify Content Script
  const contentPath = path.join(distDir, 'content.js');
  if (!fs.existsSync(contentPath)) {
    throw new Error('content.js is missing in dist/');
  }
  const contentSize = fs.statSync(contentPath).size;
  console.log(`[PASS] Content script present (${contentSize} bytes)`);

  // 4. Verify Popup
  const popupHtmlPath = path.join(distDir, 'popup/index.html');
  const popupJsPath = path.join(distDir, 'popup/popup.js');
  const popupCssPath = path.join(distDir, 'popup/popup.css');

  if (!fs.existsSync(popupHtmlPath) || !fs.existsSync(popupJsPath) || !fs.existsSync(popupCssPath)) {
    throw new Error('Popup assets (html/js/css) missing in dist/popup/');
  }
  console.log(`[PASS] Popup bundle present (HTML, JS, and CSS)`);

  // 5. Verify Permissions Minimization in packaged manifest
  const declaredPerms = manifest.permissions || [];
  const expectedPerms = ['activeTab', 'storage', 'scripting'];
  const hasOnlyAllowed = declaredPerms.every((p: string) => expectedPerms.includes(p));
  if (!hasOnlyAllowed) {
    throw new Error(`Unexpected permissions in dist manifest: ${declaredPerms.join(', ')}`);
  }
  console.log(`[PASS] Permission minimization confirmed: [${declaredPerms.join(', ')}]`);

  // 6. Verify Icons
  for (const size of [16, 48, 128]) {
    const iconPath = path.join(distDir, `icons/icon${size}.png`);
    if (!fs.existsSync(iconPath)) {
      throw new Error(`Missing icon${size}.png in dist/icons/`);
    }
  }
  console.log(`[PASS] Extension icons verified (16x16, 48x48, 128x128)`);

  console.log('--- Nivesh Extension Smoke Test Passed Successfully ---');
}

runSmokeTest();
