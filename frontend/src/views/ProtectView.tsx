import React from 'react';
import { Shield, Search, UserCheck, AlertTriangle } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { ContentEntryCard } from '../components/firewall/ContentEntryCard';
import { PrivacyNotice } from '../components/firewall/PrivacyNotice';
import { SemanticStatusBadge } from '../components/status/SemanticStatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { AnalysisResultView } from '../components/firewall/AnalysisResultView';
import type { ChannelType, FirewallAnalysisResponse, AnalysisState } from '../types/firewall';

export interface ProtectViewProps {
  onAnalyze?: (payload: { text?: string; url?: string; channel: ChannelType }) => Promise<void>;
  analysisResult?: FirewallAnalysisResponse | null;
  analysisState?: AnalysisState;
  onAnalyzeAnother?: () => void;
  isLoading?: boolean;
  error?: string | null;
  errorCode?: string | null;
  onClearError?: () => void;
  onRetry?: () => void;
  systemAvailable?: boolean;
}

export const ProtectView: React.FC<ProtectViewProps> = ({
  onAnalyze,
  analysisResult = null,
  analysisState = 'IDLE',
  onAnalyzeAnother,
  isLoading = false,
  error = null,
  errorCode = null,
  onClearError,
  onRetry,
  systemAvailable = true,
}) => {
  // 1. Result State: Render full analysis result view
  if (analysisResult) {
    return (
      <AnalysisResultView
        analysis={analysisResult}
        onAnalyzeAnother={onAnalyzeAnother || (() => {})}
      />
    );
  }

  // 2. Loading State: Render calm analysis progress
  if (isLoading || analysisState === 'ANALYZING' || analysisState === 'SUBMITTING') {
    return (
      <div style={{ width: '100%', maxWidth: '640px', margin: 'var(--space-8) auto' }}>
        <LoadingState
          message="Analyzing financial interaction across firewall pipeline..."
          steps={[
            'Ingesting & normalizing content (Engine 1)',
            'Extracting verifiable assertions & return claims (Engine 2)',
            'Analyzing requested actions & irreversibility (Engine 3)',
            'Verifying evidence against official registries (Engine 4 & 5)',
            'Checking claimed identities & lookalikes (Engine 9)',
            'Evaluating threat signals & attack paths (Engine 6)',
            'Matching collective scam fingerprints (Engine 7)',
            'Detecting behavioural escalation patterns (Engine 10)',
            'Emitting final safety policy decision (Engine 8)',
          ]}
          currentStepIndex={4}
        />
      </div>
    );
  }

  // 3. Error State with Retry
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)', width: '100%' }}>
      {analysisState === 'ERROR' && error && (
        <ErrorState
          title="Analysis Could Not Be Completed"
          message={error}
          errorCode={errorCode || 'PIPELINE_FAILURE'}
          onRetry={onRetry}
        />
      )}

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
