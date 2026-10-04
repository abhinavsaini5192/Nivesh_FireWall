import React, { useState } from 'react';
import { Menu, X, Shield } from 'lucide-react';
import type { ProtectionSystemStatus } from '../../types/firewall';
import { ProtectionStatus } from '../status/ProtectionStatus';
import { IconButton } from '../common/IconButton';
import { ExtensionInstallModal } from '../common/ExtensionInstallModal';
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
  const [isInstallModalOpen, setIsInstallModalOpen] = useState(false);

  const handleNavigate = (e: React.MouseEvent, route: string) => {
    if (typeof window !== 'undefined' && window.history) {
      e.preventDefault();
      window.history.pushState({}, '', route);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  const handleAddToChrome = (e: React.MouseEvent) => {
    e.preventDefault();

    const storeUrl =
      (typeof import.meta !== 'undefined' &&
        import.meta.env &&
        ((import.meta.env as Record<string, string | undefined>).VITE_CHROME_WEBSTORE_URL || '')) ||
      '';

    if (storeUrl) {
      window.open(storeUrl, '_blank', 'noopener,noreferrer');
      return;
    }

    // Automatically trigger browser download of Manifest V3 extension package
    const link = document.createElement('a');
    link.href = '/nivesh-firewall-v1.0.0.zip';
    link.download = 'nivesh-firewall-v1.0.0.zip';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Show instant step-by-step Chrome activation guide modal
    setIsInstallModalOpen(true);
  };

  return (
    <>
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

            {/* Right Action Controls: Protection Status & Add to Chrome Pill Button */}
            <div className="nivesh-notch-actions">
              {/* Real-time System Protection Indicator */}
              <ProtectionStatus status={systemStatus} />

              {/* High-Contrast White Pill Button: Add to Chrome */}
              <button
                type="button"
                onClick={handleAddToChrome}
                className="nivesh-notch-download-btn"
                title="Add Nivesh Firewall Extension to Chrome"
                aria-label="Add to Chrome"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="10" />
                  <circle cx="12" cy="12" r="4" />
                  <line x1="21.17" y1="8" x2="12" y2="8" />
                  <line x1="3.95" y1="6.06" x2="8.54" y2="14" />
                  <line x1="10.88" y1="21.94" x2="15.46" y2="14" />
                </svg>
                <span>Add to Chrome</span>
              </button>

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

      {/* Extension Installation Guide Modal */}
      <ExtensionInstallModal
        isOpen={isInstallModalOpen}
        onClose={() => setIsInstallModalOpen(false)}
        onNavigateExtension={() => {
          setIsInstallModalOpen(false);
          if (typeof window !== 'undefined' && window.history) {
            window.history.pushState({}, '', '/extension');
            window.dispatchEvent(new PopStateEvent('popstate'));
          }
        }}
      />
    </>
  );
};
