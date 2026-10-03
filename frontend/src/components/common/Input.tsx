import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  errorText?: string;
  prefixIcon?: React.ReactNode;
  suffixIcon?: React.ReactNode;
  showCount?: boolean;
}

export const Input: React.FC<InputProps> = ({
  id,
  label,
  helperText,
  errorText,
  prefixIcon,
  suffixIcon,
  showCount,
  maxLength,
  value,
  disabled,
  style,
  className = '',
  ...props
}) => {
  const generatedId = React.useId();
  const inputId = id || generatedId;
  const helperId = `${inputId}-helper`;
  const errorId = `${inputId}-error`;

  const currentLength = typeof value === 'string' ? value.length : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', width: '100%' }}>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label
            htmlFor={inputId}
            style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-medium)',
              color: errorText ? 'var(--color-block)' : 'var(--color-text-secondary)',
            }}
          >
            {label}
          </label>
          {showCount && maxLength && (
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: currentLength >= maxLength ? 'var(--color-warn)' : 'var(--color-text-muted)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {currentLength}/{maxLength}
            </span>
          )}
        </div>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: disabled ? 'var(--color-bg-canvas)' : 'var(--color-bg-subtle)',
          border: `1px solid ${errorText ? 'var(--color-block)' : 'var(--color-border-default)'}`,
          borderRadius: 'var(--radius-sm)',
          padding: '0 var(--space-3)',
          transition: 'border-color var(--transition-fast)',
          opacity: disabled ? 0.6 : 1,
        }}
      >
        {prefixIcon && (
          <span style={{ marginRight: 'var(--space-2)', color: 'var(--color-text-muted)', display: 'flex' }}>
            {prefixIcon}
          </span>
        )}
        <input
          id={inputId}
          disabled={disabled}
          value={value}
          maxLength={maxLength}
          aria-invalid={!!errorText}
          aria-describedby={errorText ? errorId : helperText ? helperId : undefined}
          style={{
            flex: 1,
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            color: 'var(--color-text-primary)',
            padding: 'var(--space-2) 0',
            fontSize: 'var(--font-size-base)',
            ...style,
          }}
          className={`nivesh-input ${className}`}
          {...props}
        />
        {suffixIcon && (
          <span style={{ marginLeft: 'var(--space-2)', color: 'var(--color-text-muted)', display: 'flex' }}>
            {suffixIcon}
          </span>
        )}
      </div>

      {errorText && (
        <span
          id={errorId}
          role="alert"
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-block)',
            fontWeight: 'var(--font-weight-medium)',
          }}
        >
          {errorText}
        </span>
      )}

      {!errorText && helperText && (
        <span
          id={helperId}
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-muted)',
          }}
        >
          {helperText}
        </span>
      )}
    </div>
  );
};
