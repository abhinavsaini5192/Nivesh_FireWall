import React from 'react';
import { AlertCircle, ArrowRight, Download, CreditCard, KeyRound } from 'lucide-react';
import type { FirewallActionSummary } from '../../types/firewall';
import { Badge } from '../common/Badge';

export interface HighImpactActionAlertProps {
  actions: FirewallActionSummary[];
  onSelectAction?: (action: FirewallActionSummary) => void;
}

export const HighImpactActionAlert: React.FC<HighImpactActionAlertProps> = ({
  actions,
  onSelectAction,
}) => {
  if (!actions || actions.length === 0) return null;

  const getActionIcon = (actionType: string) => {
    const lower = actionType.toLowerCase();
    if (lower.includes('pay') || lower.includes('transfer') || lower.includes('deposit')) {
      return <CreditCard size={18} color="var(--color-block)" />;
    }
    if (lower.includes('download') || lower.includes('install')) {
      return <Download size={18} color="var(--color-block)" />;
    }
    if (lower.includes('credential') || lower.includes('otp') || lower.includes('password')) {
      return <KeyRound size={18} color="var(--color-block)" />;
    }
    return <AlertCircle size={18} color="var(--color-warn)" />;
  };

  return (
    <div
      role="region"
      aria-label="High-Impact Actions Detected"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        padding: 'var(--space-4)',
        backgroundColor: 'var(--color-block-bg)',
        border: '1px solid var(--color-block-border)',
        borderLeft: '4px solid var(--color-block)',
        borderRadius: 'var(--radius-sm)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span
          style={{
            fontSize: 'var(--font-size-xs)',
            fontWeight: 700,
            color: 'var(--color-block)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          High-Impact Consequence Action Detected
        </span>
        <Badge variant="danger" size="sm">
          {actions.length} Action{actions.length === 1 ? '' : 's'}
        </Badge>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {actions.map((act) => (
          <div
            key={act.action_id}
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-3)',
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              {getActionIcon(act.action_type)}
              <div>
                <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                  Requested Action: {act.action_type.replace(/_/g, ' ')}
                </strong>
                {act.target && (
                  <span
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--color-text-secondary)',
                      display: 'block',
                    }}
                  >
                    Target: <code style={{ color: 'var(--color-accent-hover)' }}>{act.target}</code>
                  </span>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Badge
                variant={act.reversibility === 'IRREVERSIBLE' ? 'danger' : 'warning'}
                size="sm"
              >
                {act.reversibility}
              </Badge>
              {act.urgency_detected && (
                <Badge variant="warning" size="sm">
                  Urgency
                </Badge>
              )}
              {onSelectAction && (
                <button
                  onClick={() => onSelectAction(act)}
                  aria-label={`View details for ${act.action_type}`}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-accent)',
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '2px',
                    padding: '2px 4px',
                  }}
                >
                  <span>Inspect</span>
                  <ArrowRight size={12} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
