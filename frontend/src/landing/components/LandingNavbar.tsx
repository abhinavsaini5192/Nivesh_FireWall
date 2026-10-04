import React, { useState } from 'react';

export interface LandingNavbarProps {
  onOpenFirewall: () => void;
}

export const LandingNavbar: React.FC<LandingNavbarProps> = ({ onOpenFirewall }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen((prev) => !prev);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  const handleNavClick = (sectionId: string) => {
    closeMobileMenu();
    const el = document.getElementById(sectionId);
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header
      className="fade-in-delayed delay-nav"
      style={{
        position: 'relative',
        zIndex: 30,
        width: '100%',
        padding: '16px 20px',
        maxWidth: '1280px',
        margin: '0 auto',
      }}
    >
      <nav
        className="nav-glass"
        style={{
          borderRadius: '9999px',
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
        }}
        aria-label="Main Landing Navigation"
      >
        {/* Wordmark Identity: NIVESH FIREWALL */}
        <a
          href="#product"
          onClick={(e) => {
            e.preventDefault();
            handleNavClick('product');
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            textDecoration: 'none',
            outline: 'none',
          }}
        >
          <span
            style={{
              letterSpacing: '0.16em',
              textTransform: 'uppercase',
              fontWeight: 700,
              fontSize: '15px',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
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
            NIVESH <span style={{ fontWeight: 400, color: 'rgba(255, 255, 255, 0.8)' }}>FIREWALL</span>
          </span>
        </a>

        {/* Centered Navigation Links */}
        <div
          className="desktop-nav-links"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '32px',
            fontSize: '13px',
            letterSpacing: '0.02em',
            color: '#cbd5e1',
            fontWeight: 500,
          }}
        >
          <button
            type="button"
            onClick={() => handleNavClick('product')}
            style={{ background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer', padding: '4px 0' }}
          >
            Product
          </button>
          <button
            type="button"
            onClick={() => handleNavClick('how-it-works')}
            style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px 0' }}
          >
            How It Works
          </button>
          <button
            type="button"
            onClick={() => handleNavClick('features')}
            style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px 0' }}
          >
            Features
          </button>
          <button
            type="button"
            onClick={() => handleNavClick('sources')}
            style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px 0' }}
          >
            Sources
          </button>
          <button
            type="button"
            onClick={() => handleNavClick('extension')}
            style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', padding: '4px 0' }}
          >
            Extension
          </button>
        </div>

        {/* Right Side Actions */}
        <div className="desktop-actions" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            type="button"
            onClick={onOpenFirewall}
            className="btn-secondary-glass"
            style={{
              fontSize: '12px',
              fontWeight: 600,
              padding: '10px 18px',
              borderRadius: '9999px',
              letterSpacing: '0.02em',
            }}
          >
            Open Firewall
          </button>
          <button
            type="button"
            onClick={onOpenFirewall}
            className="btn-primary-white"
            style={{
              fontSize: '12px',
              fontWeight: 600,
              padding: '10px 18px',
              borderRadius: '9999px',
              letterSpacing: '0.02em',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            Get Started
            <svg
              style={{ width: '14px', height: '14px' }}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </button>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          type="button"
          onClick={toggleMobileMenu}
          aria-expanded={mobileMenuOpen}
          aria-controls="mobile-menu-drawer"
          aria-label="Toggle navigation menu"
          className="mobile-menu-toggle"
          style={{
            background: 'none',
            border: 'none',
            padding: '8px',
            color: '#cbd5e1',
            cursor: 'pointer',
          }}
        >
          {mobileMenuOpen ? (
            <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          id="mobile-menu-drawer"
          className="nav-glass"
          style={{
            marginTop: '12px',
            borderRadius: '24px',
            padding: '24px',
            fontSize: '14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          }}
        >
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontWeight: 500 }}>
            <button
              type="button"
              onClick={() => handleNavClick('product')}
              style={{ background: 'none', border: 'none', color: '#ffffff', textAlign: 'left', padding: '8px', cursor: 'pointer' }}
            >
              Product
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('how-it-works')}
              style={{ background: 'none', border: 'none', color: '#cbd5e1', textAlign: 'left', padding: '8px', cursor: 'pointer' }}
            >
              How It Works
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('features')}
              style={{ background: 'none', border: 'none', color: '#cbd5e1', textAlign: 'left', padding: '8px', cursor: 'pointer' }}
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('sources')}
              style={{ background: 'none', border: 'none', color: '#cbd5e1', textAlign: 'left', padding: '8px', cursor: 'pointer' }}
            >
              Sources
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('extension')}
              style={{ background: 'none', border: 'none', color: '#cbd5e1', textAlign: 'left', padding: '8px', cursor: 'pointer' }}
            >
              Extension
            </button>
          </nav>
          <div style={{ height: '1px', backgroundColor: 'rgba(255, 255, 255, 0.1)', margin: '4px 0' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              type="button"
              onClick={() => {
                closeMobileMenu();
                onOpenFirewall();
              }}
              className="btn-secondary-glass"
              style={{ textAlign: 'center', fontWeight: 500, fontSize: '13px', padding: '12px', borderRadius: '9999px' }}
            >
              Open Firewall
            </button>
            <button
              type="button"
              onClick={() => {
                closeMobileMenu();
                onOpenFirewall();
              }}
              className="btn-primary-white"
              style={{
                textAlign: 'center',
                fontWeight: 600,
                fontSize: '13px',
                padding: '12px',
                borderRadius: '9999px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              Get Started
              <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
