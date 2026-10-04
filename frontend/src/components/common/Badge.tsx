import React from 'react';

export type BadgeVariant = 'neutral' | 'accent' | 'success' | 'warning' | 'danger' | 'outline';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  icon,
  style,
  className = '',
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'accent':
        return {
          backgroundColor: 'var(--color-accent-subtle)',
          color: 'var(--color-accent-hover)',
          border: '1px solid var(--color-border-accent)',
        };
      case 'success':
        return {
          backgroundColor: 'var(--color-allow-bg)',
          color: 'var(--color-allow)',
          border: '1px solid var(--color-allow-border)',
        };
      case 'warning':
        return {
          backgroundColor: 'var(--color-warn-bg)',
          color: 'var(--color-warn)',
          border: '1px solid var(--color-warn-border)',
        };
      case 'danger':
        return {
          backgroundColor: 'var(--color-block-bg)',
          color: 'var(--color-block)',
          border: '1px solid var(--color-block-border)',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: 'var(--color-text-secondary)',
          border: '1px solid var(--color-border-default)',
        };
      case 'neutral':
      default:
        return {
          backgroundColor: 'var(--color-bg-surface-elevated)',
          color: 'var(--color-text-secondary)',
          border: '1px solid var(--color-border-subtle)',
        };
    }
  };

  const sizeStyles: React.CSSProperties =
    size === 'sm'
      ? { padding: '2px 6px', fontSize: 'var(--font-size-xs)' }
      : { padding: '4px 10px', fontSize: 'var(--font-size-sm)' };

  return (
    <span
      className={`nivesh-badge nivesh-badge-${variant} ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontWeight: 'var(--font-weight-medium)',
        borderRadius: 'var(--radius-full)',
        whiteSpace: 'nowrap',
        userSelect: 'none',
        lineHeight: 1.2,
        ...getVariantStyles(),
        ...sizeStyles,
        ...style,
      }}
      {...props}
    >
      {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
      {children}
    </span>
  );
};
