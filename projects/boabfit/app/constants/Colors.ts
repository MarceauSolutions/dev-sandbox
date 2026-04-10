// BOABFIT Brand Colors
// Barbie pink / blush palette — feminine, motivational, Julia's brand

export const Brand = {
  // Primary palette
  blush: '#f5e6e0',        // Main background pink
  blushLight: '#faf2ef',    // Lighter variant for cards
  blushDark: '#e8d4cc',     // Pressed/hover state
  accent: '#d4a0a0',        // Accent pink (buttons, highlights)
  accentDark: '#b87d7d',    // Darker accent for active states

  // Text
  textDark: '#2d2d2d',      // Primary text
  textMedium: '#6b6b6b',    // Secondary text
  textLight: '#9a9a9a',     // Placeholder, muted text
  textWhite: '#ffffff',     // Text on dark backgrounds

  // Backgrounds
  white: '#ffffff',
  offWhite: '#fdfbfa',      // Slight warmth
  dark: '#1a1a1a',          // Workout "Press Play" screen
  darkCard: '#2a2a2a',      // Cards on dark background

  // Functional
  success: '#7bc67e',       // Completed workouts
  warning: '#f5c842',       // Streak at risk
  error: '#e85d5d',         // Errors
  streak: '#ff6b35',        // Streak fire color

  // Tab bar
  tabActive: '#d4a0a0',
  tabInactive: '#c4b5b0',
};

const tintColorLight = Brand.accent;
const tintColorDark = Brand.blush;

export default {
  light: {
    text: Brand.textDark,
    background: Brand.blush,
    tint: tintColorLight,
    tabIconDefault: Brand.tabInactive,
    tabIconSelected: tintColorLight,
    card: Brand.white,
    border: Brand.blushDark,
  },
  dark: {
    text: Brand.textWhite,
    background: Brand.dark,
    tint: tintColorDark,
    tabIconDefault: '#666',
    tabIconSelected: tintColorDark,
    card: Brand.darkCard,
    border: '#333',
  },
};
