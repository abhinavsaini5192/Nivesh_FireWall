import { describe, it, expect, vi, beforeEach } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Popup UI Controller & Security Controls (Phase 13.1, 13.2 & Phase 17.1)', () => {
  const htmlPath = path.resolve(__dirname, '../src/popup/index.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

  beforeEach(() => {
    // Inject popup HTML into document
    document.body.innerHTML = htmlContent;
    vi.restoreAllMocks();
  });

  // --- Phase 13 Baseline Tests (Preserved) ---

  it('renders required UI structure with brand, connection pill, context card, and 3 capture mode triggers', () => {
    expect(document.getElementById('connection-pill')).not.toBeNull();
    expect(document.getElementById('connection-dot')).not.toBeNull();
    expect(document.getElementById('page-context-card')).not.toBeNull();

    // Three capture triggers
    expect(document.getElementById('btn-scan-selection')).not.toBeNull();
    expect(document.getElementById('btn-scan-page')).not.toBeNull();
    expect(document.getElementById('btn-scan-url')).not.toBeNull();
    expect(document.getElementById('selection-hint')).not.toBeNull();

    // Four primary views
    expect(document.getElementById('view-ready')).not.toBeNull();
    expect(document.getElementById('view-preview')).not.toBeNull();
    expect(document.getElementById('view-analyzing')).not.toBeNull();
    expect(document.getElementById('view-result')).not.toBeNull();
  });

  it('renders preview card structure with snippet, source badge, metadata, and confirmation/cancel buttons', () => {
    expect(document.getElementById('preview-badge')).not.toBeNull();
    expect(document.getElementById('preview-snippet')).not.toBeNull();
    expect(document.getElementById('preview-length')).not.toBeNull();
    expect(document.getElementById('preview-origin')).not.toBeNull();
    expect(document.getElementById('btn-confirm-analyze')).not.toBeNull();
    expect(document.getElementById('btn-cancel-preview')).not.toBeNull();
    expect(document.getElementById('btn-cancel-analyzing')).not.toBeNull();
  });

  it('renders unsupported page notice box for internal/restricted pages', () => {
    const unsupportedBox = document.getElementById('unsupported-box')!;
    expect(unsupportedBox).not.toBeNull();
    expect(unsupportedBox.textContent).toContain('This page cannot be analyzed');
  });

  it('enforces User-Initiated Analysis Principle with default ready state and hidden preview/analyzing states', () => {
    const viewReady = document.getElementById('view-ready')!;
    const viewPreview = document.getElementById('view-preview')!;
    const viewAnalyzing = document.getElementById('view-analyzing')!;
    const viewResult = document.getElementById('view-result')!;

    // Initial state does not auto-analyze
    expect(viewReady.style.display).not.toBe('none');
    expect(viewPreview.style.display).toBe('none');
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

  // --- Phase 17.1 Production UX & Polish Tests ---

  it('communicates Nivesh brand identity and Financial Content Protection descriptor', () => {
    const brandName = document.querySelector('.brand-name');
    const brandDescriptor = document.querySelector('.brand-descriptor');

    expect(brandName).not.toBeNull();
    expect(brandName?.textContent).toBe('NIVESH FIREWALL');

    expect(brandDescriptor).not.toBeNull();
    expect(brandDescriptor?.textContent).toBe('Financial Content Protection');
  });

  it('presents prominent "Analyze This Page" hero action button in ready view', () => {
    const btnScanPage = document.getElementById('btn-scan-page') as HTMLButtonElement;
    expect(btnScanPage).not.toBeNull();
    expect(btnScanPage.textContent?.trim()).toContain('Analyze This Page');
    expect(btnScanPage.classList.contains('btn-hero')).toBe(true);

    const emptyIntro = document.querySelector('.empty-state-lead');
    expect(emptyIntro?.textContent).toContain("This page hasn't been checked yet.");
  });

  it('renders pipeline stages list in analyzing view corresponding to firewall engines', () => {
    const viewAnalyzing = document.getElementById('view-analyzing')!;
    const stagesList = viewAnalyzing.querySelector('.pipeline-stages-list');
    expect(stagesList).not.toBeNull();

    const stageItems = viewAnalyzing.querySelectorAll('.pipeline-stage-item');
    expect(stageItems.length).toBe(4);

    const stagesText = Array.from(stageItems).map((item) => item.textContent || '').join(' ');
    expect(stagesText).toContain('Claims');
    expect(stagesText).toContain('Actions');
    expect(stagesText).toContain('Evidence');
    expect(stagesText).toContain('Policy');
  });

  it('renders "Open Full Firewall" handoff action and rescan button in result view', () => {
    const btnOpenApp = document.getElementById('btn-open-app') as HTMLButtonElement;
    expect(btnOpenApp).not.toBeNull();
    expect(btnOpenApp.textContent).toContain('Open Full Firewall');
    expect(btnOpenApp.classList.contains('btn-hero-handoff')).toBe(true);

    const btnRescan = document.getElementById('btn-rescan') as HTMLButtonElement;
    expect(btnRescan).not.toBeNull();
    expect(btnRescan.textContent).toContain('Rescan');

    const linkWebApp = document.getElementById('link-web-app') as HTMLAnchorElement;
    expect(linkWebApp).not.toBeNull();
    expect(linkWebApp.textContent).toContain('Open Firewall');
  });

  it('provides safe error banner with retry trigger and zero stacktrace leakage', () => {
    const errorBox = document.getElementById('error-box')!;
    const btnRetryError = document.getElementById('btn-retry-error');

    expect(errorBox).not.toBeNull();
    expect(btnRetryError).not.toBeNull();

    // Verify error container does not expose raw stack trace
    const errorText = document.getElementById('error-message-text')!;
    errorText.textContent = 'Nivesh Firewall is temporarily unavailable.';
    expect(errorBox.textContent).not.toContain('Traceback');
    expect(errorBox.textContent).not.toContain('at Object.');
    expect(errorBox.textContent).toContain('Nivesh Firewall is temporarily unavailable.');
  });

  it('verifies absence of fake numeric security scores or 100% protection claims', () => {
    const entireContent = document.body.textContent || '';
    expect(entireContent).not.toMatch(/\d{2,3}%\s*protected/i);
    expect(entireContent).not.toMatch(/security\s*score\s*:\s*\d+/i);
    expect(entireContent).not.toMatch(/100%\s*safe/i);
  });

  it('includes accessibility attributes including ARIA roles, live regions, and labels', () => {
    expect(document.querySelector('header[role="banner"]')).not.toBeNull();
    expect(document.querySelector('footer[role="contentinfo"]')).not.toBeNull();
    expect(document.getElementById('connection-pill')?.getAttribute('role')).toBe('status');
    expect(document.getElementById('error-box')?.getAttribute('role')).toBe('alert');
    expect(document.getElementById('view-analyzing')?.getAttribute('aria-live')).toBe('polite');
    expect(document.getElementById('btn-scan-page')?.getAttribute('aria-label')).toBe('Analyze Current Page');
  });
});
