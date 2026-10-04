import React, { useState } from 'react';
import { Shield, Menu, X } from 'lucide-react';

export interface LandingNavbarProps {
  onOpenFirewall?: () => void;
  onNavigate?: (route: string) => void;
  currentRoute?: string;
}

export const LandingNavbar: React.FC<LandingNavbarProps> = ({
  onOpenFirewall,
  onNavigate,
  currentRoute = '/',
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen((prev) => !prev);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  const handleRouteClick = (route: string) => {
    closeMobileMenu();
    if (onNavigate) {
      onNavigate(route);
    } else if (typeof window !== 'undefined') {
      window.location.pathname = route;
    }
  };

  const handleOpenFirewallAction = () => {
    closeMobileMenu();
    if (onOpenFirewall) {
      onOpenFirewall();
    } else if (onNavigate) {
      onNavigate('/firewall');
    } else if (typeof window !== 'undefined') {
      window.location.pathname = '/firewall';
    }
  };

  const isActive = (route: string) => currentRoute === route;

  return (
    <header className="nivesh-notch-header fade-in-delayed delay-nav">
      <div className="nivesh-notch-container">
        {/* Left Inverted Concave Shoulder Wing */}
        <svg className="nivesh-notch-wing-left" viewBox="0 0 20 20" aria-hidden="true">
          <path d="M 0 0 C 11.046 0 20 8.954 20 20 H 22 V 0 H 0 Z" fill="#000000" />
          <path d="M 0 0 C 11.046 0 20 8.954 20 20" stroke="rgba(255, 255, 255, 0.14)" strokeWidth="1" fill="none" />
        </svg>

        {/* Center Hanging Notch Capsule Bar */}
        <nav className="nivesh-notch-bar" aria-label="Main Site Navigation">
          {/* Brand & Glossy App Tile Lockup */}
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault();
              handleRouteClick('/');
            }}
            className="nivesh-notch-brand"
            title="Nivesh Firewall Home"
          >
            <div className="nivesh-notch-app-icon" aria-hidden="true">
              <Shield
                size={15}
                color="#ffffff"
                strokeWidth={2.4}
                style={{ filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5))' }}
              />
            </div>
            <span className="nivesh-notch-brand-text">
              <span>NIVESH</span> <span>FIREWALL</span>
            </span>
          </a>

          {/* Centered Navigation Links */}
          <div className="nivesh-notch-nav">
            <a
              href="/features"
              onClick={(e) => {
                e.preventDefault();
                handleRouteClick('/features');
              }}
              className={`nivesh-notch-link ${isActive('/features') ? 'active' : ''}`}
            >
              Features
            </a>
            <a
              href="/how-it-works"
              onClick={(e) => {
                e.preventDefault();
                handleRouteClick('/how-it-works');
              }}
              className={`nivesh-notch-link ${isActive('/how-it-works') ? 'active' : ''}`}
            >
              How It Works
            </a>
            <a
              href="/sources"
              onClick={(e) => {
                e.preventDefault();
                handleRouteClick('/sources');
              }}
              className={`nivesh-notch-link ${isActive('/sources') ? 'active' : ''}`}
            >
              Sources
            </a>
            <a
              href="/extension"
              onClick={(e) => {
                e.preventDefault();
                handleRouteClick('/extension');
              }}
              className={`nivesh-notch-link ${isActive('/extension') ? 'active' : ''}`}
            >
              Extension
            </a>
            <a
              href="/about"
              onClick={(e) => {
                e.preventDefault();
                handleRouteClick('/about');
              }}
              className={`nivesh-notch-link ${isActive('/about') ? 'active' : ''}`}
            >
              About
            </a>
          </div>

          {/* Right Action Controls: Open Firewall Ghost + Get Started / Download Button */}
          <div className="nivesh-notch-actions">
            <button
              type="button"
              onClick={handleOpenFirewallAction}
              className="desktop-hint"
              style={{
                background: 'none',
                border: 'none',
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '12px',
                fontWeight: 500,
                cursor: 'pointer',
                padding: '5px 10px',
                borderRadius: '8px',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ffffff';
                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'rgba(255, 255, 255, 0.7)';
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              Open Firewall
            </button>

            {/* High-Contrast White Pill Button ( Get Started / Download) */}
            <button
              type="button"
              onClick={handleOpenFirewallAction}
              className="nivesh-notch-download-btn"
              title="Get Started with Nivesh Firewall"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.61-.75 1.04-1.8 0.92-2.87-.93.04-2.02.63-2.66 1.38-.56.65-.98 1.7-0.87 2.73 1.02.08 2.05-.53 2.61-1.24z" />
              </svg>
              <span>Get Started</span>
            </button>

            {/* Mobile Hamburger Toggle Button */}
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
                padding: '6px',
                color: '#cbd5e1',
                cursor: 'pointer',
                display: 'none',
              }}
            >
              {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </nav>

        {/* Right Inverted Concave Shoulder Wing */}
        <svg className="nivesh-notch-wing-right" viewBox="0 0 20 20" aria-hidden="true">
          <path d="M 20 0 C 8.954 0 0 8.954 0 20 H -2 V 0 H 20 Z" fill="#000000" />
          <path d="M 20 0 C 8.954 0 0 8.954 0 20" stroke="rgba(255, 255, 255, 0.14)" strokeWidth="1" fill="none" />
        </svg>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          id="mobile-menu-drawer"
          style={{
            position: 'fixed',
            top: '56px',
            left: '12px',
            right: '12px',
            borderRadius: '20px',
            padding: '20px',
            backgroundColor: '#0a0a0c',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.9)',
            pointerEvents: 'auto',
            zIndex: 60,
          }}
          role="region"
          aria-label="Mobile Navigation"
        >
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontWeight: 500 }}>
            {['/', '/features', '/how-it-works', '/sources', '/extension', '/about', '/privacy'].map((route) => {
              const label =
                route === '/'
                  ? 'Product'
                  : route.slice(1).replace('-', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
              return (
                <a
                  key={route}
                  href={route}
                  onClick={(e) => {
                    e.preventDefault();
                    handleRouteClick(route);
                  }}
                  style={{
                    textDecoration: 'none',
                    color: isActive(route) ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    backgroundColor: isActive(route) ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                    fontSize: '14px',
                  }}
                >
                  {label}
                </a>
              );
            })}
          </nav>
          <div style={{ height: '1px', backgroundColor: 'rgba(255, 255, 255, 0.1)', margin: '12px 0' }} />
          <button
            type="button"
            onClick={handleOpenFirewallAction}
            className="nivesh-notch-download-btn"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            Get Started
          </button>
        </div>
      )}
    </header>
  );
};
