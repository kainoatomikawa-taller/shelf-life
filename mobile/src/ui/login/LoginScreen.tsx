/**
 * Login screen: username + password against the login-with-username edge
 * function. Routes into the authenticated app on success.
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
import type {AuthUser} from '../../domain/Auth';
import {useLogin} from './useLogin';

interface Props {
  onLoggedIn: (user: AuthUser) => void;
  onSwitchToSignUp: () => void;
}

export function LoginScreen({onLoggedIn, onSwitchToSignUp}: Props): React.JSX.Element {
  const {
    username,
    setUsername,
    password,
    setPassword,
    submitting,
    error,
    canSubmit,
    submit,
  } = useLogin(onLoggedIn);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.content}>
        <Text style={styles.title}>Shelf Life</Text>
        <Text style={styles.subtitle}>Sign in to continue</Text>

        <TextInput
          value={username}
          onChangeText={setUsername}
          placeholder="Username"
          style={styles.input}
          autoCapitalize="none"
          autoCorrect={false}
          editable={!submitting}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="Password"
          style={styles.input}
          secureTextEntry
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
            <Text style={styles.buttonText}>Log in</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.switchLink}
          onPress={onSwitchToSignUp}
          disabled={submitting}>
          <Text style={styles.switchLinkText}>Don't have an account? Sign up</Text>
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
