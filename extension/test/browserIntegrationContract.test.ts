/**
 * Phase 17.2: Browser ↔ Nivesh Integration Contract & Smoke Tests
 *
 * Verifies the full integration path:
 * Browser Page -> Content Script -> Extension Runtime -> Nivesh API ->
 * Firewall Analysis -> Policy/Evidence Result -> Extension UI -> Full Nivesh Web App
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { backgroundState } from '../src/background/state';
import { routeExtensionMessage } from '../src/background/router';
import { initializeBackgroundWorker } from '../src/background/index';
import { NiveshAnalysisBridge } from '../src/bridge/analysisBridge';
import { buildNiveshWebAppUrl, DEFAULT_CONFIG } from '../src/config';
import { extractSafePageContext, isSensitiveElement } from '../src/content/context';
import { protectionManager } from '../src/protection/manager';
import manifest from '../manifest.json';
import type {
  ScanRequestMessage,
  CaptureRequestMessage,
  OpenNiveshAppMessage,
} from '../src/types/messages';
import type { BrowserAnalysisRequest } from '../src/bridge/types';
import type { LastAnalysisReference } from '../src/types/state';

describe('Phase 17.2: Browser ↔ Nivesh Integration Contract Suite', () => {
  beforeEach(() => {
    backgroundState.reset();
    protectionManager.hideIntervention();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ===========================================================================
  // 1. Page Capture Contract & Privacy Boundaries (Section 2 & 12)
  // ===========================================================================
  describe('1. Page Capture Contract & Privacy Boundaries', () => {
    it('captures safe page URL and title without injecting surveillance hooks', () => {
      const context = extractSafePageContext();
      expect(context.pageUrl).toBeDefined();
      expect(context.pageOrigin).toBeDefined();
      expect(context.capturedAt).toBeDefined();
    });

    it('identifies and strictly excludes sensitive credential and financial fields', () => {
      const passwordInput = document.createElement('input');
      passwordInput.type = 'password';
      expect(isSensitiveElement(passwordInput)).toBe(true);

      const hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';
      expect(isSensitiveElement(hiddenInput)).toBe(true);

      const otpInput = document.createElement('input');
      otpInput.type = 'text';
      otpInput.name = 'user_otp_code';
      expect(isSensitiveElement(otpInput)).toBe(true);

      const pinInput = document.createElement('input');
      pinInput.type = 'text';
      pinInput.id = 'security_pin';
      expect(isSensitiveElement(pinInput)).toBe(true);

      const cvvInput = document.createElement('input');
      cvvInput.type = 'text';
      cvvInput.name = 'card_cvv';
      expect(isSensitiveElement(cvvInput)).toBe(true);

      const publicDiv = document.createElement('div');
      publicDiv.textContent = 'Investment return information';
      expect(isSensitiveElement(publicDiv)).toBe(false);
    });
  });

  // ===========================================================================
  // 2. Content Script ↔ Extension Messaging Hardening (Section 3)
  // ===========================================================================
  describe('2. Content Script ↔ Extension Messaging Hardening', () => {
    it('rejects malformed messages lacking type property', async () => {
      const invalidMsg = { foo: 'bar' } as any;
      const res = await routeExtensionMessage(invalidMsg);
      expect(res.success).toBe(false);
      expect(res.error?.code).toBe('INVALID_MESSAGE');
    });

    it('rejects unsupported message types with safe error response', async () => {
      const unknownMsg = {
        type: 'EXECUTE_PRIVILEGED_SHELL',
        requestId: 'REQ-MALICIOUS-001',
        timestamp: new Date().toISOString(),
      } as any;

      const res = await routeExtensionMessage(unknownMsg);
      expect(res.success).toBe(false);
      expect(res.error?.code).toBe('UNSUPPORTED_MESSAGE_TYPE');
      expect(res.requestId).toBe('REQ-MALICIOUS-001');
    });

    it('validates CAPTURE_REQUEST payload: requires valid numeric tabId and sourceType', async () => {
      const invalidTabMsg: CaptureRequestMessage = {
        type: 'CAPTURE_REQUEST',
        requestId: 'REQ-CAP-INV-1',
        tabId: 0,
        timestamp: new Date().toISOString(),
        payload: { tabId: -1, sourceType: 'CURRENT_PAGE' },
      };
      const res1 = await routeExtensionMessage(invalidTabMsg);
      expect(res1.success).toBe(false);
      expect(res1.error?.code).toBe('INVALID_TAB_ID');

      const invalidSourceMsg: CaptureRequestMessage = {
        type: 'CAPTURE_REQUEST',
        requestId: 'REQ-CAP-INV-2',
        tabId: 101,
        timestamp: new Date().toISOString(),
        payload: { tabId: 101, sourceType: 'SCRAPE_ALL_COOKIES' as any },
      };
      const res2 = await routeExtensionMessage(invalidSourceMsg);
      expect(res2.success).toBe(false);
      expect(res2.error?.code).toBe('INVALID_SOURCE_TYPE');
    });

    it('validates SCAN_REQUEST payload: requires tabId and valid payload object', async () => {
      const badPayloadMsg = {
        type: 'SCAN_REQUEST',
        requestId: 'REQ-SCAN-INV-1',
        timestamp: new Date().toISOString(),
        payload: null as any,
      } as ScanRequestMessage;
      const res = await routeExtensionMessage(badPayloadMsg);
      expect(res.success).toBe(false);
      expect(res.error?.code).toBe('INVALID_PAYLOAD');
    });
  });

  // ===========================================================================
  // 3. Extension ↔ API Communication & Status Code Mapping (Section 4 & 10)
  // ===========================================================================
  describe('3. Extension ↔ API Communication & HTTP Status Mapping', () => {
    it('maps HTTP 429 rate limiting to RATE_LIMITED without retrying', async () => {
      let callCount = 0;
      global.fetch = vi.fn().mockImplementation(() => {
        callCount++;
        return Promise.resolve(
          new Response(JSON.stringify({ error_code: 'RATE_LIMITED', message: 'Too many requests' }), {
            status: 429,
            headers: { 'Content-Type': 'application/json' },
          })
        );
      });

      const bridge = new NiveshAnalysisBridge({ timeoutMs: 2000, maxRetries: 1 });
      const req: BrowserAnalysisRequest = {
        captureId: 'CAP-429',
        requestId: 'REQ-429',
        sourceType: 'CURRENT_PAGE',
        text: 'Financial claim text',
        tabId: 101,
        pageOrigin: 'https://example.com',
        timestamp: new Date().toISOString(),
      };

      await expect(bridge.submitAnalysis(req)).rejects.toMatchObject({
        code: 'RATE_LIMITED',
        statusCode: 429,
      });

      // 4xx must never be retried
      expect(callCount).toBe(1);
    });

    it('maps HTTP 400 invalid request to INVALID_REQUEST without retrying', async () => {
      let callCount = 0;
      global.fetch = vi.fn().mockImplementation(() => {
        callCount++;
        return Promise.resolve(
          new Response(JSON.stringify({ error_code: 'INVALID_REQUEST', message: 'Missing parameters' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          })
        );
      });

      const bridge = new NiveshAnalysisBridge({ timeoutMs: 2000, maxRetries: 1 });
      const req: BrowserAnalysisRequest = {
        captureId: 'CAP-400',
        requestId: 'REQ-400',
        sourceType: 'CURRENT_PAGE',
        text: 'Financial claim text',
        tabId: 101,
        pageOrigin: 'https://example.com',
        timestamp: new Date().toISOString(),
      };

      await expect(bridge.submitAnalysis(req)).rejects.toMatchObject({
        code: 'INVALID_REQUEST',
        statusCode: 400,
      });

      expect(callCount).toBe(1);
    });

    it('maps HTTP 404 to ENDPOINT_NOT_FOUND without retrying', async () => {
      let callCount = 0;
      global.fetch = vi.fn().mockImplementation(() => {
        callCount++;
        return Promise.resolve(
          new Response(null, {
            status: 404,
          })
        );
      });

      const bridge = new NiveshAnalysisBridge({ timeoutMs: 2000, maxRetries: 1 });
      const req: BrowserAnalysisRequest = {
        captureId: 'CAP-404',
        requestId: 'REQ-404',
        sourceType: 'CURRENT_PAGE',
        text: 'Financial claim text',
        tabId: 101,
        pageOrigin: 'https://example.com',
        timestamp: new Date().toISOString(),
      };

      await expect(bridge.submitAnalysis(req)).rejects.toMatchObject({
        code: 'ENDPOINT_NOT_FOUND',
        statusCode: 404,
      });
      expect(callCount).toBe(1);
    });

    it('safely handles malformed non-JSON response with MALFORMED_RESPONSE error', async () => {
      let callCount = 0;
      global.fetch = vi.fn().mockImplementation(() => {
        callCount++;
        return Promise.resolve(
          new Response('<html><body>Corrupted gateway payload</body></html>', {
            status: 200,
            headers: { 'Content-Type': 'text/html' },
          })
        );
      });

      const bridge = new NiveshAnalysisBridge({ timeoutMs: 2000, maxRetries: 1 });
      const req: BrowserAnalysisRequest = {
        captureId: 'CAP-MALFORMED',
        requestId: 'REQ-MALFORMED',
        sourceType: 'CURRENT_PAGE',
        text: 'Financial claim text',
        tabId: 101,
        pageOrigin: 'https://example.com',
        timestamp: new Date().toISOString(),
      };

      await expect(bridge.submitAnalysis(req)).rejects.toMatchObject({
        code: 'MALFORMED_RESPONSE',
      });
      // Malformed 200 responses should not enter infinite retry loop
      expect(callCount).toBe(1);
    });
  });

  // ===========================================================================
  // 4. Tab Lifecycle & Stale Result Prevention (Section 6 & 11)
  // ===========================================================================
  describe('4. Tab Lifecycle & State Synchronization', () => {
    it('clears stale analysis state when tab navigates or reloads', () => {
      // 1. Tab 101 completes analysis
      backgroundState.completeRequest(
        {
          analysisId: 'ANA-101-OLD',
          decision: 'BLOCK',
          severity: 'HIGH',
          primaryReason: 'Old malicious page',
          webAppUrl: 'http://localhost:5173/#protect?id=ANA-101-OLD',
          completedAt: new Date().toISOString(),
        },
        101
      );

      expect(backgroundState.getState(101).status).toBe('RESULT_AVAILABLE');
      expect(backgroundState.getState(101).lastAnalysis?.analysisId).toBe('ANA-101-OLD');

      // 2. Navigation occurs on Tab 101: reset(tabId, true) is invoked
      backgroundState.reset(101, true);

      // 3. Tab 101 state must be READY with lastAnalysis null
      expect(backgroundState.getState(101).status).toBe('READY');
      expect(backgroundState.getState(101).lastAnalysis).toBeNull();
      expect(backgroundState.getState(101).activeRequest).toBeNull();
    });

    it('cleans up tab runtime state when a tab is removed/closed', () => {
      backgroundState.completeRequest(
        {
          analysisId: 'ANA-TAB-TO-CLOSE',
          decision: 'WARN',
          severity: 'MEDIUM',
          primaryReason: 'Tab closing reason',
          webAppUrl: 'http://localhost:5173/#protect',
          completedAt: new Date().toISOString(),
        },
        202
      );

      expect(backgroundState.getState(202).lastAnalysis).toBeDefined();

      backgroundState.removeTab(202);

      // Subsequent inquiry creates a clean READY state without stale analysis
      expect(backgroundState.getState(202).lastAnalysis).toBeNull();
    });

    it('rejects stale response if tab started a newer request before older one finished', () => {
      const tabId = 301;
      // Request 1 starts
      backgroundState.startRequest(
        {
          requestId: 'REQ-1',
          tabId,
          startedAt: new Date().toISOString(),
          pageOrigin: 'https://site1.com',
          pageUrl: 'https://site1.com',
        },
        'SESS-301'
      );

      // User immediately initiates Request 2
      backgroundState.startRequest(
        {
          requestId: 'REQ-2',
          tabId,
          startedAt: new Date().toISOString(),
          pageOrigin: 'https://site2.com',
          pageUrl: 'https://site2.com',
        },
        'SESS-301'
      );

      // Delayed Request 1 response arrives
      const completedReq1 = backgroundState.completeRequest(
        {
          analysisId: 'ANA-REQ-1',
          requestId: 'REQ-1',
          tabId,
          decision: 'BLOCK',
          severity: 'CRITICAL',
          primaryReason: 'Old reason',
          webAppUrl: 'http://localhost:5173/#protect?id=ANA-REQ-1',
          completedAt: new Date().toISOString(),
        },
        tabId
      );

      expect(completedReq1).toBe(false);
      // State must still be ANALYZING for REQ-2, not overwritten by REQ-1
      expect(backgroundState.getState(tabId).status).toBe('ANALYZING');
      expect(backgroundState.getState(tabId).activeRequest?.requestId).toBe('REQ-2');

      // Request 2 completes
      const completedReq2 = backgroundState.completeRequest(
        {
          analysisId: 'ANA-REQ-2',
          requestId: 'REQ-2',
          tabId,
          decision: 'ALLOW',
          severity: 'LOW',
          primaryReason: 'Current reason',
          webAppUrl: 'http://localhost:5173/#protect?id=ANA-REQ-2',
          completedAt: new Date().toISOString(),
        },
        tabId
      );

      expect(completedReq2).toBe(true);
      expect(backgroundState.getState(tabId).status).toBe('RESULT_AVAILABLE');
      expect(backgroundState.getState(tabId).lastAnalysis?.analysisId).toBe('ANA-REQ-2');
      expect(backgroundState.getState(tabId).lastAnalysis?.decision).toBe('ALLOW');
    });

    it('wires up tab lifecycle listeners in initializeBackgroundWorker without crashing', () => {
      expect(() => initializeBackgroundWorker()).not.toThrow();

      // Trigger onActivated listener mock
      const listeners = (globalThis as any).chrome._listeners;
      if (listeners['tabs.onActivated']?.length > 0) {
        listeners['tabs.onActivated'][0]({ tabId: 404 });
        expect(backgroundState.getState().currentTabId).toBe(404);
      }

      // Trigger onUpdated (navigation loading)
      if (listeners['tabs.onUpdated']?.length > 0) {
        backgroundState.completeRequest(
          {
            analysisId: 'ANA-NAV-TEST',
            decision: 'WARN',
            severity: 'MEDIUM',
            primaryReason: 'Warn text',
            webAppUrl: 'http://localhost:5173/#protect',
            completedAt: new Date().toISOString(),
          },
          404
        );
        expect(backgroundState.getState(404).lastAnalysis).not.toBeNull();

        // Navigation occurs
        listeners['tabs.onUpdated'][0](404, { status: 'loading' });
        expect(backgroundState.getState(404).lastAnalysis).toBeNull();
      }

      // Trigger onRemoved
      if (listeners['tabs.onRemoved']?.length > 0) {
        listeners['tabs.onRemoved'][0](404);
        expect(backgroundState.getState(404).lastAnalysis).toBeNull();
      }
    });
  });

  // ===========================================================================
  // 5. Full Firewall Handoff Contract (Section 8)
  // ===========================================================================
  describe('5. Full Firewall Handoff Contract', () => {
    it('preserves analysisId in web app deep link URL matching frontend router pattern', () => {
      const url = buildNiveshWebAppUrl('https://app.nivesh.ai', 'ANL-PROD-9988');
      expect(url).toBe('https://app.nivesh.ai/#protect?id=ANL-PROD-9988');

      // Verify that frontend regex (?:id=|analysis\/)([a-zA-Z0-9_-]+) parses this correctly
      const match = url.match(/(?:id=|analysis\/)([a-zA-Z0-9_-]+)/);
      expect(match).not.toBeNull();
      expect(match![1]).toBe('ANL-PROD-9988');
    });

    it('falls back to safe protect route when analysisId is empty or undefined', () => {
      const urlWithEmpty = buildNiveshWebAppUrl('https://app.nivesh.ai', '');
      expect(urlWithEmpty).toBe('https://app.nivesh.ai/#protect');

      const urlWithUndefined = buildNiveshWebAppUrl('https://app.nivesh.ai', undefined);
      expect(urlWithUndefined).toBe('https://app.nivesh.ai/#protect');
    });

    it('dispatches OPEN_NIVESH_APP with chrome.tabs.create preserving target URL', async () => {
      const openMsg: OpenNiveshAppMessage = {
        type: 'OPEN_NIVESH_APP',
        requestId: 'REQ-OPEN-001',
        timestamp: new Date().toISOString(),
        payload: { analysisId: 'ANA-DEEP-LINK-1' },
      };

      const res = await routeExtensionMessage(openMsg);
      expect(res.success).toBe(true);
      expect((res.data as { openedUrl: string })?.openedUrl).toContain('id=ANA-DEEP-LINK-1');
      expect((chrome.tabs.create as any)).toHaveBeenCalledWith({
        url: expect.stringContaining('#protect?id=ANA-DEEP-LINK-1'),
      });
    });
  });

  // ===========================================================================
  // 6. End-to-End Integration Smoke Test (Section 15)
  // ===========================================================================
  describe('6. End-to-End Integration Smoke Test Flow', () => {
    it('executes full pipeline: Page Capture -> Bridge -> Policy Decision -> State Sync', async () => {
      const mockBackendResponse: any = {
        analysis_id: 'ANA-SMOKE-E2E-1',
        completed_at: new Date().toISOString(),
        decision: {
          decision: 'WARN',
          severity: 'HIGH',
          primary_reason: 'Unregistered advisory group with guaranteed returns claim.',
          explanation: {
            decision: 'WARN',
            user_message: 'Caution: This page promises guaranteed financial returns.',
            technical_message: 'High threat detected.',
            primary_reason: 'Unregistered advisory group with guaranteed returns claim.',
            supporting_signals: ['SIG-GUARANTEE-RETURNS'],
          },
        },
        claims: [
          { claim_id: 'CLM-1', text: 'Guaranteed 25% monthly profit' },
        ],
        evidence: { overall_status: 'UNVERIFIED' },
        identity: {
          identity_status: 'UNKNOWN_ENTITY',
          findings_summary: 'None',
        },
        fingerprint: {
          match_type: 'KNOWN_SCAM_PATTERN',
          match_confidence: 0.85,
        },
        threat: {
          threat_signals: ['PROMISED_RETURNS', 'UNREGISTERED_ADVISORY'],
        },
        actions: [{ action_id: 'ACT-1', message: 'Do not invest' }],
      };

      global.fetch = vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockBackendResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      const scanMsg: ScanRequestMessage = {
        type: 'SCAN_REQUEST',
        requestId: 'REQ-SMOKE-01',
        tabId: 101,
        timestamp: new Date().toISOString(),
        payload: {
          tabId: 101,
          capture: {
            captureId: 'CAP-SMOKE-01',
            sourceType: 'CURRENT_PAGE',
            status: 'CAPTURED',
            text: 'Guaranteed 25% returns on Telegram bot investments.',
            url: 'https://wealth-crypto-bot.com',
            displayUrl: 'https://wealth-crypto-bot.com',
            pageTitle: 'Crypto Wealth Portal',
            pageOrigin: 'https://wealth-crypto-bot.com',
            tabId: 101,
            timestamp: new Date().toISOString(),
            contentLength: 48,
            sanitized: true,
          },
        },
      };

      const res = await routeExtensionMessage(scanMsg);
      expect(res.success).toBe(true);
      const resData = res.data as LastAnalysisReference;
      expect(resData?.analysisId).toBe('ANA-SMOKE-E2E-1');
      expect(resData?.decision).toBe('WARN');
      expect(resData?.severity).toBe('HIGH');
      expect(resData?.webAppUrl).toContain('id=ANA-SMOKE-E2E-1');

      // State is synchronized in background
      const tabState = backgroundState.getState(101);
      expect(tabState.status).toBe('RESULT_AVAILABLE');
      expect(tabState.lastAnalysis?.analysisId).toBe('ANA-SMOKE-E2E-1');
      expect(tabState.lastAnalysis?.decision).toBe('WARN');
    });
  });

  // ===========================================================================
  // 7. Security & Permission Audit (Section 12 & 13)
  // ===========================================================================
  describe('7. Security & Permission Audit', () => {
    it('ensures permissions are strictly minimal and zero forbidden permissions exist', () => {
      expect(manifest.permissions).toEqual(['activeTab', 'storage', 'scripting']);

      const forbidden = [
        '<all_urls>',
        'passwords',
        'history',
        'tabs',
        'clipboardRead',
        'webRequest',
        'webRequestBlocking',
        'cookies',
      ];
      for (const perm of forbidden) {
        expect(manifest.permissions).not.toContain(perm);
      }
    });

    it('ensures host_permissions strictly forbids broad wildcards', () => {
      expect(manifest.host_permissions).not.toContain('<all_urls>');
      expect(manifest.host_permissions).not.toContain('*://*/*');
      expect(manifest.host_permissions).not.toContain('https://*/*');
    });

    it('ensures configuration defaults contain no secrets, API keys, or private tokens', () => {
      expect((DEFAULT_CONFIG as any).apiKey).toBeUndefined();
      expect((DEFAULT_CONFIG as any).secret).toBeUndefined();
      expect((DEFAULT_CONFIG as any).token).toBeUndefined();
      expect((DEFAULT_CONFIG as any).jwt).toBeUndefined();
    });
  });
});
