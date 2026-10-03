import React, { useState } from 'react';
import { AlertOctagon, Check } from 'lucide-react';
import type { PolicyDecisionType } from '../../types/firewall';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

export interface OverrideConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmOverride: () => void;
  decision: PolicyDecisionType;
  primaryReason: string;
  actionDescription?: string;
  analysisId: string;
}

export const OverrideConfirmationModal: React.FC<OverrideConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirmOverride,
  decision,
  primaryReason,
  actionDescription = 'Proceeding with the requested financial interaction',
  analysisId,
}) => {
  const [acknowledged, setAcknowledged] = useState(false);

  const handleConfirm = () => {
    if (!acknowledged) return;
    onConfirmOverride();
    onClose();
  };

  const handleCancel = () => {
    setAcknowledged(false);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title="Explicit User Confirmation"
      description="Review policy conditions before proceeding."
      maxWidth="540px"
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', width: '100%' }}>
          <Button variant="secondary" size="md" onClick={handleCancel}>
            Cancel (Keep Protection Active)
          </Button>
          <Button
            variant="danger"
            size="md"
            onClick={handleConfirm}
            disabled={!acknowledged}
            leftIcon={<Check size={16} />}
          >
            Confirm Override & Continue
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {/* Intervention Summary Alert */}
        <div
          role="alert"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 'var(--space-3)',
            padding: 'var(--space-3) var(--space-4)',
            backgroundColor: 'var(--color-pause-bg)',
            border: '1px solid var(--color-pause-border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--color-pause)',
          }}
        >
          <AlertOctagon size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <strong style={{ fontSize: 'var(--font-size-sm)' }}>
                Policy State: {decision}
              </strong>
              <Badge variant="warning" size="sm">
                Intervention Active
              </Badge>
            </div>
            <span style={{ fontSize: 'var(--font-size-xs)', marginTop: '2px', display: 'block', color: 'var(--color-text-secondary)' }}>
              Analysis ID: {analysisId}
            </span>
          </div>
        </div>

        {/* What Is Being Overridden */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Action You Are Acknowledging
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', margin: 0 }}>
            {actionDescription}
          </p>
        </div>

        {/* Reason for Intervention */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Why Policy Intervened
          </span>
          <div
            style={{
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
              lineHeight: 1.5,
            }}
          >
            {primaryReason}
          </div>
        </div>

        {/* Non-manipulative acknowledgment checkbox */}
        <label
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 'var(--space-3)',
            padding: 'var(--space-3)',
            backgroundColor: 'var(--color-bg-surface-elevated)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
          }}
        >
          <input
            type="checkbox"
            id="override-acknowledge-checkbox"
            checked={acknowledged}
            onChange={(e) => setAcknowledged(e.target.checked)}
            style={{ marginTop: '3px', cursor: 'pointer' }}
          />
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-primary)', lineHeight: 1.5 }}>
            I understand that Nivesh Firewall paused this action due to unverified counterparties or high-consequence
            parameters. I choose to proceed under my own verification.
          </span>
        </label>
      </div>
    </Modal>
  );
};
