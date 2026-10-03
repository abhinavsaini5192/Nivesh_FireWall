import React from 'react';
import { Clock, Shield, ArrowRight } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { Card, CardContent } from '../components/common/Card';
import { SemanticStatusBadge } from '../components/status/SemanticStatusBadge';
import { Badge } from '../components/common/Badge';
import type { FirewallAnalysisResponse } from '../types/firewall';

export interface ActivityViewProps {
  onGoToProtect: () => void;
  analyses?: FirewallAnalysisResponse[];
  onSelectAnalysis?: (analysis: FirewallAnalysisResponse) => void;
}

export const ActivityView: React.FC<ActivityViewProps> = ({
  onGoToProtect,
  analyses = [],
  onSelectAnalysis,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', width: '100%' }}>
      <SectionHeader
        title="Protection Activity"
        description="Chronological log of inspected messages, links, and interventions for this session."
        badge={analyses.length > 0 ? <Badge variant="accent">{analyses.length} Total</Badge> : undefined}
      />

      {analyses.length === 0 ? (
        /* Honest Empty State - Zero Fake Data */
        <EmptyState
          icon={<Clock size={28} />}
          title="No analyses yet"
          description="Your future protection checks, claim verifications, and safety interventions will appear here."
          action={
            <Button
              variant="primary"
              size="sm"
              onClick={onGoToProtect}
              leftIcon={<Shield size={14} />}
            >
              Start an Analysis
            </Button>
          }
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {analyses.map((item) => (
            <Card key={item.analysis_id} variant="surface">
              <CardContent style={{ padding: 'var(--space-4)' }}>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 'var(--space-3)',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <SemanticStatusBadge decision={item.decision.decision} size="sm" />
                      <span
                        style={{
                          fontSize: 'var(--font-size-xs)',
                          fontFamily: 'var(--font-mono)',
                          color: 'var(--color-text-muted)',
                        }}
                      >
                        {item.analysis_id}
                      </span>
                    </div>
                    <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', marginTop: '2px' }}>
                      {item.decision.primary_reason}
                    </span>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      Channel: {item.content.channel} • Input: {item.content.input_type} • {item.created_at}
                    </span>
                  </div>

                  {onSelectAnalysis && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onSelectAnalysis(item)}
                      rightIcon={<ArrowRight size={14} />}
                    >
                      View Result
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
