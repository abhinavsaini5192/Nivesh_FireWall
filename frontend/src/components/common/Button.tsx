import React from 'react';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  disabled,
  className = '',
  style,
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: 'var(--color-accent)',
          color: 'var(--color-text-primary)',
          border: '1px solid var(--color-accent)',
        };
      case 'secondary':
        return {
          backgroundColor: 'var(--color-bg-surface-elevated)',
          color: 'var(--color-text-primary)',
          border: '1px solid var(--color-border-default)',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: 'var(--color-text-primary)',
          border: '1px solid var(--color-border-strong)',
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: 'var(--color-text-secondary)',
          border: '1px solid transparent',
        };
      case 'danger':
        return {
          backgroundColor: 'var(--color-block-bg)',
          color: 'var(--color-block)',
          border: '1px solid var(--color-block-border)',
        };
      default:
        return {};
    }
  };

  const getSizeStyles = (): React.CSSProperties => {
    switch (size) {
      case 'sm':
        return {
          padding: '4px 10px',
          fontSize: 'var(--font-size-xs)',
          gap: '6px',
          borderRadius: 'var(--radius-sm)',
        };
      case 'lg':
        return {
          padding: '12px 24px',
          fontSize: 'var(--font-size-md)',
          gap: '10px',
          borderRadius: 'var(--radius-md)',
        };
      case 'md':
      default:
        return {
          padding: '8px 16px',
          fontSize: 'var(--font-size-sm)',
          gap: '8px',
          borderRadius: 'var(--radius-sm)',
        };
    }
  };

  const baseStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'var(--font-weight-medium)',
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.55 : 1,
    transition: 'all var(--transition-fast)',
    width: fullWidth ? '100%' : 'auto',
    whiteSpace: 'nowrap',
    userSelect: 'none',
    boxShadow: variant === 'primary' ? 'var(--shadow-sm)' : 'none',
    ...getVariantStyles(),
    ...getSizeStyles(),
    ...style,
  };

  return (
    <button
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      className={`nivesh-button nivesh-button-${variant} ${className}`}
      style={baseStyles}
      {...props}
    >
      {isLoading ? (
        <Loader2
          size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16}
          style={{ animation: 'spin 1s linear infinite' }}
          aria-hidden="true"
        />
      ) : (
        leftIcon && <span aria-hidden="true">{leftIcon}</span>
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && <span aria-hidden="true">{rightIcon}</span>}
    </button>
  );
};
