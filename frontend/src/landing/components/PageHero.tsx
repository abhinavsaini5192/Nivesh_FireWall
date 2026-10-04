import React from 'react';

export interface PageHeroProps {
  eyebrow: string;
  headline: string | React.ReactNode;
  description: string;
  primaryAction?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
}

export const PageHero: React.FC<PageHeroProps> = ({
  eyebrow,
  headline,
  description,
  primaryAction,
  secondaryAction,
}) => {
  return (
    <section className="page-hero">
      {/* Eyebrow Label */}
      <div className="fade-in-delayed delay-nav" style={{ marginBottom: '20px' }}>
        <span className="section-tag">
          <span className="pulse-dot" />
          {eyebrow}
        </span>
      </div>

      {/* Main Page Headline */}
      <h1
        style={{
          fontSize: 'clamp(2.25rem, 5.5vw, 4.25rem)',
          fontWeight: 700,
          letterSpacing: '-0.035em',
          color: '#ffffff',
          lineHeight: 1.1,
          marginBottom: '20px',
        }}
      >
        {headline}
      </h1>

      {/* Supporting Description */}
      <p
        className="fade-in-delayed delay-sub"
        style={{
          maxWidth: '720px',
          margin: '0 auto',
          fontSize: 'clamp(1rem, 2vw, 1.2rem)',
          color: '#cbd5e1',
          fontWeight: 400,
          lineHeight: 1.65,
          marginBottom: primaryAction || secondaryAction ? '36px' : '0',
        }}
      >
        {description}
      </p>

      {/* Optional Hero Action Buttons */}
      {(primaryAction || secondaryAction) && (
        <div
          className="fade-in-delayed delay-cta"
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
          }}
        >
          {primaryAction && (
            <button
              type="button"
              onClick={primaryAction.onClick}
              className="btn-primary-white"
              style={{
                padding: '12px 26px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: 600,
                letterSpacing: '0.02em',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {primaryAction.label}
              <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          )}

          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="btn-secondary-glass"
              style={{
                padding: '12px 26px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: 500,
                letterSpacing: '0.02em',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {secondaryAction.label}
              <svg style={{ width: '14px', height: '14px', color: '#94a3b8' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          )}
        </div>
      )}
    </section>
  );
};
