import React from 'react';
import type { ProtectionSystemStatus } from '../../types/firewall';
import { StatusIndicator } from '../common/StatusIndicator';

export interface ProtectionStatusProps {
  status: ProtectionSystemStatus;
  showDetails?: boolean;
}

export const ProtectionStatus: React.FC<ProtectionStatusProps> = ({
  status,
  showDetails = false,
}) => {
  const getStatusLabel = () => {
    switch (status) {
      case 'active':
        return 'Protection Active';
      case 'connecting':
        return 'Connecting...';
      case 'unavailable':
        return 'Service Offline';
      case 'error':
        return 'System Degraded';
      default:
        return 'Unknown Status';
    }
  };

  const getDetails = () => {
    switch (status) {
      case 'active':
        return 'Backend Firewall online. Real-time verification ready.';
      case 'connecting':
        return 'Establishing connection to Nivesh Firewall backend...';
      case 'unavailable':
        return 'Cannot connect to backend service. Check local server.';
      case 'error':
        return 'Backend health check failed. Analysis may be limited.';
      default:
        return '';
    }
  };

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--space-2)',
        padding: 'var(--space-1) var(--space-3)',
        borderRadius: 'var(--radius-full)',
        backgroundColor: 'var(--color-bg-subtle)',
        border: '1px solid var(--color-border-subtle)',
      }}
      title={getDetails()}
    >
      <StatusIndicator status={status} label={getStatusLabel()} size="sm" />
      {showDetails && (
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          ({getDetails()})
        </span>
      )}
    </div>
  );
};
