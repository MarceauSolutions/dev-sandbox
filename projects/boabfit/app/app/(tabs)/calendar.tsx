import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Brand } from '@/constants/Colors';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

// Placeholder schedule — will be driven by Supabase in Phase 2
const PLACEHOLDER_SCHEDULE: Record<string, { title: string; duration: string } | null> = {
  Mon: { title: 'Full Body - Sculpt + Tone', duration: '25 min' },
  Tue: { title: 'Lower Body - Build', duration: '25 min' },
  Wed: null, // Rest day
  Thu: { title: 'Lower Body - Sculpt', duration: '24 min' },
  Fri: { title: 'Upper Body - Build', duration: '23 min' },
  Sat: { title: 'Upper Body - Sculpt', duration: '24 min' },
  Sun: null, // Rest day
};

export default function CalendarScreen() {
  const today = new Date();
  const todayIndex = today.getDay(); // 0=Sun, 1=Mon, ...
  // Convert to Mon=0 format
  const todayMon = todayIndex === 0 ? 6 : todayIndex - 1;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.weekLabel}>This Week</Text>

      {DAYS.map((day, index) => {
        const workout = PLACEHOLDER_SCHEDULE[day];
        const isToday = index === todayMon;

        return (
          <View
            key={day}
            style={[
              styles.dayRow,
              isToday && styles.dayRowToday,
            ]}>
            <View style={styles.dayLabelContainer}>
              <Text style={[styles.dayLabel, isToday && styles.dayLabelToday]}>
                {day}
              </Text>
              {isToday && <View style={styles.todayDot} />}
            </View>

            <View style={styles.dayContent}>
              {workout ? (
                <>
                  <Text style={[styles.workoutTitle, isToday && styles.textToday]}>
                    {workout.title}
                  </Text>
                  <Text style={styles.workoutDuration}>{workout.duration}</Text>
                </>
              ) : (
                <Text style={styles.restDay}>Rest Day</Text>
              )}
            </View>

            <View style={styles.checkCircle}>
              {/* Will show completion state in Phase 2 */}
            </View>
          </View>
        );
      })}
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
  weekLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: Brand.textLight,
    letterSpacing: 2,
    marginBottom: 16,
  },
  dayRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Brand.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  dayRowToday: {
    borderWidth: 2,
    borderColor: Brand.accent,
  },
  dayLabelContainer: {
    width: 48,
    alignItems: 'center',
  },
  dayLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Brand.textMedium,
  },
  dayLabelToday: {
    color: Brand.accent,
    fontWeight: '700',
  },
  todayDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Brand.accent,
    marginTop: 4,
  },
  dayContent: {
    flex: 1,
    marginLeft: 12,
  },
  workoutTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Brand.textDark,
  },
  textToday: {
    color: Brand.accentDark,
  },
  workoutDuration: {
    fontSize: 13,
    color: Brand.textMedium,
    marginTop: 2,
  },
  restDay: {
    fontSize: 15,
    color: Brand.textLight,
    fontStyle: 'italic',
  },
  checkCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: Brand.blushDark,
    marginLeft: 12,
  },
});
