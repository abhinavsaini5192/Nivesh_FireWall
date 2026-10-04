import React, { useEffect } from 'react';
import { LandingNavbar } from './LandingNavbar';
import { LandingFooter } from './LandingFooter';
import { GlobeCanvas } from './GlobeCanvas';

export interface PublicLayoutProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  onOpenFirewall: () => void;
  showGlobe?: boolean;
  children: React.ReactNode;
}

export const PublicLayout: React.FC<PublicLayoutProps> = ({
  currentRoute,
  onNavigate,
  onOpenFirewall,
  showGlobe = false,
  children,
}) => {
  useEffect(() => {
    if (typeof window.scrollTo === 'function') {
      window.scrollTo(0, 0);
    }
  }, [currentRoute]);

  return (
    <div className="page-root">
      {/* Background layer */}
      {showGlobe ? (
        <GlobeCanvas />
      ) : (
        <div className="hero-media-container" aria-hidden="true">
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'radial-gradient(circle at 50% 10%, rgba(168, 85, 247, 0.12) 0%, rgba(0, 0, 0, 0.75) 55%, #000000 100%)',
              zIndex: 1,
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage:
                'radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px)',
              backgroundSize: '36px 36px',
              opacity: 0.35,
              zIndex: 1,
              pointerEvents: 'none',
            }}
          />
        </div>
      )}

      {/* Shared Glass Navbar */}
      <LandingNavbar
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        onOpenFirewall={onOpenFirewall}
      />

      {/* Main Content Area */}
      <main className="page-content" style={{ zIndex: 10 }}>
        {children}
      </main>

      {/* Shared Editorial Footer */}
      <LandingFooter
        onNavigate={onNavigate}
        onOpenFirewall={onOpenFirewall}
      />
    </div>
  );
};
