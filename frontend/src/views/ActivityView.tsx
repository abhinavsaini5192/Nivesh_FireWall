import React from 'react';
import { Clock, Shield } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';

export interface ActivityViewProps {
  onGoToProtect: () => void;
}

export const ActivityView: React.FC<ActivityViewProps> = ({ onGoToProtect }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', width: '100%' }}>
      <SectionHeader
        title="Protection Activity"
        description="Chronological log of inspected messages, links, and interventions for this session."
      />

      {/* Honest Empty State - Zero Fake Data */}
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
    </div>
  );
};
