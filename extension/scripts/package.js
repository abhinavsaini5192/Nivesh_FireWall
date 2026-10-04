import fs from 'fs';
import path from 'path';
import { auditDist } from './audit-dist.js';
import { createZipBuffer, inspectZipBuffer } from './zip-util.js';

/**
 * Production Packaging & Distribution Workflow (Phase 17.3)
 */
export function packageExtension() {
  console.log('=== Nivesh Extension Production Packaging ===');

  const extensionRoot = path.resolve(import.meta.dirname, '..');
  const distDir = path.join(extensionRoot, 'dist');
  const pkgJsonPath = path.join(extensionRoot, 'package.json');

  if (!fs.existsSync(pkgJsonPath)) {
    throw new Error('package.json not found');
  }
  const pkg = JSON.parse(fs.readFileSync(pkgJsonPath, 'utf8'));
  const version = pkg.version || '1.0.0';

  // 1. Audit dist directory first
  auditDist(distDir);

  // 2. Gather files from dist
  function getFilesRecursively(dir) {
    let results = [];
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results = results.concat(getFilesRecursively(fullPath));
      } else {
        results.push(fullPath);
      }
    }
    return results;
  }

  const allFiles = getFilesRecursively(distDir);
  const zipEntries = [];

  for (const filePath of allFiles) {
    const relPath = path.relative(distDir, filePath).replace(/\\/g, '/');
    let fileBuffer = fs.readFileSync(filePath);

    // Production Manifest Hardening:
    // In the Chrome Web Store production package, replace development localhost host permissions
    // with production HTTPS endpoint to ensure clean distribution without localhost dependencies.
    if (relPath === 'manifest.json') {
      const manifest = JSON.parse(fileBuffer.toString('utf8'));
      manifest.host_permissions = ['https://api.nivesh.ai/*'];
      fileBuffer = Buffer.from(JSON.stringify(manifest, null, 2), 'utf8');
    }

    zipEntries.push({
      name: relPath,
      data: fileBuffer,
    });
  }

  // 3. Generate deterministic ZIP buffer
  const zipBuffer = createZipBuffer(zipEntries);
  const zipFileName = `nivesh-firewall-v${version}.zip`;
  const zipFilePath = path.join(extensionRoot, zipFileName);

  fs.writeFileSync(zipFilePath, zipBuffer);
  console.log(`[PASS] Generated package: ${zipFileName} (${zipBuffer.length} bytes)`);

  // 4. Inspect ZIP buffer to verify Central Directory and integrity
  const inspectedEntries = inspectZipBuffer(zipBuffer);
  console.log(`\nVerified ZIP package contents (${inspectedEntries.length} entries):`);
  for (const entry of inspectedEntries) {
    console.log(`  - ${entry.name.padEnd(25)} ${entry.uncompressedSize} B -> ${entry.compressedSize} B (CRC: 0x${entry.crc.toString(16).toUpperCase()})`);
  }

  // Verify critical files in the ZIP
  const entryNames = inspectedEntries.map((e) => e.name);
  const requiredFiles = [
    'manifest.json',
    'background.js',
    'content.js',
    'popup/index.html',
    'popup/popup.js',
    'popup/popup.css',
    'icons/icon16.png',
    'icons/icon48.png',
    'icons/icon128.png',
  ];

  for (const req of requiredFiles) {
    if (!entryNames.includes(req)) {
      throw new Error(`[FAIL] Required file missing from ZIP package: ${req}`);
    }
  }

  console.log('\n=== Nivesh Extension Packaging Complete: READY FOR CHROME WEB STORE ===');
  return {
    success: true,
    zipFileName,
    zipFilePath,
    sizeBytes: zipBuffer.length,
    entryCount: inspectedEntries.length,
    entries: inspectedEntries,
  };
}

if (process.argv[1] && process.argv[1].endsWith('package.js')) {
  packageExtension();
}
