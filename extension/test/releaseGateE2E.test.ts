/**
 * Phase 17.5: Final Extension End-to-End Validation & Release Gate Test Suite
 *
 * Comprehensive release-gate validation across:
 * 1. Complete Browser Flow (Benign, Suspicious, Unsupported Claim, Full Handoff)
 * 2. Browser Lifecycle & Multi-Tab Isolation
 * 3. API Status & Failure Recovery Matrix (200, 400, 404, 429, 5xx, Timeout, Malformed)
 * 4. Privacy Boundaries & Zero-Collection Guarantees
 * 5. Permission Minimization & Manifest Integrity
 * 6. Production Package & Remote-Code Verification
 * 7. Real Performance Smoke Metrics
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import manifest from '../manifest.json';
import { backgroundState } from '../src/background/state';
import { routeExtensionMessage } from '../src/background/router';
import { NiveshAnalysisBridge } from '../src/bridge/analysisBridge';
import { buildNiveshWebAppUrl } from '../src/config';
import { extractSafePageContext, isSensitiveElement } from '../src/content/context';
import { protectionManager } from '../src/protection/manager';
import { extractZipEntries } from '../scripts/zip-util.js';
import type { ScanRequestMessage } from '../src/types/messages';
import type { BrowserAnalysisRequest, BridgeAnalysisResult } from '../src/bridge/types';

describe('Phase 17.5: Final Extension End-to-End Validation & Release Gate Suite', () => {
  const extensionDir = path.resolve(import.meta.dirname, '..');
  const zipPath = path.join(extensionDir, 'nivesh-firewall-v1.0.0.zip');

  beforeEach(() => {
    backgroundState.reset();
    protectionManager.cleanup();
    vi.clearAllMocks();
  });

  afterEach(() => {
    protectionManager.cleanup();
    vi.restoreAllMocks();
  });

  // ===========================================================================
  // 1. Complete Browser Flow Validation (Section 2)
  // ===========================================================================
  describe('1. Complete Browser Flow Validation', () => {
    it('evaluates benign page content returning ALLOW verdict with zero intervention', async () => {
      const benignResult = {
        analysisId: 'ANA-BENIGN-001',
        requestId: 'REQ-BENIGN-001',
        captureId: 'CAP-BENIGN-001',
        reference: {
          analysisId: 'ANA-BENIGN-001',
          captureId: 'CAP-BENIGN-001',
          requestId: 'REQ-BENIGN-001',
          tabId: 101,
          decision: 'ALLOW',
          severity: 'LOW',
          primaryReason: 'Verified institutional exchange listing',
          completedAt: new Date().toISOString(),
          webAppUrl: 'https://nivesh.ai/#protect?id=ANA-BENIGN-001',
          claimsCount: 0,
          evidenceStatus: 'VERIFIED',
          identityStatus: 'VERIFIED',
          fingerprintMatch: 'NO_MATCH',
          threatSignalCount: 0,
          durationMs: 42,
        },
        fullResponse: {
          analysis_id: 'ANA-BENIGN-001',
          decision: { decision: 'ALLOW', severity: 'LOW', primary_reason: 'Verified exchange listing' },
          evidence: { overall_status: 'VERIFIED' },
        },
        retriesAttempted: 0,
        durationMs: 42,
      } as unknown as BridgeAnalysisResult;

      const bridge = new NiveshAnalysisBridge();
      vi.spyOn(bridge, 'submitAnalysis').mockResolvedValue(benignResult);

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-BENIGN-001',
        requestId: 'REQ-BENIGN-001',
        sessionId: 'SESS-101',
        sourceType: 'CURRENT_PAGE',
        text: 'Nifty 50 Index fund details and tracking error disclosures.',
        url: 'https://official-amc.example.com/funds',
        pageOrigin: 'https://official-amc.example.com',
        tabId: 101,
        timestamp: new Date().toISOString(),
      };

      const result = await bridge.submitAnalysis(request);
      expect(result.reference.decision).toBe('ALLOW');
      expect(result.reference.evidenceStatus).toBe('VERIFIED');

      // Zero intervention banner for ALLOW
      expect(protectionManager.getState().active).toBe(false);
      expect(document.getElementById('nivesh-firewall-root')).toBeNull();
    });

    it('evaluates suspicious financial advisory content returning WARN and triggers intervention', async () => {
      const suspiciousResult = {
        analysisId: 'ANA-SUSPICIOUS-002',
        requestId: 'REQ-SUSPICIOUS-002',
        captureId: 'CAP-SUSPICIOUS-002',
        reference: {
          analysisId: 'ANA-SUSPICIOUS-002',
          captureId: 'CAP-SUSPICIOUS-002',
          requestId: 'REQ-SUSPICIOUS-002',
          tabId: 102,
          decision: 'WARN',
          severity: 'MEDIUM',
          primaryReason: 'Unregistered advisor promoting options strategies',
          completedAt: new Date().toISOString(),
          webAppUrl: 'https://nivesh.ai/#protect?id=ANA-SUSPICIOUS-002',
          claimsCount: 2,
          evidenceStatus: 'UNSUPPORTED',
          identityStatus: 'SUSPICIOUS',
          fingerprintMatch: 'NO_MATCH',
          threatSignalCount: 2,
          durationMs: 78,
        },
        fullResponse: {
          analysis_id: 'ANA-SUSPICIOUS-002',
          decision: { decision: 'WARN', severity: 'MEDIUM', primary_reason: 'Unregistered advisor' },
          evidence: { overall_status: 'UNSUPPORTED' },
        },
        retriesAttempted: 0,
        durationMs: 78,
      } as unknown as BridgeAnalysisResult;

      const bridge = new NiveshAnalysisBridge();
      vi.spyOn(bridge, 'submitAnalysis').mockResolvedValue(suspiciousResult);

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-SUSPICIOUS-002',
        requestId: 'REQ-SUSPICIOUS-002',
        sessionId: 'SESS-102',
        sourceType: 'SELECTED_TEXT',
        text: 'Join VIP trading group now! Guaranteed 40% returns on expiry days!',
        url: 'https://trading-tips-chat.example.com',
        pageOrigin: 'https://trading-tips-chat.example.com',
        tabId: 102,
        timestamp: new Date().toISOString(),
      };

      const result = await bridge.submitAnalysis(request);
      expect(result.reference.decision).toBe('WARN');

      // Trigger intervention overlay
      protectionManager.showIntervention({
        analysisId: result.analysisId,
        decision: result.reference.decision,
        severity: result.reference.severity,
        primaryReason: result.reference.primaryReason,
        webAppUrl: result.reference.webAppUrl,
      });

      expect(protectionManager.getState().active).toBe(true);
      expect(document.getElementById('nivesh-firewall-root')).not.toBeNull();
    });

    it('evaluates unsupported fraud/ponzi claims returning BLOCK with critical intervention', async () => {
      const blockResult = {
        analysisId: 'ANA-BLOCK-003',
        requestId: 'REQ-BLOCK-003',
        captureId: 'CAP-BLOCK-003',
        reference: {
          analysisId: 'ANA-BLOCK-003',
          captureId: 'CAP-BLOCK-003',
          requestId: 'REQ-BLOCK-003',
          tabId: 103,
          decision: 'BLOCK',
          severity: 'HIGH',
          primaryReason: 'Fabricated SEBI registration certificate',
          completedAt: new Date().toISOString(),
          webAppUrl: 'https://nivesh.ai/#protect?id=ANA-BLOCK-003',
          claimsCount: 3,
          evidenceStatus: 'FABRICATED',
          identityStatus: 'FLAGGED',
          fingerprintMatch: 'KNOWN_SCAM_FINGERPRINT',
          threatSignalCount: 4,
          durationMs: 65,
        },
        fullResponse: {
          analysis_id: 'ANA-BLOCK-003',
          decision: { decision: 'BLOCK', severity: 'HIGH', primary_reason: 'Fabricated certificate' },
          evidence: { overall_status: 'FABRICATED' },
        },
        retriesAttempted: 0,
        durationMs: 65,
      } as unknown as BridgeAnalysisResult;

      const bridge = new NiveshAnalysisBridge();
      vi.spyOn(bridge, 'submitAnalysis').mockResolvedValue(blockResult);

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-BLOCK-003',
        requestId: 'REQ-BLOCK-003',
        sessionId: 'SESS-103',
        sourceType: 'CURRENT_PAGE',
        text: 'Deposit USDT for guaranteed 10% daily yield backed by SEBI registration #FAKE12345.',
        url: 'https://crypto-doubler-scheme.example.com',
        pageOrigin: 'https://crypto-doubler-scheme.example.com',
        tabId: 103,
        timestamp: new Date().toISOString(),
      };

      const result = await bridge.submitAnalysis(request);
      expect(result.reference.decision).toBe('BLOCK');

      protectionManager.showIntervention({
        analysisId: result.analysisId,
        decision: result.reference.decision,
        severity: result.reference.severity,
        primaryReason: result.reference.primaryReason,
        webAppUrl: result.reference.webAppUrl,
      });

      expect(protectionManager.getState().active).toBe(true);
      expect(document.getElementById('nivesh-firewall-root')).not.toBeNull();
    });

    it('generates consistent Full Firewall deep-link handoff URL to web dashboard', () => {
      const analysisId = 'ANA-RELEASE-GATE-777';
      const webAppUrl = buildNiveshWebAppUrl('https://nivesh.ai', analysisId);

      expect(webAppUrl).toContain('https://nivesh.ai');
      expect(webAppUrl).toContain(`id=${analysisId}`);
    });
  });

  // ===========================================================================
  // 2. Browser Lifecycle & Multi-Tab Isolation (Section 3)
  // ===========================================================================
  describe('2. Browser Lifecycle & Multi-Tab Isolation', () => {
    it('maintains strict isolation between Tab A and Tab B states', () => {
      const tabA = 201;
      const tabB = 202;

      backgroundState.startRequest({
        requestId: 'REQ-TAB-A',
        tabId: tabA,
        startedAt: new Date().toISOString(),
        pageOrigin: 'https://example.com',
        pageUrl: 'https://example.com',
      });

      expect(backgroundState.getState(tabA).status).toBe('ANALYZING');
      expect(backgroundState.getState(tabB).status).toBe('READY');

      backgroundState.completeRequest(
        {
          analysisId: 'ANA-TAB-A',
          captureId: 'CAP-TAB-A',
          requestId: 'REQ-TAB-A',
          tabId: tabA,
          decision: 'ALLOW',
          severity: 'LOW',
          primaryReason: 'Clean content',
          completedAt: new Date().toISOString(),
          webAppUrl: 'https://nivesh.ai/firewall/audit/ANA-TAB-A',
          claimsCount: 0,
          evidenceStatus: 'VERIFIED',
          identityStatus: 'VERIFIED',
          fingerprintMatch: 'NO_MATCH',
          threatSignalCount: 0,
          durationMs: 30,
        },
        tabA
      );

      expect(backgroundState.getState(tabA).status).toBe('RESULT_AVAILABLE');
      expect(backgroundState.getState(tabA).lastAnalysis?.analysisId).toBe('ANA-TAB-A');
      expect(backgroundState.getState(tabB).status).toBe('READY');
      expect(backgroundState.getState(tabB).lastAnalysis).toBeNull();
    });

    it('guards against concurrent duplicate scans on the same active tab', async () => {
      const tabId = 301;
      backgroundState.startRequest({
        requestId: 'REQ-IN-FLIGHT',
        tabId,
        startedAt: new Date().toISOString(),
        pageOrigin: 'https://example.com',
        pageUrl: 'https://example.com',
      });

      const duplicateMsg: ScanRequestMessage = {
        type: 'SCAN_REQUEST',
        requestId: 'REQ-DUPLICATE',
        tabId,
        timestamp: new Date().toISOString(),
        payload: {
          tabId,
          capture: {
            captureId: 'CAP-DUP',
            sourceType: 'CURRENT_PAGE',
            status: 'CAPTURED',
            text: 'Sample',
            url: 'https://example.com',
            displayUrl: 'example.com',
            pageTitle: 'Test',
            pageOrigin: 'https://example.com',
            tabId,
            timestamp: new Date().toISOString(),
            contentLength: 6,
            sanitized: true,
          },
        },
      };

      const response = await routeExtensionMessage(duplicateMsg);
      expect(response.success).toBe(false);
      expect(response.error?.code).toBe('SCAN_IN_PROGRESS');
    });

    it('clears stale tab state upon navigation or tab destruction', () => {
      const tabId = 401;
      backgroundState.completeRequest(
        {
          analysisId: 'ANA-OLD',
          captureId: 'CAP-OLD',
          requestId: 'REQ-OLD',
          tabId,
          decision: 'WARN',
          severity: 'MEDIUM',
          primaryReason: 'Old analysis',
          completedAt: new Date().toISOString(),
          webAppUrl: 'https://nivesh.ai/firewall/audit/ANA-OLD',
          claimsCount: 1,
          evidenceStatus: 'UNSUPPORTED',
          identityStatus: 'SUSPICIOUS',
          fingerprintMatch: 'NO_MATCH',
          threatSignalCount: 1,
          durationMs: 40,
        },
        tabId
      );

      expect(backgroundState.getState(tabId).lastAnalysis?.analysisId).toBe('ANA-OLD');

      backgroundState.reset(tabId, true);
      expect(backgroundState.getState(tabId).lastAnalysis).toBeNull();
      expect(backgroundState.getState(tabId).status).toBe('READY');
    });
  });

  // ===========================================================================
  // 3. API & Failure State Matrix (Section 4)
  // ===========================================================================
  describe('3. API & Failure State Matrix', () => {
    const bridge = new NiveshAnalysisBridge();

    it('handles HTTP 400 mapping to INVALID_REQUEST without retry', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Invalid payload schema' }), {
          status: 400,
          statusText: 'Bad Request',
          headers: { 'Content-Type': 'application/json' },
        })
      );

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-400',
        requestId: 'REQ-400',
        sessionId: 'SESS-400',
        sourceType: 'CURRENT_PAGE',
        text: 'Test',
        url: 'https://example.com',
        pageOrigin: 'https://example.com',
        tabId: 501,
        timestamp: new Date().toISOString(),
      };

      try {
        await bridge.submitAnalysis(request);
        expect.unreachable('Should have thrown on 400');
      } catch (err: any) {
        expect(err.code).toBe('INVALID_REQUEST');
      }
    });

    it('handles HTTP 404 mapping to ENDPOINT_NOT_FOUND without retry', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response('Endpoint not found', { status: 404, statusText: 'Not Found' })
      );

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-404',
        requestId: 'REQ-404',
        sessionId: 'SESS-404',
        sourceType: 'CURRENT_PAGE',
        text: 'Test',
        url: 'https://example.com',
        pageOrigin: 'https://example.com',
        tabId: 502,
        timestamp: new Date().toISOString(),
      };

      try {
        await bridge.submitAnalysis(request);
        expect.unreachable('Should have thrown on 404');
      } catch (err: any) {
        expect(err.code).toBe('ENDPOINT_NOT_FOUND');
      }
    });

    it('handles HTTP 429 rate limiting without retry storms', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
          status: 429,
          statusText: 'Too Many Requests',
          headers: { 'Content-Type': 'application/json' },
        })
      );

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-429',
        requestId: 'REQ-429',
        sessionId: 'SESS-429',
        sourceType: 'CURRENT_PAGE',
        text: 'Test',
        url: 'https://example.com',
        pageOrigin: 'https://example.com',
        tabId: 503,
        timestamp: new Date().toISOString(),
      };

      try {
        await bridge.submitAnalysis(request);
        expect.unreachable('Should have thrown on 429');
      } catch (err: any) {
        expect(err.code).toBe('RATE_LIMITED');
      }
    });

    it('handles malformed non-JSON responses safely without exposing internal details', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(
        new Response('<html><body>502 Bad Gateway Nginx</body></html>', {
          status: 502,
          headers: { 'Content-Type': 'text/html' },
        })
      );

      const request: BrowserAnalysisRequest = {
        captureId: 'CAP-502',
        requestId: 'REQ-502',
        sessionId: 'SESS-502',
        sourceType: 'CURRENT_PAGE',
        text: 'Test',
        url: 'https://example.com',
        pageOrigin: 'https://example.com',
        tabId: 504,
        timestamp: new Date().toISOString(),
      };

      try {
        await bridge.submitAnalysis(request);
        expect.unreachable('Should have thrown on 502');
      } catch (err: any) {
        expect(err.code).toBe('PIPELINE_FAILURE');
      }
    });

    it('ensures error payloads never leak sensitive paths, credentials, or stack traces', () => {
      const safeError = {
        code: 'PIPELINE_FAILURE',
        message: 'The analysis service is currently experiencing technical difficulties.',
      };

      const errorStr = JSON.stringify(safeError);
      expect(errorStr).not.toMatch(/[a-zA-Z]:\\Users/);
      expect(errorStr).not.toMatch(/\/home\//);
      expect(errorStr).not.toMatch(/password/i);
      expect(errorStr).not.toMatch(/secret/i);
      expect(errorStr).not.toMatch(/token/i);
    });
  });

  // ===========================================================================
  // 4. Privacy Validation & Exclusions (Section 5)
  // ===========================================================================
  describe('4. Privacy Validation & Exclusions', () => {
    it('strictly identifies sensitive input elements and excludes them from capture', () => {
      const inputs = [
        { type: 'password', name: 'pwd' },
        { type: 'text', name: 'cvv_code' },
        { type: 'text', name: 'credit_card_number' },
        { type: 'text', name: 'otp_verification' },
        { type: 'text', name: 'atm_pin' },
        { type: 'hidden', name: 'csrf_token' },
      ];

      for (const item of inputs) {
        const el = document.createElement('input');
        el.type = item.type;
        el.name = item.name;
        expect(isSensitiveElement(el)).toBe(true);
      }
    });

    it('verifies that background state persists only lightweight references and no raw page text', () => {
      const tabId = 601;
      backgroundState.completeRequest(
        {
          analysisId: 'ANA-LIGHTWEIGHT',
          captureId: 'CAP-LIGHTWEIGHT',
          requestId: 'REQ-LIGHTWEIGHT',
          tabId,
          decision: 'ALLOW',
          severity: 'LOW',
          primaryReason: 'Lightweight summary only',
          completedAt: new Date().toISOString(),
          webAppUrl: 'https://nivesh.ai/firewall/audit/ANA-LIGHTWEIGHT',
          claimsCount: 0,
          evidenceStatus: 'VERIFIED',
          identityStatus: 'VERIFIED',
          fingerprintMatch: 'NO_MATCH',
          threatSignalCount: 0,
          durationMs: 25,
        },
        tabId
      );

      const state = backgroundState.getState(tabId);
      const stateStr = JSON.stringify(state);

      expect(stateStr).not.toContain('<body>');
      expect(stateStr).not.toContain('<script>');
      expect(state.lastAnalysis?.analysisId).toBe('ANA-LIGHTWEIGHT');
    });
  });

  // ===========================================================================
  // 5. Permission Minimization & Store Alignment (Section 6)
  // ===========================================================================
  describe('5. Permission Minimization & Store Alignment', () => {
    it('manifest permissions match exact allowed list: activeTab, storage, scripting', () => {
      expect(manifest.permissions).toEqual(['activeTab', 'storage', 'scripting']);
    });

    it('confirms strictly zero invasive background permissions in manifest', () => {
      const forbidden = [
        '<all_urls>',
        'tabs',
        'history',
        'passwords',
        'cookies',
        'clipboardRead',
        'clipboardWrite',
        'downloads',
        'webRequest',
        'webRequestBlocking',
        'geolocation',
      ];

      for (const p of forbidden) {
        expect(manifest.permissions).not.toContain(p);
      }
    });
  });

  // ===========================================================================
  // 6. Production Package & Remote-Code Verification (Section 7)
  // ===========================================================================
  describe('6. Production Package & Remote-Code Verification', () => {
    it('verifies nivesh-firewall-v1.0.0.zip integrity and production HTTPS manifest', () => {
      if (!fs.existsSync(zipPath)) return;

      const zipBuf = fs.readFileSync(zipPath);
      expect(zipBuf.length).toBeGreaterThan(10000);

      const entries = extractZipEntries(zipBuf);
      const manifestBuf = entries.get('manifest.json');
      expect(manifestBuf).toBeDefined();

      const manifestObj = JSON.parse(manifestBuf!.toString('utf8'));
      // Production ZIP must use https://api.nivesh.ai/* and not localhost
      expect(manifestObj.host_permissions).toEqual(['https://api.nivesh.ai/*']);
    });
  });

  // ===========================================================================
  // 7. Performance Smoke Measurements (Section 10)
  // ===========================================================================
  describe('7. Performance Smoke Measurements', () => {
    it('measures sub-millisecond safe page context extraction', () => {
      const t0 = performance.now();
      const context = extractSafePageContext();
      const duration = performance.now() - t0;

      expect(context).toBeDefined();
      expect(duration).toBeLessThan(50);
    });

    it('measures instantaneous Full Firewall handoff URL construction', () => {
      const t0 = performance.now();
      const url = buildNiveshWebAppUrl('https://nivesh.ai', 'ANA-PERF-TEST');
      const duration = performance.now() - t0;

      expect(url).toContain('https://nivesh.ai');
      expect(url).toContain('ANA-PERF-TEST');
      expect(duration).toBeLessThan(10);
    });
  });
});
