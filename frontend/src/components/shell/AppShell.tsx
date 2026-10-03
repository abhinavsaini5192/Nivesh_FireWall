import React, { useState } from 'react';
import type { ProtectionSystemStatus } from '../../types/firewall';
import { Header } from './Header';
import { Navigation, type NavTabId } from './Navigation';

export interface AppShellProps {
  children: React.ReactNode;
  activeTab: NavTabId;
  onSelectTab: (tab: NavTabId) => void;
  systemStatus: ProtectionSystemStatus;
  sessionId?: string;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeTab,
  onSelectTab,
  systemStatus,
  sessionId,
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleSelectTab = (tab: NavTabId) => {
    onSelectTab(tab);
    setIsMobileMenuOpen(false);
  };

  return (
    <div
      className="nivesh-app-shell"
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--color-bg-canvas)',
      }}
    >
      {/* Top Header */}
      <Header
        systemStatus={systemStatus}
        isMobileMenuOpen={isMobileMenuOpen}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        sessionId={sessionId}
      />

      {/* Main Body Area: Sidebar + Content */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          width: '100%',
        }}
      >
        {/* Desktop Sidebar Navigation */}
        <aside
          className="nivesh-sidebar"
          aria-label="Sidebar Navigation"
          style={{
            width: 'var(--sidebar-width)',
            backgroundColor: 'var(--color-bg-surface)',
            borderRight: '1px solid var(--color-border-subtle)',
            padding: 'var(--space-6) var(--space-3)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div
              style={{
                fontSize: '11px',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                paddingLeft: 'var(--space-3)',
              }}
            >
              Firewall Menu
            </div>
            <Navigation activeTab={activeTab} onSelectTab={handleSelectTab} />
          </div>

          {/* Sidebar Footer Info */}
          <div
            style={{
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--color-bg-subtle)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
              Calm Protection Core
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px', lineHeight: 1.4 }}>
              Engines 1–10 Intelligence
            </div>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {isMobileMenuOpen && (
          <div
            className="mobile-nav-drawer"
            style={{
              position: 'fixed',
              top: 'var(--header-height)',
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'var(--color-bg-surface)',
              zIndex: 35,
              padding: 'var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-4)',
            }}
          >
            <Navigation activeTab={activeTab} onSelectTab={handleSelectTab} />
          </div>
        )}

        {/* Main View Area */}
        <main
          id="main-content"
          tabIndex={-1}
          style={{
            flex: 1,
            padding: 'var(--space-8) var(--space-6)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            overflowY: 'auto',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 'var(--max-content-width)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-6)',
            }}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
