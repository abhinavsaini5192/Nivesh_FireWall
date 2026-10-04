import React from 'react';
import { Shield, Menu, X, Terminal, Cpu, Globe } from 'lucide-react';
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
  sessionId,
}) => {
  return (
    <header
      className="nivesh-header"
      style={{
        height: 'var(--header-height)',
        backgroundColor: 'var(--color-bg-surface)',
        borderBottom: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-5)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Brand & Identity (links to Landing Page) */}
      <a
        href="/"
        onClick={(e) => {
          if (typeof window !== 'undefined' && window.history) {
            e.preventDefault();
            window.history.pushState({}, '', '/');
            window.dispatchEvent(new PopStateEvent('popstate'));
          }
        }}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
          textDecoration: 'none',
          color: 'inherit',
        }}
        title="View Nivesh Landing Page"
      >
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--color-bg-surface-elevated)',
            border: '1px solid var(--color-border-subtle)',
            color: 'var(--color-accent-hover)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <Shield size={16} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span
            style={{
              display: 'inline-block',
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: '#a855f7',
              boxShadow: '0 0 8px #a855f7',
            }}
          />
          <span
            style={{
              fontSize: 'var(--font-size-base)',
              fontWeight: 'var(--font-weight-semibold)',
              letterSpacing: '0.06em',
              color: 'var(--color-text-primary)',
            }}
          >
            NIVESH FIREWALL
          </span>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              padding: '1px 6px',
              backgroundColor: 'var(--color-bg-subtle)',
              color: 'var(--color-text-muted)',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--color-border-subtle)',
              letterSpacing: '0.03em',
            }}
          >
            v{config.appVersion}
          </span>
          <span
            style={{
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              paddingLeft: 'var(--space-2)',
              borderLeft: '1px solid var(--color-border-subtle)',
              display: 'none',
            }}
            className="desktop-hint"
          >
            Financial Content Protection Core
          </span>

        </div>
      </a>

      {/* Right Controls: Protection Status & Session */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        {/* Landing Page Overview Link */}
        <a
          href="/"
          onClick={(e) => {
            if (typeof window !== 'undefined' && window.history) {
              e.preventDefault();
              window.history.pushState({}, '', '/');
              window.dispatchEvent(new PopStateEvent('popstate'));
            }
          }}
          style={{
            display: 'none',
            alignItems: 'center',
            gap: '5px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-text-muted)',
            backgroundColor: 'var(--color-bg-subtle)',
            padding: '2px 8px',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--color-border-subtle)',
            textDecoration: 'none',
            cursor: 'pointer',
          }}
          className="desktop-hint"
          title="Return to Product Landing Page"
        >
          <Globe size={11} color="var(--color-accent)" />
          <span>Overview</span>
        </a>

        {/* Environment Tag */}
        <div
          style={{
            display: 'none',
            alignItems: 'center',
            gap: '4px',
            fontSize: '10px',
            fontFamily: 'var(--font-mono)',
            textTransform: 'uppercase',
            color: 'var(--color-text-muted)',
            backgroundColor: 'var(--color-bg-subtle)',
            padding: '2px 7px',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--color-border-subtle)',
          }}
          className="desktop-hint"
        >
          <Cpu size={11} color="var(--color-accent)" />
          <span>{config.mode === 'production' ? 'PROD' : 'LOCAL'}</span>
        </div>

        {/* Real-time System Protection Indicator */}
        <ProtectionStatus status={systemStatus} />

        {/* Optional Session Affordance */}
        {sessionId && (
          <div
            className="session-badge"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-text-muted)',
              backgroundColor: 'var(--color-bg-subtle)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--color-border-subtle)',
            }}
            title={`Active Firewall Session: ${sessionId}`}
          >
            <Terminal size={12} />
            <span>{sessionId.slice(0, 8)}</span>
          </div>
        )}

        {/* Mobile Hamburger Menu Toggle */}
        <div className="mobile-menu-toggle" style={{ display: 'none' }}>
          <IconButton
            aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            onClick={onToggleMobileMenu}
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </IconButton>
        </div>
      </div>
    </header>
  );
};

