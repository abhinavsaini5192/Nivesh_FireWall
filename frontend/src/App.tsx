import React, { useState, useEffect } from 'react';
import type { ProtectionSystemStatus, ChannelType } from './types/firewall';
import { apiClient, FirewallClientError } from './api/client';
import { AppShell } from './components/shell/AppShell';
import type { NavTabId } from './components/shell/Navigation';
import { ProtectView } from './views/ProtectView';
import { ActivityView } from './views/ActivityView';
import { ThreatIntelligenceView } from './views/ThreatIntelligenceView';
import { SettingsView } from './views/SettingsView';
import './styles/index.css';

export const App: React.FC = () => {
  // Navigation & Routing State
  const [activeTab, setActiveTab] = useState<NavTabId>(() => {
    if (typeof window !== 'undefined') {
      const hash = window.location.hash.replace('#', '') as NavTabId;
      if (['protect', 'activity', 'threat-intel', 'settings'].includes(hash)) {
        return hash;
      }
    }
    return 'protect';
  });

  // Backend Health & Protection Status State
  const [systemStatus, setSystemStatus] = useState<ProtectionSystemStatus>('connecting');
  const [sessionId] = useState<string>(() => `NIV-${Math.random().toString(36).substring(2, 10).toUpperCase()}`);

  // Analysis Lifecycle State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Health Check Probe on Mount
  useEffect(() => {
    let isMounted = true;
    apiClient.checkHealth(4000)
      .then((res) => {
        if (isMounted) setSystemStatus(res.status);
      })
      .catch(() => {
        if (isMounted) setSystemStatus('unavailable');
      });

    const handleHashChange = () => {
      const updated = window.location.hash.replace('#', '') as NavTabId;
      if (updated && ['protect', 'activity', 'threat-intel', 'settings'].includes(updated)) {
        setActiveTab(updated);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => {
      isMounted = false;
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  const handleSelectTab = (tab: NavTabId) => {
    setActiveTab(tab);
    window.location.hash = tab;
  };

  // Content Analysis Handler (Calling unified backend API)
  const handleAnalyze = async (payload: { text?: string; url?: string; channel: ChannelType }) => {
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      await apiClient.analyze({
        input_type: payload.url ? 'url' : 'text',
        text: payload.text,
        url: payload.url,
        channel: payload.channel,
        session_id: sessionId,
      });

      // In Phase 12.1, API request has been verified and passed.
      // Full interactive result presentation accordions belong to Phase 12.2.
    } catch (err) {
      if (err instanceof FirewallClientError) {
        setAnalysisError(err.message);
      } else {
        setAnalysisError('An unexpected error occurred while communicating with the Firewall service.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderActiveView = () => {
    switch (activeTab) {
      case 'activity':
        return <ActivityView onGoToProtect={() => handleSelectTab('protect')} />;
      case 'threat-intel':
        return <ThreatIntelligenceView />;
      case 'settings':
        return <SettingsView systemStatus={systemStatus} />;
      case 'protect':
      default:
        return (
          <ProtectView
            onAnalyze={handleAnalyze}
            isLoading={isAnalyzing}
            error={analysisError}
            onClearError={() => setAnalysisError(null)}
            systemAvailable={systemStatus !== 'unavailable'}
          />
        );
    }
  };

  return (
    <AppShell
      activeTab={activeTab}
      onSelectTab={handleSelectTab}
      systemStatus={systemStatus}
      sessionId={sessionId}
    >
      {renderActiveView()}
    </AppShell>
  );
};

export default App;
