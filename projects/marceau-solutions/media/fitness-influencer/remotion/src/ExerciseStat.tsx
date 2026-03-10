/* ============================================================
   ExerciseStat — Animated data graphic (Ryan Humiston style)
   "42% more muscle activation" with animated bar/counter
   ============================================================ */

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
} from "remotion";

export type ExerciseStatProps = {
  value: number;
  unit: string;
  label: string;
  subLabel?: string;
  accentColor: string;
  bgColor: string;
  displayStyle: "bar" | "counter" | "circular";
};

const defaults: ExerciseStatProps = {
  value: 42,
  unit: "%",
  label: "More Muscle Activation",
  subLabel: "vs Traditional Method",
  accentColor: "#FF4444",
  bgColor: "#0A0A0A",
  displayStyle: "bar",
};

/* ── Animated Counter ─────────────────────────────────────────── */

const AnimatedCounter: React.FC<{
  value: number;
  unit: string;
  color: string;
}> = ({ value, unit, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - 10,
    fps,
    config: { damping: 20, stiffness: 40, mass: 1.2 },
  });

  const displayValue = Math.round(value * progress);

  // Pulse on completion
  const pulse = frame > 40 && frame < 50
    ? 1 + Math.sin((frame - 40) * 0.8) * 0.05
    : 1;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "baseline",
        gap: 4,
        transform: `scale(${pulse})`,
      }}
    >
      <span
        style={{
          fontSize: 140,
          fontWeight: 900,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#fff",
          lineHeight: 1,
          textShadow: `0 0 40px ${color}60`,
        }}
      >
        {displayValue}
      </span>
      <span
        style={{
          fontSize: 64,
          fontWeight: 800,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color,
          lineHeight: 1,
        }}
      >
        {unit}
      </span>
    </div>
  );
};

/* ── Animated Bar ─────────────────────────────────────────────── */

const AnimatedBar: React.FC<{
  value: number;
  maxValue: number;
  color: string;
}> = ({ value, maxValue, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - 15,
    fps,
    config: { damping: 16, stiffness: 50 },
  });

  const barWidth = (value / maxValue) * 100 * progress;

  return (
    <div
      style={{
        width: "80%",
        maxWidth: 600,
        marginTop: 24,
      }}
    >
      {/* Track */}
      <div
        style={{
          width: "100%",
          height: 20,
          backgroundColor: "rgba(255,255,255,0.1)",
          borderRadius: 10,
          overflow: "hidden",
        }}
      >
        {/* Fill */}
        <div
          style={{
            width: `${barWidth}%`,
            height: "100%",
            background: `linear-gradient(90deg, ${color}, ${color}CC)`,
            borderRadius: 10,
            boxShadow: `0 0 20px ${color}60`,
          }}
        />
      </div>
    </div>
  );
};

/* ── Circular Progress ────────────────────────────────────────── */

const CircularProgress: React.FC<{
  value: number;
  maxValue: number;
  color: string;
  unit: string;
}> = ({ value, maxValue, color, unit }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - 10,
    fps,
    config: { damping: 20, stiffness: 40, mass: 1.2 },
  });

  const radius = 100;
  const circumference = 2 * Math.PI * radius;
  const fillAmount = (value / maxValue) * progress;
  const strokeDashoffset = circumference * (1 - fillAmount);
  const displayValue = Math.round(value * progress);

  return (
    <div style={{ position: "relative", width: 260, height: 260 }}>
      <svg
        width={260}
        height={260}
        viewBox="0 0 260 260"
        style={{ transform: "rotate(-90deg)" }}
      >
        {/* Background circle */}
        <circle
          cx={130}
          cy={130}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={16}
        />
        {/* Progress circle */}
        <circle
          cx={130}
          cy={130}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={16}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{
            filter: `drop-shadow(0 0 10px ${color}80)`,
          }}
        />
      </svg>
      {/* Center text */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontSize: 64,
            fontWeight: 900,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color: "#fff",
            lineHeight: 1,
          }}
        >
          {displayValue}
        </span>
        <span
          style={{
            fontSize: 28,
            fontWeight: 700,
            color,
            marginTop: 4,
          }}
        >
          {unit}
        </span>
      </div>
    </div>
  );
};

/* ── Labels ───────────────────────────────────────────────────── */

const Labels: React.FC<{
  label: string;
  subLabel?: string;
  color: string;
}> = ({ label, subLabel, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideUp = spring({
    frame: frame - 20,
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
        marginTop: 20,
        opacity: slideUp,
        transform: `translateY(${(1 - slideUp) * 30}px)`,
      }}
    >
      <span
        style={{
          fontSize: 36,
          fontWeight: 800,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#fff",
          textTransform: "uppercase",
          letterSpacing: 4,
          textAlign: "center",
        }}
      >
        {label}
      </span>
      {subLabel && (
        <span
          style={{
            fontSize: 22,
            fontWeight: 500,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color: "rgba(255,255,255,0.5)",
            textTransform: "uppercase",
            letterSpacing: 3,
          }}
        >
          {subLabel}
        </span>
      )}
    </div>
  );
};

/* ── Fade In/Out Wrapper ──────────────────────────────────────── */

const FadeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const opacity = interpolate(
    frame,
    [0, 8, durationInFrames - 10, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp" }
  );

  return <div style={{ opacity }}>{children}</div>;
};

/* ── Main Composition ─────────────────────────────────────────── */

export const ExerciseStat: React.FC<Partial<ExerciseStatProps>> = (props) => {
  const p = { ...defaults, ...props };
  const maxValue = p.unit === "%" ? 100 : p.value * 1.5;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: p.bgColor,
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {/* Subtle gradient overlay */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${p.accentColor}10 0%, transparent 70%)`,
        }}
      />

      <FadeWrapper>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            position: "relative",
            zIndex: 1,
          }}
        >
          {p.displayStyle === "circular" ? (
            <CircularProgress
              value={p.value}
              maxValue={maxValue}
              color={p.accentColor}
              unit={p.unit}
            />
          ) : (
            <>
              <AnimatedCounter
                value={p.value}
                unit={p.unit}
                color={p.accentColor}
              />
              {p.displayStyle === "bar" && (
                <AnimatedBar
                  value={p.value}
                  maxValue={maxValue}
                  color={p.accentColor}
                />
              )}
            </>
          )}

          <Labels
            label={p.label}
            subLabel={p.subLabel}
            color={p.accentColor}
          />
        </div>
      </FadeWrapper>
    </AbsoluteFill>
  );
};
