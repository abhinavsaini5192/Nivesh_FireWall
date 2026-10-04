/**
 * Policy Decision Framework Component
 * Structured horizontal progression showing Engine 8 policy decision states.
 * Calm, precise, and authoritative.
 */

import React from 'react';
import { CheckCircle2, Info, AlertTriangle, AlertOctagon, ShieldAlert, ArrowRight } from 'lucide-react';
import type { PolicyDecisionType } from '../../types/firewall';

export interface PolicyDecisionFrameworkProps {
  currentDecision?: PolicyDecisionType | null;
}

interface PolicyStateItem {
  decision: PolicyDecisionType;
  label: string;
  tagline: string;
  explanation: string;
  color: string;
  bg: string;
  border: string;
  icon: React.ReactNode;
}

const POLICY_STATES: PolicyStateItem[] = [
  {
    decision: 'ALLOW',
    label: 'ALLOW',
    tagline: 'Verified Neutral',
    explanation: 'No prohibited return promises or identity anomalies detected.',
    color: 'var(--color-allow)',
    bg: 'var(--color-allow-bg)',
    border: 'var(--color-allow-border)',
    icon: <CheckCircle2 size={15} color="var(--color-allow)" />,
  },
  {
    decision: 'INFORM',
    label: 'INFORM',
    tagline: 'Advisory Note',
    explanation: 'Contextual risk factors or disclaimer disclosures surfaced.',
    color: 'var(--color-inform)',
    bg: 'var(--color-inform-bg)',
    border: 'var(--color-inform-border)',
    icon: <Info size={15} color="var(--color-inform)" />,
  },
  {
    decision: 'WARN',
    label: 'WARN',
    tagline: 'Caution Required',
    explanation: 'Unregistered entities or questionable assertions identified.',
    color: 'var(--color-warn)',
    bg: 'var(--color-warn-bg)',
    border: 'var(--color-warn-border)',
    icon: <AlertTriangle size={15} color="var(--color-warn)" />,
  },
  {
    decision: 'PAUSE',
    label: 'PAUSE',
    tagline: 'Confirmation Required',
    explanation: 'High-impact irreversible actions detected; mandatory cooling pause.',
    color: 'var(--color-pause)',
    bg: 'var(--color-pause-bg)',
    border: 'var(--color-pause-border)',
    icon: <AlertOctagon size={15} color="var(--color-pause)" />,
  },
  {
    decision: 'BLOCK',
    label: 'BLOCK',
    tagline: 'Threat Prevented',
    explanation: 'Contradicted evidence or confirmed scam fingerprint matched.',
    color: 'var(--color-block)',
    bg: 'var(--color-block-bg)',
    border: 'var(--color-block-border)',
    icon: <ShieldAlert size={15} color="var(--color-block)" />,
  },
];

export const PolicyDecisionFramework: React.FC<PolicyDecisionFrameworkProps> = ({
  currentDecision,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        width: '100%',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 'var(--space-2)',
          alignItems: 'stretch',
        }}
      >
        {POLICY_STATES.map((item, idx) => {
          const isActive = currentDecision === item.decision;
          return (
            <div
              key={item.decision}
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isActive ? item.bg : 'var(--color-bg-surface-elevated)',
                border: `1px solid ${isActive ? item.border : 'var(--color-border-subtle)'}`,
                boxShadow: isActive ? `0 0 12px ${item.bg}` : 'none',
                transition: 'all var(--transition-normal)',
                position: 'relative',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {item.icon}
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                        fontWeight: 'var(--font-weight-bold)',
                        color: item.color,
                        letterSpacing: '0.04em',
                      }}
                    >
                      {item.label}
                    </span>
                  </div>
                  {idx < POLICY_STATES.length - 1 && (
                    <ArrowRight
                      size={12}
                      style={{ color: 'var(--color-text-muted)', opacity: 0.5, display: 'none' }}
                      className="desktop-hint"
                    />
                  )}
                </div>

                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 'var(--font-weight-medium)',
                    color: 'var(--color-text-primary)',
                    marginBottom: '4px',
                  }}
                >
                  {item.tagline}
                </div>

                <p
                  style={{
                    fontSize: '11px',
                    color: 'var(--color-text-muted)',
                    lineHeight: 1.4,
                    margin: 0,
                  }}
                >
                  {item.explanation}
                </p>
              </div>

              {isActive && (
                <div
                  style={{
                    marginTop: 'var(--space-2)',
                    paddingTop: 'var(--space-1)',
                    borderTop: `1px solid ${item.border}`,
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    color: item.color,
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  ● Active Assessment
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
