import React from 'react';
import {
  ShieldCheck,
  Info,
  AlertTriangle,
  AlertOctagon,
  ShieldAlert,
} from 'lucide-react';
import type { PolicyDecisionType } from '../../types/firewall';
import { SemanticStatusBadge } from '../status/SemanticStatusBadge';

export interface ProtectionBannerProps {
  decision: PolicyDecisionType;
  title?: string;
  description?: string;
  onAction?: () => void;
  actionLabel?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const ProtectionBanner: React.FC<ProtectionBannerProps> = ({
  decision,
  title,
  description,
  onAction,
  actionLabel,
  className = '',
  style,
}) => {
  const getBannerConfig = () => {
    switch (decision) {
      case 'ALLOW':
        return {
          icon: <ShieldCheck size={20} color="var(--color-allow)" aria-hidden="true" />,
          defaultTitle: 'Action Permitted — Verified Neutral',
          borderColor: 'var(--color-allow-border)',
          bgColor: 'var(--color-allow-bg)',
          textColor: 'var(--color-allow)',
        };
      case 'INFORM':
        return {
          icon: <Info size={20} color="var(--color-inform)" aria-hidden="true" />,
          defaultTitle: 'Informational Advisory',
          borderColor: 'var(--color-inform-border)',
          bgColor: 'var(--color-inform-bg)',
          textColor: 'var(--color-inform)',
        };
      case 'WARN':
        return {
          icon: <AlertTriangle size={20} color="var(--color-warn)" aria-hidden="true" />,
          defaultTitle: 'Review Before Continuing',
          borderColor: 'var(--color-warn-border)',
          bgColor: 'var(--color-warn-bg)',
          textColor: 'var(--color-warn)',
        };
      case 'PAUSE':
        return {
          icon: <AlertOctagon size={20} color="var(--color-pause)" aria-hidden="true" />,
          defaultTitle: 'Action Paused — Verification Required',
          borderColor: 'var(--color-pause-border)',
          bgColor: 'var(--color-pause-bg)',
          textColor: 'var(--color-pause)',
        };
      case 'BLOCK':
      default:
        return {
          icon: <ShieldAlert size={20} color="var(--color-block)" aria-hidden="true" />,
          defaultTitle: 'Action Blocked — Threat Prevented',
          borderColor: 'var(--color-block-border)',
          bgColor: 'var(--color-block-bg)',
          textColor: 'var(--color-block)',
        };
    }
  };

  const config = getBannerConfig();
  const displayTitle = title || config.defaultTitle;

  return (
    <div
      role="alert"
      className={`nivesh-protection-banner nivesh-protection-banner-${decision.toLowerCase()} ${className}`}
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 'var(--space-3)',
        padding: 'var(--space-3) var(--space-4)',
        backgroundColor: config.bgColor,
        border: `1px solid ${config.borderColor}`,
        borderLeft: `4px solid ${config.borderColor}`,
        borderRadius: 'var(--radius-sm)',
        transition: 'all var(--transition-fast)',
        ...style,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flex: 1, minWidth: '240px' }}>
        <div style={{ display: 'flex', flexShrink: 0 }}>{config.icon}</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span
            style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-semibold)',
              color: config.textColor,
            }}
          >
            {displayTitle}
          </span>
          {description && (
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-secondary)',
                lineHeight: 1.4,
              }}
            >
              {description}
            </span>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <SemanticStatusBadge decision={decision} size="sm" />
        {onAction && actionLabel && (
          <button
            onClick={onAction}
            style={{
              background: 'none',
              border: 'none',
              color: config.textColor,
              fontSize: 'var(--font-size-xs)',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: '2px 6px',
            }}
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
};
