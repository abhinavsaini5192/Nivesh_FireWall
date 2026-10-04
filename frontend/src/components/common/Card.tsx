import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'surface' | 'elevated' | 'subtle' | 'outline';
  interactive?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'surface',
  interactive = false,
  style,
  className = '',
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'elevated':
        return {
          backgroundColor: 'var(--color-bg-surface-elevated)',
          border: '1px solid var(--color-border-subtle)',
          boxShadow: 'var(--shadow-md)',
        };
      case 'subtle':
        return {
          backgroundColor: 'var(--color-bg-subtle)',
          border: '1px solid var(--color-border-subtle)',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          border: '1px solid var(--color-border-default)',
        };
      case 'surface':
      default:
        return {
          backgroundColor: 'var(--color-bg-surface-elevated)',
          border: '1px solid var(--color-border-subtle)',
          boxShadow: 'var(--shadow-sm)',
        };
    }
  };

  return (
    <div
      className={`nivesh-card ${interactive ? 'nivesh-card-interactive' : ''} ${className}`}
      style={{
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
        cursor: interactive ? 'pointer' : 'default',
        ...getVariantStyles(),
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  style,
  className = '',
  ...props
}) => (
  <div
    className={`nivesh-card-header ${className}`}
    style={{
      marginBottom: 'var(--space-4)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-1)',
      ...style,
    }}
    {...props}
  >
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  style,
  className = '',
  ...props
}) => (
  <h3
    className={`nivesh-card-title ${className}`}
    style={{
      fontSize: 'var(--font-size-lg)',
      fontWeight: 'var(--font-weight-semibold)',
      color: 'var(--color-text-primary)',
      margin: 0,
      ...style,
    }}
    {...props}
  >
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  style,
  className = '',
  ...props
}) => (
  <p
    className={`nivesh-card-description ${className}`}
    style={{
      fontSize: 'var(--font-size-sm)',
      color: 'var(--color-text-secondary)',
      margin: 0,
      ...style,
    }}
    {...props}
  >
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  style,
  className = '',
  ...props
}) => (
  <div
    className={`nivesh-card-content ${className}`}
    style={{
      display: 'flex',
      flexDirection: 'column',
      flex: 1,
      ...style,
    }}
    {...props}
  >
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  style,
  className = '',
  ...props
}) => (
  <div
    className={`nivesh-card-footer ${className}`}
    style={{
      marginTop: 'var(--space-4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-end',
      gap: 'var(--space-3)',
      ...style,
    }}
    {...props}
  >
    {children}
  </div>
);
