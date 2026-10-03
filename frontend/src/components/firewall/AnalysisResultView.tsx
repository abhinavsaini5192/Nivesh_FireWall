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
  FileText,
  UserCheck,
  Fingerprint,
  Activity,
  GitCommit,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { Card, CardContent } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Panel } from '../common/Panel';
import { MetadataRow } from '../common/MetadataRow';
import { Accordion, AccordionItem } from '../common/Accordion';
import { SemanticStatusBadge } from '../status/SemanticStatusBadge';

export interface AnalysisResultViewProps {
  analysis: FirewallAnalysisResponse;
  onAnalyzeAnother: () => void;
}

export const AnalysisResultView: React.FC<AnalysisResultViewProps> = ({
  analysis,
  onAnalyzeAnother,
}) => {
  const [copiedId, setCopiedId] = React.useState(false);
  const { decision, content, claims, actions, evidence, identity, threat, fingerprint, behaviour, provenance } =
    analysis;

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

      {/* 3. Multi-Engine Intelligence Breakdown Accordions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <h3
          style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: 'var(--font-weight-semibold)',
            color: 'var(--color-text-primary)',
            marginTop: 'var(--space-2)',
          }}
        >
          Intelligence Findings Breakdown
        </h3>

        <Accordion>
          {/* PANEL A: Claims Intelligence (Engine 2 & 5) */}
          <AccordionItem
            id="panel-claims"
            title="Extracted Financial Claims"
            subtitle={`${claims.length} atomic assertion${claims.length === 1 ? '' : 's'} identified`}
            icon={<FileText size={18} />}
            badge={<Badge variant={claims.length > 0 ? 'accent' : 'neutral'}>{claims.length}</Badge>}
            defaultOpen={claims.length > 0}
          >
            {claims.length === 0 ? (
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', margin: 0 }}>
                No verifiable financial claims or return guarantees detected in content.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {claims.map((claim) => (
                  <div
                    key={claim.claim_id}
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: 'var(--color-bg-surface)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
                      <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                        "{claim.text}"
                      </span>
                      {claim.verification_status && (
                        <Badge
                          variant={
                            claim.verification_status === 'SUPPORTED'
                              ? 'success'
                              : claim.verification_status === 'CONTRADICTED'
                              ? 'danger'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {claim.verification_status}
                        </Badge>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: 'var(--space-2)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      <span>Topic: <strong>{claim.topic}</strong></span>
                      <span>•</span>
                      <span>Predicate: <strong>{claim.predicate}</strong></span>
                      <span>•</span>
                      <span>Modality: <strong>{claim.modality}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </AccordionItem>

          {/* PANEL B: Requested Actions (Engine 3) */}
          <AccordionItem
            id="panel-actions"
            title="Requested User Actions"
            subtitle={`${actions.length} action request${actions.length === 1 ? '' : 's'} analyzed`}
            icon={<ExternalLink size={18} />}
            badge={<Badge variant={actions.length > 0 ? 'accent' : 'neutral'}>{actions.length}</Badge>}
            defaultOpen={actions.length > 0}
          >
            {actions.length === 0 ? (
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', margin: 0 }}>
                No explicit user actions (e.g. transfers, downloads, credentials) requested.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {actions.map((act) => (
                  <div
                    key={act.action_id}
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: 'var(--color-bg-surface)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <Badge variant="accent" size="sm">
                          {act.action_type}
                        </Badge>
                        {act.target && (
                          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                            Target: <code style={{ color: 'var(--color-accent-hover)' }}>{act.target}</code>
                          </span>
                        )}
                      </div>
                      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                        {act.urgency_detected && (
                          <Badge variant="warning" size="sm">
                            Urgency Detected
                          </Badge>
                        )}
                        <Badge
                          variant={act.reversibility === 'IRREVERSIBLE' ? 'danger' : 'neutral'}
                          size="sm"
                        >
                          {act.reversibility}
                        </Badge>
                      </div>
                    </div>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      Impact Category: {act.impact_category}
                    </span>
                  </div>
                ))}
              </div>
            )}
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-3)' }}>
              <Panel title="Supported Claims">
                <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-allow)' }}>
                  {evidence.supported_claims_count}
                </span>
              </Panel>
              <Panel title="Contradicted Claims">
                <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-block)' }}>
                  {evidence.contradicted_claims_count}
                </span>
              </Panel>
              <Panel title="Insufficient Evidence">
                <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-warn)' }}>
                  {evidence.insufficient_claims_count}
                </span>
              </Panel>
              <Panel title="Source Filings Retrieved">
                <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  {evidence.source_documents_count}
                </span>
              </Panel>
            </div>
            <div style={{ marginTop: 'var(--space-3)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Retrieval Status: <strong>{evidence.retrieval_status}</strong> (Total verifications: {evidence.verification_count})
            </div>
          </AccordionItem>

          {/* PANEL D: Identity Resolution (Engine 9) */}
          <AccordionItem
            id="panel-identity"
            title="Entity Identity Resolution"
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <MetadataRow
                label="Identity Resolution Status"
                value={<strong>{identity.identity_status}</strong>}
              />
              <MetadataRow
                label="Resolution Confidence"
                value={`${(identity.confidence * 100).toFixed(0)}%`}
                isMono
              />
              {identity.claimed_entities.length > 0 && (
                <div>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Claimed Entities Mentioned:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                    {identity.claimed_entities.map((ent) => (
                      <Badge key={ent} variant="accent" size="sm">
                        {ent}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {identity.findings_summary.length > 0 && (
                <div style={{ marginTop: 'var(--space-2)' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Identity Verification Findings:
                  </span>
                  <ul style={{ paddingLeft: 'var(--space-4)', marginTop: 'var(--space-1)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {identity.findings_summary.map((finding, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{finding}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {threat.attack_stage && threat.terminal_stage && (
                <MetadataRow
                  label="Attack Path Progression"
                  value={
                    <span style={{ color: 'var(--color-warn)' }}>
                      {threat.attack_stage} → {threat.terminal_stage}
                    </span>
                  }
                  isMono
                />
              )}
              <MetadataRow
                label="High Impact Consequence Actions"
                value={threat.high_impact_action_count}
              />
              {threat.threat_signals.length > 0 && (
                <div>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Detected Threat Signals:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                    {threat.threat_signals.map((sig) => (
                      <Badge key={sig} variant="danger" size="sm">
                        {sig}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {threat.threat_families.length > 0 && (
                <div style={{ marginTop: 'var(--space-1)' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Threat Classifications:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                    {threat.threat_families.map((fam) => (
                      <Badge key={fam} variant="neutral" size="sm">
                        {fam}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <MetadataRow
                label="Structural Match Type"
                value={<strong>{fingerprint.match_type}</strong>}
              />
              <MetadataRow
                label="Structural Equivalence"
                value={
                  fingerprint.match_type === 'SEMANTIC_VARIANT' || fingerprint.match_type === 'EXACT_MATCH'
                    ? 'YES (Known Template Structure)'
                    : 'NO'
                }
              />
              {fingerprint.fingerprint_id && (
                <MetadataRow
                  label="Fingerprint Identifier"
                  value={fingerprint.fingerprint_id}
                  copyableText={fingerprint.fingerprint_id}
                  isMono
                />
              )}
              <MetadataRow
                label="Network Observation Count"
                value={`${fingerprint.observation_count} sightings across ${fingerprint.distinct_channels_count} channels`}
              />
            </div>
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                {behaviour.time_pressure_detected && (
                  <Badge variant="danger" size="sm">
                    Time Pressure / Urgency
                  </Badge>
                )}
                {behaviour.rapid_escalation_detected && (
                  <Badge variant="warning" size="sm">
                    Rapid Action Escalation
                  </Badge>
                )}
                {behaviour.channel_migration_detected && (
                  <Badge variant="warning" size="sm">
                    Off-Platform Migration
                  </Badge>
                )}
              </div>

              {behaviour.signals.length > 0 && (
                <div>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Behavioural Signals:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                    {behaviour.signals.map((sig) => (
                      <Badge key={sig} variant="neutral" size="sm">
                        {sig}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {behaviour.findings.length > 0 && (
                <div>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Observed Sequence Patterns:
                  </span>
                  <ul style={{ paddingLeft: 'var(--space-4)', marginTop: 'var(--space-1)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {behaviour.findings.map((f, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              <MetadataRow
                label="Events Tracked in Session"
                value={behaviour.events_in_session}
              />
            </div>
          </AccordionItem>

          {/* PANEL H: Provenance & Audit Metadata */}
          <AccordionItem
            id="panel-provenance"
            title="Provenance & Pipeline Audit"
            subtitle={`Status: ${analysis.pipeline_status} (${analysis.duration_ms.toFixed(1)}ms)`}
            icon={<Clock size={18} />}
            defaultOpen={true}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              <MetadataRow label="Pipeline Execution Status" value={analysis.pipeline_status} isMono />
              <MetadataRow label="Ingestion Channel" value={content.channel} />
              <MetadataRow label="Input Type" value={content.input_type} />
              <MetadataRow label="Execution Duration" value={`${analysis.duration_ms.toFixed(2)} ms`} isMono />
              <MetadataRow label="Created Timestamp" value={analysis.created_at} isMono />
              {provenance && typeof provenance === 'object' && (
                <div style={{ marginTop: 'var(--space-2)' }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Engines Lineage:
                  </span>
                  <pre
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: 'var(--color-bg-surface)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '11px',
                      color: 'var(--color-text-secondary)',
                      marginTop: '4px',
                      overflowX: 'auto',
                    }}
                  >
                    {JSON.stringify(provenance, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </AccordionItem>
        </Accordion>
      </div>
    </div>
  );
};
