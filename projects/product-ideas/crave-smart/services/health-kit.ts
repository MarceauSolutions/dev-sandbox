/**
 * Apple HealthKit Integration for CraveSmart
 *
 * Reads menstrual cycle data from Apple Health.
 * Period tracking apps (Flo, Clue, etc.) sync to Apple Health,
 * so we can read cycle data without direct API integration.
 */

import { CyclePhase, CycleData } from '../src/types';

// Note: In actual React Native implementation, this would use
// react-native-health or expo-health-connect

export interface HealthKitPermissions {
  menstrualFlow: boolean;
  cycleData: boolean;
}

export interface MenstrualSample {
  date: Date;
  flowLevel: 'unspecified' | 'light' | 'medium' | 'heavy';
  isStartOfCycle: boolean;
}

/**
 * Request HealthKit permissions for menstrual data
 */
export async function requestHealthKitPermissions(): Promise<HealthKitPermissions> {
  // React Native implementation would use:
  // import AppleHealthKit from 'react-native-health';
  //
  // const permissions = {
  //   permissions: {
  //     read: [AppleHealthKit.Constants.Permissions.MenstrualFlow],
  //   },
  // };
  //
  // return new Promise((resolve) => {
  //   AppleHealthKit.initHealthKit(permissions, (error) => {
  //     resolve({ menstrualFlow: !error, cycleData: !error });
  //   });
  // });

  // Placeholder for development
  console.log('Requesting HealthKit permissions...');
  return { menstrualFlow: true, cycleData: true };
}

/**
 * Check if HealthKit is available (iOS only)
 */
export function isHealthKitAvailable(): boolean {
  // In React Native:
  // return Platform.OS === 'ios' && AppleHealthKit.isAvailable();
  return true; // Placeholder
}

/**
 * Get recent menstrual flow samples from HealthKit
 */
export async function getMenstrualSamples(
  startDate: Date,
  endDate: Date
): Promise<MenstrualSample[]> {
  // React Native implementation:
  // const options = {
  //   startDate: startDate.toISOString(),
  //   endDate: endDate.toISOString(),
  // };
  //
  // return new Promise((resolve) => {
  //   AppleHealthKit.getMenstrualFlowSamples(options, (err, results) => {
  //     if (err) resolve([]);
  //     resolve(results.map(r => ({
  //       date: new Date(r.startDate),
  //       flowLevel: r.value,
  //       isStartOfCycle: r.isStartOfCycle,
  //     })));
  //   });
  // });

  // Placeholder - return mock data for development
  return [];
}

/**
 * Calculate current cycle phase from HealthKit data
 */
export async function getCycleDataFromHealthKit(
  userId: string
): Promise<CycleData | null> {
  const threeMonthsAgo = new Date();
  threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);

  const samples = await getMenstrualSamples(threeMonthsAgo, new Date());

  if (samples.length === 0) {
    return null;
  }

  // Find period start dates
  const periodStarts = samples
    .filter(s => s.isStartOfCycle || s.flowLevel !== 'unspecified')
    .sort((a, b) => b.date.getTime() - a.date.getTime());

  if (periodStarts.length === 0) {
    return null;
  }

  const lastPeriodStart = periodStarts[0].date;

  // Calculate average cycle length from history
  let averageCycleLength = 28; // Default
  if (periodStarts.length >= 2) {
    const cycleLengths: number[] = [];
    for (let i = 0; i < periodStarts.length - 1; i++) {
      const diff = periodStarts[i].date.getTime() - periodStarts[i + 1].date.getTime();
      const days = Math.round(diff / (1000 * 60 * 60 * 24));
      if (days >= 21 && days <= 35) { // Valid cycle range
        cycleLengths.push(days);
      }
    }
    if (cycleLengths.length > 0) {
      averageCycleLength = Math.round(
        cycleLengths.reduce((a, b) => a + b, 0) / cycleLengths.length
      );
    }
  }

  // Calculate current cycle day
  const today = new Date();
  const daysSinceLastPeriod = Math.floor(
    (today.getTime() - lastPeriodStart.getTime()) / (1000 * 60 * 60 * 24)
  );
  const cycleDay = (daysSinceLastPeriod % averageCycleLength) + 1;

  // Determine phase
  const currentPhase = calculateCyclePhase(cycleDay, averageCycleLength);

  return {
    userId,
    currentPhase,
    cycleDay,
    lastPeriodStart,
    averageCycleLength,
    dataSource: 'apple_health',
    lastSyncAt: new Date(),
  };
}

/**
 * Calculate cycle phase from cycle day
 *
 * Based on typical 28-day cycle:
 * - Menstrual: Days 1-5
 * - Follicular: Days 6-13
 * - Ovulation: Days 14-16
 * - Luteal: Days 17-28
 *
 * Adjusted for different cycle lengths proportionally.
 */
export function calculateCyclePhase(
  cycleDay: number,
  cycleLength: number = 28
): CyclePhase {
  // Normalize to percentage of cycle
  const progress = cycleDay / cycleLength;

  if (progress <= 0.18) {
    return 'menstrual'; // ~Days 1-5 of 28
  } else if (progress <= 0.46) {
    return 'follicular'; // ~Days 6-13 of 28
  } else if (progress <= 0.57) {
    return 'ovulation'; // ~Days 14-16 of 28
  } else {
    return 'luteal'; // ~Days 17-28 of 28
  }
}

/**
 * Subscribe to HealthKit updates for menstrual data
 */
export function subscribeToMenstrualUpdates(
  callback: (data: CycleData) => void
): () => void {
  // React Native implementation:
  // const observer = new HealthKitObserver('MenstrualFlow');
  // observer.on('change', async () => {
  //   const data = await getCycleDataFromHealthKit(userId);
  //   if (data) callback(data);
  // });
  // return () => observer.stop();

  // Placeholder - return unsubscribe function
  return () => {};
}

/**
 * Manual cycle data entry (fallback if no HealthKit data)
 */
export function createManualCycleData(
  userId: string,
  lastPeriodStart: Date,
  averageCycleLength: number = 28
): CycleData {
  const today = new Date();
  const daysSinceLastPeriod = Math.floor(
    (today.getTime() - lastPeriodStart.getTime()) / (1000 * 60 * 60 * 24)
  );
  const cycleDay = (daysSinceLastPeriod % averageCycleLength) + 1;
  const currentPhase = calculateCyclePhase(cycleDay, averageCycleLength);

  return {
    userId,
    currentPhase,
    cycleDay,
    lastPeriodStart,
    averageCycleLength,
    dataSource: 'manual',
    lastSyncAt: new Date(),
  };
}

/**
 * Get explanation text for current cycle phase
 */
export function getCyclePhaseDescription(phase: CyclePhase): {
  title: string;
  description: string;
  cravingNote: string;
} {
  const descriptions: Record<CyclePhase, { title: string; description: string; cravingNote: string }> = {
    menstrual: {
      title: 'Menstrual Phase',
      description: 'Your period is here. Energy may be lower, and your body is renewing.',
      cravingNote: 'You might crave iron-rich foods, warm comfort foods, and chocolate.',
    },
    follicular: {
      title: 'Follicular Phase',
      description: 'Post-period energy boost. Estrogen is rising, and you may feel more energetic.',
      cravingNote: 'Lighter, fresher foods often feel right. Good time for trying new things.',
    },
    ovulation: {
      title: 'Ovulation Phase',
      description: 'Peak energy and sociability. Your body is at its most fertile.',
      cravingNote: 'Social eating feels natural. You may want to dine out or share meals.',
    },
    luteal: {
      title: 'Luteal Phase',
      description: 'Pre-period phase. Progesterone rises, PMS symptoms may appear.',
      cravingNote: 'Sweet, salty, and carb cravings are scientifically proven to increase now.',
    },
    unknown: {
      title: 'Cycle Not Tracked',
      description: 'Connect a period tracker or enter your cycle manually.',
      cravingNote: 'We\'ll use other factors to predict your cravings.',
    },
  };

  return descriptions[phase];
}
