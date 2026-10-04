import React from 'react';
import { PublicLayout } from '../landing/components/PublicLayout';
import { PageHero } from '../landing/components/PageHero';
import { CallToAction } from '../landing/components/CallToAction';
import {
  FileText,
  CheckSquare,
  Workflow,
  Compass,
  Scale,
  GitBranch,
  Fingerprint,
  ShieldCheck,
  UserCheck,
  Activity,
  AlertCircle,
} from 'lucide-react';

export interface FeaturesPageProps {
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
}

export const FeaturesPage: React.FC<FeaturesPageProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  const capabilities = [
    {
      num: '01',
      title: 'Content Intelligence',
      icon: <FileText size={20} color="#c084fc" />,
      tag: 'Engine 01',
      summary: 'Understands financial material from user-submitted content.',
      detail:
        'Normalizes heterogeneous inputs—raw chat text, URLs, formatted financial documents, or OCR extractions—into a structured representation without altering conversational context.',
    },
    {
      num: '02',
      title: 'Claim Intelligence',
      icon: <CheckSquare size={20} color="#c084fc" />,
      tag: 'Engine 02',
      summary: 'Breaks complex financial statements into atomic, verifiable claims.',
      detail:
        'Separates promotional rhetoric from concrete factual assertions (e.g., promised percentage returns, SEBI registration claims, exemption waivers), identifying exactly what evidentiary standards are required to verify each.',
    },
    {
      num: '03',
      title: 'Action Intelligence',
      icon: <Workflow size={20} color="#38bdf8" />,
      tag: 'Engine 03',
      summary: 'Identifies what the content is asking a person to do.',
      detail:
        'Traces actions along an escalation spectrum: informational browsing → messaging channel migration → APK software installation → credential disclosure → irreversible bank/UPI wire transfers.',
    },
    {
      num: '04',
      title: 'Source Intelligence',
      icon: <Compass size={20} color="#38bdf8" />,
      tag: 'Engine 04',
      summary: 'Connects claims and identity references to authoritative registries.',
      detail:
        'Directly interfaces with official statutory bodies including SEBI, RBI Sachet, NSE, and BSE, querying canonical records with precision caching and graceful degradation.',
    },
    {
      num: '05',
      title: 'Evidence Verification',
      icon: <Scale size={20} color="#34d399" />,
      tag: 'Engine 05',
      summary: 'Rigorously evaluates claim evidence across granular verdict states.',
      detail:
        'Categorizes findings into Supported, Partially Supported, Contradicted, Insufficient Evidence, Not Verifiable, and Source Conflict. Lack of evidence is never equated with proof of fraud.',
    },
    {
      num: '06',
      title: 'Threat & Attack-Path Intelligence',
      icon: <GitBranch size={20} color="#fbbf24" />,
      tag: 'Engine 06',
      summary: 'Reconstructs explicit causal graphs between claims, entities, and channels.',
      detail:
        'Instead of opaque "AI scam scores", Nivesh builds a transparent timeline graph showing how attackers guide targets across apps, fabricate legitimacy, and apply pressure.',
    },
    {
      num: '07',
      title: 'Scam Fingerprint Intelligence',
      icon: <Fingerprint size={20} color="#fbbf24" />,
      tag: 'Engine 07',
      summary: 'Detects structurally similar scam patterns while preserving privacy.',
      detail:
        'Identifies known deceptive archetypes—such as fake institutional IPO task allocations or synthetic advisory channels—while strictly stripping victim phone numbers, emails, and credentials.',
    },
    {
      num: '08',
      title: 'Policy & Intervention',
      icon: <ShieldCheck size={20} color="#f87171" />,
      tag: 'Engine 08',
      summary: 'The final authority that converts intelligence into protective action.',
      detail:
        'Translates combined evidence, risk severity, and action irreversibility into deterministic policy decisions: ALLOW, INFORM, WARN, PAUSE, or BLOCK.',
    },
    {
      num: '09',
      title: 'Identity Verification',
      icon: <UserCheck size={20} color="#c084fc" />,
      tag: 'Engine 09',
      summary: 'Determines whether claimed entities can be established through evidence.',
      detail:
        'Evaluates registration statuses: Established, Partially Established, Not Established, Identity Mismatch, Ambiguous, and Insufficient Evidence. Avoids confusing name similarity with proof.',
    },
    {
      num: '10',
      title: 'Behavioural Signals',
      icon: <Activity size={20} color="#38bdf8" />,
      tag: 'Engine 10',
      summary: 'Detects observable interaction dynamics and pressure tactics.',
      detail:
        'Monitors objective signals like artificial urgency, rapid escalation, and channel migration. Never speculates on psychology, moral character, or user gullibility.',
    },
  ];

  return (
    <PublicLayout
      currentRoute="/features"
      onNavigate={onNavigate}
      onOpenFirewall={onOpenFirewall}
    >
      {/* Page Hero */}
      <PageHero
        eyebrow="CAPABILITIES"
        headline="Ten layers of intelligence. One protection system."
        description="Nivesh Firewall combines content understanding, evidence verification, action analysis, identity resolution, behavioural signals, threat intelligence and policy enforcement into a single pre-action protection layer."
        primaryAction={{
          label: 'Open Firewall',
          onClick: onOpenFirewall,
        }}
        secondaryAction={{
          label: 'Inspect Sources',
          onClick: () => onNavigate('/sources'),
        }}
      />

      {/* Ten Capabilities Editorial Sequence */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', margin: '48px 0' }}>
        {capabilities.map((cap) => (
          <div
            key={cap.num}
            className="card-glass"
            style={{
              padding: '36px',
              borderLeft: '3px solid #a855f7',
              transition: 'border-color 0.2s ease, transform 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {cap.icon}
                </div>
                <div>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#a855f7', fontWeight: 700, letterSpacing: '0.1em' }}>
                    LAYER {cap.num} &bull; {cap.tag}
                  </span>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', marginTop: '2px' }}>
                    {cap.title}
                  </h3>
                </div>
              </div>
            </div>

            <p style={{ fontSize: '15px', color: '#ffffff', fontWeight: 500, lineHeight: 1.6, marginBottom: '8px' }}>
              {cap.summary}
            </p>
            <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.65 }}>
              {cap.detail}
            </p>
          </div>
        ))}
      </div>

      {/* Epistemic Humility Note */}
      <section
        className="card-glass"
        style={{
          padding: '36px',
          background: 'rgba(24, 24, 24, 0.65)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          marginTop: '48px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
          <div style={{ color: '#38bdf8', marginTop: '2px' }}>
            <AlertCircle size={22} />
          </div>
          <div>
            <h4 style={{ fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
              The Philosophy of Epistemic Humility
            </h4>
            <p style={{ fontSize: '14px', color: '#cbd5e1', lineHeight: 1.65 }}>
              Nivesh deliberately refuses to output vague probabilities or speculative risk scores. Every intervention decision is grounded in concrete, traceable evidence: which regulatory entity was queried, what specific claim failed verification, and what requested action caused escalation. If evidence is missing, the firewall reports &ldquo;Insufficient Evidence&rdquo; rather than fabricating a conclusion.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <CallToAction
        headline="Ten layers working together before you act."
        description="Verify any financial claim against the full 10-layer defense architecture before making a consequential decision."
        primaryLabel="Open Firewall"
        secondaryLabel="Inspect Sources"
        onPrimaryClick={onOpenFirewall}
        onSecondaryClick={() => onNavigate('/sources')}
      />
    </PublicLayout>
  );
};

export default FeaturesPage;
