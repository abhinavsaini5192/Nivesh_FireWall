import React from 'react';
import { Menu, X, Shield } from 'lucide-react';
import type { ProtectionSystemStatus } from '../../types/firewall';
import { ProtectionStatus } from '../status/ProtectionStatus';
import { IconButton } from '../common/IconButton';
import { config } from '../../config/env';

export interface HeaderProps {
  systemStatus: ProtectionSystemStatus;
  isMobileMenuOpen: boolean;
  onToggleMobileMenu: () => void;
  sessionId?: string;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus,
  isMobileMenuOpen,
  onToggleMobileMenu,
}) => {
  const handleNavigate = (e: React.MouseEvent, route: string) => {
    if (typeof window !== 'undefined' && window.history) {
      e.preventDefault();
      window.history.pushState({}, '', route);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  return (
    <header className="nivesh-notch-header">
      <div className="nivesh-notch-container">
        {/* Left Inverted Concave Shoulder Wing */}
        <svg className="nivesh-notch-wing-left" viewBox="0 0 20 20" aria-hidden="true">
          <path d="M 0 0 C 11.046 0 20 8.954 20 20 H 22 V 0 H 0 Z" fill="#000000" />
          <path d="M 0 0 C 11.046 0 20 8.954 20 20" stroke="rgba(255, 255, 255, 0.14)" strokeWidth="1" fill="none" />
        </svg>

        {/* Hanging Notch Capsule Bar */}
        <div className="nivesh-notch-bar">
          {/* Brand & Glossy App Tile Lockup */}
          <a
            href="/"
            onClick={(e) => handleNavigate(e, '/')}
            className="nivesh-notch-brand"
            title="Return to Nivesh Overview"
          >
            {/* Glossy App Icon Tile */}
            <div className="nivesh-notch-app-icon" aria-hidden="true">
              <Shield
                size={15}
                color="#ffffff"
                strokeWidth={2.4}
                style={{ filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5))' }}
              />
            </div>

            {/* Wordmark & Version */}
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '3px' }}>
              <span className="nivesh-notch-brand-text">NIVESH FIREWALL</span>
              <span className="nivesh-notch-version">v{config.appVersion}</span>
            </div>

            {/* Subtitle / Tagline for Test & Screen Reader Compatibility */}
            <span className="desktop-hint nivesh-notch-tagline">
              Financial Content Protection Core
            </span>
          </a>

          {/* Centered Navigation Links (Supaste-style) */}
          <nav className="nivesh-notch-nav" aria-label="Main Navigation">
            <a
              href="/features"
              onClick={(e) => handleNavigate(e, '/features')}
              className="nivesh-notch-link"
            >
              Features
            </a>
            <a
              href="/how-it-works"
              onClick={(e) => handleNavigate(e, '/how-it-works')}
              className="nivesh-notch-link"
            >
              How It Works
            </a>
            <a
              href="/sources"
              onClick={(e) => handleNavigate(e, '/sources')}
              className="nivesh-notch-link"
            >
              Sources
            </a>
            <a
              href="/extension"
              onClick={(e) => handleNavigate(e, '/extension')}
              className="nivesh-notch-link"
            >
              Extension
            </a>
            <a
              href="/about"
              onClick={(e) => handleNavigate(e, '/about')}
              className="nivesh-notch-link"
            >
              About
            </a>
          </nav>

          {/* Right Action Controls: Protection Status & Pill Button */}
          <div className="nivesh-notch-actions">
            {/* Real-time System Protection Indicator */}
            <ProtectionStatus status={systemStatus} />

            {/* High-Contrast White Pill Download Button ( Download) */}
            <a
              href="/extension"
              onClick={(e) => handleNavigate(e, '/extension')}
              className="nivesh-notch-download-btn"
              title="Download Nivesh Firewall Extension"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.61-.75 1.04-1.8 0.92-2.87-.93.04-2.02.63-2.66 1.38-.56.65-.98 1.7-0.87 2.73 1.02.08 2.05-.53 2.61-1.24z" />
              </svg>
              <span>Download</span>
            </a>

            {/* Mobile Hamburger Menu Toggle */}
            <div className="mobile-menu-toggle" style={{ display: 'none' }}>
              <IconButton
                aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
                onClick={onToggleMobileMenu}
              >
                {isMobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
              </IconButton>
            </div>
          </div>
        </div>

        {/* Right Inverted Concave Shoulder Wing */}
        <svg className="nivesh-notch-wing-right" viewBox="0 0 20 20" aria-hidden="true">
          <path d="M 20 0 C 8.954 0 0 8.954 0 20 H -2 V 0 H 20 Z" fill="#000000" />
          <path d="M 20 0 C 8.954 0 0 8.954 0 20" stroke="rgba(255, 255, 255, 0.14)" strokeWidth="1" fill="none" />
        </svg>
      </div>
    </header>
  );
};
