import fs from 'fs';
import path from 'path';
import zlib from 'zlib';

/**
 * Creates a valid RGBA PNG buffer in pure Node.js.
 */
function createPng(width, height, getPixel) {
  // 1. Scanlines: (1 filter byte + width * 4 bytes RGBA) per row
  const rowSize = 1 + width * 4;
  const rawScanlines = Buffer.alloc(height * rowSize);

  for (let y = 0; y < height; y++) {
    const rowOffset = y * rowSize;
    rawScanlines[rowOffset] = 0; // Filter type 0 (None)

    for (let x = 0; x < width; x++) {
      const pixelOffset = rowOffset + 1 + x * 4;
      const [r, g, b, a] = getPixel(x, y, width, height);
      rawScanlines[pixelOffset] = r;
      rawScanlines[pixelOffset + 1] = g;
      rawScanlines[pixelOffset + 2] = b;
      rawScanlines[pixelOffset + 3] = a;
    }
  }

  // 2. Compress IDAT payload with zlib
  const compressedData = zlib.deflateSync(rawScanlines, { level: 9 });

  // 3. Helper to write chunks with CRC32
  function makeChunk(typeStr, dataBuf) {
    const typeBuf = Buffer.from(typeStr, 'ascii');
    const lengthBuf = Buffer.alloc(4);
    lengthBuf.writeUInt32BE(dataBuf.length, 0);

    const crcBuf = Buffer.alloc(4);
    const toCrc = Buffer.concat([typeBuf, dataBuf]);
    const crcVal = zlib.crc32(toCrc);
    crcBuf.writeUInt32BE(crcVal >>> 0, 0);

    return Buffer.concat([lengthBuf, typeBuf, dataBuf, crcBuf]);
  }

  // 4. IHDR Chunk (13 bytes)
  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData[8] = 8; // Bit depth: 8
  ihdrData[9] = 6; // Color type: 6 (RGBA)
  ihdrData[10] = 0; // Compression method: 0 (deflate)
  ihdrData[11] = 0; // Filter method: 0 (standard)
  ihdrData[12] = 0; // Interlace method: 0 (none)

  const ihdrChunk = makeChunk('IHDR', ihdrData);
  const idatChunk = makeChunk('IDAT', compressedData);
  const iendChunk = makeChunk('IEND', Buffer.alloc(0));

  // 5. PNG Signature (8 bytes)
  const pngHeader = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

  return Buffer.concat([pngHeader, ihdrChunk, idatChunk, iendChunk]);
}

/**
 * Nivesh Shield Icon Pixel Shader:
 * Renders the Nivesh security shield with checkmark on transparent background.
 */
function niveshPixelShader(x, y, w, h) {
  // Normalize to [-1, 1] coordinate space
  const nx = (x + 0.5) / w * 2 - 1;
  const ny = (y + 0.5) / h * 2 - 1;

  // Margin around edges
  const scale = 0.88;
  const sx = nx / scale;
  const sy = ny / scale;

  // Shield Geometry:
  // Top horizontal: sy >= -0.8
  // Sides: |sx| <= 0.85
  // Bottom curve: sy <= 0.9 - 1.2 * (sx * sx)
  const insideTop = sy >= -0.85;
  const insideSides = Math.abs(sx) <= 0.85;
  const bottomBoundary = 0.85 - 1.15 * (sx * sx);
  const insideBottom = sy <= bottomBoundary;

  const inShield = insideTop && insideSides && insideBottom;

  if (!inShield) {
    return [0, 0, 0, 0]; // Transparent
  }

  // Shield Border calculation
  const borderThickness = 0.16;
  const inInnerTop = sy >= -0.85 + borderThickness;
  const inInnerSides = Math.abs(sx) <= (0.85 - borderThickness);
  const inInnerBottom = sy <= (bottomBoundary - borderThickness);
  const inInner = inInnerTop && inInnerSides && inInnerBottom;

  // Primary palette:
  // Deep Navy interior: #0f172a (15, 23, 42)
  // Cyber Blue border: #0ea5e9 (14, 165, 233)
  // Bright Cyan checkmark: #38bdf8 (56, 189, 248)
  // White accent: #ffffff (255, 255, 255)

  if (!inInner) {
    // Outer Shield Border (Cyber Blue gradient)
    const gradient = Math.floor(14 + (y / h) * 40);
    return [14, 165, Math.min(255, 220 + gradient), 255];
  }

  // Checkmark Geometry:
  // Short stroke: from (-0.35, -0.05) to (-0.05, 0.25)
  // Long stroke: from (-0.05, 0.25) to (0.40, -0.30)
  function distToSegment(px, py, x1, y1, x2, y2) {
    const l2 = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
    if (l2 === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
  }

  const d1 = distToSegment(sx, sy, -0.32, -0.05, -0.05, 0.24);
  const d2 = distToSegment(sx, sy, -0.05, 0.24, 0.38, -0.28);
  const checkDist = Math.min(d1, d2);

  const checkThickness = w <= 16 ? 0.24 : 0.14;

  if (checkDist <= checkThickness) {
    // Checkmark highlight (Bright Cyan / White)
    if (checkDist <= checkThickness * 0.5) {
      return [255, 255, 255, 255]; // Crisp white core
    }
    return [56, 189, 248, 255]; // Cyan edge
  }

  // Shield interior (Deep Midnight Navy)
  return [15, 23, 42, 255];
}

const iconsDir = path.resolve(import.meta.dirname, '../icons');
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

const sizes = [16, 48, 128];
for (const size of sizes) {
  const pngBuf = createPng(size, size, niveshPixelShader);
  const iconPath = path.join(iconsDir, `icon${size}.png`);
  fs.writeFileSync(iconPath, pngBuf);
  console.log(`Generated icon${size}.png (${pngBuf.length} bytes, ${size}x${size})`);
}
