import React from 'react';
import { Database, GitCommit, Layers } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

export const ThreatIntelligenceView: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', width: '100%' }}>
      <SectionHeader
        title="Threat Intelligence Architecture"
        description="Structural threat pattern recognition and collective scam fingerprinting derived from Engines 6 & 7."
        badge={<Badge variant="accent">Read-Only Reference</Badge>}
      />

      {/* Structural Attack-Path Model Explanation */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-6)',
        }}
      >
        <Card variant="surface">
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <GitCommit size={18} color="var(--color-accent)" />
              <CardTitle style={{ fontSize: 'var(--font-size-md)' }}>
                Attack-Path Progression Stages (Engine 6)
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent style={{ gap: 'var(--space-3)' }}>
            <Panel accent="accent" title="Stage 1: Credibility Building">
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                Impersonation of SEBI-registered entities, forged certificates, or high return guarantees.
              </span>
            </Panel>
            <Panel accent="warn" title="Stage 2: Channel Migration">
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                Moving user from public channels (YouTube, Instagram) to private channels (Telegram, WhatsApp VIP).
              </span>
            </Panel>
            <Panel accent="warn" title="Stage 3: Application Installation">
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                Requesting side-loading of unregistered APK terminals or remote desktop software.
              </span>
            </Panel>
            <Panel accent="block" title="Stage 4: Financial Requests & Urgency">
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                Demanding direct UPI transfers, registration fees, or escrow under artificial time pressure.
              </span>
            </Panel>
          </CardContent>
        </Card>

        <Card variant="surface">
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Layers size={18} color="var(--color-accent)" />
              <CardTitle style={{ fontSize: 'var(--font-size-md)' }}>
                Privacy-Preserving Fingerprints (Engine 7)
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent style={{ gap: 'var(--space-3)' }}>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
              Collective threat intelligence normalizes campaigns into structural hashes without storing raw PII, phone numbers, or user messages.
            </p>

            {/* Empty State for Network Hashes */}
            <EmptyState
              icon={<Database size={24} />}
              title="No live threat signatures loaded"
              description="Signatures are loaded dynamically as content is inspected and validated across the network."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
