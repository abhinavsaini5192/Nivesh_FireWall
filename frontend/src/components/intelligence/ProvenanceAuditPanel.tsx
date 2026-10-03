import React from 'react';
import { Terminal, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { sanitizeDataForRendering } from '../../types/intelligence';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { MetadataRow } from '../common/MetadataRow';

export interface ProvenanceAuditPanelProps {
  analysis: FirewallAnalysisResponse;
}

export const ProvenanceAuditPanel: React.FC<ProvenanceAuditPanelProps> = ({ analysis }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const cleanProvenance = sanitizeDataForRendering(analysis.provenance || {});

  const handleCopyProvenance = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(cleanProvenance, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore
    }
  };

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
            background: 'none',
            border: 'none',
            padding: 0,
            cursor: 'pointer',
            textAlign: 'left',
          }}
          aria-expanded={isExpanded}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Terminal size={18} color="var(--color-text-muted)" />
            <CardTitle>Technical Provenance & Pipeline Audit</CardTitle>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Badge variant="neutral" size="sm">
              {analysis.pipeline_status} • {analysis.duration_ms.toFixed(1)}ms
            </Badge>
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>
      </CardHeader>

      {isExpanded && (
        <CardContent style={{ gap: 'var(--space-3)', paddingTop: 0 }}>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
            Audit verification trail for technical demonstrations, verification probes, and adapter tracing.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <MetadataRow label="Analysis Correlation ID" value={analysis.analysis_id} copyableText={analysis.analysis_id} isMono />
            <MetadataRow label="Pipeline Status" value={analysis.pipeline_status} isMono />
            <MetadataRow label="Execution Duration" value={`${analysis.duration_ms.toFixed(2)} ms`} isMono />
            <MetadataRow label="Pipeline Started" value={analysis.created_at} isMono />
            {analysis.completed_at && (
              <MetadataRow label="Pipeline Completed" value={analysis.completed_at} isMono />
            )}
            <MetadataRow label="Channel Source" value={analysis.content.channel} />
            <MetadataRow label="Input Content Type" value={analysis.content.input_type} />
            <MetadataRow label="Policy Engine Version" value={`v${analysis.decision.policy_version}`} isMono />
          </div>

          {/* Sanitized Lineage JSON */}
          <div style={{ marginTop: 'var(--space-2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Sanitized Engine Lineage JSON:
              </span>
              <button
                onClick={handleCopyProvenance}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: 'none',
                  border: 'none',
                  fontSize: '11px',
                  color: copied ? 'var(--color-allow)' : 'var(--color-accent)',
                  cursor: 'pointer',
                }}
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>
            <pre
              style={{
                padding: 'var(--space-3)',
                backgroundColor: 'var(--color-bg-canvas)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border-subtle)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-text-secondary)',
                overflowX: 'auto',
                maxHeight: '260px',
                margin: 0,
              }}
            >
              {JSON.stringify(cleanProvenance, null, 2)}
            </pre>
          </div>
        </CardContent>
      )}
    </Card>
  );
};
