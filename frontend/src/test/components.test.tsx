import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Textarea } from '../components/common/Textarea';
import { Select } from '../components/common/Select';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { Panel } from '../components/common/Panel';
import { Badge } from '../components/common/Badge';
import { StatusIndicator } from '../components/common/StatusIndicator';
import { Alert } from '../components/common/Alert';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { Modal } from '../components/common/Modal';
import { Tooltip } from '../components/common/Tooltip';
import { Divider } from '../components/common/Divider';
import { SectionHeader } from '../components/common/SectionHeader';
import { MetadataRow } from '../components/common/MetadataRow';
import { SemanticStatusBadge } from '../components/status/SemanticStatusBadge';
import { ProtectionStatus } from '../components/status/ProtectionStatus';
import { ContentEntryCard } from '../components/firewall/ContentEntryCard';

describe('Nivesh Firewall Reusable Components & Presentation Systems', () => {
  it('1. Renders Button with variants, sizes, and loading state', () => {
    const { rerender } = render(<Button variant="primary">Verify</Button>);
    expect(screen.getByRole('button', { name: 'Verify' })).toBeInTheDocument();

    rerender(<Button variant="danger" isLoading>Processing</Button>);
    const loadingBtn = screen.getByRole('button');
    expect(loadingBtn).toHaveAttribute('aria-busy', 'true');
    expect(loadingBtn).toBeDisabled();
  });

  it('2. Renders accessible Input and associates labels and error messages', () => {
    render(
      <Input
        label="Target UPI Identifier"
        errorText="Invalid UPI VPA format"
        value=""
        onChange={() => {}}
      />
    );
    expect(screen.getByLabelText('Target UPI Identifier')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Invalid UPI VPA format');
    expect(screen.getByLabelText('Target UPI Identifier')).toHaveAttribute('aria-invalid', 'true');
  });

  it('3. Renders Textarea with character count and helper text', () => {
    render(
      <Textarea
        label="Advisory Message"
        helperText="Redacted at boundary"
        value="Join private group"
        maxLength={500}
        showCount
        onChange={() => {}}
      />
    );
    expect(screen.getByLabelText('Advisory Message')).toBeInTheDocument();
    expect(screen.getByText('Redacted at boundary')).toBeInTheDocument();
    expect(screen.getByText('18/500')).toBeInTheDocument();
  });

  it('4. Renders Select with options and label', () => {
    render(
      <Select
        label="Channel"
        options={[
          { value: 'web', label: 'Web Browser' },
          { value: 'telegram', label: 'Telegram' },
        ]}
        value="telegram"
        onChange={() => {}}
      />
    );
    expect(screen.getByLabelText('Channel')).toHaveValue('telegram');
  });

  it('5. Renders Card, Panel, Badge, and StatusIndicator', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Threat Context</CardTitle>
        </CardHeader>
        <CardContent>
          <Panel title="Signal" accent="warn">
            <Badge variant="warning">High Impact</Badge>
            <StatusIndicator status="active" label="Live" />
          </Panel>
        </CardContent>
      </Card>
    );

    expect(screen.getByText('Threat Context')).toBeInTheDocument();
    expect(screen.getByText('Signal')).toBeInTheDocument();
    expect(screen.getByText('High Impact')).toBeInTheDocument();
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('6. Renders SemanticStatusBadge for all 5 Engine 8 decisions', () => {
    const { rerender } = render(<SemanticStatusBadge decision="ALLOW" />);
    expect(screen.getByText('Allow / Verified Neutral')).toBeInTheDocument();

    rerender(<SemanticStatusBadge decision="INFORM" />);
    expect(screen.getByText('Inform / Advisory')).toBeInTheDocument();

    rerender(<SemanticStatusBadge decision="WARN" />);
    expect(screen.getByText('Warning / Caution Required')).toBeInTheDocument();

    rerender(<SemanticStatusBadge decision="PAUSE" />);
    expect(screen.getByText('Pause / Confirmation Required')).toBeInTheDocument();

    rerender(<SemanticStatusBadge decision="BLOCK" />);
    expect(screen.getByText('Blocked / Threat Prevented')).toBeInTheDocument();
  });

  it('7. Renders ProtectionStatus with real backend status states', () => {
    const { rerender } = render(<ProtectionStatus status="active" />);
    expect(screen.getByText('Protection Active')).toBeInTheDocument();

    rerender(<ProtectionStatus status="connecting" />);
    expect(screen.getByText('Connecting...')).toBeInTheDocument();

    rerender(<ProtectionStatus status="unavailable" />);
    expect(screen.getByText('Service Offline')).toBeInTheDocument();

    rerender(<ProtectionStatus status="error" />);
    expect(screen.getByText('System Degraded')).toBeInTheDocument();
  });

  it('8. Renders LoadingState with multi-step pipeline sequence', () => {
    render(
      <LoadingState
        message="Verifying assertions..."
        steps={['Normalizing content', 'Checking claims', 'Evaluating evidence']}
        currentStepIndex={1}
      />
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Verifying assertions...')).toBeInTheDocument();
    expect(screen.getByText('Normalizing content')).toBeInTheDocument();
    expect(screen.getByText('Checking claims')).toBeInTheDocument();
  });

  it('9. Renders ErrorState with safe error message and retry affordance', () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        title="Pipeline Offline"
        message="The firewall backend is unreachable."
        errorCode="PIPELINE_FAILURE"
        onRetry={onRetry}
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Pipeline Offline')).toBeInTheDocument();
    expect(screen.getByText(/Error Code: PIPELINE_FAILURE/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Try Again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('10. Renders EmptyState with icon, description, and action', () => {
    render(
      <EmptyState
        title="Zero Findings"
        description="No historical alerts found."
        action={<Button size="sm">Refresh</Button>}
      />
    );

    expect(screen.getByText('Zero Findings')).toBeInTheDocument();
    expect(screen.getByText('No historical alerts found.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
  });

  it('11. Renders Modal with accessibility attributes and handles close', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Safety Advisory">
        <p>Confirmation required before continuing.</p>
      </Modal>
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Safety Advisory')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Close dialog'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('12. Renders SectionHeader, MetadataRow, Divider, and Alert', () => {
    const onDismiss = vi.fn();
    render(
      <div>
        <SectionHeader title="System Audit" description="Audit log" />
        <Divider />
        <MetadataRow label="Analysis ID" value="ORCH-12345" copyableText="ORCH-12345" isMono />
        <Alert variant="warning" title="Advisory" onDismiss={onDismiss}>
          Proceed with care.
        </Alert>
        <Tooltip content="Official Registry">
          <button>SEBI</button>
        </Tooltip>
      </div>
    );

    expect(screen.getByText('System Audit')).toBeInTheDocument();
    expect(screen.getByText('Analysis ID')).toBeInTheDocument();
    expect(screen.getByText('ORCH-12345')).toBeInTheDocument();
    expect(screen.getByText('Advisory')).toBeInTheDocument();
    expect(screen.getByText('SEBI')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Dismiss alert'));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('13. ContentEntryCard input validation: disables analyze when empty, enables when valid', async () => {
    const onAnalyze = vi.fn();
    const user = userEvent.setup();

    render(<ContentEntryCard onAnalyze={onAnalyze} />);

    const submitBtn = screen.getByRole('button', { name: /Analyze Content/i });
    expect(submitBtn).toBeDisabled();

    const textarea = screen.getByLabelText('Message or Financial Content');
    await user.type(textarea, 'Guaranteed 50% returns on WhatsApp');

    expect(submitBtn).not.toBeDisabled();

    // Mode switch to Link/URL
    const linkBtn = screen.getByRole('button', { name: /Link \/ URL/i });
    await user.click(linkBtn);
    expect(screen.getByLabelText('Target URL to inspect')).toBeInTheDocument();

    // Clear content
    const clearBtn = screen.getByRole('button', { name: /Clear/i });
    await user.click(clearBtn);
    expect(submitBtn).toBeDisabled();
  });
});
