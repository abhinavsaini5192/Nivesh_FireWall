/**
 * Content Entry Placeholder Card (Phase 12.1)
 *
 * Implements the input state architecture (Empty, Ready, Loading, Error, Disabled, Success)
 * for future Phase 12.2 API integration. Contains ZERO mock intelligence logic or fake threats.
 */

import React, { useState } from 'react';
import { Shield, Globe, Send, AlertCircle } from 'lucide-react';
import type { ChannelType } from '../../types/firewall';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../common/Card';
import { Button } from '../common/Button';
import { Textarea } from '../common/Textarea';
import { Select } from '../common/Select';
import { Badge } from '../common/Badge';

export type InputMode = 'text' | 'url';
export type EntryState = 'empty' | 'ready' | 'loading' | 'error' | 'disabled' | 'success';

export interface ContentEntryCardProps {
  onAnalyze?: (payload: { text?: string; url?: string; channel: ChannelType }) => Promise<void>;
  isLoading?: boolean;
  isDisabled?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const CHANNEL_OPTIONS = [
  { value: 'web', label: 'Web / Browser' },
  { value: 'telegram', label: 'Telegram Channel / Group' },
  { value: 'whatsapp', label: 'WhatsApp Message' },
  { value: 'sms', label: 'SMS / Text Message' },
  { value: 'email', label: 'Email Communication' },
  { value: 'instagram', label: 'Instagram Direct / Post' },
  { value: 'youtube', label: 'YouTube Description / Comment' },
];

export const ContentEntryCard: React.FC<ContentEntryCardProps> = ({
  onAnalyze,
  isLoading = false,
  isDisabled = false,
  error = null,
  onClearError,
}) => {
  const [content, setContent] = useState('');
  const [channel, setChannel] = useState<ChannelType>('web');
  const [mode, setMode] = useState<InputMode>('text');

  const trimmed = content.trim();
  const isEmpty = trimmed.length === 0;
  const isReady = !isEmpty && !isLoading && !isDisabled;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isReady || !onAnalyze) return;

    if (mode === 'url') {
      await onAnalyze({ url: trimmed, channel });
    } else {
      await onAnalyze({ text: trimmed, channel });
    }
  };

  const handleClear = () => {
    setContent('');
    if (onClearError) onClearError();
  };

  return (
    <Card variant="surface" style={{ width: '100%' }}>
      <form onSubmit={handleSubmit}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <CardTitle>Protect your next financial action</CardTitle>
            <Badge variant="accent" icon={<Shield size={12} />}>
              Inspection Shell
            </Badge>
          </div>
          <CardDescription>
            Inspect messages, URLs, or requested actions before clicking links, downloading apps, or sending money.
          </CardDescription>
        </CardHeader>

        <CardContent style={{ gap: 'var(--space-4)' }}>
          {/* Channel and Mode Selector Bar */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 'var(--space-3)',
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-bg-subtle)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
            }}
          >
            {/* Input Mode Selector */}
            <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
              <Button
                type="button"
                variant={mode === 'text' ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setMode('text')}
                disabled={isLoading}
              >
                Text Message
              </Button>
              <Button
                type="button"
                variant={mode === 'url' ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setMode('url')}
                leftIcon={<Globe size={14} />}
                disabled={isLoading}
              >
                Link / URL
              </Button>
            </div>

            {/* Ingestion Channel Dropdown */}
            <div style={{ minWidth: '200px' }}>
              <Select
                aria-label="Origin Channel"
                value={channel}
                onChange={(e) => setChannel(e.target.value as ChannelType)}
                options={CHANNEL_OPTIONS}
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Input Area */}
          <Textarea
            id="firewall-content-input"
            label={mode === 'url' ? 'Target URL to inspect' : 'Message or Financial Content'}
            placeholder={
              mode === 'url'
                ? 'https://example.com/investment-platform'
                : 'Paste WhatsApp advisory, Telegram recommendation, APK install request, or payment instructions...'
            }
            rows={5}
            maxLength={10000}
            showCount
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              if (error && onClearError) onClearError();
            }}
            disabled={isLoading || isDisabled}
            errorText={error || undefined}
            helperText="Raw sensitive credentials (passwords, PINs, OTPs) are not collected and will be redacted."
          />

          {/* Error Banner if provided */}
          {error && (
            <div
              role="alert"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-block)',
                backgroundColor: 'var(--color-block-bg)',
                padding: 'var(--space-2) var(--space-3)',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--color-block-border)',
              }}
            >
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}
        </CardContent>

        <CardFooter style={{ justifyContent: 'space-between' }}>
          <div>
            {!isEmpty && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleClear}
                disabled={isLoading}
              >
                Clear
              </Button>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                display: 'none',
              }}
              className="desktop-hint"
            >
              Press <kbd style={{ padding: '1px 4px', border: '1px solid var(--color-border-subtle)', borderRadius: '2px' }}>Ctrl + Enter</kbd> to analyze
            </span>
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!isReady}
              isLoading={isLoading}
              rightIcon={<Send size={16} />}
            >
              Analyze Content
            </Button>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
};
