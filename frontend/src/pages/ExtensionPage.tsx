import React from 'react';
import { PublicLayout } from '../landing/components/PublicLayout';
import { PageHero } from '../landing/components/PageHero';
import { CallToAction } from '../landing/components/CallToAction';
import {
  XCircle,
  AlertCircle,
} from 'lucide-react';

export interface ExtensionPageProps {
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
}

export const ExtensionPage: React.FC<ExtensionPageProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  const extensionFlow = [
    { title: 'Active Webpage', desc: 'User encounters financial claim or investment solicitation' },
    { title: 'User Initiates', desc: 'Clicking "Analyze Page" triggers the extension' },
    { title: 'Content Extraction', desc: 'One-shot DOM text extraction of visible claims' },
    { title: 'Sanitization', desc: 'Automatic removal of passwords, OTPs & personal fields' },
    { title: 'Firewall API', desc: 'Secure evaluation across the 10 intelligence engines' },
    { title: 'Pre-Action Verdict', desc: 'Immediate intervention (ALLOW, WARN, PAUSE, BLOCK)' },
  ];

  return (
    <PublicLayout
      currentRoute="/extension"
      onNavigate={onNavigate}
      onOpenFirewall={onOpenFirewall}
    >
      {/* Page Hero */}
      <PageHero
        eyebrow="BROWSER EXTENSION"
        headline="Protection, where the decision happens."
        description="The Nivesh Firewall browser extension lets people initiate a protection check on financial content directly from the browser before taking a consequential action."
        primaryAction={{
          label: 'Open Firewall',
          onClick: onOpenFirewall,
        }}
        secondaryAction={{
          label: 'See How It Works',
          onClick: () => onNavigate('/how-it-works'),
        }}
      />

      {/* Engineering Release Status Banner */}
      <section style={{ maxWidth: '860px', margin: '0 auto 56px' }}>
        <div
          className="card-glass"
          style={{
            padding: '24px 28px',
            borderRadius: '16px',
            background: 'rgba(168, 85, 247, 0.08)',
            border: '1px solid rgba(168, 85, 247, 0.25)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '16px',
          }}
        >
          <div style={{ color: '#c084fc', marginTop: '2px' }}>
            <AlertCircle size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#c084fc', textTransform: 'uppercase' }}>
                Engineering Status
              </span>
              <span style={{ fontSize: '11px', padding: '1px 8px', borderRadius: '9999px', background: 'rgba(168, 85, 247, 0.2)', color: '#ffffff', fontWeight: 600 }}>
                Release Candidate
              </span>
            </div>
            <p style={{ fontSize: '14px', color: '#cbd5e1', lineHeight: 1.6 }}>
              Chrome Web Store submission preparation is complete (Manifest V3 audited, clean ZIP packaged). Public availability on the Chrome Web Store depends on production API deployment and store publication review. The web firewall remains fully operational for immediate manual inspections.
            </p>
          </div>
        </div>
      </section>

      {/* Extension Inspection Flow */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Execution Sequence
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            How In-Browser Verification Operates
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            The extension functions as an on-demand interface to the Nivesh protection layer, never as a persistent surveillance agent.
          </p>
        </div>

        <div
          className="card-glass"
          style={{
            padding: '40px 24px',
            maxWidth: '1000px',
            margin: '0 auto',
            background: 'rgba(20, 20, 20, 0.7)',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '16px', alignItems: 'center' }}>
            {extensionFlow.map((step, idx) => (
              <React.Fragment key={step.title}>
                <div style={{ textAlign: 'center', padding: '16px 8px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                  <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#a855f7', fontWeight: 700 }}>
                    STEP 0{idx + 1}
                  </span>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginTop: '6px' }}>{step.title}</p>
                  <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px', lineHeight: 1.3 }}>{step.desc}</p>
                </div>
                {idx < extensionFlow.length - 1 && (
                  <div style={{ textAlign: 'center', color: '#a855f7', fontSize: '14px' }}>&rarr;</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Non-Surveillance Guarantees */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Zero-Surveillance Guarantee
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            Strict Privacy Boundaries
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            Security software should never become spyware. Nivesh enforces technical barriers against invasive telemetry.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: '#f87171' }}>
              <XCircle size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff' }}>No Keystroke Surveillance</h4>
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              The extension registers zero keyboard event listeners. It never monitors what you type in search bars, forms, or passwords.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: '#f87171' }}>
              <XCircle size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff' }}>No Browsing History Logging</h4>
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              The extension does not track which domains you visit. Only the specific page you explicitly choose to analyze is inspected.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: '#f87171' }}>
              <XCircle size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff' }}>No Continuous Tab Monitoring</h4>
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              The extension remains dormant in the background until the user actively clicks the extension icon and submits the page.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', color: '#f87171' }}>
              <XCircle size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff' }}>Zero Credential Harvesting</h4>
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              Input fields of type password, OTP/PIN entries, and payment card numbers are automatically sanitized and excluded before analysis.
            </p>
          </div>
        </div>
      </section>

      {/* Permission Minimization Audit */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Audit &amp; Compliance
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            Minimized Manifest V3 Permissions
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            In compliance with the principle of least privilege, Nivesh requests only the minimum technical permissions required for on-demand analysis.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
          <div className="card-glass" style={{ padding: '28px', borderLeft: '3px solid #34d399' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#34d399' }}>
                activeTab
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              Grants temporary, one-time access to the current active tab only when the user explicitly clicks the extension popup.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px', borderLeft: '3px solid #34d399' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#34d399' }}>
                storage
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              Stores local user preferences (such as notification settings) and non-sensitive session cache locally in the browser.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px', borderLeft: '3px solid #34d399' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#34d399' }}>
                scripting
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              Injects an ephemeral content extraction script upon explicit request to parse visible text for atomic claim analysis.
            </p>
          </div>
        </div>

        <div
          style={{
            marginTop: '32px',
            padding: '20px',
            borderRadius: '12px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            textAlign: 'center',
            fontSize: '12px',
            color: '#94a3b8',
          }}
        >
          <strong style={{ color: '#ffffff' }}>Strictly Excluded:</strong> Nivesh does NOT request &lt;all_urls&gt;, history, cookies, webRequest, downloads, or clipboard access permissions.
        </div>
      </section>

      {/* Final CTA */}
      <CallToAction
        headline="Pre-action defense inside your browser."
        description="Experience the core firewall engine right now via the web console."
        primaryLabel="Launch Web Firewall"
        secondaryLabel="Read Privacy Architecture"
        onPrimaryClick={onOpenFirewall}
        onSecondaryClick={() => onNavigate('/privacy')}
      />
    </PublicLayout>
  );
};

export default ExtensionPage;
