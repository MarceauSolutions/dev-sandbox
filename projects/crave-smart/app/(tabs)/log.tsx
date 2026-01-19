import { StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { Text, View } from '@/components/Themed';
import { useState } from 'react';

type CravingType = 'sweet' | 'salty' | 'savory' | 'spicy' | 'comfort' | 'fresh' | 'chocolate' | 'carbs';

const CRAVING_OPTIONS: { type: CravingType; emoji: string; label: string }[] = [
  { type: 'chocolate', emoji: '🍫', label: 'Chocolate' },
  { type: 'sweet', emoji: '🍰', label: 'Sweet' },
  { type: 'salty', emoji: '🧂', label: 'Salty' },
  { type: 'savory', emoji: '🍖', label: 'Savory' },
  { type: 'spicy', emoji: '🌶️', label: 'Spicy' },
  { type: 'comfort', emoji: '🍜', label: 'Comfort' },
  { type: 'fresh', emoji: '🥗', label: 'Fresh' },
  { type: 'carbs', emoji: '🍝', label: 'Carbs' },
];

const SATISFACTION_OPTIONS = [
  { value: 1, emoji: '😞', label: 'Not satisfied' },
  { value: 2, emoji: '😐', label: 'Meh' },
  { value: 3, emoji: '🙂', label: 'Okay' },
  { value: 4, emoji: '😊', label: 'Good' },
  { value: 5, emoji: '😍', label: 'Perfect!' },
];

export default function LogScreen() {
  const [selectedCravings, setSelectedCravings] = useState<CravingType[]>([]);
  const [satisfaction, setSatisfaction] = useState<number | null>(null);
  const [foodDescription, setFoodDescription] = useState('');
  const [restaurantName, setRestaurantName] = useState('');

  const toggleCraving = (type: CravingType) => {
    if (selectedCravings.includes(type)) {
      setSelectedCravings(selectedCravings.filter(c => c !== type));
    } else {
      setSelectedCravings([...selectedCravings, type]);
    }
  };

  const canSubmit = selectedCravings.length > 0 && satisfaction !== null;

  const handleSubmit = () => {
    // TODO: Save to database
    console.log({
      selectedCravings,
      satisfaction,
      foodDescription,
      restaurantName,
      timestamp: new Date(),
    });

    // Reset form
    setSelectedCravings([]);
    setSatisfaction(null);
    setFoodDescription('');
    setRestaurantName('');

    // Show success feedback
    alert('Logged! This helps us learn your patterns.');
  };

  return (
    <ScrollView style={styles.scrollView}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>What did you eat?</Text>
          <Text style={styles.subtitle}>
            Logging meals helps us predict your cravings better
          </Text>
        </View>

        {/* Food description */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What was it?</Text>
          <TextInput
            style={styles.textInput}
            placeholder="e.g., Pad Thai from Thai Place"
            placeholderTextColor="rgba(150, 150, 150, 0.6)"
            value={foodDescription}
            onChangeText={setFoodDescription}
          />
        </View>

        {/* Restaurant (optional) */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Where from? (optional)</Text>
          <TextInput
            style={styles.textInput}
            placeholder="Restaurant name"
            placeholderTextColor="rgba(150, 150, 150, 0.6)"
            value={restaurantName}
            onChangeText={setRestaurantName}
          />
        </View>

        {/* Craving types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What kind of craving was this?</Text>
          <Text style={styles.sectionHint}>Select all that apply</Text>
          <View style={styles.cravingGrid}>
            {CRAVING_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.type}
                style={[
                  styles.cravingOption,
                  selectedCravings.includes(option.type) && styles.cravingOptionSelected,
                ]}
                onPress={() => toggleCraving(option.type)}
              >
                <Text style={styles.cravingEmoji}>{option.emoji}</Text>
                <Text style={[
                  styles.cravingLabel,
                  selectedCravings.includes(option.type) && styles.cravingLabelSelected,
                ]}>
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Satisfaction */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>How satisfied were you?</Text>
          <View style={styles.satisfactionRow}>
            {SATISFACTION_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={[
                  styles.satisfactionOption,
                  satisfaction === option.value && styles.satisfactionOptionSelected,
                ]}
                onPress={() => setSatisfaction(option.value)}
              >
                <Text style={styles.satisfactionEmoji}>{option.emoji}</Text>
                <Text style={[
                  styles.satisfactionLabel,
                  satisfaction === option.value && styles.satisfactionLabelSelected,
                ]}>
                  {option.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Submit button */}
        <TouchableOpacity
          style={[styles.submitButton, !canSubmit && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={!canSubmit}
        >
          <Text style={styles.submitButtonText}>Log This Meal</Text>
        </TouchableOpacity>

        {/* Tip */}
        <View style={styles.tipContainer}>
          <Text style={styles.tipText}>
            💡 Tip: The more you log, the better your predictions become.
            Try logging at least one meal a day for a week to see patterns emerge.
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
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  sectionHint: {
    fontSize: 12,
    opacity: 0.5,
    marginBottom: 12,
  },
  textInput: {
    borderWidth: 1,
    borderColor: 'rgba(150, 150, 150, 0.3)',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
  },
  cravingGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  cravingOption: {
    width: '23%',
    aspectRatio: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cravingOptionSelected: {
    backgroundColor: 'rgba(255, 107, 107, 0.15)',
    borderColor: '#FF6B6B',
  },
  cravingEmoji: {
    fontSize: 28,
    marginBottom: 4,
  },
  cravingLabel: {
    fontSize: 11,
    opacity: 0.7,
  },
  cravingLabelSelected: {
    opacity: 1,
    fontWeight: '600',
    color: '#FF6B6B',
  },
  satisfactionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  satisfactionOption: {
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    flex: 1,
    marginHorizontal: 2,
    backgroundColor: 'rgba(150, 150, 150, 0.1)',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  satisfactionOptionSelected: {
    backgroundColor: 'rgba(255, 107, 107, 0.15)',
    borderColor: '#FF6B6B',
  },
  satisfactionEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  satisfactionLabel: {
    fontSize: 10,
    opacity: 0.6,
    textAlign: 'center',
  },
  satisfactionLabelSelected: {
    opacity: 1,
    fontWeight: '600',
    color: '#FF6B6B',
  },
  submitButton: {
    backgroundColor: '#FF6B6B',
    paddingVertical: 18,
    borderRadius: 30,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonDisabled: {
    backgroundColor: 'rgba(150, 150, 150, 0.3)',
  },
  submitButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  tipContainer: {
    marginTop: 24,
    padding: 16,
    backgroundColor: 'rgba(100, 150, 200, 0.1)',
    borderRadius: 12,
  },
  tipText: {
    fontSize: 13,
    lineHeight: 18,
    opacity: 0.8,
  },
});
