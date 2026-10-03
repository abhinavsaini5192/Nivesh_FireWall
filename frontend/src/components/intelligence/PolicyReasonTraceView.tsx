import React from 'react';
import { GitMerge, ArrowDown } from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface PolicyReasonTraceViewProps {
  analysis: FirewallAnalysisResponse;
}

export const PolicyReasonTraceView: React.FC<PolicyReasonTraceViewProps> = ({ analysis }) => {
  const { decision, identity, actions, threat, behaviour, evidence } = analysis;

  const contributingInputs = [
    {
      engine: 'Engine 9 (Identity)',
      label: 'Identity Status',
      value: identity.identity_status,
      isTrigger: identity.identity_status === 'IDENTITY_MISMATCH' || identity.identity_status === 'NOT_ESTABLISHED',
    },
    {
      engine: 'Engine 3 (Action)',
      label: 'Requested Action',
      value: actions[0] ? `${actions[0].action_type} (${actions[0].reversibility})` : 'No Action Requested',
      isTrigger: actions.some((a) => a.impact_category === 'FINANCIAL_TRANSACTION' || a.action_type.includes('PAY')),
    },
    {
      engine: 'Engine 6 (Threat)',
      label: 'Attack Stage',
      value: threat.terminal_stage || threat.attack_stage || 'No Path Detected',
      isTrigger: threat.high_impact_action_count > 0 || threat.threat_signals.length > 0,
    },
    {
      engine: 'Engine 10 (Behaviour)',
      label: 'Temporal Dynamic',
      value: behaviour.time_pressure_detected ? 'Time Pressure Detected' : behaviour.rapid_escalation_detected ? 'Rapid Action Escalation' : 'Normal Cadence',
      isTrigger: behaviour.time_pressure_detected || behaviour.rapid_escalation_detected || behaviour.channel_migration_detected,
    },
    {
      engine: 'Engine 5 (Evidence)',
      label: 'Claim Verification',
      value: evidence.overall_status,
      isTrigger: evidence.overall_status === 'CONTRADICTED' || evidence.overall_status === 'INSUFFICIENT_EVIDENCE',
    },
  ];

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <GitMerge size={18} color="var(--color-accent)" />
            <CardTitle>Engine 8 Policy Reason Trace</CardTitle>
          </div>
          <Badge variant="neutral" size="sm">
            Policy Engine v{decision.policy_version}
          </Badge>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Traces the causal evaluation path from multi-engine structured findings to Engine 8's deterministic policy decision.
        </p>

        {/* Tree Step 1: Upstream Intelligence Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Step 1: Intelligence Engine Evaluated Signals
          </span>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
              gap: 'var(--space-2)',
            }}
          >
            {contributingInputs.map((input) => (
              <div
                key={input.engine}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  padding: 'var(--space-2) var(--space-3)',
                  backgroundColor: input.isTrigger ? 'var(--color-bg-subtle)' : 'var(--color-bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${input.isTrigger ? 'var(--color-warn-border)' : 'var(--color-border-subtle)'}`,
                }}
              >
                <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
                  {input.engine}
                </span>
                <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {input.label}
                </span>
                <span style={{ fontSize: '11px', color: input.isTrigger ? 'var(--color-warn)' : 'var(--color-text-secondary)' }}>
                  {input.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Trace Flow Arrow */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <ArrowDown size={18} color="var(--color-text-muted)" />
        </div>

        {/* Tree Step 2: Policy Reason Codes Evaluated */}
        <div
          style={{
            padding: 'var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)',
          }}
        >
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Step 2: Policy Rule & Reason Code Convergence
          </span>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 0 }}>
            {decision.primary_reason}
          </p>
          {decision.reason_codes.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
              {decision.reason_codes.map((code) => (
                <Badge key={code} variant="accent" size="sm">
                  {code}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Trace Flow Arrow */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <ArrowDown size={18} color="var(--color-text-muted)" />
        </div>

        {/* Tree Step 3: Authoritative Final Policy Decision */}
        <div
          style={{
            padding: 'var(--space-3)',
            backgroundColor: 'var(--color-bg-surface)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-3)',
          }}
        >
          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Step 3: Canonical Policy Intervention
            </span>
            <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Sole Authority: Engine 8 Policy Evaluator
            </div>
          </div>
          <Badge
            variant={
              decision.decision === 'BLOCK'
                ? 'danger'
                : decision.decision === 'WARN' || decision.decision === 'PAUSE'
                ? 'warning'
                : decision.decision === 'ALLOW'
                ? 'success'
                : 'neutral'
            }
            size="md"
          >
            Intervention: {decision.decision}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};
