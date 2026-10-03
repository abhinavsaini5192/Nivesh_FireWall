import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import App from '../App';
import { apiClient } from '../api/client';

describe('Nivesh Firewall Frontend — Application Boot & Shell', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.location.hash = '';
  });

  it('1. Boots successfully and renders main header and brand identity', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });

    await act(async () => {
      render(<App />);
    });

    expect(screen.getByText('NIVESH FIREWALL')).toBeInTheDocument();
    expect(screen.getByText('Financial Content Protection Core')).toBeInTheDocument();
  });

  it('2. Renders primary Protect view by default', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });

    await act(async () => {
      render(<App />);
    });

    expect(screen.getByText('Protect before you act.')).toBeInTheDocument();
    expect(screen.getByText('Protect your next financial action')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Content/i })).toBeInTheDocument();
  });

  it('3. Navigates cleanly between all 4 primary views', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });

    await act(async () => {
      render(<App />);
    });

    // Initially in Protect
    expect(screen.getByText('Protect before you act.')).toBeInTheDocument();

    // Click Activity tab
    const activityButtons = screen.getAllByRole('button', { name: /Activity/i });
    await act(async () => {
      fireEvent.click(activityButtons[0]);
    });
    expect(screen.getByText('Protection Activity')).toBeInTheDocument();
    expect(screen.getByText('No analyses yet')).toBeInTheDocument();

    // Click Threat Intelligence tab
    const threatButtons = screen.getAllByRole('button', { name: /Threat Intelligence/i });
    await act(async () => {
      fireEvent.click(threatButtons[0]);
    });
    expect(screen.getByText('Threat Intelligence Architecture')).toBeInTheDocument();
    expect(screen.getByText(/Attack-Path Progression Stages/i)).toBeInTheDocument();

    // Click Settings tab
    const settingsButtons = screen.getAllByRole('button', { name: /Settings/i });
    await act(async () => {
      fireEvent.click(settingsButtons[0]);
    });
    expect(screen.getByText('Settings & Privacy Configuration')).toBeInTheDocument();
    expect(screen.getByText('Backend API URL')).toBeInTheDocument();

    // Navigate back to Protect from Activity action button
    await act(async () => {
      fireEvent.click(activityButtons[0]);
    });
    const startAnalysisBtn = screen.getByRole('button', { name: /Start an Analysis/i });
    await act(async () => {
      fireEvent.click(startAnalysisBtn);
    });
    expect(screen.getByText('Protect before you act.')).toBeInTheDocument();
  });

  it('4. Updates protection status from real backend probe response', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({
      status: 'active',
      data: { status: 'healthy', version: '1.0.0' },
    });

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByText('Protection Active')).toBeInTheDocument();
    });
  });

  it('5. Reflects offline/unavailable backend state gracefully without crashing', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'unavailable' });

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByText('Service Offline')).toBeInTheDocument();
    });
  });

  it('6. Supports route synchronization via URL hash', async () => {
    window.location.hash = '#settings';
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });

    await act(async () => {
      render(<App />);
    });

    expect(screen.getByText('Settings & Privacy Configuration')).toBeInTheDocument();
  });
});
