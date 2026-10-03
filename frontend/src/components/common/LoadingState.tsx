import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps extends React.HTMLAttributes<HTMLDivElement> {
  message?: string;
  steps?: string[];
  currentStepIndex?: number;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Analyzing financial interaction...',
  steps,
  currentStepIndex = 0,
  style,
  className = '',
  ...props
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`nivesh-loading-state ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-8) var(--space-6)',
        backgroundColor: 'var(--color-bg-subtle)',
        border: '1px solid var(--color-border-subtle)',
        borderRadius: 'var(--radius-md)',
        gap: 'var(--space-4)',
        ...style,
      }}
      {...props}
    >
      <Loader2
        size={32}
        style={{
          color: 'var(--color-accent)',
          animation: 'spin 1s linear infinite',
        }}
        aria-hidden="true"
      />
      <div style={{ textAlign: 'center' }}>
        <p
          style={{
            fontSize: 'var(--font-size-base)',
            fontWeight: 'var(--font-weight-medium)',
            color: 'var(--color-text-primary)',
            margin: 0,
          }}
        >
          {message}
        </p>
      </div>

      {steps && steps.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)',
            width: '100%',
            maxWidth: '360px',
            marginTop: 'var(--space-2)',
          }}
        >
          {steps.map((step, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex;
            return (
              <div
                key={step}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  fontSize: 'var(--font-size-xs)',
                  color: isCompleted
                    ? 'var(--color-allow)'
                    : isCurrent
                    ? 'var(--color-accent)'
                    : 'var(--color-text-muted)',
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: isCompleted
                      ? 'var(--color-allow)'
                      : isCurrent
                      ? 'var(--color-accent)'
                      : 'var(--color-border-strong)',
                  }}
                />
                <span>{step}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
