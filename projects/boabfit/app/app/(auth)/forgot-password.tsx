import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '@/lib/AuthContext';
import { Brand } from '@/constants/Colors';

export default function ForgotPasswordScreen() {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    if (!email) {
      Alert.alert('Missing email', 'Please enter your email address.');
      return;
    }

    setLoading(true);
    const { error } = await resetPassword(email.trim().toLowerCase());
    setLoading(false);

    if (error) {
      Alert.alert('Error', error.message);
    } else {
      Alert.alert(
        'Check your email',
        'If an account exists with that email, we sent a password reset link.',
        [{ text: 'OK', onPress: () => router.back() }]
      );
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.inner}>
        <Text style={styles.title}>Reset Password</Text>
        <Text style={styles.subtitle}>
          Enter your email and we'll send you a link to reset your password.
        </Text>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={Brand.textLight}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleReset}
            disabled={loading}>
            {loading ? (
              <ActivityIndicator color={Brand.textWhite} />
            ) : (
              <Text style={styles.buttonText}>Send Reset Link</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkButton}
            onPress={() => router.back()}>
            <Text style={styles.linkText}>Back to Login</Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Brand.blush,
  },
  inner: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Brand.textDark,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: Brand.textMedium,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 32,
    lineHeight: 20,
  },
  form: {
    gap: 16,
  },
  input: {
    backgroundColor: Brand.white,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Brand.textDark,
    borderWidth: 1,
    borderColor: Brand.blushDark,
  },
  button: {
    backgroundColor: Brand.accent,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: Brand.textWhite,
    fontSize: 18,
    fontWeight: '700',
  },
  linkButton: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  linkText: {
    color: Brand.accentDark,
    fontSize: 14,
  },
});
