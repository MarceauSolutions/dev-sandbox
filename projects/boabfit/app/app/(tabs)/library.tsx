import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Brand } from '@/constants/Colors';

const MUSCLE_GROUPS = [
  { name: 'Glutes', icon: '🍑', count: 12 },
  { name: 'Legs', icon: '🦵', count: 15 },
  { name: 'Arms', icon: '💪', count: 10 },
  { name: 'Core', icon: '🔥', count: 8 },
  { name: 'Back', icon: '🏋️', count: 9 },
  { name: 'Full Body', icon: '⚡', count: 6 },
];

export default function LibraryScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.sectionTitle}>EXERCISE LIBRARY</Text>
      <Text style={styles.subtitle}>
        Browse exercises by muscle group. Videos coming soon!
      </Text>

      <View style={styles.grid}>
        {MUSCLE_GROUPS.map((group) => (
          <View key={group.name} style={styles.groupCard}>
            <Text style={styles.groupIcon}>{group.icon}</Text>
            <Text style={styles.groupName}>{group.name}</Text>
            <Text style={styles.groupCount}>{group.count} exercises</Text>
          </View>
        ))}
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
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Brand.textLight,
    letterSpacing: 2,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Brand.textMedium,
    marginBottom: 24,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  groupCard: {
    width: '47%',
    backgroundColor: Brand.white,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  groupIcon: {
    fontSize: 36,
    marginBottom: 8,
  },
  groupName: {
    fontSize: 16,
    fontWeight: '600',
    color: Brand.textDark,
  },
  groupCount: {
    fontSize: 12,
    color: Brand.textMedium,
    marginTop: 4,
  },
});
