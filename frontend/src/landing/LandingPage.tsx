import React, { useEffect } from 'react';
import { GlobeCanvas } from './components/GlobeCanvas';
import { LandingNavbar } from './components/LandingNavbar';
import { LandingHero } from './components/LandingHero';
import { LandingSections } from './components/LandingSections';
import { LandingFooter } from './components/LandingFooter';
import '../styles/landing.css';

export interface LandingPageProps {
  onOpenFirewall: () => void;
  onNavigate?: (route: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onOpenFirewall,
  onNavigate,
}) => {
  useEffect(() => {
    // Scroll to top on mount
    if (typeof window.scrollTo === 'function') {
      window.scrollTo(0, 0);
    }

    // If URL has a specific hash section like #how-it-works, smooth scroll to it
    const hash = window.location.hash.replace('#', '');
    if (hash && ['how-it-works', 'features', 'sources', 'extension'].includes(hash)) {
      const el = document.getElementById(hash);
      if (el && typeof el.scrollIntoView === 'function') {
        setTimeout(() => {
          el.scrollIntoView({ behavior: 'smooth' });
        }, 150);
      }
    }
  }, []);

  const handleExploreHowItWorks = () => {
    if (onNavigate) {
      onNavigate('/how-it-works');
      return;
    }
    const el = document.getElementById('how-it-works');
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="landing-root" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 3D Background: Procedural Rotating Dot-Matrix Globe & Starfield */}
      <GlobeCanvas />

      {/* Glassmorphic Navigation Bar */}
      <LandingNavbar
        currentRoute="/"
        onNavigate={onNavigate}
        onOpenFirewall={onOpenFirewall}
      />

      {/* Hero Section with Staggered Entrance Animations */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <LandingHero
          onOpenFirewall={onOpenFirewall}
          onExploreHowItWorks={handleExploreHowItWorks}
        />

        {/* Detailed Sections: How It Works, Features, Sources, Extension */}
        <LandingSections
          onOpenFirewall={onOpenFirewall}
          onNavigate={onNavigate}
        />
      </main>

      {/* Clean Minimalist Protocol Footer */}
      <LandingFooter
        onNavigate={onNavigate}
        onOpenFirewall={onOpenFirewall}
      />
    </div>
  );
};

export default LandingPage;
