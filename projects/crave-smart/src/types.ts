/**
 * CraveSmart Core Types
 */

// ============================================
// User & Profile
// ============================================

export interface User {
  id: string;
  email: string;
  displayName: string;
  createdAt: Date;
  isPremium: boolean;
  premiumExpiresAt?: Date;
  partnerId?: string; // Linked partner for sharing
}

export interface UserPreferences {
  userId: string;
  defaultCuisines: CuisineType[];
  dietaryRestrictions: DietaryRestriction[];
  pricePreference: PriceLevel;
  notificationsEnabled: boolean;
  cycleTrackingEnabled: boolean;
  partnerSharingEnabled: boolean;
}

// ============================================
// Cycle & Health Data
// ============================================

export type CyclePhase =
  | 'menstrual'      // Days 1-5: Period
  | 'follicular'     // Days 6-13: Pre-ovulation
  | 'ovulation'      // Days 14-16: Ovulation window
  | 'luteal'         // Days 17-28: Post-ovulation (craving peak)
  | 'unknown';

export interface CycleData {
  userId: string;
  currentPhase: CyclePhase;
  cycleDay: number;           // 1-28+
  lastPeriodStart: Date;
  averageCycleLength: number; // Typically 28
  dataSource: 'apple_health' | 'manual' | 'clue_terra';
  lastSyncAt: Date;
}

// Research-backed craving patterns by phase
export const PHASE_CRAVING_PATTERNS: Record<CyclePhase, CravingType[]> = {
  menstrual: ['comfort', 'iron_rich', 'warm'],
  follicular: ['fresh', 'light', 'energizing'],
  ovulation: ['social', 'indulgent', 'celebratory'],
  luteal: ['sweet', 'salty', 'carb_heavy', 'chocolate'],
  unknown: [],
};

// ============================================
// Cravings & Food Logging
// ============================================

export type CravingType =
  | 'sweet'
  | 'salty'
  | 'savory'
  | 'spicy'
  | 'carb_heavy'
  | 'protein'
  | 'comfort'
  | 'fresh'
  | 'light'
  | 'indulgent'
  | 'chocolate'
  | 'caffeine'
  | 'warm'
  | 'cold'
  | 'iron_rich'
  | 'energizing'
  | 'social'
  | 'celebratory';

export type CuisineType =
  | 'american'
  | 'mexican'
  | 'italian'
  | 'chinese'
  | 'japanese'
  | 'thai'
  | 'indian'
  | 'mediterranean'
  | 'korean'
  | 'vietnamese'
  | 'fast_food'
  | 'healthy'
  | 'comfort'
  | 'dessert';

export type DietaryRestriction =
  | 'vegetarian'
  | 'vegan'
  | 'gluten_free'
  | 'dairy_free'
  | 'keto'
  | 'halal'
  | 'kosher'
  | 'nut_free';

export type PriceLevel = 1 | 2 | 3 | 4; // $ to $$$$

export interface FoodLog {
  id: string;
  userId: string;
  timestamp: Date;

  // What they ate
  foodDescription: string;
  cuisineType?: CuisineType;
  restaurantName?: string;
  restaurantId?: string; // Google Place ID

  // Craving context
  cravingTypes: CravingType[];
  satisfactionRating: 1 | 2 | 3 | 4 | 5;

  // Context at time of eating
  cyclePhase: CyclePhase;
  cycleDay: number;
  timeOfDay: TimeOfDay;
  dayOfWeek: DayOfWeek;
  weather?: WeatherCondition;

  // For learning
  wasPredicted: boolean; // Did we suggest this?
  predictionAccuracy?: number; // If predicted, how close?
}

export type TimeOfDay =
  | 'early_morning'  // 5-8am
  | 'morning'        // 8-11am
  | 'lunch'          // 11am-2pm
  | 'afternoon'      // 2-5pm
  | 'dinner'         // 5-8pm
  | 'late_night';    // 8pm-5am

export type DayOfWeek =
  | 'monday' | 'tuesday' | 'wednesday' | 'thursday'
  | 'friday' | 'saturday' | 'sunday';

export type WeatherCondition =
  | 'hot'
  | 'warm'
  | 'mild'
  | 'cool'
  | 'cold'
  | 'rainy';

// ============================================
// Predictions
// ============================================

export interface CravingPrediction {
  id: string;
  userId: string;
  createdAt: Date;
  forDate: Date;

  // What we predict
  primaryCraving: CravingType;
  secondaryCravings: CravingType[];
  suggestedCuisines: CuisineType[];
  confidence: number; // 0-1

  // Why we predicted this
  factors: PredictionFactor[];

  // Outcome tracking
  wasAccurate?: boolean;
  userFeedback?: string;
}

export interface PredictionFactor {
  type: 'cycle_phase' | 'time_of_day' | 'day_of_week' | 'weather' | 'history' | 'pattern';
  weight: number; // How much this factor contributed
  description: string; // Human-readable explanation
}

// ============================================
// Patterns (Learned from history)
// ============================================

export interface UserPattern {
  userId: string;
  patternType: PatternType;

  // When this pattern applies
  conditions: PatternCondition[];

  // What we learned
  likelyCravings: CravingType[];
  likelyCuisines: CuisineType[];
  confidence: number;

  // Evidence
  occurrences: number;
  lastOccurred: Date;
}

export type PatternType =
  | 'cycle_phase'      // "During luteal, she wants chocolate"
  | 'day_of_week'      // "Thai food on Thursdays"
  | 'time_of_day'      // "Afternoon = caffeine"
  | 'weather'          // "Cold days = soup"
  | 'restaurant'       // "Always orders pad thai at Thai Place"
  | 'combination';     // Multiple factors

export interface PatternCondition {
  factor: 'cycle_phase' | 'day_of_week' | 'time_of_day' | 'weather';
  value: string;
}

// ============================================
// Partner Sharing (Premium)
// ============================================

export interface PartnerLink {
  id: string;
  primaryUserId: string;     // User who shares data
  partnerUserId: string;     // User who views data
  status: 'pending' | 'active' | 'revoked';
  createdAt: Date;
  permissions: PartnerPermission[];
}

export type PartnerPermission =
  | 'view_predictions'     // See today's craving predictions
  | 'view_history'         // See food log history
  | 'view_patterns'        // See learned patterns
  | 'receive_notifications'; // Get notified of cravings

export interface PartnerView {
  partnerName: string;
  todaysPrediction: CravingPrediction;
  recentHistory: FoodLog[];
  topPatterns: UserPattern[];
  lastUpdated: Date;
}

// ============================================
// Restaurant Integration
// ============================================

export interface Restaurant {
  id: string;               // Google Place ID
  name: string;
  address: string;
  rating: number;
  priceLevel: PriceLevel;
  cuisineTypes: CuisineType[];
  distanceMeters: number;
  isOpen: boolean;
  orderUrl?: string;
  phone?: string;
}

export interface RestaurantRecommendation {
  restaurant: Restaurant;
  matchScore: number;       // How well it matches current craving
  matchReasons: string[];   // "Serves comfort food", "Has chocolate desserts"
  isSponsored: boolean;     // Affiliate/promoted
}

// ============================================
// Analytics (for ML training)
// ============================================

export interface PredictionMetrics {
  totalPredictions: number;
  accuratePredictions: number;
  accuracyRate: number;
  averageConfidence: number;
  topPerformingFactors: PredictionFactor[];
}

export interface UserEngagement {
  userId: string;
  logsThisWeek: number;
  streakDays: number;
  lastActive: Date;
  predictionFeedbackRate: number;
}
