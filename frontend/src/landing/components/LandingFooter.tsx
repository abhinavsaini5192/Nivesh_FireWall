import React from 'react';

export interface LandingFooterProps {
  onNavigate?: (route: string) => void;
  onOpenFirewall?: () => void;
}

export const LandingFooter: React.FC<LandingFooterProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  const handleLinkClick = (route: string) => {
    if (route === '/firewall' && onOpenFirewall) {
      onOpenFirewall();
      return;
    }
    if (onNavigate) {
      onNavigate(route);
    } else if (typeof window !== 'undefined') {
      window.location.pathname = route;
    }
  };

  return (
    <footer
      style={{
        position: 'relative',
        zIndex: 10,
        width: '100%',
        padding: '64px 24px 32px',
        maxWidth: '1280px',
        margin: '0 auto',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      }}
    >
      {/* 4-Column Editorial Footer Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '40px',
          marginBottom: '56px',
        }}
      >
        {/* Column 1: Brand & Mantra */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span
              style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#a855f7',
                boxShadow: '0 0 8px #a855f7',
              }}
            />
            <span style={{ fontSize: '14px', fontWeight: 700, letterSpacing: '0.12em', color: '#ffffff' }}>
              NIVESH FIREWALL
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.6, maxWidth: '280px' }}>
            Protect before you act. Public-good infrastructure to inspect claims and prevent financial deception.
          </p>
        </div>

        {/* Column 2: Product */}
        <div>
          <h4 style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#ffffff', marginBottom: '16px' }}>
            Product
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <li>
              <a
                href="/how-it-works"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/how-it-works');
                }}
                style={{ fontSize: '13px', color: '#94a3b8', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                How It Works
              </a>
            </li>
            <li>
              <a
                href="/features"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/features');
                }}
                style={{ fontSize: '13px', color: '#94a3b8', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                Features
              </a>
            </li>
            <li>
              <a
                href="/sources"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/sources');
                }}
                style={{ fontSize: '13px', color: '#94a3b8', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                Sources
              </a>
            </li>
            <li>
              <a
                href="/extension"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/extension');
                }}
                style={{ fontSize: '13px', color: '#94a3b8', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                Extension
              </a>
            </li>
          </ul>
        </div>

        {/* Column 3: Trust */}
        <div>
          <h4 style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#ffffff', marginBottom: '16px' }}>
            Trust
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <li>
              <a
                href="/about"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/about');
                }}
                style={{ fontSize: '13px', color: '#94a3b8', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                About Nivesh
              </a>
            </li>
            <li>
              <a
                href="/privacy"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/privacy');
                }}
                style={{ fontSize: '13px', color: '#94a3b8', textDecoration: 'none', transition: 'color 0.2s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                Privacy Architecture
              </a>
            </li>
          </ul>
        </div>

        {/* Column 4: Application */}
        <div>
          <h4 style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#ffffff', marginBottom: '16px' }}>
            Application
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <li>
              <a
                href="/firewall"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick('/firewall');
                }}
                style={{
                  fontSize: '13px',
                  color: '#c084fc',
                  fontWeight: 600,
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                Open Firewall &rarr;
              </a>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Bar: Protocol Status & Fiduciary Disclaimer */}
      <div
        style={{
          paddingTop: '24px',
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
      </div>
    </footer>
  );
};
