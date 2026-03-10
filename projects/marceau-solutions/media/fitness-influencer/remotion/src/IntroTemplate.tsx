/* ============================================================
   IntroTemplate — Animated branded intro (Ryan Humiston style)
   3-5 second fitness intro with logo zoom, text reveal, energy burst
   ============================================================ */

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
  Easing,
} from "remotion";

export type IntroProps = {
  brandName: string;
  tagline: string;
  accentColor: string;
  bgColor: string;
  logoText?: string;
};

const defaults: IntroProps = {
  brandName: "FIT AI",
  tagline: "Let's Get After It",
  accentColor: "#FF4444",
  bgColor: "#0A0A0A",
  logoText: "FA",
};

/* ── Energy Burst Background ──────────────────────────────────── */

const EnergyBurst: React.FC<{ color: string }> = ({ color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, config: { damping: 8, stiffness: 40 } });
  const opacity = interpolate(frame, [0, 15, 60, 75], [0, 0.3, 0.3, 0], {
    extrapolateRight: "clamp",
  });

  const rays = Array.from({ length: 12 }, (_, i) => {
    const angle = (i * 30 * Math.PI) / 180;
    const len = 600 * scale;
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: 4,
          height: len,
          background: `linear-gradient(to bottom, ${color}, transparent)`,
          transformOrigin: "top center",
          transform: `translate(-50%, 0) rotate(${i * 30}deg)`,
          opacity: opacity * 0.6,
        }}
      />
    );
  });

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center", overflow: "hidden" }}
    >
      {rays}
    </AbsoluteFill>
  );
};

/* ── Logo Circle ──────────────────────────────────────────────── */

const LogoCircle: React.FC<{ text: string; color: string }> = ({
  text,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 80, mass: 0.8 },
  });

  const rotation = interpolate(frame, [0, 20], [-180, 0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(1.5)),
  });

  return (
    <div
      style={{
        width: 140,
        height: 140,
        borderRadius: "50%",
        background: color,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        transform: `scale(${scale}) rotate(${rotation}deg)`,
        boxShadow: `0 0 60px ${color}80`,
      }}
    >
      <span
        style={{
          color: "#fff",
          fontSize: 52,
          fontWeight: 900,
          fontFamily: "system-ui, -apple-system, sans-serif",
          letterSpacing: -2,
        }}
      >
        {text}
      </span>
    </div>
  );
};

/* ── Brand Name Text ──────────────────────────────────────────── */

const BrandText: React.FC<{ name: string; color: string }> = ({
  name,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const letters = name.split("");

  return (
    <div style={{ display: "flex", gap: 4, marginTop: 24 }}>
      {letters.map((char, i) => {
        const delay = i * 3;
        const y = spring({
          frame: frame - delay,
          fps,
          config: { damping: 12, stiffness: 100 },
        });
        const opacity = interpolate(frame - delay, [0, 5], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <span
            key={i}
            style={{
              fontSize: 72,
              fontWeight: 900,
              fontFamily: "system-ui, -apple-system, sans-serif",
              color: "#fff",
              letterSpacing: 6,
              transform: `translateY(${(1 - y) * 40}px)`,
              opacity,
              textShadow: `0 0 20px ${color}60`,
            }}
          >
            {char === " " ? "\u00A0" : char}
          </span>
        );
      })}
    </div>
  );
};

/* ── Tagline ──────────────────────────────────────────────────── */

const Tagline: React.FC<{ text: string; color: string }> = ({
  text,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 60 },
  });

  const lineWidth = interpolate(progress, [0, 1], [0, 200]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        marginTop: 20,
      }}
    >
      <div
        style={{
          width: lineWidth,
          height: 3,
          background: color,
          borderRadius: 2,
        }}
      />
      <span
        style={{
          fontSize: 28,
          fontWeight: 600,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#fff",
          opacity: progress,
          letterSpacing: 8,
          textTransform: "uppercase",
          transform: `translateY(${(1 - progress) * 20}px)`,
        }}
      >
        {text}
      </span>
    </div>
  );
};

/* ── Flash Transition ─────────────────────────────────────────── */

const FlashOut: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 4, 8], [0, 1, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#fff",
        opacity,
      }}
    />
  );
};

/* ── Main Composition ─────────────────────────────────────────── */

export const IntroTemplate: React.FC<Partial<IntroProps>> = (props) => {
  const p = { ...defaults, ...props };
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: p.bgColor,
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Energy burst background */}
      <Sequence from={0}>
        <EnergyBurst color={p.accentColor} />
      </Sequence>

      {/* Logo circle */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
        }}
      >
        <Sequence from={5}>
          <LogoCircle text={p.logoText || "FA"} color={p.accentColor} />
        </Sequence>

        {/* Brand name */}
        <Sequence from={Math.round(fps * 0.5)}>
          <BrandText name={p.brandName} color={p.accentColor} />
        </Sequence>

        {/* Tagline */}
        <Sequence from={Math.round(fps * 1.2)}>
          <Tagline text={p.tagline} color={p.accentColor} />
        </Sequence>
      </AbsoluteFill>

      {/* Flash out at end */}
      <Sequence from={Math.round(fps * 3.5)}>
        <FlashOut />
      </Sequence>
    </AbsoluteFill>
  );
};
