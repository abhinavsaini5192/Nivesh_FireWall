import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import App from '../App';
import {
  HowItWorksPage,
  FeaturesPage,
  SourcesPage,
  ExtensionPage,
  AboutPage,
  PrivacyPage,
} from '../pages';

describe('Nivesh Firewall — Public Website Pages & Routing Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // =========================================================================
  // 1. Direct Page Component Tests
  // =========================================================================

  describe('1. Individual Page Integrity & Content Verification', () => {
    it('/how-it-works: renders 6-stage workflow sequence from Observe to Remember', () => {
      const handleNavigate = vi.fn();
      const handleOpenFirewall = vi.fn();

      render(
        <HowItWorksPage
          onNavigate={handleNavigate}
          onOpenFirewall={handleOpenFirewall}
        />
      );

      // Hero
      expect(screen.getByText('HOW IT WORKS')).toBeInTheDocument();
      expect(screen.getByText('Protection starts before the transaction.')).toBeInTheDocument();

      // All 6 Stages present
      expect(screen.getByText('Stage 01')).toBeInTheDocument();
      expect(screen.getByText('Observe Content')).toBeInTheDocument();
      expect(screen.getByText('Stage 02')).toBeInTheDocument();
      expect(screen.getByText(/Understand Intent & Claims/i)).toBeInTheDocument();
      expect(screen.getByText('Stage 03')).toBeInTheDocument();
      expect(screen.getByText(/Verify Against Authoritative Sources/i)).toBeInTheDocument();
      expect(screen.getByText('Stage 04')).toBeInTheDocument();
      expect(screen.getByText(/Trace the Action Progression Path/i)).toBeInTheDocument();
      expect(screen.getByText('Stage 05')).toBeInTheDocument();
      expect(screen.getByText(/Intervene Before Consequential Harm/i)).toBeInTheDocument();
      expect(screen.getByText('Stage 06')).toBeInTheDocument();
      expect(screen.getByText(/Remember Privately/i)).toBeInTheDocument();

      // Policy Badges: ALLOW, INFORM, WARN, PAUSE, BLOCK
      expect(screen.getByText('ALLOW')).toBeInTheDocument();
      expect(screen.getByText('INFORM')).toBeInTheDocument();
      expect(screen.getByText('WARN')).toBeInTheDocument();
      expect(screen.getByText('PAUSE')).toBeInTheDocument();
      expect(screen.getByText('BLOCK')).toBeInTheDocument();

      // Authoritative sources referenced
      expect(screen.getByText('SEBI Registry')).toBeInTheDocument();
      expect(screen.getByText('RBI Sachet')).toBeInTheDocument();
      expect(screen.getByText('NSE Registry')).toBeInTheDocument();
      expect(screen.getByText('BSE Circulars')).toBeInTheDocument();
    });

    it('/features: renders all ten intelligence engines in numbered editorial sequence', () => {
      render(
        <FeaturesPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      expect(screen.getByText('CAPABILITIES')).toBeInTheDocument();
      expect(screen.getByText('Ten layers of intelligence. One protection system.')).toBeInTheDocument();

      // Verify all 10 engine capabilities are present
      expect(screen.getByText('Content Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Claim Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Action Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Source Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Evidence Verification')).toBeInTheDocument();
      expect(screen.getByText('Threat & Attack-Path Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Scam Fingerprint Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Policy & Intervention')).toBeInTheDocument();
      expect(screen.getByText('Identity Verification')).toBeInTheDocument();
      expect(screen.getByText('Behavioural Signals')).toBeInTheDocument();

      // Epistemic humility principle
      expect(screen.getByText('The Philosophy of Epistemic Humility')).toBeInTheDocument();
    });

    it('/sources: renders SEBI, RBI, NSE, BSE and the full 6-stage provenance model', () => {
      render(
        <SourcesPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      expect(screen.getByText('AUTHORITATIVE SOURCES')).toBeInTheDocument();
      expect(screen.getByText('Evidence should have a source.')).toBeInTheDocument();

      // 4 Statutory Sources
      expect(screen.getByText('SEBI')).toBeInTheDocument();
      expect(screen.getByText('Securities and Exchange Board of India')).toBeInTheDocument();
      expect(screen.getByText('RBI')).toBeInTheDocument();
      expect(screen.getByText('Reserve Bank of India')).toBeInTheDocument();
      expect(screen.getByText('NSE')).toBeInTheDocument();
      expect(screen.getByText('National Stock Exchange of India')).toBeInTheDocument();
      expect(screen.getByText('BSE')).toBeInTheDocument();
      expect(screen.getByText('Bombay Stock Exchange')).toBeInTheDocument();

      // Lineage stages
      expect(screen.getByText('The Provenance Verification Path')).toBeInTheDocument();
      expect(screen.getByText('Claim')).toBeInTheDocument();
      expect(screen.getByText('Source Routing')).toBeInTheDocument();
      expect(screen.getByText('Retrieval')).toBeInTheDocument();
      expect(screen.getByText('Normalization')).toBeInTheDocument();
      expect(screen.getByText('Provenance')).toBeInTheDocument();
      expect(screen.getByText('Evidence Result')).toBeInTheDocument();

      // Critical Humility Principles
      expect(screen.getByText(/No match does not automatically mean fraud/i)).toBeInTheDocument();
      expect(screen.getByText(/Restrictions do not prove authorship/i)).toBeInTheDocument();
      expect(screen.getByText(/Source availability is part of the result/i)).toBeInTheDocument();
    });

    it('/extension: renders extension flow, privacy boundaries, permissions, and Release Candidate status', () => {
      render(
        <ExtensionPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      expect(screen.getByText('BROWSER EXTENSION')).toBeInTheDocument();
      expect(screen.getByText('Protection, where the decision happens.')).toBeInTheDocument();

      // Accurate Release Candidate Status
      expect(screen.getByText('Release Candidate')).toBeInTheDocument();
      expect(screen.getByText(/Chrome Web Store submission preparation is complete/i)).toBeInTheDocument();

      // Strict Non-Surveillance Boundaries
      expect(screen.getByText('No Keystroke Surveillance')).toBeInTheDocument();
      expect(screen.getByText('No Browsing History Logging')).toBeInTheDocument();
      expect(screen.getByText('No Continuous Tab Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Zero Credential Harvesting')).toBeInTheDocument();

      // Minimized Permissions
      expect(screen.getByText('activeTab')).toBeInTheDocument();
      expect(screen.getByText('storage')).toBeInTheDocument();
      expect(screen.getByText('scripting')).toBeInTheDocument();
      expect(screen.getByText(/Strictly Excluded:/i)).toBeInTheDocument();
    });

    it('/about: explains public-good mission, core philosophy, and what Nivesh is not', () => {
      render(
        <AboutPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      expect(screen.getByText('ABOUT NIVESH')).toBeInTheDocument();
      expect(screen.getByText('A protection layer for the moment before action.')).toBeInTheDocument();

      // Philosophies
      expect(screen.getByText('Protection over Prediction')).toBeInTheDocument();
      expect(screen.getByText('Evidence over Persuasion')).toBeInTheDocument();
      expect(screen.getByText('Verification over Authority')).toBeInTheDocument();
      expect(screen.getByText('Action Awareness over Topic Detection')).toBeInTheDocument();
      expect(screen.getByText('Privacy over Surveillance')).toBeInTheDocument();

      // What Nivesh Is Not
      expect(screen.getByText('What Nivesh Firewall Is Not')).toBeInTheDocument();
      expect(screen.getByText('Not a stockbroker or securities dealer')).toBeInTheDocument();
      expect(screen.getByText('Not an investment advisory or portfolio manager')).toBeInTheDocument();
      expect(screen.getByText('Not a market prediction or stock-picking engine')).toBeInTheDocument();

      // Editorial Mission Statement
      expect(screen.getByText(/The goal is not to tell people what to invest in/i)).toBeInTheDocument();
    });

    it('/privacy: details 7 privacy principles and collective intelligence boundary', () => {
      render(
        <PrivacyPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      expect(screen.getByText('PRIVACY ARCHITECTURE')).toBeInTheDocument();
      expect(screen.getByText('Protection without unnecessary surveillance.')).toBeInTheDocument();

      // Core Privacy Principles
      expect(screen.getByText('User-Initiated Analysis')).toBeInTheDocument();
      expect(screen.getByText('Minimal Extraction')).toBeInTheDocument();
      expect(screen.getByText('Sensitive Data Exclusion')).toBeInTheDocument();
      expect(screen.getByText('No Keystroke Surveillance')).toBeInTheDocument();
      expect(screen.getByText('No Browsing-History Surveillance')).toBeInTheDocument();
      expect(screen.getByText('No Continuous Tab Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Privacy-Preserving Collective Intelligence')).toBeInTheDocument();

      // Threat Intelligence Boundary
      expect(screen.getByText('How Collective Defense Preserves Privacy')).toBeInTheDocument();
    });
  });

  // =========================================================================
  // 2. Full App Routing Integration Tests
  // =========================================================================

  describe('2. Full App Multi-Page Routing Integration', () => {
    it('Routes to /how-it-works via history state and renders How It Works page', async () => {
      window.history.replaceState(null, '', '/how-it-works');

      await act(async () => {
        render(<App />);
      });

      expect(screen.getByText('Protection starts before the transaction.')).toBeInTheDocument();
      expect(screen.getByText('Stage 01')).toBeInTheDocument();
    });

    it('Routes to /features via history state and renders Features page', async () => {
      window.history.replaceState(null, '', '/features');

      await act(async () => {
        render(<App />);
      });

      expect(screen.getByText('Ten layers of intelligence. One protection system.')).toBeInTheDocument();
      expect(screen.getByText('Content Intelligence')).toBeInTheDocument();
    });

    it('Routes to /sources via history state and renders Sources page', async () => {
      window.history.replaceState(null, '', '/sources');

      await act(async () => {
        render(<App />);
      });

      expect(screen.getByText('Evidence should have a source.')).toBeInTheDocument();
      expect(screen.getByText('SEBI')).toBeInTheDocument();
    });

    it('Routes to /extension via history state and renders Extension page', async () => {
      window.history.replaceState(null, '', '/extension');

      await act(async () => {
        render(<App />);
      });

      expect(screen.getByText('Protection, where the decision happens.')).toBeInTheDocument();
      expect(screen.getByText('Release Candidate')).toBeInTheDocument();
    });

    it('Routes to /about via history state and renders About page', async () => {
      window.history.replaceState(null, '', '/about');

      await act(async () => {
        render(<App />);
      });

      expect(screen.getByText('A protection layer for the moment before action.')).toBeInTheDocument();
      expect(screen.getByText('Protection over Prediction')).toBeInTheDocument();
    });

    it('Routes to /privacy via history state and renders Privacy page', async () => {
      window.history.replaceState(null, '', '/privacy');

      await act(async () => {
        render(<App />);
      });

      expect(screen.getByText('Protection without unnecessary surveillance.')).toBeInTheDocument();
      expect(screen.getByText('User-Initiated Analysis')).toBeInTheDocument();
    });

    it('Navigates from /how-it-works to /firewall when clicking Open Firewall button', async () => {
      window.history.replaceState(null, '', '/how-it-works');

      await act(async () => {
        render(<App />);
      });

      const openButtons = screen.getAllByRole('button', { name: /Open Firewall/i });
      expect(openButtons.length).toBeGreaterThan(0);

      await act(async () => {
        fireEvent.click(openButtons[0]);
      });

      // App should transition to the core firewall dashboard
      expect(screen.getByText('Financial Content Protection Core')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Analyze Content/i })).toBeInTheDocument();
    });
  });

  // =========================================================================
  // 3. Content Integrity & Anti-Hallucination Guardrails
  // =========================================================================

  describe('3. Public Website Truthfulness & Boundary Guardrails', () => {
    it('Never displays banned keywords: Sellix, crypto trading schemes, pricing tables, testimonials', () => {
      const { container } = render(
        <FeaturesPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      const html = container.innerHTML.toLowerCase();
      expect(html).not.toContain('sellix');
      expect(html).not.toContain('pricing table');
      expect(html).not.toContain('100% scam detection');
      expect(html).not.toContain('guaranteed returns');
      expect(html).not.toContain('cryptocurrency');
    });

    it('Extension page does not claim Chrome Web Store live publication or fabricated download metrics', () => {
      const { container } = render(
        <ExtensionPage
          onNavigate={vi.fn()}
          onOpenFirewall={vi.fn()}
        />
      );

      const html = container.innerHTML;
      expect(html).not.toMatch(/10,000\+ users/i);
      expect(html).not.toMatch(/5-star rating/i);
      expect(html).not.toMatch(/Available on Chrome Web Store now/i);
      expect(html).not.toMatch(/Install now from store/i);
    });
  });
});
