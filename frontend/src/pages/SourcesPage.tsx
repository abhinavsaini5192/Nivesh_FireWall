import React from 'react';
import { PublicLayout } from '../landing/components/PublicLayout';
import { PageHero } from '../landing/components/PageHero';
import { CallToAction } from '../landing/components/CallToAction';


export interface SourcesPageProps {
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
}

export const SourcesPage: React.FC<SourcesPageProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  const sources = [
    {
      code: 'SEBI',
      name: 'Securities and Exchange Board of India',
      role: 'Intermediary Accreditation & Regulatory Enforcement',
      description:
        'Serves as the primary statutory authority for verifying Registered Investment Advisors (RIA), Research Analysts (RA), registered stockbrokers, mutual fund distributors, and public regulatory enforcement orders.',
      records: ['RIA Accreditation Lists', 'Research Analyst Registers', 'Order & Debarment Records'],
    },
    {
      code: 'RBI',
      name: 'Reserve Bank of India',
      role: 'Banking, Currency & Deposit Protection',
      description:
        'Provides statutory validation for regulated commercial banks, non-banking financial companies (NBFCs), payment system operators, and unauthorized deposit alerts through the RBI Sachet portal.',
      records: ['Sachet Caution Alerts', 'NBFC Master Registers', 'Authorized Payment Operators'],
    },
    {
      code: 'NSE',
      name: 'National Stock Exchange of India',
      role: 'Securities Exchange Listings & Trading Members',
      description:
        'Cross-references claimed listed securities, official trading announcements, authorized trading members, and public investor caution circulars.',
      records: ['Listed Equities Database', 'Authorized Member Directory', 'Investor Caution Bulletins'],
    },
    {
      code: 'BSE',
      name: 'Bombay Stock Exchange',
      role: 'Corporate Filings & Listed Securities',
      description:
        'Authenticates corporate announcements, security identifiers, listed entity disclosures, and broker-dealer membership credentials.',
      records: ['Corporate Disclosures', 'Trading Member Verifications', 'Public Notice Archive'],
    },
  ];

  const provenanceSteps = [
    { label: 'Claim', desc: 'Atomic factual assertion extracted' },
    { label: 'Source Routing', desc: 'Matched to appropriate regulator' },
    { label: 'Retrieval', desc: 'Secure cached canonical lookup' },
    { label: 'Normalization', desc: 'Standardized entity resolution' },
    { label: 'Provenance', desc: 'Audit trail & freshness check' },
    { label: 'Evidence Result', desc: 'Granular status generated' },
  ];

  return (
    <PublicLayout
      currentRoute="/sources"
      onNavigate={onNavigate}
      onOpenFirewall={onOpenFirewall}
    >
      {/* Page Hero */}
      <PageHero
        eyebrow="AUTHORITATIVE SOURCES"
        headline="Evidence should have a source."
        description="Nivesh verifies financial claims and identity-related references against authoritative sources whenever relevant evidence is available."
        primaryAction={{
          label: 'Open Firewall',
          onClick: onOpenFirewall,
        }}
        secondaryAction={{
          label: 'Review Privacy',
          onClick: () => onNavigate('/privacy'),
        }}
      />

      {/* The Four Statutory Sources */}
      <section className="editorial-block" style={{ borderTop: 'none', paddingTop: 0 }}>
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginBottom: '12px' }}>
            Primary Regulatory Registers
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            Nivesh relies on primary regulatory records rather than speculative social sentiment or arbitrary user votes.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
          {sources.map((s) => (
            <div key={s.code} className="card-glass" style={{ padding: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <span
                  style={{
                    fontSize: '18px',
                    fontWeight: 800,
                    letterSpacing: '0.08em',
                    color: '#ffffff',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {s.code}
                </span>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#a855f7', fontWeight: 600 }}>
                  STATUTORY SOURCE
                </span>
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>{s.name}</h3>
              <p style={{ fontSize: '12px', color: '#c084fc', marginBottom: '14px', fontWeight: 500 }}>{s.role}</p>
              <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, marginBottom: '20px' }}>{s.description}</p>
              <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '16px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Coverage Records:
                </span>
                <ul style={{ listStyle: 'none', padding: 0, marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {s.records.map((rec) => (
                    <li key={rec} style={{ fontSize: '12px', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: '#a855f7' }}>&bull;</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Provenance Pipeline Model */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Data Lineage
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            The Provenance Verification Path
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            Every piece of evidence carries an auditable trace from initial claim extraction through authoritative query to verdict determination.
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
            {provenanceSteps.map((step, idx) => (
              <React.Fragment key={step.label}>
                <div style={{ textAlign: 'center', padding: '16px 8px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                  <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#a855f7', fontWeight: 700 }}>
                    STAGE 0{idx + 1}
                  </span>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginTop: '6px' }}>{step.label}</p>
                  <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px', lineHeight: 1.3 }}>{step.desc}</p>
                </div>
                {idx < provenanceSteps.length - 1 && (
                  <div style={{ textAlign: 'center', color: '#a855f7', fontSize: '14px' }}>&rarr;</div>
                )}
              </React.Fragment>
            ))}
          </div>

          <div style={{ marginTop: '36px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '24px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginBottom: '12px', textAlign: 'center' }}>
              Granular Evidence States Handled
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '12px' }}>
              <span className="flow-node" style={{ padding: '8px 14px', fontSize: '12px' }}>Supported</span>
              <span className="flow-node" style={{ padding: '8px 14px', fontSize: '12px' }}>Partially Supported</span>
              <span className="flow-node" style={{ padding: '8px 14px', fontSize: '12px' }}>Contradicted</span>
              <span className="flow-node" style={{ padding: '8px 14px', fontSize: '12px' }}>Insufficient Evidence</span>
              <span className="flow-node" style={{ padding: '8px 14px', fontSize: '12px' }}>Source Unavailable</span>
              <span className="flow-node" style={{ padding: '8px 14px', fontSize: '12px' }}>Source Conflict</span>
            </div>
          </div>
        </div>
      </section>

      {/* Critical Humility Callouts */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 40px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Truth Over Persuasion
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            Core Evidence Principles
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            Nivesh avoids overstating certainty. Evidence evaluation requires clear distinctions between absence of proof and proof of fraud.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          <div className="card-glass" style={{ padding: '28px', borderLeft: '3px solid #38bdf8' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
              No match does not automatically mean fraud.
            </h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              A newly formed private partnership, personal arrangement, or unindexed entity may not appear in statutory registers. Absence of an RIA record indicates an unverified advisory claim, not necessarily criminal deception.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px', borderLeft: '3px solid #fbbf24' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
              Restrictions do not prove authorship.
            </h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              Imposters frequently copy legitimate advisor names and genuine registration numbers. A regulatory restriction or verified license proves registry status, but does not prove the person messaging you is that individual.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px', borderLeft: '3px solid #a855f7' }}>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
              Source availability is part of the result.
            </h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6 }}>
              If a statutory registry is undergoing maintenance or network latency, Nivesh explicitly flags the source as unavailable rather than fabricating an assumption or guessing the entity&rsquo;s standing.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <CallToAction
        headline="Verify claims before taking action."
        description="Cross-reference advisor credentials, return claims, and solicitations against statutory records."
        primaryLabel="Open Firewall"
        secondaryLabel="Review Privacy Architecture"
        onPrimaryClick={onOpenFirewall}
        onSecondaryClick={() => onNavigate('/privacy')}
      />
    </PublicLayout>
  );
};

export default SourcesPage;
