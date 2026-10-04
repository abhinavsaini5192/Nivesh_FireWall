import React from 'react';
import { PublicLayout } from '../landing/components/PublicLayout';
import { PageHero } from '../landing/components/PageHero';
import { CallToAction } from '../landing/components/CallToAction';
import {
  Eye,
  ShieldCheck,
  Info,
  AlertTriangle,
  PauseCircle,
  XCircle,
  Lock,
} from 'lucide-react';

export interface HowItWorksPageProps {
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
}

export const HowItWorksPage: React.FC<HowItWorksPageProps> = ({
  onNavigate,
  onOpenFirewall,
}) => {
  return (
    <PublicLayout
      currentRoute="/how-it-works"
      onNavigate={onNavigate}
      onOpenFirewall={onOpenFirewall}
    >
      {/* Page Hero */}
      <PageHero
        eyebrow="HOW IT WORKS"
        headline="Protection starts before the transaction."
        description="Nivesh Firewall examines financial content, understands the claims and requested actions inside it, verifies available evidence, reconstructs the threat path, and applies protection before a dangerous action is completed."
        primaryAction={{
          label: 'Open Firewall',
          onClick: onOpenFirewall,
        }}
        secondaryAction={{
          label: 'Explore Features',
          onClick: () => onNavigate('/features'),
        }}
      />

      {/* Workflow Navigation Tracker */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          margin: '0 auto 64px',
          padding: '12px 20px',
          borderRadius: '9999px',
          background: 'rgba(24, 24, 24, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          maxWidth: '820px',
        }}
      >
        {['01 Observe', '02 Understand', '03 Verify', '04 Trace', '05 Intervene', '06 Remember'].map((stage, i) => (
          <React.Fragment key={stage}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono, monospace)', color: '#cbd5e1', fontWeight: 600 }}>
              {stage}
            </span>
            {i < 5 && <span style={{ color: 'rgba(255, 255, 255, 0.25)', fontSize: '12px' }}>&rarr;</span>}
          </React.Fragment>
        ))}
      </div>

      {/* Stage 01: Observe */}
      <section className="editorial-block">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '36px', alignItems: 'center' }}>
          <div>
            <span className="step-number">Stage 01</span>
            <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#ffffff', margin: '8px 0 16px', letterSpacing: '-0.02em' }}>
              Observe Content
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: 1.65, marginBottom: '16px' }}>
              Nivesh receives user-submitted financial content when a check is initiated. The firewall can inspect text messages, pasted links, active webpage content, images, OCR-derived transcripts, and social solicitations.
            </p>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                borderRadius: '8px',
                backgroundColor: 'rgba(168, 85, 247, 0.1)',
                border: '1px solid rgba(168, 85, 247, 0.25)',
                fontSize: '12px',
                color: '#c084fc',
                fontWeight: 500,
              }}
            >
              <Lock size={14} />
              <span>Strictly User-Initiated — No background monitoring or passive surveillance</span>
            </div>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
              Accepted Content Modalities
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="flow-node">
                <Eye size={16} color="#c084fc" />
                <span>Text solicitations &amp; advisory channel messages</span>
              </div>
              <div className="flow-node">
                <Eye size={16} color="#c084fc" />
                <span>Webpage DOM &amp; target URLs via extension</span>
              </div>
              <div className="flow-node">
                <Eye size={16} color="#c084fc" />
                <span>OCR transcripts of screenshots &amp; trading proofs</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stage 02: Understand */}
      <section className="editorial-block">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '36px', alignItems: 'center' }}>
          <div>
            <span className="step-number">Stage 02</span>
            <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#ffffff', margin: '8px 0 16px', letterSpacing: '-0.02em' }}>
              Understand Intent &amp; Claims
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: 1.65, marginBottom: '16px' }}>
              Nivesh decomposes the input into atomic claims, identifies named entities and regulatory assertions, isolates requested actions, and detects contextual pressure signals.
            </p>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: 1.6 }}>
              <strong style={{ color: '#ffffff' }}>Crucial Principle:</strong> Understanding content does not mean automatically deciding that the content is fraudulent. Nuance matters—legitimate financial discussions must be preserved without alarmism.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
              Semantic Decomposition
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <span style={{ fontSize: '11px', color: '#c084fc', fontFamily: 'var(--font-mono)' }}>CLAIM EXTRACTED</span>
                <p style={{ fontSize: '13px', color: '#ffffff', marginTop: '4px' }}>&ldquo;Guaranteed 40% monthly return with SEBI registered advisor&rdquo;</p>
              </div>
              <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <span style={{ fontSize: '11px', color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>REQUESTED ACTION</span>
                <p style={{ fontSize: '13px', color: '#ffffff', marginTop: '4px' }}>Download custom trading APK file outside official app store</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stage 03: Verify */}
      <section className="editorial-block">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '36px', alignItems: 'center' }}>
          <div>
            <span className="step-number">Stage 03</span>
            <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#ffffff', margin: '8px 0 16px', letterSpacing: '-0.02em' }}>
              Verify Against Authoritative Sources
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: 1.65, marginBottom: '16px' }}>
              Claims and identity references are checked against primary statutory registries: SEBI registered intermediaries, RBI cautionary lists (Sachet), and NSE/BSE announcements.
            </p>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: 1.6 }}>
              <strong style={{ color: '#ffffff' }}>Epistemic Humility:</strong> Evidence is evaluated before a conclusion is reached. Lack of evidence does not mean something is definitively false, but unsupported claims require explicit verification.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
              Official Cross-Verification Ecosystem
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#ffffff' }}>SEBI Registry</span>
                <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>RIA &amp; RA accreditation records</p>
              </div>
              <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#ffffff' }}>RBI Sachet</span>
                <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>Unauthorized deposit caution alerts</p>
              </div>
              <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#ffffff' }}>NSE Registry</span>
                <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>Listed entity verification</p>
              </div>
              <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#ffffff' }}>BSE Circulars</span>
                <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>Member &amp; corporate filings</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stage 04: Trace Action Progression */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 40px' }}>
          <span className="step-number">Stage 04</span>
          <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#ffffff', margin: '8px 0 16px', letterSpacing: '-0.02em' }}>
            Trace the Action Progression Path
          </h2>
          <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: 1.65 }}>
            Nivesh is interested in the <strong style={{ color: '#ffffff' }}>action path</strong>, not merely the financial topic. Fraud succeeds through gradual escalation across channels rather than isolated assertions.
          </p>
        </div>

        {/* Conceptual Action Chain Diagram */}
        <div
          className="card-glass"
          style={{
            padding: '36px 24px',
            maxWidth: '1000px',
            margin: '0 auto',
            background: 'rgba(18, 18, 18, 0.8)',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px', alignItems: 'center' }}>
            <div style={{ textAlign: 'center', padding: '16px 10px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>STEP 1</span>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginTop: '6px' }}>Financial Content</p>
            </div>
            <div style={{ textAlign: 'center', color: '#a855f7' }}>&rarr;</div>
            <div style={{ textAlign: 'center', padding: '16px 10px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>STEP 2</span>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginTop: '6px' }}>Return Claim</p>
            </div>
            <div style={{ textAlign: 'center', color: '#a855f7' }}>&rarr;</div>
            <div style={{ textAlign: 'center', padding: '16px 10px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>STEP 3</span>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginTop: '6px' }}>Channel Migration</p>
            </div>
            <div style={{ textAlign: 'center', color: '#a855f7' }}>&rarr;</div>
            <div style={{ textAlign: 'center', padding: '16px 10px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: '#f87171' }}>STEP 4</span>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#f87171', marginTop: '6px' }}>Credential / Fund Transfer</p>
            </div>
          </div>
          <p style={{ fontSize: '12px', color: '#94a3b8', textAlign: 'center', marginTop: '24px' }}>
            Nivesh detects the moment of channel migration and forced installation before money moves.
          </p>
        </div>
      </section>

      {/* Stage 05: Intervene */}
      <section className="editorial-block">
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 40px' }}>
          <span className="step-number">Stage 05</span>
          <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#ffffff', margin: '8px 0 16px', letterSpacing: '-0.02em' }}>
            Intervene Before Consequential Harm
          </h2>
          <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: 1.65 }}>
            Protection decisions depend on combined evidence, action impact, and explicit policy rules. Merely mentioning stocks or finances never triggers a block.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {/* ALLOW */}
          <div className="card-glass" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span className="policy-badge policy-badge-allow">
                <ShieldCheck size={13} />
                ALLOW
              </span>
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '6px' }}>Verified &amp; Benign</h4>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
              Standard educational content, corroborated claims, or verifiable statutory entities.
            </p>
          </div>

          {/* INFORM */}
          <div className="card-glass" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span className="policy-badge policy-badge-inform">
                <Info size={13} />
                INFORM
              </span>
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '6px' }}>Advisory Context</h4>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
              Standard market risks, general claims without pressure, or missing non-critical context.
            </p>
          </div>

          {/* WARN */}
          <div className="card-glass" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span className="policy-badge policy-badge-warn">
                <AlertTriangle size={13} />
                WARN
              </span>
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '6px' }}>Elevated Risk</h4>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
              Unverified regulatory assertions, urgency tactics, or uncorroborated trading promises.
            </p>
          </div>

          {/* PAUSE */}
          <div className="card-glass" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span className="policy-badge policy-badge-pause">
                <PauseCircle size={13} />
                PAUSE
              </span>
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '6px' }}>Mandatory Cooldown</h4>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
              High-stakes wire transfers or credential requests requiring explicit user confirmation.
            </p>
          </div>

          {/* BLOCK */}
          <div className="card-glass" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span className="policy-badge policy-badge-block">
                <XCircle size={13} />
                BLOCK
              </span>
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '6px' }}>Known Fraud Pattern</h4>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
              Documented scam fingerprint, impersonation of official regulators, or APK malware delivery.
            </p>
          </div>
        </div>
      </section>

      {/* Stage 06: Remember */}
      <section className="editorial-block">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '36px', alignItems: 'center' }}>
          <div>
            <span className="step-number">Stage 06</span>
            <h2 style={{ fontSize: '28px', fontWeight: 700, color: '#ffffff', margin: '8px 0 16px', letterSpacing: '-0.02em' }}>
              Remember Privately
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: 1.65, marginBottom: '16px' }}>
              Discovered deception patterns contribute to collective structural defense without ever storing or sharing personal user identity data.
            </p>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: 1.6 }}>
              Scam fingerprints preserve the transition sequence (e.g., Telegram &rarr; APK &rarr; UPI transfer) while stripping all phone numbers, email addresses, OTPs, PAN/Aadhaar cards, bank accounts, and raw private messages.
            </p>
          </div>

          <div className="card-glass" style={{ padding: '28px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
              Privacy-Preserving Structural Intelligence
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#34d399' }}>
                <span>&check;</span>
                <span>Abstract behavioral sequences indexed</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#34d399' }}>
                <span>&check;</span>
                <span>Deceptive linguistic structures recognized</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#f87171' }}>
                <span>&times;</span>
                <span>Zero phone numbers or email addresses stored</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#f87171' }}>
                <span>&times;</span>
                <span>Zero financial credentials, OTPs, or passwords captured</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <CallToAction
        headline="Protection works best before the irreversible step."
        description="Run any financial claim, solicitous message, or suspicious webpage through the Nivesh Firewall before taking action."
        primaryLabel="Open Firewall"
        secondaryLabel="Explore Features"
        onPrimaryClick={onOpenFirewall}
        onSecondaryClick={() => onNavigate('/features')}
      />
    </PublicLayout>
  );
};

export default HowItWorksPage;
