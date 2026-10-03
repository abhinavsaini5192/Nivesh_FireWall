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
        gap: 'var(--space-1)',
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
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: isActive ? 'var(--color-bg-active)' : 'transparent',
              color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              borderLeft: orientation === 'vertical' && isActive
                ? '3px solid var(--color-accent)'
                : '3px solid transparent',
              fontWeight: isActive ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)',
              fontSize: 'var(--font-size-sm)',
              textAlign: 'left',
              transition: 'all var(--transition-fast)',
              cursor: 'pointer',
              width: '100%',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <span
                style={{
                  color: isActive ? 'var(--color-accent)' : 'var(--color-text-muted)',
                  display: 'flex',
                }}
              >
                {item.icon}
              </span>
              <span>{item.label}</span>
            </div>
            {item.badge && (
              <span
                style={{
                  fontSize: 'var(--font-size-xs)',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'var(--color-bg-surface-elevated)',
                  color: 'var(--color-text-muted)',
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
