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
          backgroundColor: 'var(--white-btn, #fdfdfd)',
          color: 'var(--btn-ink, #050505)',
          border: '1px solid var(--white-btn, #fdfdfd)',
          fontWeight: 600,
          boxShadow: '0 0 16px rgba(255, 255, 255, 0.14)',
        };
      case 'secondary':
        return {
          backgroundColor: 'rgba(255, 255, 255, 0.06)',
          color: 'var(--ink, #ffffff)',
          border: '1px solid var(--color-border-default)',
          backdropFilter: 'blur(8px)',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: 'var(--ink, #ffffff)',
          border: '1px solid var(--color-border-default)',
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
          padding: '6px 14px',
          fontSize: 'var(--font-size-xs)',
          gap: '6px',
          borderRadius: '9999px',
        };
      case 'lg':
        return {
          padding: '12px 28px',
          fontSize: 'var(--font-size-md)',
          gap: '10px',
          borderRadius: '9999px',
        };
      case 'md':
      default:
        return {
          padding: '8px 18px',
          fontSize: 'var(--font-size-sm)',
          gap: '8px',
          borderRadius: '9999px',
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
