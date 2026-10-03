/**
 * Semantic Policy Status Presentation Component (Phase 12.1)
 *
 * IMPORTANT ARCHITECTURAL CONSTRAINT:
 * This component is strictly a PRESENTATION SYSTEM for Engine 8 policy decisions.
 * It contains ZERO policy or intervention logic. Decisions are calculated exclusively
 * by backend Engine 8 and passed to this component for rendering.
 */

import React from 'react';
import { CheckCircle2, Info, AlertTriangle, AlertOctagon, ShieldAlert } from 'lucide-react';
import type { PolicyDecisionType } from '../../types/firewall';

export interface SemanticStatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  decision: PolicyDecisionType | string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const SemanticStatusBadge: React.FC<SemanticStatusBadgeProps> = ({
  decision,
  size = 'md',
  showLabel = true,
  style,
  className = '',
  ...props
}) => {
  const normDecision = (decision || '').toUpperCase() as PolicyDecisionType;

  const getConfig = () => {
    switch (normDecision) {
      case 'ALLOW':
        return {
          label: 'Allow / Verified Neutral',
          bg: 'var(--color-allow-bg)',
          border: 'var(--color-allow-border)',
          color: 'var(--color-allow)',
          icon: <CheckCircle2 size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} aria-hidden="true" />,
        };
      case 'INFORM':
        return {
          label: 'Inform / Advisory',
          bg: 'var(--color-inform-bg)',
          border: 'var(--color-inform-border)',
          color: 'var(--color-inform)',
          icon: <Info size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} aria-hidden="true" />,
        };
      case 'WARN':
        return {
          label: 'Warning / Caution Required',
          bg: 'var(--color-warn-bg)',
          border: 'var(--color-warn-border)',
          color: 'var(--color-warn)',
          icon: <AlertTriangle size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} aria-hidden="true" />,
        };
      case 'PAUSE':
        return {
          label: 'Pause / Confirmation Required',
          bg: 'var(--color-pause-bg)',
          border: 'var(--color-pause-border)',
          color: 'var(--color-pause)',
          icon: <AlertOctagon size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} aria-hidden="true" />,
        };
      case 'BLOCK':
        return {
          label: 'Blocked / Threat Prevented',
          bg: 'var(--color-block-bg)',
          border: 'var(--color-block-border)',
          color: 'var(--color-block)',
          icon: <ShieldAlert size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} aria-hidden="true" />,
        };
      default:
        return {
          label: normDecision || 'Pending',
          bg: 'var(--color-bg-surface-elevated)',
          border: 'var(--color-border-subtle)',
          color: 'var(--color-text-secondary)',
          icon: <Info size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} aria-hidden="true" />,
        };
    }
  };

  const config = getConfig();

  const sizeStyles: React.CSSProperties =
    size === 'sm'
      ? { padding: '2px 8px', fontSize: 'var(--font-size-xs)' }
      : size === 'lg'
      ? { padding: '6px 14px', fontSize: 'var(--font-size-base)' }
      : { padding: '4px 10px', fontSize: 'var(--font-size-sm)' };

  return (
    <span
      className={`nivesh-semantic-status nivesh-status-${normDecision.toLowerCase()} ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        fontWeight: 'var(--font-weight-semibold)',
        borderRadius: 'var(--radius-full)',
        backgroundColor: config.bg,
        border: `1px solid ${config.border}`,
        color: config.color,
        whiteSpace: 'nowrap',
        lineHeight: 1.2,
        userSelect: 'none',
        ...sizeStyles,
        ...style,
      }}
      {...props}
    >
      <span style={{ display: 'flex', alignItems: 'center' }}>{config.icon}</span>
      {showLabel && <span>{config.label}</span>}
    </span>
  );
};
