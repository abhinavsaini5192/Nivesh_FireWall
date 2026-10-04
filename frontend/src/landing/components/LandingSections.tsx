import React from 'react';
import { Shield, Eye, Cpu, CheckCircle2, AlertTriangle, Database, ArrowRight, Lock, ExternalLink } from 'lucide-react';

const chromeWebstoreUrl =
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    ((import.meta.env as Record<string, string | undefined>).VITE_CHROME_WEBSTORE_URL || '')) ||
  '';

const ChromeIcon: React.FC<{ size?: number }> = ({ size = 16 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="4" />
    <line x1="21.17" y1="8" x2="12" y2="8" />
    <line x1="3.95" y1="6.06" x2="8.54" y2="14" />
    <line x1="10.88" y1="21.94" x2="15.46" y2="14" />
  </svg>
);

export interface LandingSectionsProps {
  onOpenFirewall: () => void;
  onNavigate?: (route: string) => void;
}

export const LandingSections: React.FC<LandingSectionsProps> = ({ onOpenFirewall, onNavigate }) => {
  return (
    <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
      
      {/* =================================================================== */}
      {/* 1. HOW IT WORKS SECTION */}
      {/* =================================================================== */}
      <section id="how-it-works" style={{ padding: '80px 0', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <div style={{ textAlign: 'center', marginBottom: '56px' }}>
          <span className="section-tag" style={{ marginBottom: '16px' }}>
            <span className="pulse-dot" />
            Four-Stage Defense Architecture
          </span>
          <h2 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginTop: '12px' }}>
            How Nivesh Firewall Protects You
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '640px', margin: '16px auto 0', fontSize: '15px', lineHeight: 1.6 }}>
            Operating strictly before consequential actions, Nivesh provides rigorous pre-transaction safety checks across 4 coordinated verification stages.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          {/* Stage 1 */}
          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(168, 85, 247, 0.12)', border: '1px solid rgba(168, 85, 247, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#c084fc' }}>
                <Eye size={20} />
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#a855f7', fontWeight: 600 }}>STAGE 01</span>
            </div>
            <h3 style={{ fontSize: '17px', fontWeight: 600, color: '#ffffff', marginBottom: '10px' }}>Observe Content</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              Inspects visible text, financial claims, and solicitations upon user invocation. Zero background monitoring or passive tracking.
            </p>
          </div>

          {/* Stage 2 */}
          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
                <Cpu size={20} />
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>STAGE 02</span>
            </div>
            <h3 style={{ fontSize: '17px', fontWeight: 600, color: '#ffffff', marginBottom: '10px' }}>Understand Intent</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              Dissects return promises, pressure tactics, and identifies requested actions: money transfers, APK downloads, or credential requests.
            </p>
          </div>

          {/* Stage 3 */}
          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#34d399' }}>
                <Database size={20} />
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#10b981', fontWeight: 600 }}>STAGE 03</span>
            </div>
            <h3 style={{ fontSize: '17px', fontWeight: 600, color: '#ffffff', marginBottom: '10px' }}>Verify Provenance</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              Validates claims against authoritative registers: SEBI registered entities, RBI unauthorized alert lists, and exchange filings.
            </p>
          </div>

          {/* Stage 4 */}
          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f87171' }}>
                <Shield size={20} />
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#ef4444', fontWeight: 600 }}>STAGE 04</span>
            </div>
            <h3 style={{ fontSize: '17px', fontWeight: 600, color: '#ffffff', marginBottom: '10px' }}>Pre-Action Intervene</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              Delivers policy verdicts (ALLOW, WARN, PAUSE, BLOCK) with clear reasoning to stop fraudulent actions before money leaves your account.
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '36px' }}>
          <a
            href="/how-it-works"
            onClick={(e) => {
              if (onNavigate) {
                e.preventDefault();
                onNavigate('/how-it-works');
              }
            }}
            className="btn-secondary-glass"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '9999px',
              fontSize: '13px',
              fontWeight: 500,
              textDecoration: 'none',
            }}
          >
            <span>Explore Complete 6-Stage Defense Workflow</span>
            <ArrowRight size={14} color="#c084fc" />
          </a>
        </div>
      </section>

      {/* =================================================================== */}
      {/* 2. FEATURES SECTION */}
      {/* =================================================================== */}
      <section id="features" style={{ padding: '80px 0', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <div style={{ textAlign: 'center', marginBottom: '56px' }}>
          <span className="section-tag" style={{ marginBottom: '16px' }}>
            Core Capabilities
          </span>
          <h2 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginTop: '12px' }}>
            Built for High-Stakes Financial Safety
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '640px', margin: '16px auto 0', fontSize: '15px', lineHeight: 1.6 }}>
            Technical verification systems designed to prevent digital financial deception without acting as an investment advisor or custodian.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          {/* Feature 1 */}
          <div className="card-glass" style={{ padding: '32px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#c084fc', marginBottom: '20px' }}>
              <Shield size={22} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#ffffff', marginBottom: '12px' }}>Pre-Action Intervention</h3>
            <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
              Unlike post-incident fraud reporting, Nivesh Firewall introduces calculated cognitive friction right before you wire funds, join an unverified group, or download an unverified trading tool.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="card-glass" style={{ padding: '32px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8', marginBottom: '20px' }}>
              <CheckCircle2 size={22} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#ffffff', marginBottom: '12px' }}>Authoritative Ground Truth</h3>
            <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
              Directly cross-checks claimed registration numbers against official regulatory databases (SEBI, RBI, exchanges) to flag forged credentials and imposter advisor identities.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="card-glass" style={{ padding: '32px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fbbf24', marginBottom: '20px' }}>
              <AlertTriangle size={22} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#ffffff', marginBottom: '12px' }}>Pattern & Fingerprint Matching</h3>
            <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
              Detects structural scam patterns: high-pressure Telegram trading channels, fake institutional task schemes, synthetic IPO allocations, and pyramid yield solicitations.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="card-glass" style={{ padding: '32px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#34d399', marginBottom: '20px' }}>
              <Lock size={22} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#ffffff', marginBottom: '12px' }}>Zero-Collection Privacy</h3>
            <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
              Strict privacy boundaries: zero passwords, zero OTPs, zero PINs, and zero keystroke surveillance. Content is analyzed ephemerally upon explicit user request only.
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '36px' }}>
          <a
            href="/features"
            onClick={(e) => {
              if (onNavigate) {
                e.preventDefault();
                onNavigate('/features');
              }
            }}
            className="btn-secondary-glass"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '9999px',
              fontSize: '13px',
              fontWeight: 500,
              textDecoration: 'none',
            }}
          >
            <span>Explore All 10 Intelligence Layers</span>
            <ArrowRight size={14} color="#c084fc" />
          </a>
        </div>
      </section>

      {/* =================================================================== */}
      {/* 3. SOURCES SECTION */}
      {/* =================================================================== */}
      <section id="sources" style={{ padding: '80px 0', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <div style={{ textAlign: 'center', marginBottom: '56px' }}>
          <span className="section-tag" style={{ marginBottom: '16px' }}>
            Authoritative Verification
          </span>
          <h2 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginTop: '12px' }}>
            Verified Against Official Registries
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '640px', margin: '16px auto 0', fontSize: '15px', lineHeight: 1.6 }}>
            Nivesh relies on primary regulatory records rather than speculative social sentiment.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
          <div className="card-glass" style={{ padding: '24px', textAlign: 'center' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>SEBI Registry</h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
              Registered Investment Advisors (RIA), Research Analysts (RA), and Broker verification.
            </p>
          </div>
          <div className="card-glass" style={{ padding: '24px', textAlign: 'center' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>RBI Sachet</h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
              Unauthorized deposit schemes, illegal forex platforms, and cautionary alerts.
            </p>
          </div>
          <div className="card-glass" style={{ padding: '24px', textAlign: 'center' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>NSE & BSE</h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
              Listed securities cross-checks, official trading announcements, and caution circulars.
            </p>
          </div>
          <div className="card-glass" style={{ padding: '24px', textAlign: 'center' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>Threat Intelligence</h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
              Known phishing domain fingerprints, fraudulent certificate hashes, and scam clusters.
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '36px' }}>
          <a
            href="/sources"
            onClick={(e) => {
              if (onNavigate) {
                e.preventDefault();
                onNavigate('/sources');
              }
            }}
            className="btn-secondary-glass"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '9999px',
              fontSize: '13px',
              fontWeight: 500,
              textDecoration: 'none',
            }}
          >
            <span>Inspect Statutory Verification Architecture</span>
            <ArrowRight size={14} color="#c084fc" />
          </a>
        </div>
      </section>

      {/* =================================================================== */}
      {/* 4. EXTENSION SECTION */}
      {/* =================================================================== */}
      <section id="extension" style={{ padding: '80px 0', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <div className="card-glass" style={{ padding: '48px 32px', textAlign: 'center', background: 'radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.12) 0%, rgba(18, 18, 18, 0.7) 100%)' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255, 255, 255, 0.06)', padding: '6px 16px', borderRadius: '9999px', fontSize: '12px', color: '#c084fc', marginBottom: '24px' }}>
            <ChromeIcon size={16} />
            <span>Chrome Manifest V3 Extension Ready</span>
          </div>

          <h2 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginBottom: '16px' }}>
            Inspect Content Directly in Your Browser
          </h2>
          <p style={{ color: '#cbd5e1', maxWidth: '600px', margin: '0 auto 32px', fontSize: '15px', lineHeight: 1.6 }}>
            Install Nivesh Firewall for one-click in-page claim inspections and pre-action safety alerts before financial commitments.
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
            <a
              href={chromeWebstoreUrl || '#'}
              onClick={(e) => {
                if (!chromeWebstoreUrl) {
                  e.preventDefault();
                  alert('The Nivesh Chrome Web Store package is built and submission-ready. Store publication is pending public backend deployment.');
                }
              }}
              className="btn-primary-white"
              style={{
                padding: '12px 24px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <ChromeIcon size={16} />
              Add to Chrome
              <ExternalLink size={14} />
            </a>

            <button
              type="button"
              onClick={onOpenFirewall}
              className="btn-secondary-glass"
              style={{
                padding: '12px 24px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: 500,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              Launch Web Firewall
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </section>

    </div>
  );
};
