import { AlertTriangle, ExternalLink } from 'lucide-react';
import type { FirewallActionSummary } from '../../types/firewall';
import { deriveActionHierarchy } from '../../types/intelligence';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface ActionHierarchyCardProps {
  actions: FirewallActionSummary[];
}

export const ActionHierarchyCard: React.FC<ActionHierarchyCardProps> = ({ actions }) => {
  const hierarchy = deriveActionHierarchy(actions);
  const highestDetected = [...hierarchy].reverse().find((h) => h.isDetected);

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <ExternalLink size={18} color="var(--color-accent)" />
            <CardTitle>Action Progression Hierarchy</CardTitle>
          </div>
          {highestDetected && (
            <Badge variant="accent" size="sm">
              Progression Level {highestDetected.level} of 5: {highestDetected.name}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Evaluates requested interactions along the standard progression scale (from informational queries to irreversible financial extraction).
        </p>

        {/* Visual Progression Steps */}
        <div
          role="region"
          aria-label="Action Progression Scale"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: 'var(--space-2)',
            padding: 'var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          {hierarchy.map((stage) => {
            const borderCol = stage.isDetected
              ? stage.level === 5
                ? 'var(--color-block)'
                : stage.level >= 3
                ? 'var(--color-warn)'
                : 'var(--color-accent)'
              : 'var(--color-border-subtle)';
            const bgCol = stage.isDetected
              ? stage.level === 5
                ? 'var(--color-block-bg)'
                : stage.level >= 3
                ? 'var(--color-warn-bg)'
                : 'var(--color-accent-subtle)'
              : 'var(--color-bg-surface)';

            return (
              <div
                key={stage.level}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  padding: 'var(--space-2)',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${borderCol}`,
                  backgroundColor: bgCol,
                  opacity: stage.isDetected ? 1 : 0.6,
                  transition: 'var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      fontFamily: 'var(--font-mono)',
                      color: stage.isDetected ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                    }}
                  >
                    Level {stage.level}
                  </span>
                  {stage.isDetected && (
                    <span
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: borderCol,
                      }}
                      title="Detected in interaction"
                    />
                  )}
                </div>
                <span
                  style={{
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: 600,
                    color: stage.isDetected ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                  }}
                >
                  {stage.name}
                </span>
                <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', lineHeight: 1.3 }}>
                  {stage.description}
                </span>
              </div>
            );
          })}
        </div>

        {/* Detected Action Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
            Detected Action Items ({actions.length})
          </span>

          {actions.length === 0 ? (
            <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              No explicit user actions or extraction requests detected.
            </div>
          ) : (
            actions.map((act) => (
              <div
                key={act.action_id}
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
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Badge variant="accent" size="sm">
                      {act.action_type}
                    </Badge>
                    {act.target && (
                      <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                        Target: <code style={{ color: 'var(--color-accent-hover)', backgroundColor: 'var(--color-bg-subtle)', padding: '2px 4px', borderRadius: '2px' }}>{act.target}</code>
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    {act.urgency_detected && (
                      <Badge variant="warning" size="sm">
                        <AlertTriangle size={12} style={{ marginRight: '4px' }} /> Urgency Detected
                      </Badge>
                    )}
                    <Badge variant={act.reversibility === 'IRREVERSIBLE' ? 'danger' : 'neutral'} size="sm">
                      {act.reversibility}
                    </Badge>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-3)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  <span>Impact Category: <strong style={{ color: 'var(--color-text-secondary)' }}>{act.impact_category.replace(/_/g, ' ')}</strong></span>
                  <span>•</span>
                  <span>Action ID: <code style={{ color: 'var(--color-text-muted)' }}>{act.action_id}</code></span>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};
