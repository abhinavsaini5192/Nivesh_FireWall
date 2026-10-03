import React from 'react';
import { FileText, CheckCircle2, XCircle, AlertCircle, HelpCircle } from 'lucide-react';
import type { FirewallClaimSummary } from '../../types/firewall';
import { deriveClaimSPO } from '../../types/intelligence';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface ClaimsCardProps {
  claims: FirewallClaimSummary[];
}

export const ClaimsCard: React.FC<ClaimsCardProps> = ({ claims }) => {
  const claimSPOs = deriveClaimSPO(claims);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUPPORTED':
        return <CheckCircle2 size={16} color="var(--color-allow)" />;
      case 'CONTRADICTED':
        return <XCircle size={16} color="var(--color-block)" />;
      case 'INSUFFICIENT_EVIDENCE':
      case 'SOURCE_CONFLICT':
      case 'SOURCE_UNAVAILABLE':
        return <AlertCircle size={16} color="var(--color-warn)" />;
      default:
        return <HelpCircle size={16} color="var(--color-text-muted)" />;
    }
  };

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

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <FileText size={18} color="var(--color-accent)" />
            <CardTitle>Structured Subject-Predicate-Object Claims</CardTitle>
          </div>
          <Badge variant={claims.length > 0 ? 'accent' : 'neutral'} size="sm">
            {claims.length} Claim{claims.length === 1 ? '' : 's'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-3)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Atomic assertions decomposed into subject, predicate, modality, and empirical verification requirements.
        </p>

        {claimSPOs.length === 0 ? (
          <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            No explicit factual claims or return promises extracted from content.
          </div>
        ) : (
          claimSPOs.map((spo) => (
            <div
              key={spo.claimId}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
                padding: 'var(--space-3)',
                backgroundColor: 'var(--color-bg-surface)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border-subtle)',
              }}
            >
              {/* Header: Raw text & Evidence status */}
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
                  {getStatusIcon(spo.verificationStatus)}
                  <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                    "{spo.rawText}"
                  </span>
                </div>
                <Badge variant={getStatusBadgeVariant(spo.verificationStatus)} size="sm">
                  {spo.verificationStatus}
                </Badge>
              </div>

              {/* SPO Triple Visualization */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  padding: 'var(--space-2) var(--space-3)',
                  backgroundColor: 'var(--color-bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-xs)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Subject:</span>
                  <strong style={{ color: 'var(--color-text-primary)' }}>{spo.subject}</strong>
                </div>
                <span style={{ color: 'var(--color-accent)' }}>─[&nbsp;<code>{spo.predicate}</code>&nbsp;]─►</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Target/Object:</span>
                  <strong style={{ color: 'var(--color-text-primary)' }}>{spo.object}</strong>
                </div>
                <span style={{ color: 'var(--color-text-muted)' }}>•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Topic:</span>
                  <strong style={{ color: 'var(--color-text-secondary)' }}>{spo.topic}</strong>
                </div>
                <span style={{ color: 'var(--color-text-muted)' }}>•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>Modality:</span>
                  <code style={{ color: 'var(--color-text-secondary)' }}>{spo.modality}</code>
                </div>
              </div>

              {/* Semantic Status Explanation */}
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 0 }}>
                <strong>Verification Finding:</strong> {spo.statusExplanation}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
};
