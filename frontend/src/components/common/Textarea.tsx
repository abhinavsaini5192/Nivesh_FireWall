import React from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  errorText?: string;
  showCount?: boolean;
}

export const Textarea: React.FC<TextareaProps> = ({
  id,
  label,
  helperText,
  errorText,
  showCount,
  maxLength,
  value,
  rows = 4,
  disabled,
  style,
  className = '',
  ...props
}) => {
  const generatedId = React.useId();
  const textareaId = id || generatedId;
  const helperId = `${textareaId}-helper`;
  const errorId = `${textareaId}-error`;

  const currentLength = typeof value === 'string' ? value.length : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', width: '100%' }}>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label
            htmlFor={textareaId}
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

      <textarea
        id={textareaId}
        disabled={disabled}
        value={value}
        rows={rows}
        maxLength={maxLength}
        aria-invalid={!!errorText}
        aria-describedby={errorText ? errorId : helperText ? helperId : undefined}
        style={{
          backgroundColor: disabled ? 'var(--color-bg-canvas)' : 'var(--color-bg-subtle)',
          border: `1px solid ${errorText ? 'var(--color-block)' : 'var(--color-border-default)'}`,
          borderRadius: 'var(--radius-sm)',
          padding: 'var(--space-3)',
          color: 'var(--color-text-primary)',
          fontSize: 'var(--font-size-base)',
          resize: 'vertical',
          lineHeight: 'var(--line-height-relaxed)',
          transition: 'border-color var(--transition-fast)',
          opacity: disabled ? 0.6 : 1,
          width: '100%',
          ...style,
        }}
        className={`nivesh-textarea ${className}`}
        {...props}
      />

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
