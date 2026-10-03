import React from 'react';
import { Activity } from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { deriveCombinedTimeline } from '../../types/intelligence';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface BehaviourTimelineViewProps {
  analysis: FirewallAnalysisResponse;
}

export const BehaviourTimelineView: React.FC<BehaviourTimelineViewProps> = ({ analysis }) => {
  const { behaviour } = analysis;
  const timelineEvents = deriveCombinedTimeline(analysis);

  const getEventCategoryBadge = (category: string) => {
    switch (category) {
      case 'action':
        return <Badge variant="accent" size="sm">Action</Badge>;
      case 'behaviour':
        return <Badge variant="warning" size="sm">Behaviour</Badge>;
      case 'policy':
        return <Badge variant="danger" size="sm">Policy</Badge>;
      case 'user':
        return <Badge variant="neutral" size="sm">Interaction</Badge>;
      case 'content':
      default:
        return <Badge variant="neutral" size="sm">Content</Badge>;
    }
  };

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Activity size={18} color="var(--color-warn)" />
            <CardTitle>Observed Interaction Dynamics & Timeline</CardTitle>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            {behaviour.time_pressure_detected && (
              <Badge variant="danger" size="sm">
                Time Pressure / Urgency
              </Badge>
            )}
            {behaviour.rapid_escalation_detected && (
              <Badge variant="warning" size="sm">
                Rapid Action Escalation
              </Badge>
            )}
            {behaviour.channel_migration_detected && (
              <Badge variant="warning" size="sm">
                Off-Platform Migration
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-4)' }}>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
          Traces the temporal sequence of interaction events and escalation patterns without making psychological inferences about the user.
        </p>

        {/* Pattern Confidence Semantics (Section 17: Never Scam Probability) */}
        <div
          style={{
            padding: 'var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-3)',
          }}
        >
          <div>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Interaction Pattern Confidence
            </span>
            <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', margin: 0 }}>
              Confidence that this behavioural sequence was observed during interaction monitoring.
            </p>
          </div>
          <Badge variant="accent" size="sm">
            Observed ({behaviour.events_in_session || timelineEvents.length} events)
          </Badge>
        </div>

        {/* Chronological Timeline Track */}
        <div
          role="region"
          aria-label="Chronological Interaction Timeline"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            position: 'relative',
            paddingLeft: 'var(--space-5)',
            borderLeft: '2px solid var(--color-border-subtle)',
            marginLeft: 'var(--space-3)',
            marginTop: 'var(--space-2)',
          }}
        >
          {timelineEvents.map((evt) => (
            <div
              key={evt.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                position: 'relative',
              }}
            >
              {/* Timeline Dot Indicator */}
              <div
                style={{
                  position: 'absolute',
                  left: 'calc(-1 * var(--space-5) - 5px)',
                  top: '4px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: evt.isEscalation
                    ? 'var(--color-block)'
                    : evt.category === 'policy'
                    ? 'var(--color-warn)'
                    : 'var(--color-accent)',
                  border: '2px solid var(--color-bg-canvas)',
                }}
              />

              {/* Event Header */}
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span
                  style={{
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--color-text-muted)',
                  }}
                >
                  {evt.timestamp}
                </span>
                <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {evt.title}
                </span>
                {getEventCategoryBadge(evt.category)}
              </div>

              {/* Event Description */}
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                {evt.description}
              </span>
            </div>
          ))}
        </div>

        {/* Behaviour Findings Summary */}
        {behaviour.findings.length > 0 && (
          <div style={{ marginTop: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Observed Behavioural Patterns:
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
              {behaviour.findings.map((f, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
