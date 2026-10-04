import React from 'react';

export interface LandingHeroProps {
  onOpenFirewall: () => void;
  onExploreHowItWorks: () => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({
  onOpenFirewall,
  onExploreHowItWorks,
}) => {
  return (
    <section
      id="product"
      style={{
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '64px 20px',
        textAlign: 'center',
        maxWidth: '1024px',
        margin: '0 auto',
        width: '100%',
        minHeight: 'calc(100vh - 180px)',
      }}
    >
      {/* Protocol Badge */}
      <div className="fade-in-delayed delay-nav" style={{ marginBottom: '24px' }}>
        <span className="section-tag">
          <span className="pulse-dot" />
          Pre-Action Financial Defense Protocol
        </span>
      </div>

      {/* Headline: Staggered line reveal animation */}
      <h1
        style={{
          fontSize: 'clamp(2.5rem, 7vw, 5.25rem)',
          fontWeight: 700,
          letterSpacing: '-0.035em',
          color: '#ffffff',
          userSelect: 'none',
          lineHeight: 1.08,
          marginBottom: '24px',
        }}
      >
        <span className="ln">
          <span className="ln-i">Protect before</span>
        </span>
        <span className="ln">
          <span className="ln-i">you act.</span>
        </span>
      </h1>

      {/* Subtitle: Centered explanatory paragraph */}
      <p
        className="fade-in-delayed delay-sub"
        style={{
          maxWidth: '680px',
          fontSize: 'clamp(1rem, 2vw, 1.25rem)',
          color: '#cbd5e1',
          fontWeight: 400,
          lineHeight: 1.6,
          marginBottom: '36px',
        }}
      >
        Nivesh Firewall analyzes financial content, verifies claims, traces requested actions, and helps you make a safer decision before it becomes consequential.
      </p>

      {/* Action Buttons: Primary White & Secondary Dark Glass */}
      <div
        className="fade-in-delayed delay-cta"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          width: '100%',
        }}
      >
        <button
          type="button"
          onClick={onOpenFirewall}
          className="btn-primary-white"
          style={{
            padding: '14px 28px',
            borderRadius: '9999px',
            fontSize: '14px',
            fontWeight: 600,
            letterSpacing: '0.02em',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
          }}
        >
          Open Firewall
          <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.25">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </button>

        <button
          type="button"
          onClick={onExploreHowItWorks}
          className="btn-secondary-glass"
          style={{
            padding: '14px 28px',
            borderRadius: '9999px',
            fontSize: '14px',
            fontWeight: 500,
            letterSpacing: '0.02em',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          How It Works
          <svg style={{ width: '16px', height: '16px', color: '#94a3b8' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.25">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </button>
      </div>
    </section>
  );
};
