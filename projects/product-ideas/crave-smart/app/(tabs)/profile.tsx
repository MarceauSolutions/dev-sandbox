import { StyleSheet, ScrollView, TouchableOpacity, Switch, Alert } from 'react-native';
import { Text, View } from '@/components/Themed';
import { useState } from 'react';

// Mock user data
const MOCK_USER = {
  displayName: 'Sarah',
  email: 'sarah@example.com',
  isPremium: false,
  cycleTrackingEnabled: true,
  partnerSharingEnabled: false,
  notificationsEnabled: true,
  averageCycleLength: 28,
  dataSource: 'apple_health' as const,
};

export default function ProfileScreen() {
  const [cycleTracking, setCycleTracking] = useState(MOCK_USER.cycleTrackingEnabled);
  const [partnerSharing, setPartnerSharing] = useState(MOCK_USER.partnerSharingEnabled);
  const [notifications, setNotifications] = useState(MOCK_USER.notificationsEnabled);

  const handleUpgrade = () => {
    Alert.alert(
      'Upgrade to Premium',
      'Get partner sharing, unlimited pattern history, and priority support for $5.99/month.',
      [
        { text: 'Maybe Later', style: 'cancel' },
        { text: 'Upgrade', onPress: () => console.log('Open payment flow') },
      ]
    );
  };

  const handleConnectHealthKit = () => {
    Alert.alert(
      'Connect Apple Health',
      'CraveSmart will read your menstrual cycle data to improve predictions. Your data stays on your device.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Connect', onPress: () => console.log('Request HealthKit permissions') },
      ]
    );
  };

  const handleInvitePartner = () => {
    if (!MOCK_USER.isPremium) {
      Alert.alert(
        'Premium Feature',
        'Partner sharing lets your significant other see your daily cravings. Upgrade to unlock.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Upgrade', onPress: handleUpgrade },
        ]
      );
      return;
    }
    Alert.alert('Invite Partner', 'Share link copied! Send to your partner.');
  };

  return (
    <ScrollView style={styles.scrollView}>
      <View style={styles.container}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {MOCK_USER.displayName.charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text style={styles.displayName}>{MOCK_USER.displayName}</Text>
          <Text style={styles.email}>{MOCK_USER.email}</Text>
          {!MOCK_USER.isPremium && (
            <TouchableOpacity style={styles.upgradeButton} onPress={handleUpgrade}>
              <Text style={styles.upgradeButtonText}>Upgrade to Premium</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Cycle Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Cycle Tracking</Text>

          <TouchableOpacity style={styles.settingRow} onPress={handleConnectHealthKit}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Data Source</Text>
              <Text style={styles.settingValue}>
                {MOCK_USER.dataSource === 'apple_health' ? 'Apple Health' : 'Manual Entry'}
              </Text>
            </View>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Average Cycle Length</Text>
              <Text style={styles.settingValue}>{MOCK_USER.averageCycleLength} days</Text>
            </View>
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Use Cycle for Predictions</Text>
              <Text style={styles.settingDescription}>
                Improve accuracy with cycle-aware predictions
              </Text>
            </View>
            <Switch
              value={cycleTracking}
              onValueChange={setCycleTracking}
              trackColor={{ false: '#767577', true: '#FF6B6B' }}
              thumbColor="#fff"
            />
          </View>
        </View>

        {/* Partner Sharing */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Partner Sharing</Text>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Share Predictions</Text>
              <Text style={styles.settingDescription}>
                Let your partner see today's cravings
              </Text>
            </View>
            <Switch
              value={partnerSharing}
              onValueChange={(value) => {
                if (!MOCK_USER.isPremium && value) {
                  handleInvitePartner();
                  return;
                }
                setPartnerSharing(value);
              }}
              trackColor={{ false: '#767577', true: '#FF6B6B' }}
              thumbColor="#fff"
            />
          </View>

          <TouchableOpacity style={styles.settingRow} onPress={handleInvitePartner}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Invite Partner</Text>
              <Text style={styles.settingValue}>
                {MOCK_USER.isPremium ? 'Send invite link' : 'Premium feature'}
              </Text>
            </View>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>
        </View>

        {/* Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Daily Predictions</Text>
              <Text style={styles.settingDescription}>
                Get notified of your predicted cravings each morning
              </Text>
            </View>
            <Switch
              value={notifications}
              onValueChange={setNotifications}
              trackColor={{ false: '#767577', true: '#FF6B6B' }}
              thumbColor="#fff"
            />
          </View>
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>

          <TouchableOpacity style={styles.settingRow}>
            <Text style={styles.settingLabel}>Privacy Policy</Text>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingRow}>
            <Text style={styles.settingLabel}>Terms of Service</Text>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingRow}>
            <Text style={styles.settingLabel}>How It Works</Text>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>

          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Version</Text>
            <Text style={styles.settingValue}>0.1.0</Text>
          </View>
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutButton}>
          <Text style={styles.logoutButtonText}>Sign Out</Text>
        </TouchableOpacity>

        <Text style={styles.footer}>
          Made with science and love
        </Text>
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
  profileHeader: {
    alignItems: 'center',
    marginBottom: 32,
    paddingTop: 20,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#FF6B6B',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  displayName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    opacity: 0.6,
    marginBottom: 16,
  },
  upgradeButton: {
    backgroundColor: '#FF6B6B',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
  },
  upgradeButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    opacity: 0.5,
    textTransform: 'uppercase',
    marginBottom: 8,
    paddingLeft: 4,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
    borderRadius: 12,
    marginBottom: 8,
  },
  settingInfo: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingValue: {
    fontSize: 14,
    opacity: 0.6,
    marginTop: 2,
  },
  settingDescription: {
    fontSize: 12,
    opacity: 0.5,
    marginTop: 2,
  },
  chevron: {
    fontSize: 20,
    opacity: 0.4,
    marginLeft: 8,
  },
  logoutButton: {
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  logoutButtonText: {
    color: '#FF6B6B',
    fontSize: 16,
    fontWeight: '500',
  },
  footer: {
    textAlign: 'center',
    fontSize: 12,
    opacity: 0.4,
    marginTop: 24,
  },
});
