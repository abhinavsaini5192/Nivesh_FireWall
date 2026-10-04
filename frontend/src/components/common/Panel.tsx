import React from 'react';

export interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  badge?: React.ReactNode;
  accent?: 'default' | 'accent' | 'warn' | 'block' | 'allow';
}

export const Panel: React.FC<PanelProps> = ({
  children,
  title,
  badge,
  accent = 'default',
  style,
  className = '',
  ...props
}) => {
  const getAccentBorder = () => {
    switch (accent) {
      case 'accent':
        return 'var(--color-accent)';
      case 'warn':
        return 'var(--color-warn)';
      case 'block':
        return 'var(--color-block)';
      case 'allow':
        return 'var(--color-allow)';
      case 'default':
      default:
        return 'var(--color-border-default)';
    }
  };

  return (
    <div
      className={`nivesh-panel ${className}`}
      style={{
        backgroundColor: 'var(--color-bg-surface-elevated)',
        border: '1px solid var(--color-border-subtle)',
        borderLeft: `3px solid ${getAccentBorder()}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        ...style,
      }}
      {...props}
    >
      {(title || badge) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--color-border-subtle)',
            paddingBottom: 'var(--space-2)',
          }}
        >
          {title && (
            <h4
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                margin: 0,
              }}
            >
              {title}
            </h4>
          )}
          {badge && <div>{badge}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
