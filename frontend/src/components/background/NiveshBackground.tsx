import React from 'react';
import { GradientWaves } from './GradientWaves';

export interface NiveshBackgroundProps {
  className?: string;
  style?: React.CSSProperties;
}

export const NiveshBackground: React.FC<NiveshBackgroundProps> = ({
  className = '',
  style,
}) => {
  return (
    <div
      className={`nivesh-background-root ${className}`.trim()}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
        backgroundColor: '#000000',
        ...style,
      }}
    >
      {/* 1. Deep Black & Subtle Ambient Violet Underlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse 90% 70% at 55% 25%, rgba(76, 29, 149, 0.14) 0%, rgba(8, 0, 15, 0.08) 50%, rgba(0, 0, 0, 1) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* 2. Official Nivesh GradientWaves WebGL Layer */}
      <GradientWaves
        horizonColor="#08000F"
        waveColor="#4C1D95"
        crestColor="#C084FC"
        speed={0.16}
        amplitude={1.8}
        waveScale={0.55}
        waveRatio={0.9}
        swell={28}
        turbulence={14}
        tilt={1.08}
        zoom={1.0}
        height={5.5}
        fogDepth={18}
        detail="medium"
        brightness={0.75}
        opacity={0.30}
        mouseInteraction={false}
        parallaxStrength={0.15}
        grain={false}
        className="nivesh-dashboard-waves"
        style={{ position: 'absolute', inset: 0 }}
      />

      {/* 3. Dark Vignette / Readability Layer */}
      <div
        className="nivesh-background-vignette"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: `radial-gradient(
            ellipse at 50% 35%,
            rgba(0, 0, 0, 0.08) 0%,
            rgba(0, 0, 0, 0.35) 65%,
            rgba(0, 0, 0, 0.78) 100%
          )`,
        }}
      />

      {/* 4. Sidebar Zone Shield: Ensures sidebar region remains deep black and stable */}
      <div
        className="nivesh-sidebar-shield"
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: 0,
          width: '320px',
          background: 'linear-gradient(to right, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.5) 240px, rgba(0, 0, 0, 0) 100%)',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};

export default NiveshBackground;
