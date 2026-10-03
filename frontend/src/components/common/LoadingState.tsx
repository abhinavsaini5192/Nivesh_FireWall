import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps extends React.HTMLAttributes<HTMLDivElement> {
  message?: string;
  steps?: string[];
  currentStepIndex?: number;
}

interface PipelineStageItem {
  id: string;
  label: string;
}

const PIPELINE_FLOW_STAGES: PipelineStageItem[] = [
  { id: 'content', label: 'CONTENT' },
  { id: 'claims', label: 'CLAIMS' },
  { id: 'actions', label: 'ACTIONS' },
  { id: 'identity', label: 'IDENTITY' },
  { id: 'evidence', label: 'EVIDENCE' },
  { id: 'threat', label: 'THREAT PATH' },
  { id: 'policy', label: 'POLICY' },
];

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
        backgroundColor: 'var(--color-bg-surface-elevated)',
        border: '1px solid var(--color-border-default)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-md)',
        gap: 'var(--space-6)',
        ...style,
      }}
      {...props}
    >
      {/* Pipeline Architecture Sequential Flow */}
      <div
        style={{
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--space-3)',
          paddingBottom: 'var(--space-4)',
          borderBottom: '1px solid var(--color-border-subtle)',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--color-text-muted)',
          }}
        >
          Sequential Verification Pipeline
        </div>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            maxWidth: '560px',
          }}
        >
          {PIPELINE_FLOW_STAGES.map((stg, i) => {
            const isDone = i < Math.floor((currentStepIndex / 9) * 7);
            const isNow = i === Math.min(6, Math.floor((currentStepIndex / 9) * 7));
            return (
              <React.Fragment key={stg.id}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-xs)',
                    backgroundColor: isDone
                      ? 'var(--color-allow-bg)'
                      : isNow
                      ? 'var(--color-accent-subtle)'
                      : 'var(--color-bg-subtle)',
                    border: `1px solid ${
                      isDone
                        ? 'var(--color-allow-border)'
                        : isNow
                        ? 'var(--color-border-accent)'
                        : 'var(--color-border-subtle)'
                    }`,
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                    color: isDone
                      ? 'var(--color-allow)'
                      : isNow
                      ? 'var(--color-accent-hover)'
                      : 'var(--color-text-muted)',
                  }}
                >
                  <span
                    style={{
                      width: '5px',
                      height: '5px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: isDone
                        ? 'var(--color-allow)'
                        : isNow
                        ? 'var(--color-accent)'
                        : 'var(--color-border-strong)',
                    }}
                  />
                  <span>{stg.label}</span>
                </div>
                {i < PIPELINE_FLOW_STAGES.length - 1 && (
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', opacity: 0.4 }}>→</span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
        <Loader2
          size={28}
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
      </div>

      {steps && steps.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)',
            width: '100%',
            maxWidth: '440px',
            backgroundColor: 'var(--color-bg-subtle)',
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
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
                    ? 'var(--color-accent-hover)'
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
                    boxShadow: isCurrent ? '0 0 6px var(--color-accent)' : 'none',
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

