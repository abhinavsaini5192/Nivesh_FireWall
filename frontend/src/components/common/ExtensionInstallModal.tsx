import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { Check, Copy, Download, ExternalLink, Sparkles } from 'lucide-react';

export interface ExtensionInstallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateExtension?: () => void;
}

export const ExtensionInstallModal: React.FC<ExtensionInstallModalProps> = ({
  isOpen,
  onClose,
  onNavigateExtension,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText('chrome://extensions');
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleDownloadAgain = () => {
    const link = document.createElement('a');
    link.href = '/nivesh-firewall-v1.0.0.zip';
    link.download = 'nivesh-firewall-v1.0.0.zip';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Nivesh Firewall to Chrome"
      description="Manifest V3 Extension Ready • Fast 3-Step Setup"
      maxWidth="540px"
      footer={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', gap: '12px' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={onNavigateExtension ? onNavigateExtension : onClose}
          >
            <ExternalLink size={13} style={{ marginRight: '6px' }} />
            View Full Docs
          </Button>

          <Button variant="primary" size="sm" onClick={onClose}>
            Done
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Status Callout */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '12px',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
          }}
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Sparkles size={16} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff' }}>
              Extension Package Downloaded!
            </div>
            <div style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.65)' }}>
              Follow these 3 quick steps to activate in your Chrome or Chromium browser.
            </div>
          </div>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Step 1 */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <span
              style={{
                width: '22px',
                height: '22px',
                borderRadius: '50%',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '1px',
              }}
            >
              1
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginBottom: '2px' }}>
                Unzip the package
              </div>
              <p style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.65)', lineHeight: 1.5 }}>
                Extract <code style={{ color: '#38bdf8', backgroundColor: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '4px' }}>nivesh-firewall-v1.0.0.zip</code> in your Downloads folder to create an unpacked folder.
              </p>
            </div>
            <button
              type="button"
              onClick={handleDownloadAgain}
              title="Download again"
              style={{
                background: 'none',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: 'rgba(255, 255, 255, 0.7)',
                padding: '4px 8px',
                fontSize: '11px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                flexShrink: 0,
              }}
            >
              <Download size={11} />
              Re-download
            </button>
          </div>

          {/* Step 2 */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <span
              style={{
                width: '22px',
                height: '22px',
                borderRadius: '50%',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '1px',
              }}
            >
              2
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginBottom: '2px' }}>
                Open Chrome Extensions
              </div>
              <p style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.65)', lineHeight: 1.5, marginBottom: '6px' }}>
                Open a new tab and go to <code style={{ color: '#38bdf8', backgroundColor: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '4px' }}>chrome://extensions</code>
              </p>
              <button
                type="button"
                onClick={handleCopyUrl}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: copied ? '#059669' : 'rgba(255, 255, 255, 0.08)',
                  color: '#ffffff',
                  fontSize: '11px',
                  fontWeight: 500,
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copied URL to Clipboard!' : 'Copy chrome://extensions'}
              </button>
            </div>
          </div>

          {/* Step 3 */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <span
              style={{
                width: '22px',
                height: '22px',
                borderRadius: '50%',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '1px',
              }}
            >
              3
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginBottom: '2px' }}>
                Load Unpacked Extension
              </div>
              <p style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.65)', lineHeight: 1.5 }}>
                Turn on <strong>Developer mode</strong> (toggle in top right) and click <strong>"Load unpacked"</strong>. Select the unzipped folder.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};
