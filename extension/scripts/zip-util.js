import zlib from 'zlib';

/**
 * Creates a deterministic, valid ZIP archive buffer in pure Node.js.
 * @param {Array<{ name: string, data: Buffer }>} entries
 * @returns {Buffer}
 */
export function createZipBuffer(entries) {
  const localHeaders = [];
  const centralHeaders = [];
  let offset = 0;

  // DOS Date / Time: Fixed deterministic timestamp (e.g. 2026-01-01 00:00:00)
  const dosTime = (0 << 11) | (0 << 5) | (0 >> 1);
  const dosDate = ((2026 - 1980) << 9) | (1 << 5) | 1;

  for (const entry of entries) {
    const filenameBuf = Buffer.from(entry.name.replace(/\\/g, '/'), 'utf8');
    const crc = zlib.crc32(entry.data) >>> 0;
    const uncompressedSize = entry.data.length;

    // Compress data with deflateRaw (no zlib headers)
    const compressedData = zlib.deflateRawSync(entry.data, { level: 9 });
    const useCompression = compressedData.length < uncompressedSize;
    const finalData = useCompression ? compressedData : entry.data;
    const compressionMethod = useCompression ? 8 : 0;
    const compressedSize = finalData.length;

    // Local file header (30 bytes + filename)
    const localHeader = Buffer.alloc(30);
    localHeader.writeUInt32LE(0x04034b50, 0); // Local header signature
    localHeader.writeUInt16LE(20, 4);         // Version needed: 2.0
    localHeader.writeUInt16LE(0, 6);          // Flags: 0
    localHeader.writeUInt16LE(compressionMethod, 8); // Method: 8 (deflate) or 0 (store)
    localHeader.writeUInt16LE(dosTime, 10);
    localHeader.writeUInt16LE(dosDate, 12);
    localHeader.writeUInt32LE(crc, 14);
    localHeader.writeUInt32LE(compressedSize, 18);
    localHeader.writeUInt32LE(uncompressedSize, 22);
    localHeader.writeUInt16LE(filenameBuf.length, 26);
    localHeader.writeUInt16LE(0, 28);         // Extra field length

    const localChunk = Buffer.concat([localHeader, filenameBuf, finalData]);
    localHeaders.push(localChunk);

    // Central directory header (46 bytes + filename)
    const centralHeader = Buffer.alloc(46);
    centralHeader.writeUInt32LE(0x02014b50, 0); // Central header signature
    centralHeader.writeUInt16LE(20, 4);          // Version made by: 2.0
    centralHeader.writeUInt16LE(20, 6);          // Version needed: 2.0
    centralHeader.writeUInt16LE(0, 8);           // Flags: 0
    centralHeader.writeUInt16LE(compressionMethod, 10);
    centralHeader.writeUInt16LE(dosTime, 12);
    centralHeader.writeUInt16LE(dosDate, 14);
    centralHeader.writeUInt32LE(crc, 16);
    centralHeader.writeUInt32LE(compressedSize, 20);
    centralHeader.writeUInt32LE(uncompressedSize, 24);
    centralHeader.writeUInt16LE(filenameBuf.length, 28);
    centralHeader.writeUInt16LE(0, 30);          // Extra field length
    centralHeader.writeUInt16LE(0, 32);          // Comment length
    centralHeader.writeUInt16LE(0, 34);          // Disk number start
    centralHeader.writeUInt16LE(0, 36);          // Internal file attributes
    centralHeader.writeUInt32LE(0, 38);          // External file attributes
    centralHeader.writeUInt32LE(offset, 42);     // Relative offset of local header

    centralHeaders.push(Buffer.concat([centralHeader, filenameBuf]));

    offset += localChunk.length;
  }

  const centralDirOffset = offset;
  const centralDirData = Buffer.concat(centralHeaders);
  const centralDirSize = centralDirData.length;

  // End of Central Directory Record (22 bytes)
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);         // EOCD signature
  eocd.writeUInt16LE(0, 4);                  // Disk number: 0
  eocd.writeUInt16LE(0, 6);                  // Disk with start of CD: 0
  eocd.writeUInt16LE(entries.length, 8);      // Entries on this disk
  eocd.writeUInt16LE(entries.length, 10);     // Total entries
  eocd.writeUInt32LE(centralDirSize, 12);     // Size of CD
  eocd.writeUInt32LE(centralDirOffset, 16);   // Offset of start of CD
  eocd.writeUInt16LE(0, 20);                 // Comment length: 0

  return Buffer.concat([...localHeaders, centralDirData, eocd]);
}

/**
 * Inspects a ZIP buffer and reads all central directory entries.
 * @param {Buffer} zipBuf
 * @returns {Array<{ name: string, uncompressedSize: number, compressedSize: number, crc: number }>}
 */
export function inspectZipBuffer(zipBuf) {
  // Find EOCD by scanning from end
  let eocdOffset = -1;
  for (let i = zipBuf.length - 22; i >= Math.max(0, zipBuf.length - 65557); i--) {
    if (zipBuf.readUInt32LE(i) === 0x06054b50) {
      eocdOffset = i;
      break;
    }
  }

  if (eocdOffset === -1) {
    throw new Error('Invalid ZIP file: End of Central Directory signature not found');
  }

  const totalEntries = zipBuf.readUInt16LE(eocdOffset + 10);
  const cdOffset = zipBuf.readUInt32LE(eocdOffset + 16);

  const entries = [];
  let currOffset = cdOffset;

  for (let i = 0; i < totalEntries; i++) {
    if (zipBuf.readUInt32LE(currOffset) !== 0x02014b50) {
      throw new Error(`Invalid Central Directory header signature at offset ${currOffset}`);
    }

    const compressedSize = zipBuf.readUInt32LE(currOffset + 20);
    const uncompressedSize = zipBuf.readUInt32LE(currOffset + 24);
    const filenameLen = zipBuf.readUInt16LE(currOffset + 28);
    const extraLen = zipBuf.readUInt16LE(currOffset + 30);
    const commentLen = zipBuf.readUInt16LE(currOffset + 32);
    const crc = zipBuf.readUInt32LE(currOffset + 16);

    const filename = zipBuf.subarray(currOffset + 46, currOffset + 46 + filenameLen).toString('utf8');
    const localHeaderOffset = zipBuf.readUInt32LE(currOffset + 42);
    entries.push({ name: filename, uncompressedSize, compressedSize, crc, localHeaderOffset });

    currOffset += 46 + filenameLen + extraLen + commentLen;
  }

  return entries;
}

/**
 * Extracts and decompresses all entries from a ZIP buffer.
 * @param {Buffer} zipBuf
 * @returns {Map<string, Buffer>} Map of relative filename to uncompressed Buffer
 */
export function extractZipEntries(zipBuf) {
  const inspected = inspectZipBuffer(zipBuf);
  const result = new Map();

  for (const entry of inspected) {
    const locOffset = entry.localHeaderOffset;
    if (zipBuf.readUInt32LE(locOffset) !== 0x04034b50) {
      throw new Error(`Invalid local file header signature for ${entry.name}`);
    }

    const compressionMethod = zipBuf.readUInt16LE(locOffset + 8);
    const filenameLen = zipBuf.readUInt16LE(locOffset + 26);
    const extraLen = zipBuf.readUInt16LE(locOffset + 28);
    const dataOffset = locOffset + 30 + filenameLen + extraLen;
    const compressedData = zipBuf.subarray(dataOffset, dataOffset + entry.compressedSize);

    let uncompressedData;
    if (compressionMethod === 8) {
      uncompressedData = zlib.inflateRawSync(compressedData);
    } else if (compressionMethod === 0) {
      uncompressedData = compressedData;
    } else {
      throw new Error(`Unsupported compression method ${compressionMethod} for ${entry.name}`);
    }

    result.set(entry.name, uncompressedData);
  }

  return result;
}

