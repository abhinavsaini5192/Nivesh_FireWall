import React from 'react';

export interface DividerProps extends React.HTMLAttributes<HTMLHRElement> {
  orientation?: 'horizontal' | 'vertical';
  spacing?: 'sm' | 'md' | 'lg';
}

export const Divider: React.FC<DividerProps> = ({
  orientation = 'horizontal',
  spacing = 'md',
  style,
  className = '',
  ...props
}) => {
  const getMargin = () => {
    switch (spacing) {
      case 'sm':
        return orientation === 'horizontal' ? 'var(--space-2) 0' : '0 var(--space-2)';
      case 'lg':
        return orientation === 'horizontal' ? 'var(--space-6) 0' : '0 var(--space-6)';
      case 'md':
      default:
        return orientation === 'horizontal' ? 'var(--space-4) 0' : '0 var(--space-4)';
    }
  };

  if (orientation === 'vertical') {
    return (
      <span
        role="separator"
        aria-orientation="vertical"
        className={`nivesh-divider-v ${className}`}
        style={{
          display: 'inline-block',
          width: '1px',
          alignSelf: 'stretch',
          backgroundColor: 'var(--color-border-subtle)',
          margin: getMargin(),
          ...style,
        }}
      />
    );
  }

  return (
    <hr
      role="separator"
      className={`nivesh-divider-h ${className}`}
      style={{
        border: 'none',
        borderTop: '1px solid var(--color-border-subtle)',
        margin: getMargin(),
        width: '100%',
        ...style,
      }}
      {...props}
    />
  );
};
