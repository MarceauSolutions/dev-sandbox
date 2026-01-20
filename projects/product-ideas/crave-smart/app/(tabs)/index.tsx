import { StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Text, View } from '@/components/Themed';
import { useState, useEffect } from 'react';

// Types (will import from src/types.ts when properly configured)
type CyclePhase = 'menstrual' | 'follicular' | 'ovulation' | 'luteal' | 'unknown';
type CravingType = 'sweet' | 'salty' | 'savory' | 'spicy' | 'comfort' | 'fresh' | 'chocolate';

interface TodaysPrediction {
  primaryCraving: CravingType;
  secondaryCravings: CravingType[];
  confidence: number;
  explanation: string;
}

// Mock data for development
const MOCK_CYCLE: { phase: CyclePhase; day: number } = {
  phase: 'luteal',
  day: 22,
};

const MOCK_PREDICTION: TodaysPrediction = {
  primaryCraving: 'chocolate',
  secondaryCravings: ['sweet', 'comfort'],
  confidence: 0.78,
  explanation: "Day 22 of your cycle (luteal phase) - progesterone is high. Sweet and chocolate cravings are scientifically proven to increase now.",
};

const CRAVING_EMOJIS: Record<CravingType, string> = {
  sweet: '🍰',
  salty: '🧂',
  savory: '🍖',
  spicy: '🌶️',
  comfort: '🍜',
  fresh: '🥗',
  chocolate: '🍫',
};

// Grammatically correct craving descriptions
const CRAVING_PHRASES: Record<CravingType, string> = {
  sweet: 'something sweet',
  salty: 'something salty',
  savory: 'something savory',
  spicy: 'something spicy',
  comfort: 'comfort food',
  fresh: 'something fresh and light',
  chocolate: 'chocolate',
};

const PHASE_COLORS: Record<CyclePhase, string> = {
  menstrual: '#E57373',
  follicular: '#81C784',
  ovulation: '#FFD54F',
  luteal: '#9575CD',
  unknown: '#90A4AE',
};

export default function HomeScreen() {
  const [cycle, setCycle] = useState(MOCK_CYCLE);
  const [prediction, setPrediction] = useState<TodaysPrediction>(MOCK_PREDICTION);
  const [hasHealthKitAccess, setHasHealthKitAccess] = useState(false);

  return (
    <ScrollView style={styles.scrollView}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>Good afternoon! 👋</Text>
          <Text style={styles.subtitle}>Here's what you might crave today</Text>
        </View>

        {/* Cycle Status Card */}
        <View style={[styles.card, { borderLeftColor: PHASE_COLORS[cycle.phase] }]}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Cycle Status</Text>
            <View style={[styles.phaseBadge, { backgroundColor: PHASE_COLORS[cycle.phase] }]}>
              <Text style={styles.phaseBadgeText}>{cycle.phase.charAt(0).toUpperCase() + cycle.phase.slice(1)}</Text>
            </View>
          </View>
          <Text style={styles.cycleDay}>Day {cycle.day}</Text>
          {!hasHealthKitAccess && (
            <TouchableOpacity style={styles.connectButton}>
              <Text style={styles.connectButtonText}>Connect Apple Health</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Today's Prediction Card */}
        <View style={styles.predictionCard}>
          <Text style={styles.predictionTitle}>Today's Prediction</Text>

          <View style={styles.primaryCraving}>
            <Text style={styles.cravingEmoji}>
              {CRAVING_EMOJIS[prediction.primaryCraving]}
            </Text>
            <Text style={styles.primaryCravingText}>
              You're probably craving {CRAVING_PHRASES[prediction.primaryCraving]}
            </Text>
          </View>

          <View style={styles.confidenceBar}>
            <View style={[styles.confidenceFill, { width: `${prediction.confidence * 100}%` }]} />
          </View>
          <Text style={styles.confidenceText}>
            {Math.round(prediction.confidence * 100)}% confidence
          </Text>

          <Text style={styles.explanation}>{prediction.explanation}</Text>

          <View style={styles.secondaryCravings}>
            <Text style={styles.secondaryTitle}>Also likely:</Text>
            <View style={styles.cravingTags}>
              {prediction.secondaryCravings.map((craving) => (
                <View key={craving} style={styles.cravingTag}>
                  <Text style={styles.cravingTagText}>
                    {CRAVING_EMOJIS[craving]} {craving}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionEmoji}>📝</Text>
            <Text style={styles.actionText}>Log a Meal</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionEmoji}>🍽️</Text>
            <Text style={styles.actionText}>Find Food</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionEmoji}>📊</Text>
            <Text style={styles.actionText}>My Patterns</Text>
          </TouchableOpacity>
        </View>

        {/* Science Note */}
        <View style={styles.scienceNote}>
          <Text style={styles.scienceTitle}>💡 Did you know?</Text>
          <Text style={styles.scienceText}>
            91.78% of women report food cravings tied to their menstrual cycle.
            During the luteal phase, sweet and carb cravings increase due to rising progesterone levels.
          </Text>
          <Text style={styles.scienceSource}>Source: PMC Research, 2023</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
  },
  container: {
    flex: 1,
    padding: 20,
    paddingBottom: 100,
  },
  header: {
    marginBottom: 20,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 16,
    opacity: 0.7,
    marginTop: 4,
  },
  card: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderLeftWidth: 4,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'transparent',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  phaseBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  phaseBadgeText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 12,
  },
  cycleDay: {
    fontSize: 32,
    fontWeight: 'bold',
    marginTop: 8,
  },
  connectButton: {
    marginTop: 12,
    padding: 10,
    backgroundColor: '#FF6B6B',
    borderRadius: 8,
    alignItems: 'center',
  },
  connectButtonText: {
    color: 'white',
    fontWeight: '600',
  },
  predictionCard: {
    padding: 20,
    borderRadius: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
  },
  predictionTitle: {
    fontSize: 14,
    fontWeight: '600',
    opacity: 0.7,
    marginBottom: 12,
  },
  primaryCraving: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    backgroundColor: 'transparent',
  },
  cravingEmoji: {
    fontSize: 48,
    marginRight: 16,
  },
  primaryCravingText: {
    fontSize: 20,
    fontWeight: 'bold',
    flex: 1,
  },
  confidenceBar: {
    height: 6,
    backgroundColor: 'rgba(150, 150, 150, 0.2)',
    borderRadius: 3,
    marginBottom: 4,
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#FF6B6B',
    borderRadius: 3,
  },
  confidenceText: {
    fontSize: 12,
    opacity: 0.6,
    marginBottom: 12,
  },
  explanation: {
    fontSize: 14,
    lineHeight: 20,
    opacity: 0.8,
    marginBottom: 16,
  },
  secondaryCravings: {
    backgroundColor: 'transparent',
  },
  secondaryTitle: {
    fontSize: 12,
    fontWeight: '600',
    opacity: 0.6,
    marginBottom: 8,
  },
  cravingTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    backgroundColor: 'transparent',
  },
  cravingTag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: 'rgba(150, 150, 150, 0.15)',
  },
  cravingTagText: {
    fontSize: 14,
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    backgroundColor: 'transparent',
  },
  actionButton: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    marginHorizontal: 4,
    borderRadius: 12,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
  },
  actionEmoji: {
    fontSize: 24,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 12,
    fontWeight: '600',
  },
  scienceNote: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(100, 150, 200, 0.1)',
  },
  scienceTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  scienceText: {
    fontSize: 13,
    lineHeight: 18,
    opacity: 0.8,
  },
  scienceSource: {
    fontSize: 11,
    opacity: 0.5,
    marginTop: 8,
    fontStyle: 'italic',
  },
});
