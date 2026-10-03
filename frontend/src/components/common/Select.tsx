import React from 'react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  helperText?: string;
  errorText?: string;
}

export const Select: React.FC<SelectProps> = ({
  id,
  label,
  options,
  helperText,
  errorText,
  disabled,
  style,
  className = '',
  ...props
}) => {
  const generatedId = React.useId();
  const selectId = id || generatedId;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', width: '100%' }}>
      {label && (
        <label
          htmlFor={selectId}
          style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: 'var(--font-weight-medium)',
            color: errorText ? 'var(--color-block)' : 'var(--color-text-secondary)',
          }}
        >
          {label}
        </label>
      )}

      <select
        id={selectId}
        disabled={disabled}
        aria-invalid={!!errorText}
        style={{
          backgroundColor: disabled ? 'var(--color-bg-canvas)' : 'var(--color-bg-subtle)',
          border: `1px solid ${errorText ? 'var(--color-block)' : 'var(--color-border-default)'}`,
          borderRadius: 'var(--radius-sm)',
          padding: 'var(--space-2) var(--space-3)',
          color: 'var(--color-text-primary)',
          fontSize: 'var(--font-size-base)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          width: '100%',
          ...style,
        }}
        className={`nivesh-select ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option
            key={opt.value}
            value={opt.value}
            disabled={opt.disabled}
            style={{ backgroundColor: 'var(--color-bg-surface-elevated)', color: 'var(--color-text-primary)' }}
          >
            {opt.label}
          </option>
        ))}
      </select>

      {errorText && (
        <span
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
