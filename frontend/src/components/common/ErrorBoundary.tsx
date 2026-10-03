import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';
import { Button } from './Button';
import { Card, CardHeader, CardTitle, CardContent } from './Card';
import { Badge } from './Badge';

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

/**
 * Global UI Error Boundary for Nivesh Firewall (Phase 12.5)
 *
 * Catches rendering exceptions safely. Never downgrades protection state to ALLOW,
 * never exposes stack traces to users, and offers a safe reset path.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error internally in development without exposing stack traces to end users
    if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
      console.error('[Nivesh Firewall ErrorBoundary]', error, errorInfo);
    }
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: undefined });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: 'var(--space-8)',
            width: '100%',
          }}
        >
          <Card
            variant="surface"
            style={{
              maxWidth: '540px',
              width: '100%',
              borderLeft: '4px solid var(--color-warn)',
            }}
          >
            <CardHeader>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <AlertOctagon size={22} color="var(--color-warn)" />
                  <CardTitle style={{ fontSize: 'var(--font-size-lg)' }}>
                    Something went wrong.
                  </CardTitle>
                </div>
                <Badge variant="warning" size="sm">
                  Analysis Incomplete
                </Badge>
              </div>
            </CardHeader>
            <CardContent style={{ gap: 'var(--space-4)' }}>
              <p
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  margin: 0,
                  lineHeight: 1.5,
                }}
              >
                We couldn't display this analysis.
              </p>
              <p
                style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-muted)',
                  margin: 0,
                  lineHeight: 1.4,
                }}
              >
                Nivesh Firewall encountered an unexpected presentation error. For your safety, unverified content is never treated as verified neutral. Please return to the protection view to inspect again.
              </p>
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: 'var(--space-2)' }}>
                <Button
                  variant="primary"
                  size="md"
                  onClick={this.handleReset}
                  leftIcon={<RotateCcw size={16} />}
                >
                  Return to protection
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
