/* ============================================================
   TextBomb — Bold text overlay animation (Ryan Humiston style)
   "SHOULDER HACK" / "DO THIS INSTEAD" zoom-in with impact shake
   ============================================================ */

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

export type TextBombProps = {
  text: string;
  subtext?: string;
  accentColor: string;
  position: "center" | "top" | "bottom";
  style: "impact" | "slide" | "glitch";
  bgOpacity: number;
};

const defaults: TextBombProps = {
  text: "SHOULDER HACK",
  subtext: "",
  accentColor: "#FF4444",
  position: "center",
  style: "impact",
  bgOpacity: 0.7,
};

/* ── Impact Style: Zoom in with shake ─────────────────────────── */

const ImpactText: React.FC<{ text: string; color: string; subtext?: string }> = ({
  text,
  color,
  subtext,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Zoom in from large to normal
  const scaleIn = spring({
    frame,
    fps,
    config: { damping: 8, stiffness: 200, mass: 0.5 },
  });
  const scale = interpolate(scaleIn, [0, 1], [3, 1]);

  // Shake effect (first 10 frames after landing)
  const shakeIntensity = interpolate(frame, [6, 16], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shakeX = Math.sin(frame * 15) * shakeIntensity;
  const shakeY = Math.cos(frame * 12) * shakeIntensity * 0.5;

  // Fade out
  const opacity = interpolate(frame, [0, 5, fps * 1.5, fps * 1.8], [0, 1, 1, 0], {
    extrapolateRight: "clamp",
  });

  // Subtext slide up
  const subY = spring({
    frame: frame - 10,
    fps,
    config: { damping: 14, stiffness: 80 },
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
        transform: `scale(${scale}) translate(${shakeX}px, ${shakeY}px)`,
        opacity,
      }}
    >
      <span
        style={{
          fontSize: 96,
          fontWeight: 900,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#fff",
          textTransform: "uppercase",
          letterSpacing: 4,
          textShadow: `4px 4px 0 ${color}, -2px -2px 0 ${color}, 0 0 40px ${color}80`,
          WebkitTextStroke: `2px ${color}`,
          lineHeight: 1,
          textAlign: "center",
          padding: "0 40px",
        }}
      >
        {text}
      </span>
      {subtext && (
        <span
          style={{
            fontSize: 36,
            fontWeight: 700,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color,
            textTransform: "uppercase",
            letterSpacing: 6,
            opacity: interpolate(subY, [0, 1], [0, 1]),
            transform: `translateY(${(1 - subY) * 20}px)`,
          }}
        >
          {subtext}
        </span>
      )}
    </div>
  );
};

/* ── Slide Style: Slide in from side with bar ─────────────────── */

const SlideText: React.FC<{ text: string; color: string; subtext?: string }> = ({
  text,
  color,
  subtext,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Bar slides in
  const barProgress = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  // Text follows bar
  const textX = spring({
    frame: frame - 5,
    fps,
    config: { damping: 12, stiffness: 80 },
  });

  // Fade out
  const opacity = interpolate(frame, [fps * 1.5, fps * 1.8], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4, opacity }}>
      {/* Accent bar */}
      <div
        style={{
          width: interpolate(barProgress, [0, 1], [0, 600]),
          height: 6,
          background: color,
          borderRadius: 3,
        }}
      />
      {/* Main text */}
      <span
        style={{
          fontSize: 80,
          fontWeight: 900,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#fff",
          textTransform: "uppercase",
          letterSpacing: 2,
          transform: `translateX(${(1 - textX) * -400}px)`,
          opacity: textX,
          textShadow: `0 4px 20px rgba(0,0,0,0.5)`,
        }}
      >
        {text}
      </span>
      {subtext && (
        <span
          style={{
            fontSize: 32,
            fontWeight: 600,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color: color,
            textTransform: "uppercase",
            letterSpacing: 4,
            transform: `translateX(${(1 - textX) * -200}px)`,
            opacity: textX,
          }}
        >
          {subtext}
        </span>
      )}
    </div>
  );
};

/* ── Glitch Style: Digital glitch with color split ────────────── */

const GlitchText: React.FC<{ text: string; color: string; subtext?: string }> = ({
  text,
  color,
  subtext,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Appear with glitch
  const appear = interpolate(frame, [0, 3], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Glitch offset (random-ish using sin)
  const isGlitching = frame < 15 || (frame > 20 && frame < 25);
  const glitchX = isGlitching ? Math.sin(frame * 47) * 8 : 0;
  const glitchY = isGlitching ? Math.cos(frame * 31) * 3 : 0;

  // Fade out
  const opacity = interpolate(frame, [fps * 1.5, fps * 1.8], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const textStyle: React.CSSProperties = {
    fontSize: 88,
    fontWeight: 900,
    fontFamily: "system-ui, -apple-system, sans-serif",
    textTransform: "uppercase",
    letterSpacing: 4,
    lineHeight: 1,
    textAlign: "center" as const,
    padding: "0 40px",
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        opacity: appear * opacity,
      }}
    >
      {/* Color-split layers */}
      <div style={{ position: "relative" }}>
        {/* Red channel offset */}
        <span
          style={{
            ...textStyle,
            color: "transparent",
            WebkitTextStroke: `1px ${color}`,
            position: "absolute",
            transform: `translate(${glitchX + 3}px, ${glitchY - 2}px)`,
            opacity: 0.7,
          }}
        >
          {text}
        </span>
        {/* Cyan channel offset */}
        <span
          style={{
            ...textStyle,
            color: "transparent",
            WebkitTextStroke: "1px #00FFFF",
            position: "absolute",
            transform: `translate(${-glitchX - 3}px, ${-glitchY + 2}px)`,
            opacity: 0.5,
          }}
        >
          {text}
        </span>
        {/* Main text */}
        <span
          style={{
            ...textStyle,
            color: "#fff",
            position: "relative",
            textShadow: `0 0 20px ${color}60`,
            transform: `translate(${glitchX * 0.3}px, ${glitchY * 0.3}px)`,
          }}
        >
          {text}
        </span>
      </div>
      {subtext && (
        <span
          style={{
            fontSize: 30,
            fontWeight: 700,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color,
            letterSpacing: 6,
            textTransform: "uppercase",
          }}
        >
          {subtext}
        </span>
      )}
    </div>
  );
};

/* ── Main Composition ─────────────────────────────────────────── */

export const TextBomb: React.FC<Partial<TextBombProps>> = (props) => {
  const p = { ...defaults, ...props };

  const positionStyle: React.CSSProperties =
    p.position === "top"
      ? { justifyContent: "flex-start", paddingTop: 120 }
      : p.position === "bottom"
      ? { justifyContent: "flex-end", paddingBottom: 120 }
      : { justifyContent: "center" };

  const TextComponent =
    p.style === "slide"
      ? SlideText
      : p.style === "glitch"
      ? GlitchText
      : ImpactText;

  return (
    <AbsoluteFill
      style={{
        ...positionStyle,
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Semi-transparent background for readability */}
      <AbsoluteFill
        style={{
          backgroundColor: `rgba(0,0,0,${p.bgOpacity})`,
        }}
      />

      {/* Text content */}
      <div style={{ position: "relative", zIndex: 1 }}>
        <TextComponent
          text={p.text}
          color={p.accentColor}
          subtext={p.subtext}
        />
      </div>
    </AbsoluteFill>
  );
};
