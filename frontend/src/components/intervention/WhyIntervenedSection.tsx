import React from 'react';
import { HelpCircle, ArrowRight } from 'lucide-react';
import type { InterventionReasonItem } from '../../types/intervention';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface WhyIntervenedSectionProps {
  primaryReason: string;
  reasonCodes: string[];
  reasons: InterventionReasonItem[];
  onSelectSection?: (sectionId: string) => void;
}

export const WhyIntervenedSection: React.FC<WhyIntervenedSectionProps> = ({
  primaryReason,
  reasonCodes,
  reasons,
  onSelectSection,
}) => {
  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader
        style={{
          padding: 'var(--space-4) var(--space-5)',
          borderBottom: '1px solid var(--color-border-subtle)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-2)',
        }}
      >
        <CardTitle
          style={{
            fontSize: 'var(--font-size-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
          }}
        >
          <HelpCircle size={18} color="var(--color-accent)" />
          <span>Why did Nivesh intervene?</span>
        </CardTitle>

        {reasonCodes.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
            {reasonCodes.map((code) => (
              <Badge key={code} variant="neutral" size="sm">
                {code}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {/* Primary Reason Headline */}
        <div
          style={{
            padding: 'var(--space-3) var(--space-4)',
            backgroundColor: 'var(--color-bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            borderLeft: '3px solid var(--color-accent)',
          }}
        >
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Primary Evaluated Condition
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', margin: 'var(--space-1) 0 0 0', fontWeight: 500 }}>
            {primaryReason}
          </p>
        </div>

        {/* Detailed Supporting Reasons Connected to Respective Engines */}
        {reasons.length > 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Supporting Signal Breakdown
            </span>

            <ol
              style={{
                paddingLeft: 'var(--space-5)',
                margin: 0,
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
              }}
            >
              {reasons.slice(1).map((item) => (
                <li
                  key={item.id}
                  style={{
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-secondary)',
                    lineHeight: 1.5,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 'var(--space-2)',
                    }}
                  >
                    <span>{item.label}</span>
                    {item.actionText && onSelectSection && (
                      <button
                        onClick={() => onSelectSection(item.targetSectionId)}
                        aria-label={`Jump to ${item.actionText}`}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--color-accent)',
                          fontSize: 'var(--font-size-xs)',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        <span>{item.actionText}</span>
                        <ArrowRight size={12} />
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
