/**
 * CraveSmart Prediction Engine
 *
 * Predicts food cravings based on:
 * 1. Cycle phase (scientifically-backed patterns)
 * 2. Time of day
 * 3. Day of week
 * 4. Weather
 * 5. Personal history
 */

import {
  CyclePhase,
  CravingType,
  CuisineType,
  TimeOfDay,
  DayOfWeek,
  WeatherCondition,
  FoodLog,
  UserPattern,
  CravingPrediction,
  PredictionFactor,
  PHASE_CRAVING_PATTERNS,
} from './types';

// ============================================
// Weight Configuration
// ============================================

const FACTOR_WEIGHTS = {
  cycle_phase: 0.35,    // Highest weight - scientifically proven
  history: 0.25,        // Personal patterns are strong
  time_of_day: 0.15,
  day_of_week: 0.15,
  weather: 0.10,
};

// ============================================
// Base Craving Patterns (Research-Backed)
// ============================================

// Time of day patterns
const TIME_CRAVING_PATTERNS: Record<TimeOfDay, CravingType[]> = {
  early_morning: ['light', 'energizing', 'caffeine'],
  morning: ['protein', 'energizing', 'fresh'],
  lunch: ['savory', 'protein', 'fresh'],
  afternoon: ['sweet', 'caffeine', 'light'],
  dinner: ['savory', 'comfort', 'indulgent'],
  late_night: ['salty', 'comfort', 'indulgent'],
};

// Day of week patterns
const DAY_CRAVING_PATTERNS: Record<DayOfWeek, CravingType[]> = {
  monday: ['light', 'fresh', 'energizing'],
  tuesday: ['savory', 'protein'],
  wednesday: ['comfort', 'carb_heavy'],
  thursday: ['spicy', 'social'],
  friday: ['indulgent', 'social', 'celebratory'],
  saturday: ['indulgent', 'comfort', 'social'],
  sunday: ['comfort', 'warm', 'carb_heavy'],
};

// Weather patterns
const WEATHER_CRAVING_PATTERNS: Record<WeatherCondition, CravingType[]> = {
  hot: ['cold', 'fresh', 'light'],
  warm: ['fresh', 'light'],
  mild: ['savory', 'fresh'],
  cool: ['warm', 'comfort'],
  cold: ['warm', 'comfort', 'carb_heavy'],
  rainy: ['warm', 'comfort', 'indulgent'],
};

// Craving to cuisine mapping
const CRAVING_TO_CUISINE: Record<CravingType, CuisineType[]> = {
  sweet: ['dessert', 'thai', 'indian'],
  salty: ['mexican', 'fast_food', 'chinese'],
  savory: ['italian', 'american', 'mediterranean'],
  spicy: ['mexican', 'thai', 'indian', 'korean'],
  carb_heavy: ['italian', 'american', 'comfort'],
  protein: ['american', 'japanese', 'korean'],
  comfort: ['american', 'comfort', 'italian'],
  fresh: ['healthy', 'mediterranean', 'vietnamese'],
  light: ['healthy', 'japanese', 'vietnamese'],
  indulgent: ['italian', 'fast_food', 'dessert'],
  chocolate: ['dessert'],
  caffeine: [], // Not a cuisine
  warm: ['comfort', 'vietnamese', 'thai'],
  cold: ['healthy', 'japanese'],
  iron_rich: ['american', 'korean'],
  energizing: ['healthy', 'japanese'],
  social: ['mexican', 'italian', 'korean'],
  celebratory: ['italian', 'japanese', 'indian'],
};

// ============================================
// Prediction Engine
// ============================================

export interface PredictionContext {
  cyclePhase: CyclePhase;
  cycleDay: number;
  timeOfDay: TimeOfDay;
  dayOfWeek: DayOfWeek;
  weather?: WeatherCondition;
  recentLogs?: FoodLog[];
  userPatterns?: UserPattern[];
}

export function predictCravings(context: PredictionContext): CravingPrediction {
  const factors: PredictionFactor[] = [];
  const cravingScores: Map<CravingType, number> = new Map();

  // Helper to add score
  const addScore = (craving: CravingType, score: number) => {
    const current = cravingScores.get(craving) || 0;
    cravingScores.set(craving, current + score);
  };

  // 1. Cycle Phase (35% weight)
  if (context.cyclePhase !== 'unknown') {
    const phaseCravings = PHASE_CRAVING_PATTERNS[context.cyclePhase];
    phaseCravings.forEach((craving, index) => {
      // First craving in list gets highest score
      const score = FACTOR_WEIGHTS.cycle_phase * (1 - index * 0.2);
      addScore(craving, score);
    });

    factors.push({
      type: 'cycle_phase',
      weight: FACTOR_WEIGHTS.cycle_phase,
      description: getCyclePhaseExplanation(context.cyclePhase, context.cycleDay),
    });
  }

  // 2. Time of Day (15% weight)
  const timeCravings = TIME_CRAVING_PATTERNS[context.timeOfDay];
  timeCravings.forEach((craving, index) => {
    const score = FACTOR_WEIGHTS.time_of_day * (1 - index * 0.2);
    addScore(craving, score);
  });

  factors.push({
    type: 'time_of_day',
    weight: FACTOR_WEIGHTS.time_of_day,
    description: getTimeExplanation(context.timeOfDay),
  });

  // 3. Day of Week (15% weight)
  const dayCravings = DAY_CRAVING_PATTERNS[context.dayOfWeek];
  dayCravings.forEach((craving, index) => {
    const score = FACTOR_WEIGHTS.day_of_week * (1 - index * 0.2);
    addScore(craving, score);
  });

  factors.push({
    type: 'day_of_week',
    weight: FACTOR_WEIGHTS.day_of_week,
    description: getDayExplanation(context.dayOfWeek),
  });

  // 4. Weather (10% weight)
  if (context.weather) {
    const weatherCravings = WEATHER_CRAVING_PATTERNS[context.weather];
    weatherCravings.forEach((craving, index) => {
      const score = FACTOR_WEIGHTS.weather * (1 - index * 0.2);
      addScore(craving, score);
    });

    factors.push({
      type: 'weather',
      weight: FACTOR_WEIGHTS.weather,
      description: getWeatherExplanation(context.weather),
    });
  }

  // 5. Personal History (25% weight)
  if (context.userPatterns && context.userPatterns.length > 0) {
    const applicablePatterns = findApplicablePatterns(context);
    applicablePatterns.forEach(pattern => {
      pattern.likelyCravings.forEach((craving, index) => {
        const score = FACTOR_WEIGHTS.history * pattern.confidence * (1 - index * 0.1);
        addScore(craving, score);
      });
    });

    if (applicablePatterns.length > 0) {
      factors.push({
        type: 'history',
        weight: FACTOR_WEIGHTS.history,
        description: `Based on your personal patterns (${applicablePatterns.length} matching)`,
      });
    }
  }

  // Sort cravings by score
  const sortedCravings = Array.from(cravingScores.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([craving]) => craving);

  const primaryCraving = sortedCravings[0] || 'savory';
  const secondaryCravings = sortedCravings.slice(1, 4);

  // Map cravings to cuisines
  const suggestedCuisines = getSuggestedCuisines([primaryCraving, ...secondaryCravings]);

  // Calculate confidence based on factor agreement
  const confidence = calculateConfidence(cravingScores, factors);

  return {
    id: generateId(),
    userId: '', // Set by caller
    createdAt: new Date(),
    forDate: new Date(),
    primaryCraving,
    secondaryCravings,
    suggestedCuisines,
    confidence,
    factors,
  };
}

// ============================================
// Helper Functions
// ============================================

function getCyclePhaseExplanation(phase: CyclePhase, day: number): string {
  const explanations: Record<CyclePhase, string> = {
    menstrual: `Day ${day} of your period - your body often craves iron-rich and comforting foods`,
    follicular: `Pre-ovulation phase (day ${day}) - energy is rising, lighter foods often feel right`,
    ovulation: `Ovulation window (day ${day}) - peak energy, social eating feels natural`,
    luteal: `Luteal phase (day ${day}) - progesterone rises, sweet and carb cravings are common`,
    unknown: 'Cycle phase unknown',
  };
  return explanations[phase];
}

function getTimeExplanation(time: TimeOfDay): string {
  const explanations: Record<TimeOfDay, string> = {
    early_morning: 'Early morning - light, energizing options',
    morning: 'Morning - protein and energy for the day ahead',
    lunch: 'Lunchtime - satisfying midday fuel',
    afternoon: 'Afternoon - energy boost time',
    dinner: 'Dinner - winding down, comfort and satisfaction',
    late_night: 'Late night - comfort cravings peak',
  };
  return explanations[time];
}

function getDayExplanation(day: DayOfWeek): string {
  const explanations: Record<DayOfWeek, string> = {
    monday: 'Monday - fresh start, lighter choices',
    tuesday: 'Tuesday - settling into the week',
    wednesday: 'Wednesday - midweek comfort',
    thursday: 'Thursday - almost weekend energy',
    friday: 'Friday - celebration mode',
    saturday: 'Saturday - indulgent weekend',
    sunday: 'Sunday - comfort and preparation',
  };
  return explanations[day];
}

function getWeatherExplanation(weather: WeatherCondition): string {
  const explanations: Record<WeatherCondition, string> = {
    hot: 'Hot weather - cooling, refreshing foods',
    warm: 'Warm weather - light and fresh',
    mild: 'Mild weather - balanced options',
    cool: 'Cool weather - warming comfort foods',
    cold: 'Cold weather - hearty, warming meals',
    rainy: 'Rainy day - cozy comfort foods',
  };
  return explanations[weather];
}

function findApplicablePatterns(context: PredictionContext): UserPattern[] {
  if (!context.userPatterns) return [];

  return context.userPatterns.filter(pattern => {
    return pattern.conditions.every(condition => {
      switch (condition.factor) {
        case 'cycle_phase':
          return condition.value === context.cyclePhase;
        case 'day_of_week':
          return condition.value === context.dayOfWeek;
        case 'time_of_day':
          return condition.value === context.timeOfDay;
        case 'weather':
          return condition.value === context.weather;
        default:
          return false;
      }
    });
  });
}

function getSuggestedCuisines(cravings: CravingType[]): CuisineType[] {
  const cuisineScores: Map<CuisineType, number> = new Map();

  cravings.forEach((craving, index) => {
    const cuisines = CRAVING_TO_CUISINE[craving] || [];
    cuisines.forEach(cuisine => {
      const current = cuisineScores.get(cuisine) || 0;
      cuisineScores.set(cuisine, current + (1 - index * 0.2));
    });
  });

  return Array.from(cuisineScores.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([cuisine]) => cuisine);
}

function calculateConfidence(
  scores: Map<CravingType, number>,
  factors: PredictionFactor[]
): number {
  // Higher confidence when:
  // 1. Clear winner in craving scores
  // 2. Multiple factors agree
  // 3. Personal history matches

  const sortedScores = Array.from(scores.values()).sort((a, b) => b - a);
  if (sortedScores.length < 2) return 0.5;

  // Gap between top two cravings (clearer = more confident)
  const clarity = (sortedScores[0] - sortedScores[1]) / sortedScores[0];

  // Number of factors contributing
  const factorCoverage = factors.length / 5;

  // Personal history factor (if present, boost confidence)
  const hasHistory = factors.some(f => f.type === 'history');
  const historyBoost = hasHistory ? 0.1 : 0;

  const confidence = Math.min(
    0.95,
    clarity * 0.4 + factorCoverage * 0.3 + 0.2 + historyBoost
  );

  return Math.round(confidence * 100) / 100;
}

function generateId(): string {
  return `pred_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================
// Pattern Learning
// ============================================

export function learnPatterns(logs: FoodLog[]): UserPattern[] {
  const patterns: UserPattern[] = [];

  // Group logs by various conditions
  const byCyclePhase = groupBy(logs, log => log.cyclePhase);
  const byDayOfWeek = groupBy(logs, log => log.dayOfWeek);
  const byTimeOfDay = groupBy(logs, log => log.timeOfDay);

  // Learn cycle phase patterns
  Object.entries(byCyclePhase).forEach(([phase, phaseLogs]) => {
    if (phaseLogs.length >= 3) { // Minimum occurrences
      const cravings = getMostCommonCravings(phaseLogs);
      const cuisines = getMostCommonCuisines(phaseLogs);

      patterns.push({
        userId: phaseLogs[0].userId,
        patternType: 'cycle_phase',
        conditions: [{ factor: 'cycle_phase', value: phase }],
        likelyCravings: cravings,
        likelyCuisines: cuisines,
        confidence: Math.min(0.9, phaseLogs.length / 10),
        occurrences: phaseLogs.length,
        lastOccurred: new Date(Math.max(...phaseLogs.map(l => l.timestamp.getTime()))),
      });
    }
  });

  // Learn day of week patterns
  Object.entries(byDayOfWeek).forEach(([day, dayLogs]) => {
    if (dayLogs.length >= 4) {
      const cravings = getMostCommonCravings(dayLogs);
      const cuisines = getMostCommonCuisines(dayLogs);

      patterns.push({
        userId: dayLogs[0].userId,
        patternType: 'day_of_week',
        conditions: [{ factor: 'day_of_week', value: day }],
        likelyCravings: cravings,
        likelyCuisines: cuisines,
        confidence: Math.min(0.85, dayLogs.length / 12),
        occurrences: dayLogs.length,
        lastOccurred: new Date(Math.max(...dayLogs.map(l => l.timestamp.getTime()))),
      });
    }
  });

  return patterns;
}

function groupBy<T>(array: T[], keyFn: (item: T) => string): Record<string, T[]> {
  return array.reduce((acc, item) => {
    const key = keyFn(item);
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {} as Record<string, T[]>);
}

function getMostCommonCravings(logs: FoodLog[]): CravingType[] {
  const counts: Map<CravingType, number> = new Map();

  logs.forEach(log => {
    log.cravingTypes.forEach(craving => {
      counts.set(craving, (counts.get(craving) || 0) + 1);
    });
  });

  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([craving]) => craving);
}

function getMostCommonCuisines(logs: FoodLog[]): CuisineType[] {
  const counts: Map<CuisineType, number> = new Map();

  logs.forEach(log => {
    if (log.cuisineType) {
      counts.set(log.cuisineType, (counts.get(log.cuisineType) || 0) + 1);
    }
  });

  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([cuisine]) => cuisine);
}
