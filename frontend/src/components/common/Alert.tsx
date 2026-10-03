import React from 'react';
import { Info, AlertTriangle, AlertOctagon, CheckCircle2, X } from 'lucide-react';

export type AlertVariant = 'info' | 'warning' | 'error' | 'success';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  onDismiss?: () => void;
}

export const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'info',
  title,
  onDismiss,
  style,
  className = '',
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'warning':
        return {
          bg: 'var(--color-warn-bg)',
          border: 'var(--color-warn-border)',
          color: 'var(--color-warn)',
          icon: <AlertTriangle size={18} color="var(--color-warn)" aria-hidden="true" />,
        };
      case 'error':
        return {
          bg: 'var(--color-block-bg)',
          border: 'var(--color-block-border)',
          color: 'var(--color-block)',
          icon: <AlertOctagon size={18} color="var(--color-block)" aria-hidden="true" />,
        };
      case 'success':
        return {
          bg: 'var(--color-allow-bg)',
          border: 'var(--color-allow-border)',
          color: 'var(--color-allow)',
          icon: <CheckCircle2 size={18} color="var(--color-allow)" aria-hidden="true" />,
        };
      case 'info':
      default:
        return {
          bg: 'var(--color-inform-bg)',
          border: 'var(--color-inform-border)',
          color: 'var(--color-inform)',
          icon: <Info size={18} color="var(--color-inform)" aria-hidden="true" />,
        };
    }
  };

  const config = getVariantStyles();

  return (
    <div
      role="alert"
      className={`nivesh-alert nivesh-alert-${variant} ${className}`}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 'var(--space-3)',
        padding: 'var(--space-3) var(--space-4)',
        backgroundColor: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: 'var(--radius-sm)',
        color: 'var(--color-text-primary)',
        ...style,
      }}
      {...props}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>{config.icon}</div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {title && (
          <strong style={{ fontSize: 'var(--font-size-sm)', color: config.color }}>
            {title}
          </strong>
        )}
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
          {children}
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss alert"
          style={{
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: '2px',
            display: 'flex',
          }}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};
