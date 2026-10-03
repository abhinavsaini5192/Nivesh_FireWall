import React from 'react';
import { CheckCircle2, Database } from 'lucide-react';
import type { FirewallEvidenceSummary } from '../../types/firewall';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { Panel } from '../common/Panel';

export interface ClaimEvidenceDetailCardProps {
  evidence: FirewallEvidenceSummary;
  sourceMode?: string;
  claims?: Array<{
    claim_id: string;
    text: string;
    topic?: string;
    predicate?: string;
    verification_status?: string;
    discrepancy_explanation?: string;
  }>;
}

export const ClaimEvidenceDetailCard: React.FC<ClaimEvidenceDetailCardProps> = ({
  evidence,
  sourceMode,
  claims = [],
}) => {
  const getStatusBadgeVariant = (status: string): 'success' | 'danger' | 'warning' | 'neutral' => {
    switch (status) {
      case 'SUPPORTED':
      case 'VERIFIED':
        return 'success';
      case 'CONTRADICTED':
        return 'danger';
      case 'INSUFFICIENT_EVIDENCE':
      case 'UNVERIFIED':
      case 'SOURCE_CONFLICT':
      case 'SOURCE_UNAVAILABLE':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'SUPPORTED':
      case 'VERIFIED':
        return 'Verified';
      case 'CONTRADICTED':
        return 'Contradicted';
      case 'INSUFFICIENT_EVIDENCE':
      case 'UNVERIFIED':
        return 'Insufficient Record Evidence';
      case 'INAPPLICABLE':
        return 'Inapplicable';
      default:
        return status || 'Unverified';
    }
  };

  const displaySourceMode = sourceMode ? sourceMode.toUpperCase() : 'AUTHORITATIVE_CACHE';

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
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

        {/* 4-Column Forensic Verification Metrics */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: 'var(--space-2)',
          }}
        >
          <Panel title="Supported Claims">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-allow)', fontFamily: 'var(--font-mono)' }}>
              {evidence.supported_claims_count}
            </span>
          </Panel>
          <Panel title="Contradicted Claims">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-block)', fontFamily: 'var(--font-mono)' }}>
              {evidence.contradicted_claims_count}
            </span>
          </Panel>
          <Panel title="Insufficient Evidence">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-warn)', fontFamily: 'var(--font-mono)' }}>
              {evidence.insufficient_claims_count}
            </span>
          </Panel>
          <Panel title="Source Filings Retrieved">
            <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
              {evidence.source_documents_count}
            </span>
          </Panel>
        </div>

        {/* Forensic Claim-by-Claim Audit Table */}
        {claims && claims.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Forensic Claim Audit Log
            </span>
            <div
              style={{
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border-subtle)',
                overflow: 'hidden',
                backgroundColor: 'var(--color-bg-subtle)',
              }}
            >
              {claims.map((claim, cIdx) => {
                const status = claim.verification_status || 'INSUFFICIENT_EVIDENCE';
                const badgeVariant = getStatusBadgeVariant(status);
                const isContradicted = status === 'CONTRADICTED';
                const isSupported = status === 'SUPPORTED';

                return (
                  <div
                    key={claim.claim_id || cIdx}
                    style={{
                      padding: 'var(--space-3) var(--space-4)',
                      borderBottom: cIdx < claims.length - 1 ? '1px solid var(--color-border-subtle)' : 'none',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)',
                      backgroundColor: isContradicted
                        ? 'rgba(239, 68, 68, 0.03)'
                        : isSupported
                        ? 'rgba(34, 197, 94, 0.03)'
                        : 'transparent',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                          {claim.claim_id}
                        </span>
                        {claim.topic && (
                          <Badge variant="neutral" size="sm">
                            {claim.topic}
                          </Badge>
                        )}
                      </div>
                      <Badge variant={badgeVariant} size="sm">
                        {getStatusLabel(status)}
                      </Badge>
                    </div>

                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-primary)', fontWeight: 500 }}>
                      &ldquo;{claim.text}&rdquo;
                    </div>

                    {isContradicted && (
                      <div
                        style={{
                          fontSize: '11px',
                          color: 'var(--color-block)',
                          padding: 'var(--space-1) var(--space-2)',
                          backgroundColor: 'var(--color-block-bg)',
                          borderRadius: 'var(--radius-xs)',
                          borderLeft: '2px solid var(--color-block)',
                        }}
                      >
                        <strong>Forensic Discrepancy:</strong> Asserted claim directly contradicts authoritative regulatory disclosure data.
                      </div>
                    )}
                    {status === 'INSUFFICIENT_EVIDENCE' && (
                      <div
                        style={{
                          fontSize: '11px',
                          color: 'var(--color-warn)',
                          padding: 'var(--space-1) var(--space-2)',
                          backgroundColor: 'var(--color-warn-bg)',
                          borderRadius: 'var(--radius-xs)',
                          borderLeft: '2px solid var(--color-warn)',
                        }}
                      >
                        <strong>Unverified Status:</strong> No corroborating evidence located in verified registries. High caution required.
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

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
                    case 'LIVE_AUTHORIZED':
                      return <Badge variant="success" size="sm">LIVE AUTHORIZED: Authenticated Feed</Badge>;
                    case 'LIVE_PUBLIC':
                      return <Badge variant="accent" size="sm">LIVE PUBLIC: Public Dissemination</Badge>;
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
                      backgroundColor: 'var(--color-bg-subtle)',
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
                        {src.provider && (
                          <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', backgroundColor: 'var(--color-bg-surface)', padding: '1px 6px', borderRadius: '4px', border: '1px solid var(--color-border-subtle)' }}>
                            {src.provider}
                          </span>
                        )}
                      </div>
                      <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                        {getModeBadge(src.retrieval_mode)}
                        <Badge variant="neutral" size="sm">Freshness: {src.freshness}</Badge>
                      </div>
                    </div>

                    <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {src.evidence}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '4px', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
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

