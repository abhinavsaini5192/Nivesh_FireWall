import React from 'react';
import { Shield, Search, UserCheck, AlertTriangle } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { ContentEntryCard } from '../components/firewall/ContentEntryCard';
import { PrivacyNotice } from '../components/firewall/PrivacyNotice';
import { SemanticStatusBadge } from '../components/status/SemanticStatusBadge';
import { PolicyDecisionFramework } from '../components/status/PolicyDecisionFramework';
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

  // 3. Main Workspace View
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', width: '100%' }}>
      {analysisState === 'ERROR' && error && (
        <ErrorState
          title="Analysis Could Not Be Completed"
          message={error}
          errorCode={errorCode || 'PIPELINE_FAILURE'}
          onRetry={onRetry}
        />
      )}

      {/* Header & Protection Intelligence Pipeline Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <SectionHeader
          title="Protect before you act."
          description="Analyze financial messages, investment links, and fund transfer requests before taking consequential actions."
        />

        {/* 4 Connected Protection Intelligence Stages */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 'var(--space-3)',
          }}
        >
          {/* Stage 01: VERIFY */}
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-1)',
              position: 'relative',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ color: 'var(--color-accent)', display: 'flex' }}>
                  <Search size={15} />
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 'var(--font-weight-bold)',
                    color: 'var(--color-accent)',
                    letterSpacing: '0.04em',
                  }}
                >
                  01 VERIFY
                </span>
              </div>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                REGISTRIES
              </span>
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Claims & Authoritative Evidence
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.4 }}>
              Resolves assertions against SEBI, RBI, NSE, and BSE official disclosure records.
            </p>
          </div>

          {/* Stage 02: IDENTITY */}
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-1)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ color: 'var(--color-accent)', display: 'flex' }}>
                  <UserCheck size={15} />
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 'var(--font-weight-bold)',
                    color: 'var(--color-accent)',
                    letterSpacing: '0.04em',
                  }}
                >
                  02 IDENTITY
                </span>
              </div>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                ENTITIES
              </span>
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Entity & Source Verification
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.4 }}>
              Unmasks lookalike domains, registration mismatches, and impersonated intermediaries.
            </p>
          </div>

          {/* Stage 03: THREAT PATH */}
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-1)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ color: 'var(--color-warn)', display: 'flex' }}>
                  <AlertTriangle size={15} />
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 'var(--font-weight-bold)',
                    color: 'var(--color-warn)',
                    letterSpacing: '0.04em',
                  }}
                >
                  03 THREAT PATH
                </span>
              </div>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                ACTIONS
              </span>
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Action-Chain Reconstruction
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.4 }}>
              Maps consequential actions, off-platform migrations, and irreversible fund transfers.
            </p>
          </div>

          {/* Stage 04: INTERVENTION */}
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'var(--color-bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-1)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ color: 'var(--color-allow)', display: 'flex' }}>
                  <Shield size={15} />
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 'var(--font-weight-bold)',
                    color: 'var(--color-allow)',
                    letterSpacing: '0.04em',
                  }}
                >
                  04 INTERVENTION
                </span>
              </div>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                POLICY
              </span>
            </div>
            <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
              Policy Decision Support
            </strong>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.4 }}>
              Enforces calm, proportional interventions: Allow, Inform, Warn, Pause, or Block.
            </p>
          </div>
        </div>
      </div>

      {/* Dominant Hero Inspection Workspace */}
      <ContentEntryCard
        onAnalyze={onAnalyze}
        isLoading={isLoading}
        isDisabled={!systemAvailable}
        error={error}
        onClearError={onClearError}
      />

      {/* Safety Policy Decision Framework (Engine 8) */}
      <Card variant="surface">
        <CardHeader style={{ paddingBottom: 'var(--space-2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <CardTitle style={{ fontSize: 'var(--font-size-md)', letterSpacing: '-0.01em' }}>
              Safety Policy Decision Framework
            </CardTitle>
            <div style={{ display: 'none' }}>
              <SemanticStatusBadge decision="ALLOW" />
              <SemanticStatusBadge decision="INFORM" />
              <SemanticStatusBadge decision="WARN" />
              <SemanticStatusBadge decision="PAUSE" />
              <SemanticStatusBadge decision="BLOCK" />
            </div>
          </div>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
            Authoritative Engine 8 evaluation hierarchy. Calm and proportional intervention before harm occurs.
          </p>
        </CardHeader>
        <CardContent>
          <PolicyDecisionFramework />
        </CardContent>
      </Card>

      {/* Trust & Boundary Notice */}
      <PrivacyNotice />
    </div>
  );
};

