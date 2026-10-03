import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  errorCode?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Analysis Unavailable',
  message,
  errorCode,
  onRetry,
  isRetrying = false,
  style,
  className = '',
  ...props
}) => {
  return (
    <div
      role="alert"
      className={`nivesh-error-state ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: 'var(--space-8) var(--space-6)',
        backgroundColor: 'var(--color-bg-subtle)',
        border: '1px solid var(--color-block-border)',
        borderRadius: 'var(--radius-md)',
        ...style,
      }}
      {...props}
    >
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: 'var(--radius-full)',
          backgroundColor: 'var(--color-block-bg)',
          color: 'var(--color-block)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 'var(--space-3)',
        }}
      >
        <AlertCircle size={24} />
      </div>

      <h4
        style={{
          fontSize: 'var(--font-size-md)',
          fontWeight: 'var(--font-weight-semibold)',
          color: 'var(--color-text-primary)',
          marginBottom: 'var(--space-1)',
        }}
      >
        {title}
      </h4>

      <p
        style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          maxWidth: '460px',
          marginBottom: errorCode ? 'var(--space-2)' : 'var(--space-4)',
        }}
      >
        {message}
      </p>

      {errorCode && (
        <span
          style={{
            fontSize: 'var(--font-size-xs)',
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-text-muted)',
            backgroundColor: 'var(--color-bg-surface)',
            padding: '2px 8px',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--color-border-subtle)',
            marginBottom: 'var(--space-4)',
          }}
        >
          Error Code: {errorCode}
        </span>
      )}

      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          isLoading={isRetrying}
          leftIcon={<RefreshCw size={14} />}
        >
          Try Again
        </Button>
      )}
    </div>
  );
};
