import React from 'react';
import { Fingerprint, Check, X } from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { deriveFingerprintDimensions } from '../../types/intelligence';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { MetadataRow } from '../common/MetadataRow';

export interface FingerprintIntelligenceCardProps {
  analysis: FirewallAnalysisResponse;
}

export const FingerprintIntelligenceCard: React.FC<FingerprintIntelligenceCardProps> = ({ analysis }) => {
  const { fingerprint } = analysis;
  const dimensions = deriveFingerprintDimensions(analysis);
  const isMatch = fingerprint.match_type !== 'NO_MATCH';

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Fingerprint size={18} color="var(--color-accent)" />
            <CardTitle>Structural Match Blueprint & Dimensions</CardTitle>
          </div>
          <Badge variant={isMatch ? 'warning' : 'neutral'} size="sm">
            Pattern: {fingerprint.match_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Compares interaction structure against privacy-preserving structural template signatures across historical observations.
        </p>

        {/* Primary Fingerprint Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <MetadataRow
            label="Structural Match Type"
            value={<strong>{fingerprint.match_type}</strong>}
          />
          <MetadataRow
            label="Structural Equivalence"
            value={
              fingerprint.match_type === 'SEMANTIC_VARIANT' || fingerprint.match_type === 'EXACT_MATCH'
                ? 'YES (Known Template Structure)'
                : 'NO'
            }
          />
          {fingerprint.fingerprint_id && (
            <MetadataRow
              label="Fingerprint Identifier"
              value={fingerprint.fingerprint_id}
              copyableText={fingerprint.fingerprint_id}
              isMono
            />
          )}
          <MetadataRow
            label="Network Observation Count"
            value={
              isMatch
                ? `${fingerprint.observation_count} sightings across ${fingerprint.distinct_channels_count} channels`
                : '0 matching sightings recorded'
            }
          />
        </div>

        {/* Structural Pattern Dimensions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
            Structural Pattern Dimensions ({dimensions.filter((d) => d.matched).length} / {dimensions.length} Matched)
          </span>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--space-2)',
            }}
          >
            {dimensions.map((dim) => (
              <div
                key={dim.name}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 'var(--space-2)',
                  padding: 'var(--space-3)',
                  backgroundColor: dim.matched ? 'var(--color-bg-subtle)' : 'var(--color-bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${dim.matched ? 'var(--color-warn-border)' : 'var(--color-border-subtle)'}`,
                }}
              >
                <div
                  style={{
                    padding: '2px',
                    borderRadius: '50%',
                    backgroundColor: dim.matched ? 'var(--color-warn-bg)' : 'var(--color-bg-subtle)',
                    color: dim.matched ? 'var(--color-warn)' : 'var(--color-text-muted)',
                    flexShrink: 0,
                  }}
                >
                  {dim.matched ? <Check size={14} /> : <X size={14} />}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: dim.matched ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>
                    {dim.name}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    {dim.detail}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Non-Accusatory Collective Intelligence Disclosure */}
        <div
          style={{
            padding: 'var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            lineHeight: 1.4,
          }}
        >
          <strong>Collective Intelligence Note:</strong> Structural pattern matching identifies architectural similarity to known campaign blueprints. A structural match informs safety interventions but is not used in isolation as automated proof of criminal misconduct.
        </div>
      </CardContent>
    </Card>
  );
};
