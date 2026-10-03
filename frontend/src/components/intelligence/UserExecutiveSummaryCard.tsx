import { HelpCircle, ArrowRight } from 'lucide-react';
import type { FirewallAnalysisResponse } from '../../types/firewall';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';

export interface UserExecutiveSummaryCardProps {
  analysis: FirewallAnalysisResponse;
  onExploreTechnical: () => void;
}

export const UserExecutiveSummaryCard: React.FC<UserExecutiveSummaryCardProps> = ({
  analysis,
  onExploreTechnical,
}) => {
  const { decision, content, actions, claims, identity, evidence } = analysis;

  const topAction = actions[0];
  const topClaim = claims[0];
  const claimedName = identity.claimed_entities[0] || 'Unknown person/group';

  return (
    <Card variant="elevated" style={{ width: '100%', borderLeft: '4px solid var(--color-accent)' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <HelpCircle size={18} color="var(--color-accent)" />
            <CardTitle>Protection Overview (Plain English)</CardTitle>
          </div>
          <Badge variant="accent" size="sm">
            Consumer Summary
          </Badge>
        </div>
      </CardHeader>
      <CardContent style={{ gap: 'var(--space-3)' }}>
        {/* Question 1: What happened? */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            1. What content was inspected?
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
            {content.summary ? `"${content.summary}"` : `Financial communication received via ${content.channel || 'web'}.`}
          </p>
        </div>

        {/* Question 2: What was requested? */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            2. What was requested from you?
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
            {topAction
              ? `Requested action: ${topAction.action_type.replace(/_/g, ' ')}${topAction.target ? ` targeting ${topAction.target}` : ''}. (${topAction.reversibility === 'IRREVERSIBLE' ? 'This action cannot be undone once executed.' : 'Action is reversible.'})`
              : 'No explicit transaction, transfer, or download was requested in this content.'}
          </p>
        </div>

        {/* Question 3: What was claimed? */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            3. What claims were made?
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
            {topClaim
              ? `Main assertion: "${topClaim.text}" (Topic: ${topClaim.topic}).`
              : 'No quantifiable financial return claims or regulatory affiliations were asserted.'}
          </p>
        </div>

        {/* Question 4: What was verified? */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            4. What did authoritative records show?
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
            Official registry check for <strong>{claimedName}</strong> returned{' '}
            <strong style={{ color: identity.identity_status === 'ESTABLISHED' ? 'var(--color-allow)' : 'var(--color-warn)' }}>
              {identity.identity_status}
            </strong>
            . {evidence.overall_status === 'CONTRADICTED'
              ? 'Authoritative regulatory filings directly contradict the claims made.'
              : evidence.overall_status === 'SUPPORTED'
              ? 'Official filings verify the stated information.'
              : 'Official registries did not provide sufficient public filings to verify this assertion.'}
          </p>
        </div>

        {/* Question 5: Why did Nivesh intervene? */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            5. Why did Nivesh Firewall intervene?
          </span>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
            {decision.explanation.user_message}
          </p>
        </div>

        {/* Switch to technical mode affordance */}
        <div style={{ paddingTop: 'var(--space-2)', borderTop: '1px solid var(--color-border-subtle)' }}>
          <button
            onClick={onExploreTechnical}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              background: 'none',
              border: 'none',
              padding: 0,
              fontSize: 'var(--font-size-xs)',
              fontWeight: 600,
              color: 'var(--color-accent)',
              cursor: 'pointer',
            }}
          >
            Explore technical attack-paths, fingerprint dimensions & audit trace <ArrowRight size={14} />
          </button>
        </div>
      </CardContent>
    </Card>
  );
};
