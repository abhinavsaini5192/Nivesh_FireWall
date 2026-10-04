import React, { useEffect, useRef } from 'react';

/**
 * Procedural Violet Dot-Matrix Earth and Starfield Canvas Component
 * Renders an interactive 3D particle sphere using Fibonacci distribution,
 * axial tilt, atmospheric violet radial glow, and depth projection.
 */
export const GlobeCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let animationFrameId: number | undefined = undefined;

    const resize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', resize);
    resize();

    // 1. Starfield particles
    const starCount = 140;
    const stars: Array<{ x: number; y: number; z: number; size: number; alpha: number }> = [];
    for (let i = 0; i < starCount; i++) {
      stars.push({
        x: Math.random() * 2000 - 1000,
        y: Math.random() * 2000 - 1000,
        z: Math.random() * 1000 + 10,
        size: Math.random() * 1.5 + 0.5,
        alpha: Math.random() * 0.7 + 0.2,
      });
    }

    // 2. Dot-Matrix Earth Sphere coordinates
    const numPoints = 1400;
    const globePoints: Array<{ x: number; y: number; z: number; baseAlpha: number }> = [];

    // Fibonacci sphere distribution for uniform dot matrix
    const phi = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < numPoints; i++) {
      const y = 1 - (i / (numPoints - 1)) * 2; // y: 1 to -1
      const radiusAtY = Math.sqrt(1 - y * y);
      const theta = phi * i;
      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      // Add continent-like density clustering
      const isContinent = Math.sin(x * 3.5) * Math.cos(y * 4) + Math.sin(z * 3) > -0.2;
      if (isContinent || Math.random() > 0.4) {
        globePoints.push({ x, y, z, baseAlpha: isContinent ? 0.85 : 0.25 });
      }
    }

    let angle = 0;

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      const centerX = width * 0.5;
      const centerY = height * 0.56;
      const currentRadius = Math.min(width, height) * (width < 640 ? 0.52 : 0.44);

      // A. Draw Starfield
      for (let i = 0; i < stars.length; i++) {
        const star = stars[i];
        const k = 250 / star.z;
        const px = star.x * k + centerX;
        const py = star.y * k + centerY;
        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          ctx.fillStyle = `rgba(216, 180, 254, ${star.alpha * 0.6})`;
          ctx.beginPath();
          ctx.arc(px, py, star.size, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // B. Draw Soft Violet Atmosphere Glow Behind Globe
      if (typeof ctx.createRadialGradient === 'function') {
        const glowGrad = ctx.createRadialGradient(
          centerX,
          centerY,
          currentRadius * 0.2,
          centerX,
          centerY,
          currentRadius * 1.35
        );
        glowGrad.addColorStop(0, 'rgba(168, 85, 247, 0.16)');
        glowGrad.addColorStop(0.5, 'rgba(126, 34, 206, 0.08)');
        glowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, currentRadius * 1.35, 0, Math.PI * 2);
        ctx.fill();
      }

      // C. Render Rotating Violet Dot-Matrix Earth
      angle += 0.0035;
      const cosA = Math.cos(angle);
      const sinA = Math.sin(angle);
      // Axial tilt (23.5 degrees)
      const tilt = 0.35;
      const cosT = Math.cos(tilt);
      const sinT = Math.sin(tilt);

      for (let i = 0; i < globePoints.length; i++) {
        const pt = globePoints[i];

        // Rotate around Y axis
        const rx = pt.x * cosA - pt.z * sinA;
        const rz = pt.x * sinA + pt.z * cosA;
        const ry = pt.y;

        // Apply axial tilt
        const finalY = ry * cosT - rz * sinT;
        const finalZ = ry * sinT + rz * cosT;
        const finalX = rx;

        // Depth perspective projection
        const perspective = 2.4 / (2.4 + finalZ);
        const screenX = centerX + finalX * currentRadius * perspective;
        const screenY = centerY + finalY * currentRadius * perspective;

        // Backface cull & shading (only render points with positive or near-zero Z)
        if (finalZ > -0.4) {
          const zFactor = (finalZ + 0.4) / 1.4;
          const dotSize = Math.max(0.6, 1.8 * perspective * zFactor);
          const alpha = Math.max(0.08, zFactor * pt.baseAlpha);

          // Violet / purple palette accents (#c084fc / #a855f7)
          ctx.fillStyle = `rgba(192, 132, 252, ${alpha * 0.85})`;
          ctx.beginPath();
          ctx.arc(screenX, screenY, dotSize, 0, Math.PI * 2);
          ctx.fill();

          // Highlight brightest front points with subtle glow
          if (finalZ > 0.6 && pt.baseAlpha > 0.6) {
            ctx.fillStyle = `rgba(233, 213, 255, ${alpha * 0.4})`;
            ctx.beginPath();
            ctx.arc(screenX, screenY, dotSize * 1.7, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }

      if (typeof requestAnimationFrame === 'function') {
        animationFrameId = requestAnimationFrame(draw);
      }
    };

    const mediaQuery = typeof window.matchMedia === 'function' ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    if (!mediaQuery || !mediaQuery.matches) {
      draw();
    } else {
      angle = 0.5;
      draw();
      if (typeof cancelAnimationFrame === 'function' && animationFrameId !== undefined) {
        cancelAnimationFrame(animationFrameId);
      }
    }

    return () => {
      window.removeEventListener('resize', resize);
      if (typeof cancelAnimationFrame === 'function' && animationFrameId !== undefined) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, []);

  return (
    <div className="hero-media-container" aria-hidden="true">
      <canvas
        id="globeCanvas"
        ref={canvasRef}
        className="procedural-globe-canvas"
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          mixBlendMode: 'screen',
          opacity: 0.95,
        }}
      />
      <div
        className="hero-vignette"
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.65) 65%, #000000 100%), linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 25%, transparent 75%, #000000 100%)',
          zIndex: 2,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};
