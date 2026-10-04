import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { LandingPage } from '../landing';
import App from '../App';
import { apiClient } from '../api/client';

describe('Nivesh Firewall — Landing Page Component & Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.location.hash = '';
  });

  it('1. Renders the full landing page structure with brand, headline, and canvas', () => {
    const handleOpen = vi.fn();
    const { container } = render(<LandingPage onOpenFirewall={handleOpen} />);

    // Brand Identity
    expect(screen.getByText('NIVESH')).toBeInTheDocument();
    expect(screen.getAllByText('FIREWALL').length).toBeGreaterThan(0);

    // Headline & Subtitle
    expect(screen.getByText('Protect before')).toBeInTheDocument();
    expect(screen.getByText('you act.')).toBeInTheDocument();
    expect(
      screen.getByText(/Nivesh Firewall analyzes financial content, verifies claims, traces requested actions/i)
    ).toBeInTheDocument();

    // Canvas background
    const canvas = container.querySelector('#globeCanvas');
    expect(canvas).toBeInTheDocument();

    // Footer indicators
    expect(screen.getByText(/Pre-Transaction Defense Protocol Active/i)).toBeInTheDocument();
    expect(screen.getByText(/Observe • Understand • Verify • Trace • Intervene/i)).toBeInTheDocument();
  });

  it('2. Triggers onOpenFirewall callback when clicking primary CTA buttons', () => {
    const handleOpen = vi.fn();
    render(<LandingPage onOpenFirewall={handleOpen} />);

    // Click Hero 'Open Firewall' button
    const openButtons = screen.getAllByRole('button', { name: /Open Firewall/i });
    expect(openButtons.length).toBeGreaterThan(0);
    fireEvent.click(openButtons[0]);
    expect(handleOpen).toHaveBeenCalledTimes(1);

    // Click 'Get Started' button
    const getStartedButtons = screen.getAllByRole('button', { name: /Get Started/i });
    expect(getStartedButtons.length).toBeGreaterThan(0);
    fireEvent.click(getStartedButtons[0]);
    expect(handleOpen).toHaveBeenCalledTimes(2);
  });

  it('3. Renders all detailed landing sections: How It Works, Features, Sources, Extension', () => {
    render(<LandingPage onOpenFirewall={vi.fn()} />);

    // How It Works section
    expect(screen.getByText('How Nivesh Firewall Protects You')).toBeInTheDocument();
    expect(screen.getByText('STAGE 01')).toBeInTheDocument();
    expect(screen.getByText('Observe Content')).toBeInTheDocument();
    expect(screen.getByText('Pre-Action Intervene')).toBeInTheDocument();

    // Features section
    expect(screen.getByText('Built for High-Stakes Financial Safety')).toBeInTheDocument();
    expect(screen.getByText('Authoritative Ground Truth')).toBeInTheDocument();
    expect(screen.getByText('Zero-Collection Privacy')).toBeInTheDocument();

    // Sources section
    expect(screen.getByText('Verified Against Official Registries')).toBeInTheDocument();
    expect(screen.getByText('SEBI Registry')).toBeInTheDocument();
    expect(screen.getByText('RBI Sachet')).toBeInTheDocument();

    // Extension section
    expect(screen.getByText('Inspect Content Directly in Your Browser')).toBeInTheDocument();
    expect(screen.getByText(/Add to Chrome/i)).toBeInTheDocument();
  });

  it('4. Toggles mobile drawer navigation menu open and closed', () => {
    render(<LandingPage onOpenFirewall={vi.fn()} />);

    const menuToggle = screen.getByLabelText(/Toggle navigation menu/i);
    expect(menuToggle).toBeInTheDocument();

    // Drawer should not be present initially
    expect(screen.queryByRole('region', { name: /Mobile Navigation/i })).not.toBeInTheDocument();

    // Open mobile menu
    fireEvent.click(menuToggle);
    const drawer = document.getElementById('mobile-menu-drawer');
    expect(drawer).toBeInTheDocument();

    // Close mobile menu
    fireEvent.click(menuToggle);
    expect(document.getElementById('mobile-menu-drawer')).not.toBeInTheDocument();
  });

  it('5. Integrates with App routing: switches to landing on #landing and back to console on Open Firewall', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    window.location.hash = '#landing';

    await act(async () => {
      render(<App />);
    });

    // Landing Page should be active
    expect(screen.getByText('Protect before')).toBeInTheDocument();
    expect(screen.getByText('you act.')).toBeInTheDocument();

    // Click 'Open Firewall' on landing page
    const openButtons = screen.getAllByRole('button', { name: /Open Firewall/i });
    await act(async () => {
      fireEvent.click(openButtons[0]);
    });

    // App should transition to console Protect view
    expect(screen.getByText('Financial Content Protection Core')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Content/i })).toBeInTheDocument();
  });
});
