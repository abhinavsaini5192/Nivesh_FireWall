import React from 'react';
import { ShieldAlert, Menu, X, Terminal } from 'lucide-react';
import type { ProtectionSystemStatus } from '../../types/firewall';
import { ProtectionStatus } from '../status/ProtectionStatus';
import { IconButton } from '../common/IconButton';

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
        padding: '0 var(--space-6)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Brand & Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--color-accent-subtle)',
            border: '1px solid rgba(14, 165, 233, 0.4)',
            color: 'var(--color-accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ShieldAlert size={20} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-md)',
                fontWeight: 'var(--font-weight-bold)',
                letterSpacing: '0.04em',
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
                padding: '1px 5px',
                backgroundColor: 'var(--color-bg-surface-elevated)',
                color: 'var(--color-accent-hover)',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--color-border-subtle)',
              }}
            >
              v1.0
            </span>
          </div>
          <span
            style={{
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              letterSpacing: '0.02em',
            }}
          >
            Financial Content Protection Core
          </span>
        </div>
      </div>

      {/* Right Controls: Protection Status & Session */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        {/* Real-time System Protection Indicator */}
        <ProtectionStatus status={systemStatus} />

        {/* Optional Session Affordance */}
        {sessionId && (
          <div
            className="session-badge"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
              fontSize: 'var(--font-size-xs)',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-text-muted)',
              backgroundColor: 'var(--color-bg-subtle)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <Terminal size={12} />
            <span>{sessionId.slice(0, 8)}...</span>
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
