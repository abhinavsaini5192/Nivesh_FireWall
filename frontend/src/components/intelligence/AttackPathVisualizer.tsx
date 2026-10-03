import React from 'react';
import { GitCommit, Circle } from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { deriveAttackPathNodes } from '../../types/intelligence';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { MetadataRow } from '../common/MetadataRow';

export interface AttackPathVisualizerProps {
  analysis: FirewallAnalysisResponse;
}

export const AttackPathVisualizer: React.FC<AttackPathVisualizerProps> = ({ analysis }) => {
  const nodes = deriveAttackPathNodes(analysis);
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(
    nodes.find((n) => n.status === 'active')?.id || nodes[0]?.id || null
  );

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);
  const activeNodesCount = nodes.filter((n) => n.status === 'active').length;

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <GitCommit size={18} color="var(--color-block)" />
            <CardTitle>Sequential Attack-Path Stages</CardTitle>
          </div>
          <Badge variant={activeNodesCount > 1 ? 'danger' : 'neutral'} size="sm">
            {activeNodesCount} of {nodes.length} Stages Detected
          </Badge>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Maps sequential interaction transitions across structured threat stages without calculating subjective risk scores.
        </p>

        {/* Attack Stage Progression */}
        {analysis.threat.attack_stage && analysis.threat.terminal_stage && (
          <MetadataRow
            label="Attack Path Progression"
            value={
              <span style={{ color: 'var(--color-warn)' }}>
                {analysis.threat.attack_stage} → {analysis.threat.terminal_stage}
              </span>
            }
            isMono
          />
        )}

        {/* Screen-reader linear representation */}
        <div className="sr-only" aria-live="polite">
          Attack Path Progression: {nodes.map((n) => `${n.stageName} (${n.status})`).join(' then ')}
        </div>

        {/* Visual Connected Node Timeline */}
        <div
          role="region"
          aria-label="Attack Path Progression Flow"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            padding: 'var(--space-4)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
              gap: 'var(--space-3)',
              position: 'relative',
            }}
          >
            {nodes.map((node, idx) => {
              const isSelected = node.id === selectedNodeId;
              const isActive = node.status === 'active';
              const borderCol = isSelected
                ? 'var(--color-accent)'
                : isActive
                ? node.isTerminal
                  ? 'var(--color-block)'
                  : 'var(--color-warn)'
                : 'var(--color-border-subtle)';
              const bgCol = isSelected
                ? 'var(--color-bg-surface)'
                : isActive
                ? node.isTerminal
                  ? 'var(--color-block-bg)'
                  : 'var(--color-warn-bg)'
                : 'var(--color-bg-surface)';

              const severityTag = node.isTerminal
                ? 'Critical Consequence'
                : idx === 0
                ? 'Low Severity'
                : idx === 1
                ? 'Medium Severity'
                : 'High Severity';

              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedNodeId(node.id)}
                  aria-selected={isSelected}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '6px',
                    padding: 'var(--space-3) var(--space-4)',
                    backgroundColor: bgCol,
                    borderRadius: 'var(--radius-sm)',
                    border: `2px solid ${borderCol}`,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'var(--transition-fast)',
                    position: 'relative',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                        color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                      }}
                    >
                      STAGE {idx + 1}
                    </span>
                    {isActive ? (
                      <span
                        style={{
                          width: '10px',
                          height: '10px',
                          borderRadius: '50%',
                          backgroundColor: node.isTerminal ? 'var(--color-block)' : 'var(--color-warn)',
                          boxShadow: '0 0 6px rgba(239, 68, 68, 0.4)',
                        }}
                      />
                    ) : (
                      <Circle size={10} color="var(--color-text-muted)" />
                    )}
                  </div>

                  <span
                    style={{
                      fontSize: 'var(--font-size-sm)',
                      fontWeight: 600,
                      color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                    }}
                  >
                    {node.stageName}
                  </span>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '2px' }}>
                    <span
                      style={{
                        fontSize: '10px',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        backgroundColor: isActive
                          ? node.isTerminal
                            ? 'var(--color-block-bg)'
                            : 'var(--color-warn-bg)'
                          : 'var(--color-bg-subtle)',
                        color: isActive
                          ? node.isTerminal
                            ? 'var(--color-block)'
                            : 'var(--color-warn)'
                          : 'var(--color-text-muted)',
                        fontWeight: 600,
                      }}
                    >
                      {isActive ? (node.isTerminal ? 'Observed (Terminal)' : 'Observed Signal') : 'Absent / Not Detected'}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        backgroundColor: 'var(--color-bg-subtle)',
                        color: 'var(--color-text-muted)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {severityTag}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Node Deep Inspection */}
        {selectedNode && (
          <div
            style={{
              padding: 'var(--space-4)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Stage Inspection: {selectedNode.stageName}
              </span>
              <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                <Badge variant={selectedNode.status === 'active' ? (selectedNode.isTerminal ? 'danger' : 'warning') : 'neutral'} size="sm">
                  {selectedNode.status === 'active' ? 'OBSERVED IN SESSION' : 'SIGNAL ABSENT'}
                </Badge>
                {selectedNode.isTerminal && (
                  <Badge variant="danger" size="sm">
                    IRREVERSIBLE CONSEQUENCE TARGET
                  </Badge>
                )}
              </div>
            </div>

            {selectedNode.associatedAction && (
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                <strong>Correlated Action Target:</strong> <code>{selectedNode.associatedAction}</code>
              </div>
            )}
            {selectedNode.associatedClaim && (
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                <strong>Correlated Rationale:</strong> {selectedNode.associatedClaim}
              </div>
            )}
            {selectedNode.supportingSignal && (
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                <strong>Engine 6 Threat Signal:</strong> <Badge variant="neutral" size="sm">{selectedNode.supportingSignal}</Badge>
              </div>
            )}
          </div>
        )}

        {/* Claim → Action Relationship Connection */}
        {analysis.claims.length > 0 && analysis.actions.length > 0 && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'var(--color-bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Claim → Action Linkage
            </span>
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: 'var(--space-2)',
                fontSize: 'var(--font-size-xs)',
              }}
            >
              <span style={{ color: 'var(--color-text-primary)' }}>
                Rationale: {analysis.claims[0].text}
              </span>
              <span style={{ color: 'var(--color-warn)', fontWeight: 600 }}>──( RATIONALE FOR )──►</span>
              <span style={{ color: 'var(--color-accent-hover)', fontWeight: 600 }}>
                Target Action: {analysis.actions[0].action_type}
              </span>
              {analysis.actions[0].target && <code>{analysis.actions[0].target}</code>}
            </div>
          </div>
        )}

        {/* Threat Signals List */}
        {analysis.threat.threat_signals.length > 0 && (
          <div>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Detected Threat Signals:
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
              {analysis.threat.threat_signals.map((sig) => (
                <Badge key={sig} variant="danger" size="sm">
                  {sig}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
