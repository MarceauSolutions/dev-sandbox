import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Brand } from '@/constants/Colors';
import { useAuth } from '@/lib/AuthContext';

export default function ProfileScreen() {
  const { user, signOut } = useAuth();

  const displayName =
    user?.user_metadata?.display_name ||
    user?.email?.split('@')[0] ||
    'User';

  const handleSignOut = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: signOut },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Profile Header */}
      <View style={styles.header}>
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarText}>
            {displayName.charAt(0).toUpperCase()}
          </Text>
        </View>
        <Text style={styles.name}>{displayName}</Text>
        <Text style={styles.email}>{user?.email}</Text>
      </View>

      {/* Stats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>MY STATS</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>0</Text>
            <Text style={styles.statLabel}>Total Workouts</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>0</Text>
            <Text style={styles.statLabel}>Current Streak</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>--</Text>
            <Text style={styles.statLabel}>Best Streak</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>--</Text>
            <Text style={styles.statLabel}>Member Since</Text>
          </View>
        </View>
      </View>

      {/* Workout History Placeholder */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>RECENT WORKOUTS</Text>
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>🏋️‍♀️</Text>
          <Text style={styles.emptyText}>
            Complete your first workout to see it here!
          </Text>
        </View>
      </View>

      {/* Sign Out */}
      <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
        <Text style={styles.signOutText}>Sign Out</Text>
      </TouchableOpacity>
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
  header: {
    alignItems: 'center',
    marginBottom: 32,
    marginTop: 12,
  },
  avatarCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Brand.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
    color: Brand.textWhite,
  },
  name: {
    fontSize: 22,
    fontWeight: '700',
    color: Brand.textDark,
  },
  email: {
    fontSize: 14,
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
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statItem: {
    width: '47%',
    backgroundColor: Brand.white,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 22,
    fontWeight: '700',
    color: Brand.accent,
  },
  statLabel: {
    fontSize: 12,
    color: Brand.textMedium,
    marginTop: 4,
  },
  emptyState: {
    backgroundColor: Brand.white,
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  emptyEmoji: {
    fontSize: 40,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 14,
    color: Brand.textMedium,
    textAlign: 'center',
  },
  signOutButton: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Brand.blushDark,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 12,
  },
  signOutText: {
    color: Brand.textMedium,
    fontSize: 16,
    fontWeight: '500',
  },
});
