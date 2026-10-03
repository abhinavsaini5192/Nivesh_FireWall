import React, { useState, useEffect, useRef } from 'react';
import type {
  ProtectionSystemStatus,
  ChannelType,
  FirewallAnalysisResponse,
  AnalysisState,
} from './types/firewall';
import { mapBackendErrorToUserMessage } from './types/firewall';
import { apiClient, FirewallClientError } from './api/client';
import { AppShell } from './components/shell/AppShell';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import type { NavTabId } from './components/shell/Navigation';
import { ProtectView } from './views/ProtectView';
import { ActivityView } from './views/ActivityView';
import { ThreatIntelligenceView } from './views/ThreatIntelligenceView';
import { SettingsView } from './views/SettingsView';
import './styles/index.css';

const getAnalysisIdFromHash = (hash: string): string | null => {
  const match = hash.match(/(?:id=|analysis\/)([a-zA-Z0-9_-]+)/);
  return match ? match[1] : null;
};

const getTabFromHash = (hash: string): NavTabId => {
  const clean = hash.replace('#', '').split('?')[0] as NavTabId;
  if (['protect', 'activity', 'threat-intel', 'settings'].includes(clean)) {
    return clean;
  }
  return 'protect';
};

function navigateHash(hash: string): void {
  if (typeof window !== 'undefined') {
    window.location.hash = hash;
  }
}

export const App: React.FC = () => {
  // Navigation & Routing State
  const [activeTab, setActiveTab] = useState<NavTabId>(() => {
    if (typeof window !== 'undefined') {
      return getTabFromHash(window.location.hash);
    }
    return 'protect';
  });

  // Backend Health & Protection Status State
  const [systemStatus, setSystemStatus] = useState<ProtectionSystemStatus>('connecting');
  const [sessionId] = useState<string>(() => `NIV-${Math.random().toString(36).substring(2, 10).toUpperCase()}`);

  // Request counter for race condition protection
  const activeRequestIdRef = useRef<number>(0);

  // Analysis Lifecycle & History State
  const [analysisState, setAnalysisState] = useState<AnalysisState>(() => {
    if (typeof window !== 'undefined' && getAnalysisIdFromHash(window.location.hash)) {
      return 'ANALYZING';
    }
    return 'IDLE';
  });
  const [currentAnalysis, setCurrentAnalysis] = useState<FirewallAnalysisResponse | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<FirewallAnalysisResponse[]>([]);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisErrorCode, setAnalysisErrorCode] = useState<string | null>(null);

  // Health Check Probe & Deep-link on Mount
  useEffect(() => {
    let isMounted = true;

    // 1. Health Probe
    apiClient.checkHealth(4000)
      .then((res) => {
        if (isMounted) setSystemStatus(res.status);
      })
      .catch(() => {
        if (isMounted) setSystemStatus('unavailable');
      });

    // 2. Check for deep-linked analysis ID in URL hash
    const initialId = getAnalysisIdFromHash(window.location.hash);
    if (initialId) {
      const reqId = ++activeRequestIdRef.current;
      apiClient.getAnalysis(initialId)
        .then((res) => {
          if (isMounted && reqId === activeRequestIdRef.current) {
            setCurrentAnalysis(res);
            setAnalysisHistory((prev) => {
              const exists = prev.some((p) => p.analysis_id === res.analysis_id);
              return exists ? prev : [res, ...prev];
            });
            setAnalysisState(res.pipeline_status === 'PARTIAL' ? 'PARTIAL_RESULT' : 'SUCCESS');
          }
        })
        .catch((err) => {
          if (isMounted && reqId === activeRequestIdRef.current) {
            setAnalysisError(err instanceof FirewallClientError ? err.message : 'Unable to retrieve analysis.');
            setAnalysisErrorCode(err instanceof FirewallClientError ? err.errorCode : 'ANALYSIS_NOT_FOUND');
            setAnalysisState('ERROR');
          }
        });
    }

    // 3. Hash Change Listener
    const handleHashChange = () => {
      const targetTab = getTabFromHash(window.location.hash);
      setActiveTab(targetTab);

      const targetId = getAnalysisIdFromHash(window.location.hash);
      if (targetId && (!currentAnalysis || currentAnalysis.analysis_id !== targetId)) {
        const reqId = ++activeRequestIdRef.current;
        setAnalysisState('ANALYZING');
        apiClient.getAnalysis(targetId)
          .then((res) => {
            if (isMounted && reqId === activeRequestIdRef.current) {
              setCurrentAnalysis(res);
              setAnalysisState(res.pipeline_status === 'PARTIAL' ? 'PARTIAL_RESULT' : 'SUCCESS');
            }
          })
          .catch((err) => {
            if (isMounted && reqId === activeRequestIdRef.current) {
              setAnalysisError(err instanceof FirewallClientError ? err.message : 'Unable to retrieve analysis.');
              setAnalysisErrorCode(err instanceof FirewallClientError ? err.errorCode : 'ANALYSIS_NOT_FOUND');
              setAnalysisState('ERROR');
            }
          });
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => {
      isMounted = false;
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, [currentAnalysis]);

  const handleSelectTab = (tab: NavTabId) => {
    setActiveTab(tab);
    navigateHash(tab);
  };

  // Content Analysis Handler (Calling unified backend API)
  const handleAnalyze = async (payload: { text?: string; url?: string; channel: ChannelType }) => {
    // Prevent duplicate concurrent submissions
    if (analysisState === 'SUBMITTING' || analysisState === 'ANALYZING' || analysisState === 'VALIDATING') {
      return;
    }

    setAnalysisState('VALIDATING');

    // Client-side validation
    const hasText = !!(payload.text && payload.text.trim());
    const hasUrl = !!(payload.url && payload.url.trim());
    if (!hasText && !hasUrl) {
      setAnalysisError('Please enter text content or a target URL to analyze.');
      setAnalysisErrorCode('INVALID_REQUEST');
      setAnalysisState('ERROR');
      return;
    }

    // Race condition protection: track active request sequence
    const currentReqId = ++activeRequestIdRef.current;

    // Stale result protection: clear previous analysis immediately
    setCurrentAnalysis(null);
    setAnalysisError(null);
    setAnalysisErrorCode(null);
    setAnalysisState('SUBMITTING');

    try {
      setAnalysisState('ANALYZING');
      const response = await apiClient.analyze({
        input_type: payload.url ? 'url' : 'text',
        text: payload.text,
        url: payload.url,
        channel: payload.channel,
        session_id: sessionId,
      });

      // Ignore if a newer request was dispatched while this was in-flight
      if (currentReqId !== activeRequestIdRef.current) {
        return;
      }

      setCurrentAnalysis(response);
      setAnalysisHistory((prev) => {
        const exists = prev.some((p) => p.analysis_id === response.analysis_id);
        return exists ? prev : [response, ...prev];
      });
      setAnalysisState(response.pipeline_status === 'PARTIAL' ? 'PARTIAL_RESULT' : 'SUCCESS');
      navigateHash(`protect?id=${response.analysis_id}`);
    } catch (err) {
      // Ignore if a newer request was dispatched while this was in-flight
      if (currentReqId !== activeRequestIdRef.current) {
        return;
      }

      if (err instanceof FirewallClientError) {
        setAnalysisError(err.message || mapBackendErrorToUserMessage(err.errorCode));
        setAnalysisErrorCode(err.errorCode);
      } else {
        setAnalysisError(mapBackendErrorToUserMessage('PIPELINE_FAILURE', 'An unexpected error occurred while communicating with the Firewall service.'));
        setAnalysisErrorCode('PIPELINE_FAILURE');
      }
      setAnalysisState('ERROR');
    }
  };

  // Reset to Clean Input State
  const handleResetAnalysis = () => {
    setCurrentAnalysis(null);
    setAnalysisState('IDLE');
    setAnalysisError(null);
    setAnalysisErrorCode(null);
    setActiveTab('protect');
    navigateHash('protect');
  };

  // Select Prior Analysis from Activity View
  const handleSelectPastAnalysis = (analysis: FirewallAnalysisResponse) => {
    setCurrentAnalysis(analysis);
    setAnalysisState(analysis.pipeline_status === 'PARTIAL' ? 'PARTIAL_RESULT' : 'SUCCESS');
    setActiveTab('protect');
    navigateHash(`protect?id=${analysis.analysis_id}`);
  };

  const renderActiveView = () => {
    switch (activeTab) {
      case 'activity':
        return (
          <ActivityView
            onGoToProtect={handleResetAnalysis}
            analyses={analysisHistory}
            onSelectAnalysis={handleSelectPastAnalysis}
          />
        );
      case 'threat-intel':
        return <ThreatIntelligenceView />;
      case 'settings':
        return <SettingsView systemStatus={systemStatus} />;
      case 'protect':
      default:
        return (
          <ProtectView
            onAnalyze={handleAnalyze}
            analysisResult={currentAnalysis}
            analysisState={analysisState}
            onAnalyzeAnother={handleResetAnalysis}
            isLoading={analysisState === 'SUBMITTING' || analysisState === 'ANALYZING'}
            error={analysisError}
            errorCode={analysisErrorCode}
            onClearError={() => {
              setAnalysisError(null);
              setAnalysisErrorCode(null);
              if (analysisState === 'ERROR') setAnalysisState('IDLE');
            }}
            onRetry={() => {
              if (currentAnalysis) {
                handleAnalyze({
                  text: currentAnalysis.content.summary,
                  url: currentAnalysis.content.summary.startsWith('http') ? currentAnalysis.content.summary : undefined,
                  channel: currentAnalysis.content.channel as ChannelType,
                });
              } else {
                setAnalysisError(null);
                setAnalysisState('IDLE');
              }
            }}
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
      <ErrorBoundary onReset={handleResetAnalysis}>
        {renderActiveView()}
      </ErrorBoundary>
    </AppShell>
  );
};

export default App;
