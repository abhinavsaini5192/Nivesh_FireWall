import React from 'react';
import { UserCheck, ArrowRight } from 'lucide-react';
import type { FirewallIdentitySummary } from '../../types/firewall';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { MetadataRow } from '../common/MetadataRow';

export interface EntityRelationshipGraphProps {
  identity: FirewallIdentitySummary;
}

export const EntityRelationshipGraph: React.FC<EntityRelationshipGraphProps> = ({ identity }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ESTABLISHED':
        return 'var(--color-allow)';
      case 'IDENTITY_MISMATCH':
        return 'var(--color-block)';
      case 'NOT_ESTABLISHED':
      case 'AMBIGUOUS':
      default:
        return 'var(--color-warn)';
    }
  };

  const getStatusBadgeVariant = (status: string): 'success' | 'danger' | 'warning' | 'neutral' => {
    switch (status) {
      case 'ESTABLISHED':
        return 'success';
      case 'IDENTITY_MISMATCH':
        return 'danger';
      case 'NOT_ESTABLISHED':
      case 'AMBIGUOUS':
      default:
        return 'warning';
    }
  };

  const claimedName = identity.claimed_entities[0] || 'Unidentified Entity';
  const confidencePercent = (identity.confidence * 100).toFixed(0);

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <UserCheck size={18} color="var(--color-accent)" />
            <CardTitle>Entity Identity Resolution</CardTitle>
          </div>
          <Badge variant={getStatusBadgeVariant(identity.identity_status)} size="sm">
            Status: {identity.identity_status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Traces entity identity assertions against official regulatory registries without drawing subjective or accusatory conclusions.
        </p>

        {/* Visual Entity Resolution Flow */}
        <div
          role="region"
          aria-label="Entity Verification Flow"
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-3)',
            padding: 'var(--space-4)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          {/* Node 1: Claimed Entity */}
          <div
            style={{
              flex: '1 1 180px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Claimed Persona / Entity
            </span>
            <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Subject: {claimedName}
            </span>
            <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
              From content presentation
            </span>
          </div>

          <ArrowRight size={18} color="var(--color-text-muted)" style={{ flexShrink: 0 }} />

          {/* Node 2: Authoritative Database Cross-Reference */}
          <div
            style={{
              flex: '1 1 200px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Official Cross-Reference
            </span>
            <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-accent)' }}>
              SEBI / Registered Directory
            </span>
            <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
              Registration & intermediary records
            </span>
          </div>

          <ArrowRight size={18} color="var(--color-text-muted)" style={{ flexShrink: 0 }} />

          {/* Node 3: Verification Outcome */}
          <div
            style={{
              flex: '1 1 200px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: `1px solid ${getStatusColor(identity.identity_status)}`,
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Resolution Finding
            </span>
            <span
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 700,
                color: getStatusColor(identity.identity_status),
              }}
            >
              {identity.identity_status}
            </span>
            <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
              Resolution Confidence: {confidencePercent}%
            </span>
          </div>
        </div>

        {/* Structured Identity Metadata & Findings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <MetadataRow
            label="Claimed Identity Resolution"
            value={<strong>{identity.identity_status}</strong>}
          />
          <MetadataRow
            label="Resolution Confidence"
            value={`${confidencePercent}%`}
            isMono
          />

          {identity.claimed_entities.length > 0 && (
            <div style={{ marginTop: 'var(--space-1)' }}>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Identified Entity References:
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                {identity.claimed_entities.map((ent) => (
                  <Badge key={ent} variant="accent" size="sm">
                    {ent}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {identity.findings_summary.length > 0 && (
            <div style={{ marginTop: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Authoritative Findings Summary:
              </span>
              <ul
                style={{
                  paddingLeft: 'var(--space-4)',
                  marginTop: 'var(--space-1)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.5,
                }}
              >
                {identity.findings_summary.map((finding, idx) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>
                    {finding}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
