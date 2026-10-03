/**
 * Canonical Analysis Result View (Phase 12.2)
 *
 * Renders the authoritative Engine 8 safety decision and full multi-engine
 * intelligence breakdown (Claims, Actions, Evidence, Identity, Threat,
 * Fingerprint, Behaviour, Provenance). ZERO mock or fabricated intelligence.
 */

import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  Info,
  Clock,
  RotateCcw,
  Copy,
  Check,
  LayoutDashboard,
  CheckCircle2,
  UserCheck,
  Activity,
  Compass,
} from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { deriveInterventionModel, type UserActionType } from '../../types/intervention';
import { Card, CardContent } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { SemanticStatusBadge } from '../status/SemanticStatusBadge';
import { ErrorState } from '../common/ErrorState';
import {
  ProtectionBanner,
  HighImpactActionAlert,
  ProtectionSummaryCard,
  WhyIntervenedSection,
  RecommendedNextStepCard,
  OverrideConfirmationModal,
} from '../intervention';
import { IntelligenceDetailView } from '../intelligence';

export interface AnalysisResultViewProps {
  analysis: FirewallAnalysisResponse;
  onAnalyzeAnother: () => void;
  onGoBack?: () => void;
  onOverrideConfirmed?: () => void;
}

export const AnalysisResultView: React.FC<AnalysisResultViewProps> = ({
  analysis,
  onAnalyzeAnother,
  onGoBack,
  onOverrideConfirmed,
}) => {
  const [copiedId, setCopiedId] = React.useState(false);
  const [isOverrideModalOpen, setIsOverrideModalOpen] = React.useState(false);
  const [isConfirmedOverride, setIsConfirmedOverride] = React.useState(false);

  // Safety Boundary (Section 28 & 29): Never downgrade stronger decision on error
  if (!analysis || !analysis.decision) {
    return (
      <div style={{ width: '100%', maxWidth: '640px', margin: 'var(--space-8) auto' }}>
        <ErrorState
          title="Analysis Result Incomplete"
          message="We couldn't display the full protection details. The analysis result is incomplete or malformed."
          errorCode="ANALYSIS_RESULT_INCOMPLETE"
          onRetry={onAnalyzeAnother}
        />
      </div>
    );
  }

  const model = deriveInterventionModel(analysis);

  const { decision, content } = analysis;

  const handleSelectSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      const btn = el.querySelector('button');
      if (btn) {
        btn.focus();
      }
    }
  };

  const handleActionClick = (action: UserActionType) => {
    switch (action) {
      case 'view-details':
      case 'review-details':
      case 'review-why':
      case 'view-evidence':
        handleSelectSection('intelligence-breakdown-heading');
        break;
      case 'go-back':
      case 'return-to-protect':
        if (onGoBack) {
          onGoBack();
        } else {
          onAnalyzeAnother();
        }
        break;
      case 'override':
        setIsOverrideModalOpen(true);
        break;
      case 'analyze-another':
        onAnalyzeAnother();
        break;
      case 'continue':
      default:
        break;
    }
  };

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(analysis.analysis_id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    } catch {
      // Ignore
    }
  };

  const getDecisionHeaderConfig = () => {
    switch (decision.decision) {
      case 'ALLOW':
        return {
          title: 'ACTION PERMITTED — VERIFIED NEUTRAL',
          icon: <ShieldCheck size={28} color="var(--color-allow)" />,
          borderAccent: 'var(--color-allow-border)',
          bg: 'var(--color-allow-bg)',
          textColor: 'var(--color-allow)',
        };
      case 'INFORM':
        return {
          title: 'INFORMATIONAL ADVISORY',
          icon: <Info size={28} color="var(--color-inform)" />,
          borderAccent: 'var(--color-inform-border)',
          bg: 'var(--color-inform-bg)',
          textColor: 'var(--color-inform)',
        };
      case 'WARN':
        return {
          title: 'CAUTION RECOMMENDED',
          icon: <AlertTriangle size={28} color="var(--color-warn)" />,
          borderAccent: 'var(--color-warn-border)',
          bg: 'var(--color-warn-bg)',
          textColor: 'var(--color-warn)',
        };
      case 'PAUSE':
        return {
          title: 'ACTION PAUSED — VERIFICATION REQUIRED',
          icon: <AlertOctagon size={28} color="var(--color-pause)" />,
          borderAccent: 'var(--color-pause-border)',
          bg: 'var(--color-pause-bg)',
          textColor: 'var(--color-pause)',
        };
      case 'BLOCK':
      default:
        return {
          title: 'ACTION BLOCKED — THREAT PREVENTED',
          icon: <ShieldAlert size={28} color="var(--color-block)" />,
          borderAccent: 'var(--color-block-border)',
          bg: 'var(--color-block-bg)',
          textColor: 'var(--color-block)',
        };
    }
  };

  const headerConfig = getDecisionHeaderConfig();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', width: '100%' }}>
      {/* 1. Primary Action & Navigation Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-3)',
          paddingBottom: 'var(--space-2)',
          borderBottom: '1px solid var(--color-border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Analysis ID:</span>
          <span
            style={{
              fontSize: 'var(--font-size-sm)',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-text-primary)',
              fontWeight: 600,
            }}
          >
            {analysis.analysis_id}
          </span>
          <button
            onClick={handleCopyId}
            aria-label="Copy Analysis ID"
            style={{
              color: copiedId ? 'var(--color-allow)' : 'var(--color-text-muted)',
              cursor: 'pointer',
              display: 'flex',
              padding: '2px',
            }}
          >
            {copiedId ? <Check size={14} /> : <Copy size={14} />}
          </button>
          {content.channel && (
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Channel: <strong style={{ color: 'var(--color-text-primary)' }}>{content.channel}</strong>
            </span>
          )}
          {analysis.session_id && (
            <span style={{ fontSize: 'var(--font-size-xs)', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
              Session: {analysis.session_id}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={onAnalyzeAnother}
            leftIcon={<RotateCcw size={14} />}
          >
            Analyze Another Content
          </Button>
        </div>
      </div>

      {/* 2. Hero Decision Banner (Sole Policy Authority: Engine 8) */}
      <Card
        variant="elevated"
        style={{
          borderLeft: `4px solid ${headerConfig.borderAccent}`,
          backgroundColor: 'var(--color-bg-surface)',
        }}
      >
        <CardContent style={{ gap: 'var(--space-4)' }}>
          {/* Header Row */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-3)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              {headerConfig.icon}
              <div>
                <h2
                  style={{
                    fontSize: 'var(--font-size-xl)',
                    fontWeight: 'var(--font-weight-bold)',
                    color: headerConfig.textColor,
                    margin: 0,
                    letterSpacing: '0.02em',
                  }}
                >
                  {headerConfig.title}
                </h2>
                <span
                  style={{
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--color-text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  Severity: {decision.severity} • Policy Engine v{decision.policy_version}
                </span>
              </div>
            </div>

            <SemanticStatusBadge decision={decision.decision} size="lg" />
          </div>

          {/* SOC Operational State Strip */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-2)',
              padding: 'var(--space-2) var(--space-3)',
              backgroundColor: 'var(--color-bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              fontSize: 'var(--font-size-xs)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>PRIMARY REASON CODE:</span>
              <strong style={{ color: 'var(--color-text-primary)' }}>
                {decision.reason_codes[0] || 'DECISION_FINALIZED'}
              </strong>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>OPERATIONAL DIRECTIVE:</span>
              <span
                style={{
                  fontWeight: 600,
                  color:
                    decision.decision === 'ALLOW'
                      ? 'var(--color-allow)'
                      : decision.decision === 'BLOCK'
                      ? 'var(--color-block)'
                      : decision.decision === 'PAUSE'
                      ? 'var(--color-pause)'
                      : 'var(--color-warn)',
                }}
              >
                {decision.decision === 'ALLOW' && 'SAFE — NO INTERVENTION REQUIRED'}
                {decision.decision === 'INFORM' && 'ADVISORY — DISCLOSURE AWARENESS'}
                {decision.decision === 'WARN' && 'CAUTION — USER SCRUTINY ADVISED'}
                {decision.decision === 'PAUSE' && 'INTERVENTION — MANDATORY PAUSE & VERIFICATION'}
                {decision.decision === 'BLOCK' && 'ENFORCEMENT — ACTION STRICTLY BLOCKED'}
              </span>
            </div>
          </div>

          {/* User-facing Non-accusatory Message */}
          <div
            style={{
              padding: 'var(--space-4)',
              backgroundColor: 'var(--color-bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            <p
              style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--color-text-primary)',
                lineHeight: 1.6,
                margin: 0,
              }}
            >
              {decision.explanation.user_message}
            </p>
          </div>

          {/* User Confirmation & Cooldown Alerts */}
          {decision.required_user_confirmation && (
            <div
              role="alert"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-3)',
                padding: 'var(--space-3) var(--space-4)',
                backgroundColor: 'var(--color-pause-bg)',
                border: '1px solid var(--color-pause-border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--color-pause)',
                fontSize: 'var(--font-size-sm)',
                fontWeight: 500,
              }}
            >
              <AlertOctagon size={18} flex-shrink="0" />
              <span>
                <strong>Explicit Confirmation Required:</strong> Do not proceed without independent out-of-band verification.
              </span>
            </div>
          )}

          {decision.cooldown_seconds && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
              }}
            >
              <Clock size={14} />
              <span>Recommended cooldown pause: {decision.cooldown_seconds} seconds before taking any action.</span>
            </div>
          )}

          {/* Primary Reason & Reason Codes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
              Why this decision?
            </span>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
              {decision.primary_reason}
            </p>
            {decision.reason_codes.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                {decision.reason_codes.map((code) => (
                  <Badge key={code} variant="neutral" size="sm">
                    {code}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 2.2 Structured Intelligence Panel Navigator */}
      <div
        role="navigation"
        aria-label="Intelligence Sections"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
          padding: 'var(--space-2) var(--space-3)',
          backgroundColor: 'var(--color-bg-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <button
          type="button"
          onClick={() => handleSelectSection('section-overview')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: 'var(--space-2) var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
          }}
        >
          <LayoutDashboard size={14} color="var(--color-accent)" />
          Overview / Executive Summary
        </button>

        <button
          type="button"
          onClick={() => handleSelectSection('panel-evidence')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: 'var(--space-2) var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
          }}
        >
          <CheckCircle2 size={14} color="var(--color-accent)" />
          Evidence & Verification
          <Badge
            size="sm"
            variant={
              analysis.evidence.overall_status === 'SUPPORTED'
                ? 'success'
                : analysis.evidence.overall_status === 'CONTRADICTED'
                ? 'danger'
                : 'warning'
            }
          >
            {analysis.evidence.overall_status}
          </Badge>
        </button>

        <button
          type="button"
          onClick={() => handleSelectSection('panel-identity')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: 'var(--space-2) var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
          }}
        >
          <UserCheck size={14} color="var(--color-accent)" />
          Identity Resolution
          <Badge
            size="sm"
            variant={analysis.identity.identity_status === 'ESTABLISHED' ? 'success' : 'warning'}
          >
            {analysis.identity.identity_status}
          </Badge>
        </button>

        <button
          type="button"
          onClick={() => handleSelectSection('panel-threat')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: 'var(--space-2) var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
          }}
        >
          <Activity size={14} color="var(--color-accent)" />
          Threat & Action Chain
          <Badge
            size="sm"
            variant={analysis.threat.high_impact_action_count > 0 ? 'danger' : 'neutral'}
          >
            {analysis.threat.attack_stage || (analysis.threat.high_impact_action_count > 0 ? 'HIGH' : 'STANDARD')}
          </Badge>
        </button>

        <button
          type="button"
          onClick={() => handleSelectSection('section-response')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: 'var(--space-2) var(--space-3)',
            backgroundColor: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
          }}
        >
          <Compass size={14} color="var(--color-accent)" />
          Recommended Response
        </button>
      </div>

      {/* 2.5 Intervention Experience Layer (Phase 12.3) */}
      {isConfirmedOverride && (
        <ProtectionBanner
          decision={decision.decision}
          title="User Manual Override Confirmed"
          description={`Original policy was acknowledged by the user (${decision.decision}). Proceeding under user manual verification.`}
        />
      )}

      {/* Section 1: Overview & Executive Summary */}
      <section
        id="section-overview"
        aria-label="Executive Overview"
        style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
      >
        {/* High-Impact Consequence Action (Engine 3) */}
        {model.highImpactActions.length > 0 && (
          <HighImpactActionAlert
            actions={model.highImpactActions}
            onSelectAction={() => handleSelectSection('panel-actions')}
          />
        )}

        {/* Protection Summary (5 Core Analytical Dimensions) */}
        <ProtectionSummaryCard
          dimensions={model.protectionSummary}
          onSelectSection={handleSelectSection}
        />

        {/* Why Did Nivesh Intervene? */}
        <WhyIntervenedSection
          primaryReason={decision.primary_reason}
          reasonCodes={decision.reason_codes}
          reasons={model.reasons}
          onSelectSection={handleSelectSection}
        />
      </section>

      {/* Section 2: Recommended Response */}
      <section id="section-response" aria-label="Recommended Response">
        {/* Recommended Next Step & Contextual Action Controls */}
        <RecommendedNextStepCard
          decision={decision.decision}
          recommendedInstruction={model.recommendedNextStep}
          availableActions={model.availableActions}
          onActionClick={handleActionClick}
          isConfirmedOverride={isConfirmedOverride}
        />
      </section>

      {/* Override Confirmation Modal */}
      <OverrideConfirmationModal
        isOpen={isOverrideModalOpen}
        onClose={() => setIsOverrideModalOpen(false)}
        onConfirmOverride={() => {
          setIsConfirmedOverride(true);
          if (onOverrideConfirmed) onOverrideConfirmed();
        }}
        decision={decision.decision}
        primaryReason={decision.primary_reason}
        actionDescription={
          model.highImpactActions[0]
            ? `Proceeding with ${model.highImpactActions[0].action_type.replace(/_/g, ' ')} (${model.highImpactActions[0].target || 'interaction'})`
            : undefined
        }
        analysisId={analysis.analysis_id}
      />

      {/* 3. Multi-Engine Intelligence & Visualization Layer (Phase 12.4) */}
      <IntelligenceDetailView analysis={analysis} />
    </div>
  );
};
