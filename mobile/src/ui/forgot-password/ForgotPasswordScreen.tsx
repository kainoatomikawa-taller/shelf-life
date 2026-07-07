/**
 * Forgot-password screen: a single username-or-email input against the
 * "forgot-password" edge function. Always ends on the same confirmation
 * message, whether or not the identifier matched an account, so the flow
 * never reveals account existence. Setting the new password itself happens
 * on the link Supabase emails, outside the app.
 */

import React from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {useForgotPassword} from './useForgotPassword';

interface Props {
  onBackToLogin: () => void;
}

export function ForgotPasswordScreen({onBackToLogin}: Props): React.JSX.Element {
  const {identifier, setIdentifier, submitting, error, submitted, canSubmit, submit} =
    useForgotPassword();

  if (submitted) {
    return (
      <View style={styles.content}>
        <Text style={styles.title}>Check your email</Text>
        <Text style={styles.subtitle}>
          If that username or email matches an account, we've sent a link to reset
          your password.
        </Text>
        <TouchableOpacity style={styles.switchLink} onPress={onBackToLogin}>
          <Text style={styles.switchLinkText}>Back to log in</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.content}>
        <Text style={styles.title}>Forgot password?</Text>
        <Text style={styles.subtitle}>
          Enter your username or email and we'll send you a reset link.
        </Text>

        <TextInput
          value={identifier}
          onChangeText={setIdentifier}
          placeholder="Username or email"
          style={styles.input}
          autoCapitalize="none"
          autoCorrect={false}
          editable={!submitting}
          onSubmitEditing={() => void submit()}
        />

        {error && <Text style={styles.error}>{error}</Text>}

        <TouchableOpacity
          style={[styles.button, !canSubmit && styles.buttonDisabled]}
          disabled={!canSubmit}
          onPress={() => void submit()}>
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Send reset link</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.switchLink}
          onPress={onBackToLogin}
          disabled={submitting}>
          <Text style={styles.switchLinkText}>Back to log in</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#fff'},
  content: {flex: 1, justifyContent: 'center', padding: 24},
  title: {fontSize: 32, fontWeight: '700', textAlign: 'center'},
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 32,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    marginBottom: 12,
  },
  error: {color: '#c62828', marginBottom: 12},
  button: {
    marginTop: 8,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: '#2e7d32',
  },
  buttonDisabled: {backgroundColor: '#a5c9a8'},
  buttonText: {color: '#fff', fontWeight: '700', fontSize: 16},
  switchLink: {marginTop: 20, alignItems: 'center'},
  switchLinkText: {color: '#2e7d32', fontSize: 14, fontWeight: '600'},
});
