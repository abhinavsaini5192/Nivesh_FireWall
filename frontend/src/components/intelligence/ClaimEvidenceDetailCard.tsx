import React from 'react';
import { CheckCircle2, Database } from 'lucide-react';
import type { FirewallEvidenceSummary } from '../../types/firewall';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { Panel } from '../common/Panel';

export interface ClaimEvidenceDetailCardProps {
  evidence: FirewallEvidenceSummary;
  sourceMode?: string;
}

export const ClaimEvidenceDetailCard: React.FC<ClaimEvidenceDetailCardProps> = ({
  evidence,
  sourceMode,
}) => {
  const getStatusBadgeVariant = (status: string): 'success' | 'danger' | 'warning' | 'neutral' => {
    switch (status) {
      case 'SUPPORTED':
        return 'success';
      case 'CONTRADICTED':
        return 'danger';
      case 'INSUFFICIENT_EVIDENCE':
      case 'SOURCE_CONFLICT':
      case 'SOURCE_UNAVAILABLE':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  const displaySourceMode = sourceMode ? sourceMode.toUpperCase() : 'AUTHORITATIVE_CACHE';

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <CheckCircle2 size={18} color="var(--color-accent)" />
            <CardTitle>Authoritative Registry & Evidence Verification</CardTitle>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <Badge variant={getStatusBadgeVariant(evidence.overall_status)} size="sm">
              Status: {evidence.overall_status}
            </Badge>
            <Badge variant="neutral" size="sm">
              <Database size={12} style={{ marginRight: '4px' }} />
              Source Mode: {displaySourceMode}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Direct verification metrics compiled from regulatory filings, public registries, and authoritative disclosures.
        </p>

        {/* Evidence Verification Metric Panels */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 'var(--space-2)',
          }}
        >
          <Panel title="Supported Claims">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-allow)' }}>
              {evidence.supported_claims_count}
            </span>
          </Panel>
          <Panel title="Contradicted Claims">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-block)' }}>
              {evidence.contradicted_claims_count}
            </span>
          </Panel>
          <Panel title="Insufficient Evidence">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-warn)' }}>
              {evidence.insufficient_claims_count}
            </span>
          </Panel>
          <Panel title="Source Filings Retrieved">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              {evidence.source_documents_count}
            </span>
          </Panel>
        </div>

        {/* Authoritative Sources Provenance Drilldown */}
        {evidence.authoritative_sources && evidence.authoritative_sources.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Authoritative Registry & Source Provenance
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {evidence.authoritative_sources.map((src, idx) => {
                const getModeBadge = (mode: string) => {
                  switch (mode) {
                    case 'LIVE':
                      return <Badge variant="success" size="sm">LIVE: Checked Live</Badge>;
                    case 'OFFICIAL_SNAPSHOT':
                      return <Badge variant="accent" size="sm">OFFICIAL SNAPSHOT: Downloaded Dataset</Badge>;
                    case 'CACHE':
                      return <Badge variant="neutral" size="sm">CACHE: Cached Evidence</Badge>;
                    case 'SOURCE_UNAVAILABLE':
                      return <Badge variant="warning" size="sm">UNAVAILABLE: Source Unreachable</Badge>;
                    default:
                      return <Badge variant="neutral" size="sm">FIXTURE: Test Fixture</Badge>;
                  }
                };

                return (
                  <div
                    key={idx}
                    style={{
                      padding: 'var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface-subtle)',
                      border: '1px solid var(--color-border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-1)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                          {src.source}
                        </span>
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                          ({src.source_authority})
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                        {getModeBadge(src.retrieval_mode)}
                        <Badge variant="neutral" size="sm">Freshness: {src.freshness}</Badge>
                      </div>
                    </div>

                    <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {src.evidence}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                      <span>Record ID: {src.source_record_id || 'N/A'}</span>
                      <span>Retrieved: {new Date(src.retrieved_at).toLocaleString()}</span>
                      {src.source_reference && (
                        <span style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          Ref: {src.source_reference}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ marginTop: 'var(--space-1)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          Retrieval Status: <strong>{evidence.retrieval_status}</strong> (Total verifications: {evidence.verification_count})
        </div>
      </CardContent>
    </Card>
  );
};
