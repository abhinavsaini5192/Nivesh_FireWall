import React from 'react';
import { PublicLayout } from '../landing/components/PublicLayout';
import { PageHero } from '../landing/components/PageHero';
import { CallToAction } from '../landing/components/CallToAction';
import { XCircle } from 'lucide-react';

export interface AboutPageProps {
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
}

export const AboutPage: React.FC<AboutPageProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  const philosophies = [
    {
      title: 'Protection over Prediction',
      desc: 'Nivesh does not forecast stock market directions, cryptocurrency prices, or trading yields. Our mission is strictly defensive: identifying deception and preventing unauthorized financial extraction before money leaves your control.',
    },
    {
      title: 'Evidence over Persuasion',
      desc: 'Marketing claims, professional logos, and emotional urgency are irrelevant without verifiable evidence. Nivesh evaluates claims against public statutory registries rather than charisma or persuasive language.',
    },
    {
      title: 'Verification over Authority',
      desc: 'Claiming an affiliation with SEBI, a major bank, or an institutional desk is never accepted as proof. Verification requires cross-referencing against primary registers to prevent imposter fraud.',
    },
    {
      title: 'Action Awareness over Topic Detection',
      desc: 'Financial discussions are not inherently hazardous. What matters is the action path: is the user being pushed into joining private channels, installing unverified APKs, or wiring funds to individual accounts?',
    },
    {
      title: 'Privacy over Surveillance',
      desc: 'Collective threat intelligence must never come at the cost of personal surveillance. Nivesh isolates abstract structural deception patterns while discarding personal identity records and financial credentials.',
    },
  ];

  const whatWeAreNot = [
    'Not a stockbroker or securities dealer',
    'Not an investment advisory or portfolio manager',
    'Not an algorithmic trading or yield system',
    'Not a cryptocurrency exchange or custodial wallet',
    'Not a market prediction or stock-picking engine',
    'Not a commercial financial product distributor',
  ];

  return (
    <PublicLayout
      currentRoute="/about"
      onNavigate={onNavigate}
      onOpenFirewall={onOpenFirewall}
    >
      {/* Page Hero */}
      <PageHero
        eyebrow="ABOUT NIVESH"
        headline="A protection layer for the moment before action."
        description="Nivesh Firewall is public-good infrastructure designed to help people recognize dangerous financial-content pathways before those pathways become consequential."
        primaryAction={{
          label: 'Open Firewall',
          onClick: onOpenFirewall,
        }}
        secondaryAction={{
          label: 'Review Principles',
          onClick: () => {
            const el = document.getElementById('philosophy');
            if (el && typeof el.scrollIntoView === 'function') {
              el.scrollIntoView({ behavior: 'smooth' });
            }
          },
        }}
      />

      {/* Core Philosophy Section */}
      <section id="philosophy" className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 48px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Guiding Values
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            The Nivesh Philosophy
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            Modern digital financial fraud exploits the gap between persuasion and transaction. Our architectural decisions prioritize objectivity, user dignity, and zero-compromise safety.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '900px', margin: '0 auto' }}>
          {philosophies.map((p, idx) => (
            <div
              key={p.title}
              className="card-glass"
              style={{
                padding: '28px 32px',
                borderLeft: '3px solid #a855f7',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#c084fc', fontWeight: 700 }}>
                  0{idx + 1}
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#ffffff' }}>
                  {p.title}
                </h3>
              </div>
              <p style={{ fontSize: '14px', color: '#cbd5e1', lineHeight: 1.65 }}>
                {p.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* What Nivesh Is Not */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 40px' }}>
          <span className="section-tag" style={{ marginBottom: '12px' }}>
            Clear Boundaries
          </span>
          <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', margin: '8px 0 12px' }}>
            What Nivesh Firewall Is Not
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6 }}>
            To prevent conflicts of interest and maintain public trust, Nivesh strictly avoids investment advice, execution, or commercial financial promotion.
          </p>
        </div>

        <div
          className="card-glass"
          style={{
            padding: '36px',
            maxWidth: '820px',
            margin: '0 auto',
            background: 'rgba(20, 20, 20, 0.7)',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {whatWeAreNot.map((item) => (
              <div key={item} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: '#f87171' }}>
                <XCircle size={16} />
                <span style={{ color: '#cbd5e1' }}>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Concluding Mission Statement */}
      <section style={{ maxWidth: '860px', margin: '64px auto 0', textAlign: 'center' }}>
        <blockquote
          style={{
            fontSize: 'clamp(1.25rem, 3vw, 1.75rem)',
            fontWeight: 600,
            color: '#ffffff',
            lineHeight: 1.5,
            letterSpacing: '-0.02em',
            fontStyle: 'normal',
            borderLeft: 'none',
            padding: '0 20px',
          }}
        >
          &ldquo;The goal is not to tell people what to invest in. The goal is to help them recognize when someone is trying to push them toward a dangerous action.&rdquo;
        </blockquote>
      </section>

      {/* Final CTA */}
      <CallToAction
        headline="Experience the pre-action firewall."
        description="Public-good defense architecture designed to safeguard your financial decisions."
        primaryLabel="Open Firewall"
        secondaryLabel="Explore How It Works"
        onPrimaryClick={onOpenFirewall}
        onSecondaryClick={() => onNavigate('/how-it-works')}
      />
    </PublicLayout>
  );
};

export default AboutPage;
