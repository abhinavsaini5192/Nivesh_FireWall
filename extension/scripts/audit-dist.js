import fs from 'fs';
import path from 'path';

/**
 * Production Artifact Audit & Security Scan (Phase 17.3)
 */
export function auditDist(distDir = path.resolve(import.meta.dirname, '../dist')) {
  console.log('=== Running Nivesh Extension Production Artifact Audit ===');

  if (!fs.existsSync(distDir)) {
    throw new Error(`Production dist directory does not exist at: ${distDir}`);
  }

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
  console.log(`Found ${allFiles.length} files in production bundle:`);
  for (const f of allFiles) {
    const rel = path.relative(distDir, f).replace(/\\/g, '/');
    console.log(`  - ${rel} (${fs.statSync(f).size} bytes)`);
  }

  // 1. Prohibited files check
  const prohibitedPatterns = [
    /\.env/i,
    /\.test\./i,
    /\.spec\./i,
    /\.ts$/i,
    /\.map$/i,
    /\.git/i,
    /\.vscode/i,
    /\.idea/i,
    /\.DS_Store/i,
    /thumbs\.db/i,
    /\.log$/i,
    /\.tmp$/i,
    /\.bak$/i,
  ];

  for (const f of allFiles) {
    const rel = path.relative(distDir, f);
    for (const pat of prohibitedPatterns) {
      if (pat.test(rel)) {
        throw new Error(`[FAIL] Prohibited file found in dist/: ${rel}`);
      }
    }
  }
  console.log('[PASS] No prohibited files, test files, or source files in dist/');

  // 2. Secret and local-path scanning in text files
  const sensitivePatterns = [
    { name: 'API Key / Secret assignment', regex: /(?:api_?key|secret_?key|client_?secret)\s*[:=]\s*['"][a-zA-Z0-9_-]{8,}['"]/i },
    { name: 'Private JWT secret', regex: /jwt_?secret\s*[:=]\s*['"][^'"]+['"]/i },
    { name: 'Database connection URI', regex: /(?:postgres|mysql|mongodb|redis):\/\/[^'"\s]+/i },
    { name: 'Hardcoded password credentials', regex: /password\s*[:=]\s*['"][^'"]{4,}['"]/i },
    { name: 'Local Windows filesystem path', regex: /[a-zA-Z]:\\Users\\[a-zA-Z0-9_-]+/i },
    { name: 'Local Unix home directory path', regex: /\/home\/[a-zA-Z0-9_-]+\//i },
  ];

  // 2b. Remote code execution scan (Chrome Web Store Developer Program Policy compliance)
  const remoteCodePatterns = [
    { name: 'Dynamic eval() execution', regex: /\beval\s*\(/ },
    { name: 'Dynamic Function() constructor', regex: /new\s+Function\s*\(/ },
    { name: 'Remote script source in HTML', regex: /<script[^>]+src=["']https?:\/\//i },
  ];

  let scannedCount = 0;
  for (const f of allFiles) {
    if (f.endsWith('.png') || f.endsWith('.jpg') || f.endsWith('.ico')) {
      continue;
    }

    scannedCount++;
    const content = fs.readFileSync(f, 'utf-8');

    for (const { name, regex } of sensitivePatterns) {
      if (regex.test(content)) {
        throw new Error(`[FAIL] Sensitive data detected (${name}) in ${path.relative(distDir, f)}`);
      }
    }

    for (const { name, regex } of remoteCodePatterns) {
      if (regex.test(content)) {
        throw new Error(`[FAIL] Prohibited remote code pattern detected (${name}) in ${path.relative(distDir, f)}`);
      }
    }
  }
  console.log(`[PASS] Secret, local-path & remote-code scans passed (${scannedCount} text/bundle files audited)`);

  // 3. Manifest V3 Integrity check
  const manifestPath = path.join(distDir, 'manifest.json');
  if (!fs.existsSync(manifestPath)) {
    throw new Error('manifest.json is missing in dist/');
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  if (manifest.manifest_version !== 3) {
    throw new Error(`Manifest version must be 3, found ${manifest.manifest_version}`);
  }
  if (!manifest.name || manifest.name !== 'Nivesh Firewall') {
    throw new Error(`Extension name must be "Nivesh Firewall", found "${manifest.name}"`);
  }
  if (!manifest.description || manifest.description.length > 132) {
    throw new Error(`Description must be under 132 chars, current length: ${manifest.description?.length}`);
  }
  if (!manifest.icons || !manifest.icons['16'] || !manifest.icons['48'] || !manifest.icons['128']) {
    throw new Error('Missing 16, 48, or 128 icon declarations in manifest.json');
  }

  // 4. Permissions Minimization Audit
  const allowedPermissions = ['activeTab', 'storage', 'scripting'];
  for (const perm of manifest.permissions || []) {
    if (!allowedPermissions.includes(perm)) {
      throw new Error(`[FAIL] Forbidden broad permission in production manifest: ${perm}`);
    }
  }
  console.log(`[PASS] Permissions minimized to: [${(manifest.permissions || []).join(', ')}]`);

  // 5. Icons presence and validity
  for (const size of [16, 48, 128]) {
    const iconRelPath = manifest.icons[size.toString()];
    const iconFullPath = path.join(distDir, iconRelPath);
    if (!fs.existsSync(iconFullPath)) {
      throw new Error(`Icon file does not exist: ${iconRelPath}`);
    }
    const buf = fs.readFileSync(iconFullPath);
    // Verify PNG header 89 50 4E 47 0D 0A 1A 0A
    if (buf.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') {
      throw new Error(`Icon file is not a valid PNG: ${iconRelPath}`);
    }
    const width = buf.readUInt32BE(16);
    const height = buf.readUInt32BE(20);
    if (width !== size || height !== size) {
      throw new Error(`Icon dimensions mismatch for ${iconRelPath}: expected ${size}x${size}, got ${width}x${height}`);
    }
  }
  console.log('[PASS] Icons presence and dimensions validated (16x16, 48x48, 128x128 PNG)');

  console.log('=== Production Artifact Audit: SUCCESS ===\n');
  return { success: true, fileCount: allFiles.length, manifest };
}

// Auto-run if executed directly
if (process.argv[1] && process.argv[1].endsWith('audit-dist.js')) {
  auditDist();
}
