import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Brand } from '@/constants/Colors';
import { useAuth } from '@/lib/AuthContext';

export default function HomeScreen() {
  const { user } = useAuth();

  const today = new Date();
  const dayName = today.toLocaleDateString('en-US', { weekday: 'long' });
  const dateStr = today.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
  });

  const displayName =
    user?.user_metadata?.display_name ||
    user?.email?.split('@')[0] ||
    'Babe';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Greeting */}
      <View style={styles.greetingSection}>
        <Text style={styles.greeting}>Hey {displayName}!</Text>
        <Text style={styles.date}>
          {dayName}, {dateStr}
        </Text>
      </View>

      {/* Today's Workout */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>THINGS TO DO TODAY</Text>
        <TouchableOpacity style={styles.workoutCard} activeOpacity={0.8}>
          <View style={styles.workoutCardInner}>
            <Text style={styles.workoutEmoji}>💪</Text>
            <View style={styles.workoutInfo}>
              <Text style={styles.workoutTitle}>Today's Workout</Text>
              <Text style={styles.workoutSubtitle}>
                Coming soon — your daily workout will appear here
              </Text>
            </View>
          </View>
        </TouchableOpacity>
      </View>

      {/* Quick Stats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>MY PROGRESS</Text>
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>0</Text>
            <Text style={styles.statLabel}>Workouts</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>0</Text>
            <Text style={styles.statLabel}>Day Streak</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>--</Text>
            <Text style={styles.statLabel}>This Week</Text>
          </View>
        </View>
      </View>

      {/* Nutrition Tip */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>DAILY TIP</Text>
        <View style={styles.tipCard}>
          <Text style={styles.tipText}>
            Protein is your best friend. Try to hit 0.8-1g per pound of body weight daily for optimal muscle recovery and growth.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Brand.blush,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  greetingSection: {
    marginBottom: 28,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '700',
    color: Brand.textDark,
  },
  date: {
    fontSize: 15,
    color: Brand.textMedium,
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Brand.textLight,
    letterSpacing: 2,
    marginBottom: 12,
  },
  workoutCard: {
    backgroundColor: Brand.white,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  workoutCardInner: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  workoutEmoji: {
    fontSize: 36,
    marginRight: 16,
  },
  workoutInfo: {
    flex: 1,
  },
  workoutTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Brand.textDark,
  },
  workoutSubtitle: {
    fontSize: 14,
    color: Brand.textMedium,
    marginTop: 4,
    lineHeight: 20,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: Brand.white,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: Brand.accent,
  },
  statLabel: {
    fontSize: 12,
    color: Brand.textMedium,
    marginTop: 4,
  },
  tipCard: {
    backgroundColor: Brand.white,
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: Brand.accent,
  },
  tipText: {
    fontSize: 14,
    color: Brand.textDark,
    lineHeight: 22,
  },
});
