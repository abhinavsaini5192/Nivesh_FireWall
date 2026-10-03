import React from 'react';
import {
  ShieldCheck,
  Info,
  AlertTriangle,
  AlertOctagon,
  ShieldAlert,
  Clock,
  Copy,
  Check,
} from 'lucide-react';
import type { InterventionModel } from '../../types/intervention';
import { Card, CardContent } from '../common/Card';
import { SemanticStatusBadge } from '../status/SemanticStatusBadge';

export interface InterventionHeaderProps {
  model: InterventionModel;
  policyVersion?: string;
  onCopyAnalysisId?: () => void;
  isCopied?: boolean;
}

export const InterventionHeader: React.FC<InterventionHeaderProps> = ({
  model,
  policyVersion = '8.0.0',
  onCopyAnalysisId,
  isCopied = false,
}) => {
  const getHeaderVisuals = () => {
    switch (model.decision) {
      case 'ALLOW':
        return {
          icon: <ShieldCheck size={32} color="var(--color-allow)" aria-hidden="true" />,
          borderColor: 'var(--color-allow-border)',
          titleColor: 'var(--color-allow)',
          subtleBg: 'rgba(16, 185, 129, 0.05)',
        };
      case 'INFORM':
        return {
          icon: <Info size={32} color="var(--color-inform)" aria-hidden="true" />,
          borderColor: 'var(--color-inform-border)',
          titleColor: 'var(--color-inform)',
          subtleBg: 'rgba(14, 165, 233, 0.05)',
        };
      case 'WARN':
        return {
          icon: <AlertTriangle size={32} color="var(--color-warn)" aria-hidden="true" />,
          borderColor: 'var(--color-warn-border)',
          titleColor: 'var(--color-warn)',
          subtleBg: 'rgba(245, 158, 11, 0.05)',
        };
      case 'PAUSE':
        return {
          icon: <AlertOctagon size={32} color="var(--color-pause)" aria-hidden="true" />,
          borderColor: 'var(--color-pause-border)',
          titleColor: 'var(--color-pause)',
          subtleBg: 'rgba(236, 72, 153, 0.05)',
        };
      case 'BLOCK':
      default:
        return {
          icon: <ShieldAlert size={32} color="var(--color-block)" aria-hidden="true" />,
          borderColor: 'var(--color-block-border)',
          titleColor: 'var(--color-block)',
          subtleBg: 'rgba(239, 68, 68, 0.05)',
        };
    }
  };

  const visuals = getHeaderVisuals();

  return (
    <Card
      variant="elevated"
      style={{
        borderLeft: `5px solid ${visuals.borderColor}`,
        backgroundColor: 'var(--color-bg-surface)',
        width: '100%',
      }}
    >
      <CardContent style={{ gap: 'var(--space-4)', padding: 'var(--space-6)' }}>
        {/* Top Meta Bar */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-3)',
            paddingBottom: 'var(--space-3)',
            borderBottom: '1px solid var(--color-border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              Analysis ID:
            </span>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-text-primary)',
                fontWeight: 600,
              }}
            >
              {model.analysisId}
            </span>
            {onCopyAnalysisId && (
              <button
                onClick={onCopyAnalysisId}
                aria-label="Copy Analysis ID"
                style={{
                  background: 'none',
                  border: 'none',
                  color: isCopied ? 'var(--color-allow)' : 'var(--color-text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  padding: '2px',
                }}
              >
                {isCopied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              Severity: <strong>{model.severity}</strong> • Policy v{policyVersion}
            </span>
          </div>
        </div>

        {/* Hero Title & Status Badge */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', flex: 1, minWidth: '260px' }}>
            <div style={{ display: 'flex', flexShrink: 0 }}>{visuals.icon}</div>
            <div>
              <h2
                style={{
                  fontSize: 'var(--font-size-xl)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: visuals.titleColor,
                  margin: 0,
                  letterSpacing: '0.01em',
                }}
              >
                {model.headline}
              </h2>
              <span
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  marginTop: '2px',
                  display: 'block',
                }}
              >
                {model.subheadline}
              </span>
            </div>
          </div>

          <SemanticStatusBadge decision={model.decision} size="lg" />
        </div>

        {/* User-facing Non-accusatory Message */}
        <div
          style={{
            padding: 'var(--space-4)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          <p
            style={{
              fontSize: 'var(--font-size-base)',
              color: 'var(--color-text-primary)',
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            {model.userMessage}
          </p>
        </div>

        {/* Cooldown Timer Alert (Engine 8 Policy Recommendation) */}
        {model.cooldownSeconds && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
            }}
          >
            <Clock size={14} color="var(--color-pause)" />
            <span>
              Policy recommends a minimum cooldown pause of <strong>{model.cooldownSeconds} seconds</strong> before
              taking any irreversible action.
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
