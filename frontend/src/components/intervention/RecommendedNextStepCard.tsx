import React from 'react';
import { ShieldCheck, ArrowRight, CornerDownLeft, Lock } from 'lucide-react';
import type { PolicyDecisionType, UserActionType } from '../../types/intervention';
import { Card, CardContent } from '../common/Card';
import { Button } from '../common/Button';

export interface RecommendedNextStepCardProps {
  decision: PolicyDecisionType;
  recommendedInstruction: string;
  availableActions: UserActionType[];
  onActionClick: (action: UserActionType) => void;
  isConfirmedOverride?: boolean;
}

export const RecommendedNextStepCard: React.FC<RecommendedNextStepCardProps> = ({
  decision: _decision,
  recommendedInstruction,
  availableActions,
  onActionClick,
  isConfirmedOverride = false,
}) => {
  const getActionVisuals = (action: UserActionType) => {
    switch (action) {
      case 'continue':
        return {
          label: 'Continue to Destination',
          variant: 'primary' as const,
          rightIcon: <ArrowRight size={14} />,
        };
      case 'review-why':
        return {
          label: 'Review Policy Basis',
          variant: 'primary' as const,
          rightIcon: <ArrowRight size={14} />,
        };
      case 'review-details':
        return {
          label: 'Review Findings & Details',
          variant: 'primary' as const,
          rightIcon: <ArrowRight size={14} />,
        };
      case 'view-evidence':
        return {
          label: 'Inspect Contradicted Evidence',
          variant: 'primary' as const,
          rightIcon: <ArrowRight size={14} />,
        };
      case 'go-back':
      case 'return-to-protect':
        return {
          label: 'Return to Protection',
          variant: 'secondary' as const,
          leftIcon: <CornerDownLeft size={14} />,
        };
      case 'override':
        return {
          label: isConfirmedOverride ? 'Override Acknowledged' : 'Explicit User Override...',
          variant: 'outline' as const,
          leftIcon: <Lock size={14} />,
        };
      case 'analyze-another':
        return {
          label: 'Inspect Different Content',
          variant: 'ghost' as const,
        };
      default:
        return {
          label: action,
          variant: 'secondary' as const,
        };
    }
  };

  return (
    <Card
      variant="elevated"
      style={{
        backgroundColor: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border-default)',
        width: '100%',
      }}
    >
      <CardContent style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
          <div style={{ color: 'var(--color-accent)', marginTop: '2px', display: 'flex' }}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                fontWeight: 600,
                color: 'var(--color-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Protective Guidance (Safety Advisory)
            </span>
            <p
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 500,
                color: 'var(--color-text-primary)',
                margin: '4px 0 0 0',
                lineHeight: 1.5,
              }}
            >
              {recommendedInstruction}
            </p>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
              Nivesh provides investor-safety verification only. It does not provide financial, trading, or investment advice.
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 'var(--space-3)',
            paddingTop: 'var(--space-3)',
            borderTop: '1px solid var(--color-border-subtle)',
          }}
        >
          {availableActions.map((action) => {
            const config = getActionVisuals(action);
            return (
              <Button
                key={action}
                variant={config.variant}
                size="md"
                onClick={() => onActionClick(action)}
                leftIcon={config.leftIcon}
                rightIcon={config.rightIcon}
                disabled={action === 'override' && isConfirmedOverride}
              >
                {config.label}
              </Button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
