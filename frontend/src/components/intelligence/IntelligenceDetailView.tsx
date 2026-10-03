import React from 'react';
import {
  FileText,
  ExternalLink,
  CheckCircle2,
  UserCheck,
  GitCommit,
  Fingerprint,
  Activity,
  Clock,
  GitMerge,
  Eye,
  FileCode,
  Sliders,
} from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import type { IntelligenceViewMode } from '../../types/intelligence';
import { Accordion, AccordionItem } from '../common/Accordion';
import { Badge } from '../common/Badge';
import { UserExecutiveSummaryCard } from './UserExecutiveSummaryCard';
import { ClaimsCard } from './ClaimsCard';
import { ActionHierarchyCard } from './ActionHierarchyCard';
import { ClaimEvidenceDetailCard } from './ClaimEvidenceDetailCard';
import { EntityRelationshipGraph } from './EntityRelationshipGraph';
import { AttackPathVisualizer } from './AttackPathVisualizer';
import { FingerprintIntelligenceCard } from './FingerprintIntelligenceCard';
import { BehaviourTimelineView } from './BehaviourTimelineView';
import { PolicyReasonTraceView } from './PolicyReasonTraceView';
import { ProvenanceAuditPanel } from './ProvenanceAuditPanel';
import { PrivacySafeguardNotice } from './PrivacySafeguardNotice';

export interface IntelligenceDetailViewProps {
  analysis: FirewallAnalysisResponse;
}

export const IntelligenceDetailView: React.FC<IntelligenceDetailViewProps> = ({ analysis }) => {
  const [viewMode, setViewMode] = React.useState<IntelligenceViewMode>('technical');
  const { claims, actions, evidence, identity, threat, fingerprint, behaviour } = analysis;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', width: '100%' }}>
      {/* View Mode Switcher Header */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <Sliders size={18} color="var(--color-accent)" />
          <h3
            id="intelligence-breakdown-heading"
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 'var(--font-weight-semibold)',
              color: 'var(--color-text-primary)',
              margin: 0,
            }}
          >
            Intelligence Findings Breakdown
          </h3>
        </div>

        {/* Mode Selector Buttons */}
        <div
          role="group"
          aria-label="Intelligence Detail Presentation Mode"
          style={{
            display: 'flex',
            backgroundColor: 'var(--color-bg-subtle)',
            padding: '2px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          <button
            onClick={() => setViewMode('user')}
            aria-pressed={viewMode === 'user'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
              padding: 'var(--space-1) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: viewMode === 'user' ? 'var(--color-bg-surface)' : 'transparent',
              color: viewMode === 'user' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
              fontWeight: viewMode === 'user' ? 600 : 400,
              fontSize: 'var(--font-size-xs)',
              cursor: 'pointer',
              boxShadow: viewMode === 'user' ? 'var(--shadow-sm)' : 'none',
              transition: 'var(--transition-fast)',
            }}
          >
            <Eye size={14} />
            Executive Summary
          </button>
          <button
            onClick={() => setViewMode('technical')}
            aria-pressed={viewMode === 'technical'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
              padding: 'var(--space-1) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: viewMode === 'technical' ? 'var(--color-bg-surface)' : 'transparent',
              color: viewMode === 'technical' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
              fontWeight: viewMode === 'technical' ? 600 : 400,
              fontSize: 'var(--font-size-xs)',
              cursor: 'pointer',
              boxShadow: viewMode === 'technical' ? 'var(--shadow-sm)' : 'none',
              transition: 'var(--transition-fast)',
            }}
          >
            <FileCode size={14} />
            Deep Intelligence & Timelines
          </button>
        </div>
      </div>

      {/* User Executive Summary Mode */}
      {viewMode === 'user' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <UserExecutiveSummaryCard
            analysis={analysis}
            onExploreTechnical={() => setViewMode('technical')}
          />
          <PrivacySafeguardNotice />
        </div>
      ) : (
        /* Technical Intelligence & Visual Graph Mode */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <Accordion>
            {/* PANEL A: Claims Intelligence (Engine 2 & 5) */}
            <AccordionItem
              id="panel-claims"
              title="Extracted Financial Claims"
              subtitle={`${claims.length} atomic assertion${claims.length === 1 ? '' : 's'} identified`}
              icon={<FileText size={18} />}
              badge={<Badge variant={claims.length > 0 ? 'accent' : 'neutral'}>{claims.length}</Badge>}
              defaultOpen={true}
            >
              <ClaimsCard claims={analysis.claims} />
            </AccordionItem>

            {/* PANEL B: Requested Actions (Engine 3) */}
            <AccordionItem
              id="panel-actions"
              title="Requested User Actions"
              subtitle={`${actions.length} action request${actions.length === 1 ? '' : 's'} analyzed`}
              icon={<ExternalLink size={18} />}
              badge={<Badge variant={actions.length > 0 ? 'accent' : 'neutral'}>{actions.length}</Badge>}
              defaultOpen={true}
            >
              <ActionHierarchyCard actions={analysis.actions} />
            </AccordionItem>

            {/* PANEL C: Evidence Verification (Engine 5 & 4) */}
            <AccordionItem
              id="panel-evidence"
              title="Evidence Verification"
              subtitle={`Overall status: ${evidence.overall_status}`}
              icon={<CheckCircle2 size={18} />}
              badge={
                <Badge
                  variant={
                    evidence.overall_status === 'SUPPORTED'
                      ? 'success'
                      : evidence.overall_status === 'CONTRADICTED'
                      ? 'danger'
                      : 'warning'
                  }
                >
                  {evidence.overall_status}
                </Badge>
              }
              defaultOpen={true}
            >
              <ClaimEvidenceDetailCard
                evidence={analysis.evidence}
                sourceMode={analysis.evidence.retrieval_status}
                claims={analysis.claims}
              />
            </AccordionItem>

            {/* PANEL D: Identity Resolution (Engine 9) */}
            <AccordionItem
              id="panel-identity"
              title="Entity Verification & Registry Flow"
              subtitle={`Status: ${identity.identity_status}`}
              icon={<UserCheck size={18} />}
              badge={
                <Badge
                  variant={
                    identity.identity_status === 'ESTABLISHED'
                      ? 'success'
                      : identity.identity_status === 'IDENTITY_MISMATCH'
                      ? 'danger'
                      : 'warning'
                  }
                >
                  {identity.identity_status}
                </Badge>
              }
              defaultOpen={true}
            >
              <EntityRelationshipGraph identity={analysis.identity} />
            </AccordionItem>

            {/* PANEL E: Threat & Attack Path Intelligence (Engine 6) */}
            <AccordionItem
              id="panel-threat"
              title="Threat & Attack-Path Analysis"
              subtitle={`${threat.threat_signals.length} signal${threat.threat_signals.length === 1 ? '' : 's'} mapped`}
              icon={<GitCommit size={18} />}
              badge={<Badge variant={threat.threat_signals.length > 0 ? 'danger' : 'neutral'}>{threat.threat_signals.length}</Badge>}
              defaultOpen={true}
            >
              <AttackPathVisualizer analysis={analysis} />
            </AccordionItem>

            {/* PANEL F: Scam Fingerprints (Engine 7) */}
            <AccordionItem
              id="panel-fingerprint"
              title="Scam Fingerprint Intelligence"
              subtitle={`Match: ${fingerprint.match_type}`}
              icon={<Fingerprint size={18} />}
              badge={
                <Badge variant={fingerprint.match_type === 'NO_MATCH' ? 'neutral' : 'warning'}>
                  {fingerprint.match_type}
                </Badge>
              }
              defaultOpen={true}
            >
              <FingerprintIntelligenceCard analysis={analysis} />
            </AccordionItem>

            {/* PANEL G: Behavioural Intelligence (Engine 10) */}
            <AccordionItem
              id="panel-behaviour"
              title="Behavioural Signal Intelligence"
              subtitle={`${behaviour.signals.length} signal${behaviour.signals.length === 1 ? '' : 's'} tracked`}
              icon={<Activity size={18} />}
              badge={<Badge variant={behaviour.signals.length > 0 ? 'warning' : 'neutral'}>{behaviour.signals.length}</Badge>}
              defaultOpen={true}
            >
              <BehaviourTimelineView analysis={analysis} />
            </AccordionItem>

            {/* PANEL H: Policy Reason Trace (Engine 8) */}
            <AccordionItem
              id="panel-policy-trace"
              title="Policy Reason Trace"
              subtitle={`Decision: ${analysis.decision.decision}`}
              icon={<GitMerge size={18} />}
              badge={<Badge variant="neutral">{analysis.decision.decision}</Badge>}
              defaultOpen={true}
            >
              <PolicyReasonTraceView analysis={analysis} />
            </AccordionItem>

            {/* PANEL I: Provenance & Audit Metadata */}
            <AccordionItem
              id="panel-provenance"
              title="Provenance & Pipeline Audit"
              subtitle={`Status: ${analysis.pipeline_status} (${analysis.duration_ms.toFixed(1)}ms)`}
              icon={<Clock size={18} />}
              defaultOpen={true}
            >
              <ProvenanceAuditPanel analysis={analysis} />
            </AccordionItem>
          </Accordion>

          {/* Privacy Safeguard Notice */}
          <PrivacySafeguardNotice />
        </div>
      )}
    </div>
  );
};
