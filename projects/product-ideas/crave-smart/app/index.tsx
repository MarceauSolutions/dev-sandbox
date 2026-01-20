import { StyleSheet, Dimensions, TouchableOpacity, Animated } from 'react-native';
import { Text, View } from '@/components/Themed';
import { useRouter } from 'expo-router';
import { useState, useEffect, useRef } from 'react';
import { LinearGradient } from 'expo-linear-gradient';

const { width, height } = Dimensions.get('window');

// Emotional storytelling sequence - designed to create connection
const SCENARIOS = [
  {
    emoji: '😩',
    setup: '"I don\'t know, you pick."',
    punchline: 'Every. Single. Time.',
  },
  {
    emoji: '🤷‍♂️',
    setup: 'You suggest pizza.',
    punchline: '"I\'m not really feeling that."',
  },
  {
    emoji: '😤',
    setup: 'You suggest tacos.',
    punchline: '"No, not that either."',
  },
  {
    emoji: '💔',
    setup: 'Another argument about dinner.',
    punchline: 'It didn\'t have to be this way.',
  },
  {
    emoji: '🧬',
    setup: 'Her cravings aren\'t random.',
    punchline: 'They\'re predictable. Scientifically.',
  },
  {
    emoji: '🍫',
    setup: 'Day 22: Chocolate.',
    punchline: 'Day 5: Comfort food. Day 14: Something adventurous.',
  },
  {
    emoji: '💡',
    setup: 'What if you knew what she wanted...',
    punchline: 'Before she did?',
  },
  {
    emoji: '❤️',
    setup: 'No more guessing. No more frustration.',
    punchline: 'Just connection.',
  },
];

export default function LandingScreen() {
  const router = useRouter();
  const [currentScenario, setCurrentScenario] = useState(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;

  // Rotate through scenarios
  useEffect(() => {
    const interval = setInterval(() => {
      // Fade out
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start(() => {
        // Change scenario
        setCurrentScenario((prev) => (prev + 1) % SCENARIOS.length);
        // Fade in
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }).start();
      });
    }, 3500);

    return () => clearInterval(interval);
  }, []);

  const scenario = SCENARIOS[currentScenario];

  return (
    <View style={styles.container}>
      {/* Background gradient */}
      <LinearGradient
        colors={['#FF6B6B', '#FF8E8E', '#FFB4B4']}
        style={styles.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />

      {/* Content */}
      <View style={styles.content}>
        {/* Animated scenario display */}
        <Animated.View style={[styles.scenarioContainer, { opacity: fadeAnim }]}>
          <Text style={styles.scenarioEmoji}>{scenario.emoji}</Text>
          <Text style={styles.scenarioSetup}>{scenario.setup}</Text>
          <Text style={styles.scenarioPunchline}>{scenario.punchline}</Text>
        </Animated.View>

        {/* App name and tagline */}
        <View style={styles.brandContainer}>
          <Text style={styles.appName}>CraveSmart</Text>
          <Text style={styles.tagline}>
            Stop guessing. Start knowing.{'\n'}
            Her cravings, predicted by science.
          </Text>
        </View>

        {/* Social proof */}
        <View style={styles.proofContainer}>
          <Text style={styles.proofStat}>91.78%</Text>
          <Text style={styles.proofText}>
            of women have predictable cravings{'\n'}tied to their cycle
          </Text>
          <Text style={styles.proofSource}>— PMC Peer-Reviewed Research</Text>
        </View>

        {/* CTA buttons */}
        <View style={styles.ctaContainer}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.push('/(tabs)')}
          >
            <Text style={styles.primaryButtonText}>Never Guess Again</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => router.push('/(tabs)')}
          >
            <Text style={styles.secondaryButtonText}>Sign in</Text>
          </TouchableOpacity>
        </View>

        {/* Trust indicators */}
        <View style={styles.trustContainer}>
          <Text style={styles.trustText}>🔒 Your data stays on your device</Text>
          <Text style={styles.trustText}>🍎 Connects to Apple Health</Text>
        </View>
      </View>

      {/* Scenario dots */}
      <View style={styles.dotsContainer}>
        {SCENARIOS.map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              index === currentScenario && styles.dotActive,
            ]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  content: {
    flex: 1,
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: height * 0.1,
    paddingBottom: 40,
    paddingHorizontal: 30,
    backgroundColor: 'transparent',
  },
  scenarioContainer: {
    alignItems: 'center',
    height: 180,
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  scenarioEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  scenarioSetup: {
    fontSize: 24,
    fontWeight: '600',
    color: 'white',
    textAlign: 'center',
    marginBottom: 8,
  },
  scenarioPunchline: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  brandContainer: {
    alignItems: 'center',
    backgroundColor: 'transparent',
  },
  appName: {
    fontSize: 48,
    fontWeight: 'bold',
    color: 'white',
    letterSpacing: -1,
    marginBottom: 12,
  },
  tagline: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.95)',
    textAlign: 'center',
    lineHeight: 26,
  },
  proofContainer: {
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingVertical: 20,
    paddingHorizontal: 30,
    borderRadius: 16,
  },
  proofStat: {
    fontSize: 42,
    fontWeight: 'bold',
    color: 'white',
  },
  proofText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 20,
  },
  proofSource: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 8,
    fontStyle: 'italic',
  },
  ctaContainer: {
    width: '100%',
    backgroundColor: 'transparent',
  },
  primaryButton: {
    backgroundColor: 'white',
    paddingVertical: 18,
    borderRadius: 30,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  primaryButtonText: {
    color: '#FF6B6B',
    fontSize: 18,
    fontWeight: 'bold',
  },
  secondaryButton: {
    paddingVertical: 14,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 14,
  },
  trustContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: 16,
    backgroundColor: 'transparent',
  },
  trustText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  dotsContainer: {
    position: 'absolute',
    bottom: 120,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'transparent',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.4)',
  },
  dotActive: {
    backgroundColor: 'white',
    width: 24,
  },
});
