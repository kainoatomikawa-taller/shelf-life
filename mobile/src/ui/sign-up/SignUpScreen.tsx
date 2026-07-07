/**
 * Sign-up screen: collects name, username, email, password, and
 * confirmation, validates them client-side, then submits to the
 * sign-up-with-username edge function. Routes into onboarding on success.
 */

import React from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
} from 'react-native';
import type {AuthUser} from '../../domain/Auth';
import {useSignUp} from './useSignUp';

interface Props {
  onSignedUp: (user: AuthUser) => void;
  onSwitchToLogin: () => void;
}

export function SignUpScreen({onSignedUp, onSwitchToLogin}: Props): React.JSX.Element {
  const {
    name,
    setName,
    username,
    setUsername,
    email,
    setEmail,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    fieldErrors,
    submitting,
    serverError,
    canSubmit,
    submit,
  } = useSignUp(onSignedUp);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Shelf Life</Text>
        <Text style={styles.subtitle}>Create your account</Text>

        <TextInput
          value={name}
          onChangeText={setName}
          placeholder="Name"
          style={styles.input}
          autoCorrect={false}
          editable={!submitting}
        />
        {fieldErrors.name && <Text style={styles.fieldError}>{fieldErrors.name}</Text>}

        <TextInput
          value={username}
          onChangeText={setUsername}
          placeholder="Username"
          style={styles.input}
          autoCapitalize="none"
          autoCorrect={false}
          editable={!submitting}
        />
        {fieldErrors.username && <Text style={styles.fieldError}>{fieldErrors.username}</Text>}

        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="Email"
          style={styles.input}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          editable={!submitting}
        />
        {fieldErrors.email && <Text style={styles.fieldError}>{fieldErrors.email}</Text>}

        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="Password"
          style={styles.input}
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
          editable={!submitting}
        />
        {fieldErrors.password && <Text style={styles.fieldError}>{fieldErrors.password}</Text>}

        <TextInput
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          placeholder="Confirm password"
          style={styles.input}
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
          editable={!submitting}
          onSubmitEditing={() => void submit()}
        />
        {fieldErrors.confirmPassword && (
          <Text style={styles.fieldError}>{fieldErrors.confirmPassword}</Text>
        )}

        {serverError && <Text style={styles.error}>{serverError}</Text>}

        <TouchableOpacity
          style={[styles.button, !canSubmit && styles.buttonDisabled]}
          disabled={!canSubmit}
          onPress={() => void submit()}>
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Sign up</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.switchLink} onPress={onSwitchToLogin} disabled={submitting}>
          <Text style={styles.switchLinkText}>Already have an account? Log in</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#fff'},
  content: {flexGrow: 1, justifyContent: 'center', padding: 24},
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
    marginBottom: 4,
  },
  fieldError: {color: '#c62828', fontSize: 13, marginBottom: 8},
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
