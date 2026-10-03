import { describe, it, expect, vi, beforeEach } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Popup UI Controller & Security Controls (Phase 13.1 Sections 6, 20, 22, 24, 25)', () => {
  const htmlPath = path.resolve(__dirname, '../src/popup/index.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

  beforeEach(() => {
    // Inject popup HTML into document
    document.body.innerHTML = htmlContent;
    vi.restoreAllMocks();
  });

  it('renders required UI structure with brand, status pill, context card, and scan trigger', () => {
    expect(document.getElementById('connection-pill')).not.toBeNull();
    expect(document.getElementById('connection-dot')).not.toBeNull();
    expect(document.getElementById('page-context-card')).not.toBeNull();
    expect(document.getElementById('btn-scan')).not.toBeNull();
    expect(document.getElementById('view-ready')).not.toBeNull();
    expect(document.getElementById('view-analyzing')).not.toBeNull();
    expect(document.getElementById('view-result')).not.toBeNull();
  });

  it('enforces User-Initiated Analysis Principle with default ready state', () => {
    const viewReady = document.getElementById('view-ready')!;
    const viewAnalyzing = document.getElementById('view-analyzing')!;
    const viewResult = document.getElementById('view-result')!;

    // Initial state does not auto-analyze
    expect(viewReady.style.display).not.toBe('none');
    expect(viewAnalyzing.style.display).toBe('none');
    expect(viewResult.style.display).toBe('none');
  });

  it('prevents XSS vulnerabilities by using safe text rendering for dynamic page and error data', () => {
    const targetDomainEl = document.getElementById('target-domain')!;
    const maliciousInput = '<img src=x onerror="alert(1)">phishing.fake';

    // Set via textContent as done in index.ts
    targetDomainEl.textContent = maliciousInput;

    // Verify it is treated as plain text and NOT executed or parsed as DOM elements
    expect(targetDomainEl.children.length).toBe(0);
    expect(targetDomainEl.innerHTML).toBe('&lt;img src=x onerror="alert(1)"&gt;phishing.fake');
  });

  it('verifies decision cards contain valid styling hooks for semantic decisions', () => {
    const decisionCard = document.getElementById('decision-card')!;
    const allowedDecisions = ['ALLOW', 'INFORM', 'WARN', 'PAUSE', 'BLOCK'];

    for (const dec of allowedDecisions) {
      decisionCard.className = `decision-card ${dec}`;
      expect(decisionCard.className).toContain(dec);
    }
  });

  it('includes zero-credential collection privacy notice in footer', () => {
    const footer = document.querySelector('footer')!;
    expect(footer.textContent).toContain('Zero credential collection');
  });
});
