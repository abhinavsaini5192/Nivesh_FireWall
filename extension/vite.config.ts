import { defineConfig } from 'vitest/config';
import { resolve } from 'path';
import fs from 'fs';

export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2022',
    rollupOptions: {
      input: {
        popup: resolve(import.meta.dirname, 'src/popup/index.html'),
        background: resolve(import.meta.dirname, 'src/background/index.ts'),
        content: resolve(import.meta.dirname, 'src/content/index.ts'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'background') return 'background.js';
          if (chunkInfo.name === 'content') return 'content.js';
          return 'popup/[name].js';
        },
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith('.css')) {
            return 'popup/[name][extname]';
          }
          return 'assets/[name][extname]';
        },
      },
    },
  },
  plugins: [
    {
      name: 'copy-manifest-and-assets',
      closeBundle() {
        const manifestSrc = resolve(import.meta.dirname, 'manifest.json');
        const manifestDest = resolve(import.meta.dirname, 'dist/manifest.json');
        if (fs.existsSync(manifestSrc)) {
          fs.copyFileSync(manifestSrc, manifestDest);
        }

        // Copy extension icons to dist/icons
        const iconsSrc = resolve(import.meta.dirname, 'icons');
        const iconsDest = resolve(import.meta.dirname, 'dist/icons');
        if (fs.existsSync(iconsSrc)) {
          fs.cpSync(iconsSrc, iconsDest, { recursive: true });
        }

        // Relocate popup HTML to dist/popup/index.html to match manifest action.default_popup
        const popupSrc = resolve(import.meta.dirname, 'dist/src/popup/index.html');
        const popupDest = resolve(import.meta.dirname, 'dist/popup/index.html');
        if (fs.existsSync(popupSrc)) {
          fs.copyFileSync(popupSrc, popupDest);
          const srcDir = resolve(import.meta.dirname, 'dist/src');
          fs.rmSync(srcDir, { recursive: true, force: true });
        }
      },
    },
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './test/setup.ts',
  },
});
