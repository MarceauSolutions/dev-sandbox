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
import { Link } from 'expo-router';
import { useAuth } from '@/lib/AuthContext';
import { Brand } from '@/constants/Colors';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Missing fields', 'Please enter your email and password.');
      return;
    }

    setLoading(true);
    const { error } = await signIn(email.trim().toLowerCase(), password);
    setLoading(false);

    if (error) {
      Alert.alert('Login failed', error.message);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.inner}>
        <Text style={styles.logo}>BOABFIT</Text>
        <Text style={styles.tagline}>Embrace the Burn</Text>

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
          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor={Brand.textLight}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoComplete="password"
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}>
            {loading ? (
              <ActivityIndicator color={Brand.textWhite} />
            ) : (
              <Text style={styles.buttonText}>Log In</Text>
            )}
          </TouchableOpacity>

          <Link href="/(auth)/forgot-password" asChild>
            <TouchableOpacity style={styles.linkButton}>
              <Text style={styles.linkText}>Forgot password?</Text>
            </TouchableOpacity>
          </Link>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Don't have an account? </Text>
          <Link href="/(auth)/signup" asChild>
            <TouchableOpacity>
              <Text style={styles.footerLink}>Sign Up</Text>
            </TouchableOpacity>
          </Link>
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
  logo: {
    fontSize: 48,
    fontWeight: '800',
    color: Brand.textDark,
    textAlign: 'center',
    letterSpacing: 4,
  },
  tagline: {
    fontSize: 16,
    color: Brand.textMedium,
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 48,
    letterSpacing: 1,
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
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 32,
  },
  footerText: {
    color: Brand.textMedium,
    fontSize: 14,
  },
  footerLink: {
    color: Brand.accent,
    fontSize: 14,
    fontWeight: '600',
  },
});
