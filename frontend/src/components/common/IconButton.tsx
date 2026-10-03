import React from 'react';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  'aria-label': string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'outline' | 'surface';
}

export const IconButton: React.FC<IconButtonProps> = ({
  children,
  size = 'md',
  variant = 'ghost',
  disabled,
  style,
  className = '',
  ...props
}) => {
  const sizeMap = {
    sm: { width: '28px', height: '28px', padding: '4px', fontSize: '14px' },
    md: { width: '36px', height: '36px', padding: '8px', fontSize: '16px' },
    lg: { width: '44px', height: '44px', padding: '10px', fontSize: '20px' },
  };

  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'outline':
        return {
          backgroundColor: 'transparent',
          border: '1px solid var(--color-border-default)',
          color: 'var(--color-text-secondary)',
        };
      case 'surface':
        return {
          backgroundColor: 'var(--color-bg-surface-elevated)',
          border: '1px solid var(--color-border-subtle)',
          color: 'var(--color-text-primary)',
        };
      case 'ghost':
      default:
        return {
          backgroundColor: 'transparent',
          border: '1px solid transparent',
          color: 'var(--color-text-secondary)',
        };
    }
  };

  return (
    <button
      disabled={disabled}
      className={`nivesh-icon-button ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 'var(--radius-sm)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all var(--transition-fast)',
        ...sizeMap[size],
        ...getVariantStyles(),
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
};
