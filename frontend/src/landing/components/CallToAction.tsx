import React from 'react';

export interface CallToActionProps {
  eyebrow?: string;
  headline: string;
  description?: string;
  primaryLabel?: string;
  secondaryLabel?: string;
  onPrimaryClick: () => void;
  onSecondaryClick?: () => void;
}

export const CallToAction: React.FC<CallToActionProps> = ({
  eyebrow = 'Pre-Action Intervention',
  headline,
  description = 'Protection works best before the irreversible step. Inspect any financial content, claim, or communication in seconds.',
  primaryLabel = 'Open Firewall',
  secondaryLabel,
  onPrimaryClick,
  onSecondaryClick,
}) => {
  return (
    <section style={{ padding: '80px 0 20px', width: '100%' }}>
      <div
        className="card-glass"
        style={{
          padding: '56px 32px',
          textAlign: 'center',
          background: 'radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.14) 0%, rgba(18, 18, 18, 0.8) 100%)',
          border: '1px solid rgba(168, 85, 247, 0.25)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
        }}
      >
        {eyebrow && (
          <div style={{ marginBottom: '16px' }}>
            <span className="section-tag">
              <span className="pulse-dot" />
              {eyebrow}
            </span>
          </div>
        )}

        <h2
          style={{
            fontSize: 'clamp(1.75rem, 4vw, 2.75rem)',
            fontWeight: 700,
            letterSpacing: '-0.025em',
            color: '#ffffff',
            maxWidth: '680px',
            margin: '0 auto 16px',
            lineHeight: 1.2,
          }}
        >
          {headline}
        </h2>

        {description && (
          <p
            style={{
              color: '#cbd5e1',
              maxWidth: '620px',
              margin: '0 auto 36px',
              fontSize: '15px',
              lineHeight: 1.6,
            }}
          >
            {description}
          </p>
        )}

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
          }}
        >
          <button
            type="button"
            onClick={onPrimaryClick}
            className="btn-primary-white"
            style={{
              padding: '14px 28px',
              borderRadius: '9999px',
              fontSize: '13px',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {primaryLabel}
            <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </button>

          {secondaryLabel && onSecondaryClick && (
            <button
              type="button"
              onClick={onSecondaryClick}
              className="btn-secondary-glass"
              style={{
                padding: '14px 28px',
                borderRadius: '9999px',
                fontSize: '13px',
                fontWeight: 500,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {secondaryLabel}
              <svg style={{ width: '14px', height: '14px', color: '#94a3b8' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </section>
  );
};
