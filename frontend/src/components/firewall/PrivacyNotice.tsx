import React from 'react';
import { Lock, FileCheck, EyeOff, ShieldCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';

export const PrivacyNotice: React.FC = () => {
  return (
    <Card variant="subtle" style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <ShieldCheck size={18} color="var(--color-accent)" />
          <CardTitle style={{ fontSize: 'var(--font-size-md)' }}>
            System Principles & Privacy Boundaries
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <div style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: '2px' }}>
              <EyeOff size={18} />
            </div>
            <div>
              <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                Zero Credential Collection
              </strong>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                Passwords, banking OTPs, PINs, and card numbers are never stored and are automatically redacted at the boundary.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <div style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: '2px' }}>
              <FileCheck size={18} />
            </div>
            <div>
              <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                Evidence-Based Verification
              </strong>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                Claims are matched against official registries (SEBI, NSE, MCA) rather than generic heuristic guesses.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <div style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: '2px' }}>
              <Lock size={18} />
            </div>
            <div>
              <strong style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                Explainable Decisions
              </strong>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                Every intervention presents specific factual findings, machine-readable reason codes, and non-accusatory advice.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
