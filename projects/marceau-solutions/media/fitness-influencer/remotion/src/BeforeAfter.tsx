/* ============================================================
   BeforeAfter — Split-screen comparison animation
   Animated before/after comparison frame for form correction
   ============================================================ */

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  Sequence,
} from "remotion";

export type BeforeAfterProps = {
  beforeLabel: string;
  afterLabel: string;
  beforeImage?: string;
  afterImage?: string;
  beforeColor: string;
  afterColor: string;
  bgColor: string;
  title?: string;
  animationStyle: "wipe" | "slide" | "split";
};

const defaults: BeforeAfterProps = {
  beforeLabel: "WRONG",
  afterLabel: "RIGHT",
  beforeColor: "#FF4444",
  afterColor: "#44FF44",
  bgColor: "#0A0A0A",
  title: "FORM CHECK",
  animationStyle: "wipe",
};

/* ── Wipe Reveal ──────────────────────────────────────────────── */

const WipeComparison: React.FC<{
  beforeLabel: string;
  afterLabel: string;
  beforeColor: string;
  afterColor: string;
  beforeImage?: string;
  afterImage?: string;
}> = ({ beforeLabel, afterLabel, beforeColor, afterColor, beforeImage, afterImage }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Before side visible first, then wipe reveals after
  const wipeProgress = spring({
    frame: frame - 30,
    fps,
    config: { damping: 16, stiffness: 50 },
  });

  const wipeX = interpolate(wipeProgress, [0, 1], [width, width / 2]);

  // Label animations
  const beforeOpacity = interpolate(frame, [5, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const afterOpacity = interpolate(frame, [45, 55], [0, 1], {
    extrapolateRight: "clamp",
  });

  const panelStyle: React.CSSProperties = {
    position: "absolute",
    top: 0,
    bottom: 0,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  };

  const labelStyle = (color: string): React.CSSProperties => ({
    fontSize: 48,
    fontWeight: 900,
    fontFamily: "system-ui, -apple-system, sans-serif",
    color: "#fff",
    textTransform: "uppercase",
    letterSpacing: 6,
    padding: "12px 32px",
    background: color,
    borderRadius: 8,
  });

  const crossStyle: React.CSSProperties = {
    fontSize: 120,
    fontWeight: 900,
    opacity: 0.15,
    position: "absolute",
  };

  return (
    <AbsoluteFill>
      {/* Before side (full width, behind) */}
      <div
        style={{
          ...panelStyle,
          left: 0,
          right: 0,
          backgroundColor: `${beforeColor}15`,
        }}
      >
        {beforeImage ? (
          <Img src={beforeImage} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <>
            <span style={{ ...crossStyle, color: beforeColor }}>&#10007;</span>
            <div style={{ opacity: beforeOpacity }}>
              <span style={labelStyle(beforeColor)}>{beforeLabel}</span>
            </div>
          </>
        )}
      </div>

      {/* After side (clips from right) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: wipeX,
          right: 0,
          backgroundColor: `${afterColor}15`,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {afterImage ? (
          <Img src={afterImage} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <>
            <span style={{ ...crossStyle, color: afterColor }}>&#10003;</span>
            <div style={{ opacity: afterOpacity }}>
              <span style={labelStyle(afterColor)}>{afterLabel}</span>
            </div>
          </>
        )}
      </div>

      {/* Divider line */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: wipeX - 3,
          width: 6,
          background: "#fff",
          boxShadow: "0 0 20px rgba(255,255,255,0.5)",
          zIndex: 2,
        }}
      />
    </AbsoluteFill>
  );
};

/* ── Slide Comparison ─────────────────────────────────────────── */

const SlideComparison: React.FC<{
  beforeLabel: string;
  afterLabel: string;
  beforeColor: string;
  afterColor: string;
}> = ({ beforeLabel, afterLabel, beforeColor, afterColor }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  // Before slides in from left
  const beforeSlide = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 80 },
  });

  // After slides in from right (delayed)
  const afterSlide = spring({
    frame: frame - 25,
    fps,
    config: { damping: 14, stiffness: 80 },
  });

  const panelStyle = (color: string): React.CSSProperties => ({
    width: "48%",
    aspectRatio: "1",
    maxHeight: 400,
    backgroundColor: `${color}15`,
    border: `3px solid ${color}40`,
    borderRadius: 16,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: 16,
  });

  return (
    <div
      style={{
        display: "flex",
        gap: 24,
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        padding: "0 40px",
      }}
    >
      {/* Before panel */}
      <div
        style={{
          ...panelStyle(beforeColor),
          transform: `translateX(${(1 - beforeSlide) * -width}px)`,
          opacity: beforeSlide,
        }}
      >
        <span
          style={{
            fontSize: 80,
            color: beforeColor,
            opacity: 0.3,
          }}
        >
          &#10007;
        </span>
        <span
          style={{
            fontSize: 36,
            fontWeight: 900,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color: beforeColor,
            textTransform: "uppercase",
            letterSpacing: 4,
          }}
        >
          {beforeLabel}
        </span>
      </div>

      {/* After panel */}
      <div
        style={{
          ...panelStyle(afterColor),
          transform: `translateX(${(1 - afterSlide) * width}px)`,
          opacity: afterSlide,
        }}
      >
        <span
          style={{
            fontSize: 80,
            color: afterColor,
            opacity: 0.3,
          }}
        >
          &#10003;
        </span>
        <span
          style={{
            fontSize: 36,
            fontWeight: 900,
            fontFamily: "system-ui, -apple-system, sans-serif",
            color: afterColor,
            textTransform: "uppercase",
            letterSpacing: 4,
          }}
        >
          {afterLabel}
        </span>
      </div>
    </div>
  );
};

/* ── Split Comparison (diagonal) ──────────────────────────────── */

const SplitComparison: React.FC<{
  beforeLabel: string;
  afterLabel: string;
  beforeColor: string;
  afterColor: string;
}> = ({ beforeLabel, afterLabel, beforeColor, afterColor }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const reveal = spring({
    frame: frame - 5,
    fps,
    config: { damping: 12, stiffness: 60 },
  });

  // Diagonal split using clip-path
  const splitAngle = interpolate(reveal, [0, 1], [100, 55]);

  return (
    <AbsoluteFill>
      {/* Before (left side) */}
      <AbsoluteFill
        style={{
          backgroundColor: `${beforeColor}15`,
          clipPath: `polygon(0 0, ${splitAngle}% 0, ${splitAngle - 10}% 100%, 0 100%)`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          paddingRight: "25%",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12,
            opacity: reveal,
          }}
        >
          <span style={{ fontSize: 60, color: beforeColor, opacity: 0.4 }}>
            &#10007;
          </span>
          <span
            style={{
              fontSize: 40,
              fontWeight: 900,
              fontFamily: "system-ui, -apple-system, sans-serif",
              color: beforeColor,
              textTransform: "uppercase",
              letterSpacing: 4,
            }}
          >
            {beforeLabel}
          </span>
        </div>
      </AbsoluteFill>

      {/* After (right side) */}
      <AbsoluteFill
        style={{
          backgroundColor: `${afterColor}15`,
          clipPath: `polygon(${splitAngle}% 0, 100% 0, 100% 100%, ${splitAngle - 10}% 100%)`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          paddingLeft: "25%",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12,
            opacity: reveal,
          }}
        >
          <span style={{ fontSize: 60, color: afterColor, opacity: 0.4 }}>
            &#10003;
          </span>
          <span
            style={{
              fontSize: 40,
              fontWeight: 900,
              fontFamily: "system-ui, -apple-system, sans-serif",
              color: afterColor,
              textTransform: "uppercase",
              letterSpacing: 4,
            }}
          >
            {afterLabel}
          </span>
        </div>
      </AbsoluteFill>

      {/* Diagonal divider */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `linear-gradient(${75}deg, transparent ${splitAngle - 1}%, white ${splitAngle - 0.3}%, white ${splitAngle + 0.3}%, transparent ${splitAngle + 1}%)`,
          opacity: reveal * 0.8,
        }}
      />
    </AbsoluteFill>
  );
};

/* ── Title Bar ────────────────────────────────────────────────── */

const TitleBar: React.FC<{ title: string }> = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideDown = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80 },
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 40,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        zIndex: 10,
        transform: `translateY(${(1 - slideDown) * -60}px)`,
        opacity: slideDown,
      }}
    >
      <span
        style={{
          fontSize: 32,
          fontWeight: 800,
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#fff",
          textTransform: "uppercase",
          letterSpacing: 8,
          padding: "8px 32px",
          background: "rgba(0,0,0,0.6)",
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,0.2)",
        }}
      >
        {title}
      </span>
    </div>
  );
};

/* ── Main Composition ─────────────────────────────────────────── */

export const BeforeAfter: React.FC<Partial<BeforeAfterProps>> = (props) => {
  const p = { ...defaults, ...props };
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Fade out at end
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  const ComparisonComponent =
    p.animationStyle === "slide"
      ? SlideComparison
      : p.animationStyle === "split"
      ? SplitComparison
      : WipeComparison;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: p.bgColor,
        overflow: "hidden",
        opacity: fadeOut,
      }}
    >
      {/* Title */}
      {p.title && (
        <Sequence from={0}>
          <TitleBar title={p.title} />
        </Sequence>
      )}

      {/* Comparison */}
      <ComparisonComponent
        beforeLabel={p.beforeLabel}
        afterLabel={p.afterLabel}
        beforeColor={p.beforeColor}
        afterColor={p.afterColor}
        {...(p.animationStyle === "wipe"
          ? {
              beforeImage: p.beforeImage,
              afterImage: p.afterImage,
            }
          : {})}
      />
    </AbsoluteFill>
  );
};
