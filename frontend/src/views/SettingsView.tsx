import { Shield, Server, Check } from 'lucide-react';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { MetadataRow } from '../components/common/MetadataRow';
import { Badge } from '../components/common/Badge';
import { apiClient } from '../api/client';
import type { ProtectionSystemStatus } from '../types/firewall';

export interface SettingsViewProps {
  systemStatus: ProtectionSystemStatus;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ systemStatus }) => {
  const apiUrl = apiClient.getBaseUrl();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', width: '100%' }}>
      <SectionHeader
        title="Settings & Privacy Configuration"
        description="Firewall connection parameters and automated boundary protection rules."
      />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-6)',
        }}
      >
        {/* Backend Service Connection */}
        <Card variant="surface">
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Server size={18} color="var(--color-accent)" />
              <CardTitle style={{ fontSize: 'var(--font-size-md)' }}>
                Firewall API Connection
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <MetadataRow label="Backend API URL" value={apiUrl} copyableText={apiUrl} isMono />
            <MetadataRow
              label="Protection Status"
              value={
                <Badge
                  variant={systemStatus === 'active' ? 'success' : systemStatus === 'connecting' ? 'accent' : 'danger'}
                >
                  {systemStatus.toUpperCase()}
                </Badge>
              }
            />
            <MetadataRow label="API Version" value="Phase 11.4 Unified API" isMono />
            <MetadataRow label="Endpoint Path" value="/api/v1/firewall/analyze" isMono />
          </CardContent>
        </Card>

        {/* Boundary Protections */}
        <Card variant="surface">
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Shield size={18} color="var(--color-accent)" />
              <CardTitle style={{ fontSize: 'var(--font-size-md)' }}>
                Security & Boundary Controls
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <MetadataRow
              label="Credential Redaction"
              value={
                <Badge variant="success" icon={<Check size={12} />}>
                  Enforced at Boundary
                </Badge>
              }
            />
            <MetadataRow
              label="Sensitive PII Scrubbing"
              value={
                <Badge variant="success" icon={<Check size={12} />}>
                  Active (Passwords, OTPs, PINs)
                </Badge>
              }
            />
            <MetadataRow
              label="Local Storage Usage"
              value="Ephemeral Only"
            />
            <MetadataRow
              label="Policy Decision Engine"
              value="Engine 8 (Authoritative)"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
