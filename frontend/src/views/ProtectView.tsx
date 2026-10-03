import React from 'react';
import { Shield, Search, UserCheck, AlertTriangle } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { ContentEntryCard } from '../components/firewall/ContentEntryCard';
import { PrivacyNotice } from '../components/firewall/PrivacyNotice';
import { SemanticStatusBadge } from '../components/status/SemanticStatusBadge';
import type { ChannelType } from '../types/firewall';

export interface ProtectViewProps {
  onAnalyze?: (payload: { text?: string; url?: string; channel: ChannelType }) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
  systemAvailable?: boolean;
}

export const ProtectView: React.FC<ProtectViewProps> = ({
  onAnalyze,
  isLoading = false,
  error = null,
  onClearError,
  systemAvailable = true,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)', width: '100%' }}>
      {/* Hero / Value Proposition Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        <SectionHeader
          title="Protect before you act."
          description="Analyze financial messages, investment links, and fund transfer requests before taking consequential actions."
        />

        {/* 4 Protection Pillars (Honest, Technical, Calm) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
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
            <div style={{ color: 'var(--color-accent)', display: 'flex' }}>
              <Search size={18} />
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Verify Assertions
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
              Checks return guarantees and regulatory claims against official registry records.
            </p>
          </div>

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
            <div style={{ color: 'var(--color-accent)', display: 'flex' }}>
              <UserCheck size={18} />
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Check Identities
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
              Resolves claimed entities and flags domain lookalikes or unauthorized representation.
            </p>
          </div>

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
            <div style={{ color: 'var(--color-accent)', display: 'flex' }}>
              <AlertTriangle size={18} />
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Trace Threat Paths
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
              Identifies high-impact actions, remote app installations, and off-platform migrations.
            </p>
          </div>

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
            <div style={{ color: 'var(--color-accent)', display: 'flex' }}>
              <Shield size={18} />
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Calm Decision Support
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
              Presents transparent evidence, reason codes, and cooling pauses instead of alarming scores.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Entry Card */}
      <ContentEntryCard
        onAnalyze={onAnalyze}
        isLoading={isLoading}
        isDisabled={!systemAvailable}
        error={error}
        onClearError={onClearError}
      />

      {/* Presentation System Preview for Engine 8 Decisions */}
      <Card variant="surface">
        <CardHeader>
          <CardTitle style={{ fontSize: 'var(--font-size-md)' }}>
            Safety Policy Decision Framework
          </CardTitle>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
            Visual presentation states mapped directly to Engine 8 authoritative policy outcomes.
          </p>
        </CardHeader>
        <CardContent>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--space-3)',
              alignItems: 'center',
            }}
          >
            <SemanticStatusBadge decision="ALLOW" />
            <SemanticStatusBadge decision="INFORM" />
            <SemanticStatusBadge decision="WARN" />
            <SemanticStatusBadge decision="PAUSE" />
            <SemanticStatusBadge decision="BLOCK" />
          </div>
        </CardContent>
      </Card>

      {/* Trust & Privacy Notice */}
      <PrivacyNotice />
    </div>
  );
};
