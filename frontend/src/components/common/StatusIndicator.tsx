import React from 'react';
import type { ProtectionSystemStatus } from '../../types/firewall';

export interface StatusIndicatorProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: ProtectionSystemStatus | 'neutral';
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = 'md',
  style,
  className = '',
  ...props
}) => {
  const getColor = () => {
    switch (status) {
      case 'active':
        return 'var(--color-allow)';
      case 'connecting':
        return 'var(--color-accent)';
      case 'unavailable':
        return 'var(--color-text-muted)';
      case 'error':
        return 'var(--color-block)';
      case 'neutral':
      default:
        return 'var(--color-text-secondary)';
    }
  };

  const dotSize = size === 'sm' ? 8 : 10;

  return (
    <span
      className={`nivesh-status-indicator ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--space-2)',
        fontSize: size === 'sm' ? 'var(--font-size-xs)' : 'var(--font-size-sm)',
        color: 'var(--color-text-secondary)',
        ...style,
      }}
      {...props}
    >
      <span
        style={{
          width: `${dotSize}px`,
          height: `${dotSize}px`,
          borderRadius: 'var(--radius-full)',
          backgroundColor: getColor(),
          boxShadow: status === 'active' ? '0 0 8px rgba(16, 185, 129, 0.5)' : 'none',
          display: 'inline-block',
          flexShrink: 0,
        }}
      />
      {label && <span>{label}</span>}
    </span>
  );
};
