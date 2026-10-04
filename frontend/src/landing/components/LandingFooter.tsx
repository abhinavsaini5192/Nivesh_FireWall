import React from 'react';

export const LandingFooter: React.FC = () => {
  return (
    <footer
      style={{
        position: 'relative',
        zIndex: 10,
        width: '100%',
        padding: '24px 20px',
        maxWidth: '1280px',
        margin: '0 auto',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        fontSize: '11px',
        color: '#94a3b8',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: '#34d399',
            boxShadow: '0 0 6px #34d399',
          }}
        />
        <span style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Pre-Transaction Defense Protocol Active
        </span>
      </div>

      <div
        style={{
          letterSpacing: '0.12em',
          color: '#94a3b8',
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: '11px',
        }}
      >
        Observe &bull; Understand &bull; Verify &bull; Trace &bull; Intervene
      </div>

      <div style={{ color: '#64748b' }}>
        &copy; 2025 Nivesh Firewall. Non-custodial infrastructure.
      </div>
    </footer>
  );
};
