import { Lock } from 'lucide-react';
import { Card, CardContent } from '../common/Card';

export const PrivacySafeguardNotice: React.FC = () => {
  return (
    <Card variant="subtle" style={{ width: '100%', border: '1px solid var(--color-border-subtle)' }}>
      <CardContent style={{ flexDirection: 'row', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-3) var(--space-4)' }}>
        <Lock size={18} color="var(--color-accent)" style={{ flexShrink: 0 }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Privacy & Confidentiality Safeguards Active
          </span>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
            Nivesh Firewall inspects structured assertions and interaction dynamics. Sensitive user credentials, authentication codes, secret access keys, and account identifiers are sanitized and strictly excluded from display.
          </span>
        </div>
      </CardContent>
    </Card>
  );
};
