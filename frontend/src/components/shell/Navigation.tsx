import React from 'react';
import { Shield, Clock, Database, Settings } from 'lucide-react';

export type NavTabId = 'protect' | 'activity' | 'threat-intel' | 'settings';

export interface NavItem {
  id: NavTabId;
  label: string;
  icon: React.ReactNode;
  badge?: string;
}

export interface NavigationProps {
  activeTab: NavTabId;
  onSelectTab: (tab: NavTabId) => void;
  orientation?: 'vertical' | 'horizontal';
}

const navItems: NavItem[] = [
  { id: 'protect', label: 'Protect', icon: <Shield size={18} /> },
  { id: 'activity', label: 'Activity', icon: <Clock size={18} /> },
  { id: 'threat-intel', label: 'Threat Intelligence', icon: <Database size={18} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={18} /> },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onSelectTab,
  orientation = 'vertical',
}) => {
  return (
    <nav
      aria-label="Main Navigation"
      style={{
        display: 'flex',
        flexDirection: orientation === 'vertical' ? 'column' : 'row',
        gap: '2px',
        width: '100%',
      }}
    >
      {navItems.map((item) => {
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onSelectTab(item.id)}
            aria-current={isActive ? 'page' : undefined}
            className={`nivesh-nav-item ${isActive ? 'nivesh-nav-item-active' : ''}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: 'var(--space-2) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: isActive ? 'var(--color-bg-active)' : 'transparent',
              color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              borderLeft: orientation === 'vertical' && isActive
                ? '2px solid var(--color-accent)'
                : '2px solid transparent',
              borderTop: orientation === 'horizontal' && isActive
                ? '2px solid var(--color-accent)'
                : 'none',
              fontWeight: isActive ? 'var(--font-weight-medium)' : 'var(--font-weight-normal)',
              fontSize: 'var(--font-size-sm)',
              textAlign: 'left',
              transition: 'background-color var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast)',
              cursor: 'pointer',
              width: '100%',
              position: 'relative',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span
                style={{
                  color: isActive ? 'var(--color-accent)' : 'var(--color-text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {item.icon}
              </span>
              <span style={{ letterSpacing: '0.01em' }}>{item.label}</span>
            </div>
            {item.badge && (
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-xs)',
                  backgroundColor: 'var(--color-bg-surface-elevated)',
                  color: 'var(--color-text-muted)',
                  border: '1px solid var(--color-border-subtle)',
                }}
              >
                {item.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};

