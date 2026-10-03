import React from 'react';
import { ChevronRight } from 'lucide-react';
import type { ProtectionSummaryDimension } from '../../types/intervention';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface ProtectionSummaryCardProps {
  dimensions: ProtectionSummaryDimension[];
  onSelectSection?: (sectionId: string) => void;
}

export const ProtectionSummaryCard: React.FC<ProtectionSummaryCardProps> = ({
  dimensions,
  onSelectSection,
}) => {
  const getBadgeVariant = (variant: string) => {
    switch (variant) {
      case 'allow':
        return 'success';
      case 'block':
      case 'danger':
        return 'danger';
      case 'warn':
      case 'pause':
        return 'warning';
      case 'inform':
        return 'accent';
      default:
        return 'neutral';
    }
  };

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <CardHeader style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--color-border-subtle)' }}>
        <CardTitle style={{ fontSize: 'var(--font-size-md)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Protection Summary</span>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 400, color: 'var(--color-text-muted)' }}>
            Key analytical indicators at a glance
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent style={{ padding: 0 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
          {dimensions.map((dim, idx) => (
            <div
              key={dim.dimension}
              onClick={() => onSelectSection && onSelectSection(dim.targetSectionId)}
              role={onSelectSection ? 'button' : undefined}
              tabIndex={onSelectSection ? 0 : undefined}
              onKeyDown={(e) => {
                if (onSelectSection && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault();
                  onSelectSection(dim.targetSectionId);
                }
              }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
                padding: 'var(--space-4)',
                borderRight: idx < dimensions.length - 1 ? '1px solid var(--color-border-subtle)' : undefined,
                borderBottom: '1px solid var(--color-border-subtle)',
                backgroundColor: 'var(--color-bg-surface)',
                cursor: onSelectSection ? 'pointer' : 'default',
                transition: 'background-color var(--transition-fast)',
              }}
              className="nivesh-protection-summary-item"
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {dim.dimension}
                </span>
                {onSelectSection && <ChevronRight size={14} color="var(--color-text-muted)" />}
              </div>

              <div>
                <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', display: 'block', textTransform: 'capitalize' }}>
                  {dim.status}
                </strong>
                {dim.detail && (
                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px', display: 'block' }}>
                    {dim.detail}
                  </span>
                )}
              </div>

              <div style={{ marginTop: 'auto', paddingTop: 'var(--space-1)' }}>
                <Badge variant={getBadgeVariant(dim.variant) as any} size="sm">
                  {dim.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
