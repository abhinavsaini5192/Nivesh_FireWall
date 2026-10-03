import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export interface MetadataRowProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  copyableText?: string;
  isMono?: boolean;
}

export const MetadataRow: React.FC<MetadataRowProps> = ({
  label,
  value,
  copyableText,
  isMono = false,
  style,
  className = '',
  ...props
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!copyableText) return;
    try {
      await navigator.clipboard.writeText(copyableText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback or ignore
    }
  };

  return (
    <div
      className={`nivesh-metadata-row ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-2) 0',
        borderBottom: '1px solid var(--color-border-subtle)',
        fontSize: 'var(--font-size-sm)',
        ...style,
      }}
      {...props}
    >
      <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <span
          style={{
            color: 'var(--color-text-primary)',
            fontFamily: isMono ? 'var(--font-mono)' : 'inherit',
            fontWeight: 'var(--font-weight-medium)',
          }}
        >
          {value}
        </span>
        {copyableText && (
          <button
            onClick={handleCopy}
            aria-label={`Copy ${label}`}
            style={{
              color: copied ? 'var(--color-allow)' : 'var(--color-text-muted)',
              cursor: 'pointer',
              display: 'flex',
              padding: '2px',
            }}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        )}
      </div>
    </div>
  );
};
