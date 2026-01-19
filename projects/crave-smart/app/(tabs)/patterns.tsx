import { StyleSheet, ScrollView } from 'react-native';
import { Text, View } from '@/components/Themed';

// Mock pattern data
const MOCK_PATTERNS = [
  {
    id: 1,
    title: 'Chocolate cravings peak during luteal phase',
    description: 'You tend to crave chocolate 80% of the time during days 17-28 of your cycle.',
    confidence: 0.82,
    occurrences: 12,
    emoji: '🍫',
  },
  {
    id: 2,
    title: 'Thai food on Thursdays',
    description: 'You\'ve ordered Thai food 6 out of the last 8 Thursdays.',
    confidence: 0.75,
    occurrences: 8,
    emoji: '🍜',
  },
  {
    id: 3,
    title: 'Comfort food when it\'s cold',
    description: 'When temperature drops below 50°F, you prefer warm, hearty meals.',
    confidence: 0.68,
    occurrences: 5,
    emoji: '🥘',
  },
  {
    id: 4,
    title: 'Afternoon sweet tooth',
    description: 'Between 2-4pm, you crave something sweet 70% of the time.',
    confidence: 0.70,
    occurrences: 14,
    emoji: '🍰',
  },
];

const PHASE_INSIGHTS = [
  { phase: 'Menstrual', emoji: '🔴', insight: 'You prefer iron-rich and comforting foods' },
  { phase: 'Follicular', emoji: '🟢', insight: 'You gravitate toward fresh, light options' },
  { phase: 'Ovulation', emoji: '🟡', insight: 'Social dining and trying new places' },
  { phase: 'Luteal', emoji: '🟣', insight: 'Sweet and carb cravings increase significantly' },
];

export default function PatternsScreen() {
  return (
    <ScrollView style={styles.scrollView}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Your Patterns</Text>
          <Text style={styles.subtitle}>
            Insights learned from your food history
          </Text>
        </View>

        {/* Cycle phase insights */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>By Cycle Phase</Text>
          <View style={styles.phaseGrid}>
            {PHASE_INSIGHTS.map((item) => (
              <View key={item.phase} style={styles.phaseCard}>
                <Text style={styles.phaseEmoji}>{item.emoji}</Text>
                <Text style={styles.phaseName}>{item.phase}</Text>
                <Text style={styles.phaseInsight}>{item.insight}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Discovered patterns */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Discovered Patterns</Text>
          {MOCK_PATTERNS.map((pattern) => (
            <View key={pattern.id} style={styles.patternCard}>
              <View style={styles.patternHeader}>
                <Text style={styles.patternEmoji}>{pattern.emoji}</Text>
                <View style={styles.patternTitleContainer}>
                  <Text style={styles.patternTitle}>{pattern.title}</Text>
                  <View style={styles.confidenceBadge}>
                    <Text style={styles.confidenceText}>
                      {Math.round(pattern.confidence * 100)}% confident
                    </Text>
                  </View>
                </View>
              </View>
              <Text style={styles.patternDescription}>{pattern.description}</Text>
              <Text style={styles.patternOccurrences}>
                Based on {pattern.occurrences} observations
              </Text>
            </View>
          ))}
        </View>

        {/* Empty state hint */}
        <View style={styles.hintContainer}>
          <Text style={styles.hintTitle}>📈 More patterns coming</Text>
          <Text style={styles.hintText}>
            Keep logging meals to discover more patterns. The more data you provide,
            the more accurate your predictions become.
          </Text>
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
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 14,
    opacity: 0.6,
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  phaseGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  phaseCard: {
    width: '48%',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
  },
  phaseEmoji: {
    fontSize: 24,
    marginBottom: 8,
  },
  phaseName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  phaseInsight: {
    fontSize: 12,
    opacity: 0.7,
    lineHeight: 16,
  },
  patternCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
    marginBottom: 12,
  },
  patternHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
    backgroundColor: 'transparent',
  },
  patternEmoji: {
    fontSize: 32,
    marginRight: 12,
  },
  patternTitleContainer: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  patternTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  confidenceBadge: {
    backgroundColor: 'rgba(255, 107, 107, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  confidenceText: {
    fontSize: 11,
    color: '#FF6B6B',
    fontWeight: '500',
  },
  patternDescription: {
    fontSize: 14,
    opacity: 0.8,
    lineHeight: 20,
    marginBottom: 8,
  },
  patternOccurrences: {
    fontSize: 11,
    opacity: 0.5,
    fontStyle: 'italic',
  },
  hintContainer: {
    padding: 16,
    backgroundColor: 'rgba(100, 150, 200, 0.1)',
    borderRadius: 12,
    marginTop: 8,
  },
  hintTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  hintText: {
    fontSize: 13,
    opacity: 0.7,
    lineHeight: 18,
  },
});
