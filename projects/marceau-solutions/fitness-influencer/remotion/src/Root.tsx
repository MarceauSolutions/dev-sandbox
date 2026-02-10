/* ============================================================
   Root — Remotion Composition Registry
   All fitness influencer animated templates registered here
   ============================================================ */

import React from "react";
import { Composition } from "remotion";
import { IntroTemplate } from "./IntroTemplate";
import { TextBomb } from "./TextBomb";
import { ExerciseStat } from "./ExerciseStat";
import { BeforeAfter } from "./BeforeAfter";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ── Intro Templates ──────────────────────────────────── */}

      <Composition
        id="FitnessIntro"
        component={IntroTemplate}
        durationInFrames={FPS * 4}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          brandName: "FIT AI",
          tagline: "Let's Get After It",
          accentColor: "#FF4444",
          bgColor: "#0A0A0A",
          logoText: "FA",
        }}
      />

      <Composition
        id="FitnessIntroShort"
        component={IntroTemplate}
        durationInFrames={FPS * 3}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          brandName: "FIT AI",
          tagline: "Let's Get After It",
          accentColor: "#FF4444",
          bgColor: "#0A0A0A",
          logoText: "FA",
        }}
      />

      <Composition
        id="FitnessIntroWide"
        component={IntroTemplate}
        durationInFrames={FPS * 4}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          brandName: "FIT AI",
          tagline: "Let's Get After It",
          accentColor: "#FF4444",
          bgColor: "#0A0A0A",
          logoText: "FA",
        }}
      />

      {/* ── Text Bomb Templates ──────────────────────────────── */}

      <Composition
        id="TextBomb"
        component={TextBomb}
        durationInFrames={FPS * 2}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          text: "SHOULDER HACK",
          subtext: "",
          accentColor: "#FF4444",
          position: "center" as const,
          style: "impact" as const,
          bgOpacity: 0.7,
        }}
      />

      <Composition
        id="TextBombSlide"
        component={TextBomb}
        durationInFrames={FPS * 2}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          text: "DO THIS INSTEAD",
          subtext: "Trust Me",
          accentColor: "#FFD700",
          position: "bottom" as const,
          style: "slide" as const,
          bgOpacity: 0.5,
        }}
      />

      <Composition
        id="TextBombGlitch"
        component={TextBomb}
        durationInFrames={FPS * 2}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          text: "STOP DOING THIS",
          subtext: "",
          accentColor: "#FF4444",
          position: "center" as const,
          style: "glitch" as const,
          bgOpacity: 0.6,
        }}
      />

      <Composition
        id="TextBombWide"
        component={TextBomb}
        durationInFrames={FPS * 2}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          text: "SHOULDER HACK",
          subtext: "",
          accentColor: "#FF4444",
          position: "center" as const,
          style: "impact" as const,
          bgOpacity: 0.7,
        }}
      />

      {/* ── Exercise Stat Templates ──────────────────────────── */}

      <Composition
        id="ExerciseStat"
        component={ExerciseStat}
        durationInFrames={FPS * 3}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          value: 42,
          unit: "%",
          label: "More Muscle Activation",
          subLabel: "vs Traditional Method",
          accentColor: "#FF4444",
          bgColor: "#0A0A0A",
          displayStyle: "bar" as const,
        }}
      />

      <Composition
        id="ExerciseStatCircular"
        component={ExerciseStat}
        durationInFrames={FPS * 3}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          value: 85,
          unit: "%",
          label: "Optimal Range of Motion",
          subLabel: "",
          accentColor: "#44FF44",
          bgColor: "#0A0A0A",
          displayStyle: "circular" as const,
        }}
      />

      <Composition
        id="ExerciseStatCounter"
        component={ExerciseStat}
        durationInFrames={FPS * 3}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          value: 3,
          unit: "x",
          label: "More Effective",
          subLabel: "Than Standard Curls",
          accentColor: "#FFD700",
          bgColor: "#0A0A0A",
          displayStyle: "counter" as const,
        }}
      />

      <Composition
        id="ExerciseStatWide"
        component={ExerciseStat}
        durationInFrames={FPS * 3}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          value: 42,
          unit: "%",
          label: "More Muscle Activation",
          subLabel: "vs Traditional Method",
          accentColor: "#FF4444",
          bgColor: "#0A0A0A",
          displayStyle: "bar" as const,
        }}
      />

      {/* ── Before/After Templates ───────────────────────────── */}

      <Composition
        id="BeforeAfter"
        component={BeforeAfter}
        durationInFrames={FPS * 4}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          beforeLabel: "WRONG",
          afterLabel: "RIGHT",
          beforeColor: "#FF4444",
          afterColor: "#44FF44",
          bgColor: "#0A0A0A",
          title: "FORM CHECK",
          animationStyle: "wipe" as const,
        }}
      />

      <Composition
        id="BeforeAfterSlide"
        component={BeforeAfter}
        durationInFrames={FPS * 4}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          beforeLabel: "BEFORE",
          afterLabel: "AFTER",
          beforeColor: "#FF8800",
          afterColor: "#00FF88",
          bgColor: "#0A0A0A",
          title: "TRANSFORMATION",
          animationStyle: "slide" as const,
        }}
      />

      <Composition
        id="BeforeAfterSplit"
        component={BeforeAfter}
        durationInFrames={FPS * 4}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          beforeLabel: "DON'T",
          afterLabel: "DO",
          beforeColor: "#FF4444",
          afterColor: "#44FF44",
          bgColor: "#0A0A0A",
          title: "FORM TIP",
          animationStyle: "split" as const,
        }}
      />

      <Composition
        id="BeforeAfterWide"
        component={BeforeAfter}
        durationInFrames={FPS * 4}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          beforeLabel: "WRONG",
          afterLabel: "RIGHT",
          beforeColor: "#FF4444",
          afterColor: "#44FF44",
          bgColor: "#0A0A0A",
          title: "FORM CHECK",
          animationStyle: "wipe" as const,
        }}
      />
    </>
  );
};
