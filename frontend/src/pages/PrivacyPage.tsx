import React from 'react';
import { PublicLayout } from '../landing/components/PublicLayout';
import { PageHero } from '../landing/components/PageHero';
import { CallToAction } from '../landing/components/CallToAction';


export interface PrivacyPageProps {
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
}

export const PrivacyPage: React.FC<PrivacyPageProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  const principles = [
    {
      title: 'User-Initiated Analysis',
      tag: 'CONTROL',
      desc: 'Content evaluation occurs exclusively when you submit text, paste a URL, or click "Analyze Page" in the extension. Nivesh never performs unprompted background scraping or passive network monitoring.',
    },
    {
      title: 'Minimal Extraction',
      tag: 'MINIMIZATION',
      desc: 'Only the text and link attributes necessary to deconstruct atomic claims and identify requested user actions are analyzed. Extraneous webpage scripts, cookies, session storage, and DOM nodes are ignored.',
    },
    {
      title: 'Sensitive Data Exclusion',
      tag: 'SANITIZATION',
      desc: 'Form inputs for passwords, one-time passwords (OTPs), multi-factor authentication (MFA) codes, CVVs, credit/debit card numbers, bank account credentials, and Aadhaar/PAN cards are automatically detected and redacted prior to pipeline analysis.',
    },
    {
      title: 'No Keystroke Surveillance',
      tag: 'SECURITY',
      desc: 'Nivesh contains zero keylogging or input event monitoring code. What you type in other tabs, search engines, password managers, or private messaging applications remains strictly inaccessible.',
    },
    {
      title: 'No Browsing-History Surveillance',
      tag: 'PRIVACY',
      desc: 'The firewall does not catalog visited URLs or compile user navigation histories. There is no session cross-referencing between the financial content you inspect and your wider browsing behavior.',
    },
    {
      title: 'No Continuous Tab Monitoring',
      tag: 'ISOLATION',
      desc: 'The browser extension operates with strictly minimized Manifest V3 permissions (activeTab, storage, scripting) and remains dormant until explicitly invoked on the active tab.',
    },
    {
      title: 'Privacy-Preserving Collective Intelligence',
      tag: 'DEFENSE',
      desc: 'Discovered deception structures contribute to community protection without exposing personal victim details. Scam fingerprints store structural transition vectors while stripping all names, contact details, and private content.',
    },
  ];

  return (
    <PublicLayout
      currentRoute="/privacy"
      onNavigate={onNavigate}
      onOpenFirewall={onOpenFirewall}
    >
      {/* Page Hero */}
      <PageHero
        eyebrow="PRIVACY ARCHITECTURE"
        headline="Protection without unnecessary surveillance."
        description="Nivesh Firewall is designed to analyze user-initiated financial content while minimizing collection of sensitive information."
        primaryAction={{
          label: 'Open Firewall',
          onClick: onOpenFirewall,
        }}
        secondaryAction={{
          label: 'Inspect Sources',
          onClick: () => onNavigate('/sources'),
        }}
      />

      {/* Seven Privacy Principles Sequence */}
      <section className="editorial-block" style={{ borderTop: 'none', paddingTop: 0 }}>
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginBottom: '12px' }}>
            Core Privacy Commitments
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            These principles are technically enforced throughout our browser extension, API gateway, and backend analysis pipelines.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '900px', margin: '0 auto' }}>
          {principles.map((pr, idx) => (
            <div
              key={pr.title}
              className="card-glass"
              style={{
                padding: '28px 32px',
                borderLeft: '3px solid #34d399',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#34d399', fontWeight: 700 }}>
                  0{idx + 1} &bull; {pr.tag}
                </span>
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
                {pr.title}
              </h3>
              <p style={{ fontSize: '14px', color: '#cbd5e1', lineHeight: 1.65 }}>
                {pr.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Transparency & Collective Intelligence */}
      <section className="editorial-block">
        <div
          className="card-glass"
          style={{
            padding: '40px',
            maxWidth: '900px',
            margin: '0 auto',
            background: 'rgba(20, 20, 20, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <span className="section-tag" style={{ marginBottom: '16px' }}>
            Threat Intelligence Boundary
          </span>
          <h3 style={{ fontSize: '22px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 16px' }}>
            How Collective Defense Preserves Privacy
          </h3>
          <p style={{ fontSize: '15px', color: '#cbd5e1', lineHeight: 1.7, marginBottom: '16px' }}>
            Nivesh turns discovered structural scam patterns into reusable intelligence without treating people&rsquo;s private credentials or identity data as the product.
          </p>
          <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.65 }}>
            When a novel deception campaign is identified, our fingerprint engine indexes the abstract transition path (e.g., social invite &rarr; fake trading simulator &rarr; individual UPI payment handle request) rather than the victim&rsquo;s identity or conversation context. Other users benefit from immediate pattern recognition without ever sharing or viewing private data.
          </p>
        </div>
      </section>

      {/* Final CTA */}
      <CallToAction
        headline="Privacy-preserving pre-action security."
        description="Verify any financial claim with complete confidence in technical privacy protections."
        primaryLabel="Open Firewall"
        secondaryLabel="Review Authoritative Sources"
        onPrimaryClick={onOpenFirewall}
        onSecondaryClick={() => onNavigate('/sources')}
      />
    </PublicLayout>
  );
};

export default PrivacyPage;
