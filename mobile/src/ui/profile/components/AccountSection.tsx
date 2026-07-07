/**
 * Editable display_name and username (§6 AC1-5). Each field has its own
 * Save button, saving indicator, and error message so a username conflict
 * never blocks or gets confused with a display_name edit.
 */

import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

interface FieldProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  onSave: () => void;
  saving: boolean;
  error: string | null;
  autoCapitalize?: 'none' | 'words';
}

function EditableField({
  label,
  value,
  onChangeText,
  onSave,
  saving,
  error,
  autoCapitalize = 'words',
}: FieldProps): React.JSX.Element {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.row}>
        <TextInput
          value={value}
          onChangeText={onChangeText}
          style={styles.input}
          autoCapitalize={autoCapitalize}
          autoCorrect={false}
          editable={!saving}
        />
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          disabled={saving}
          onPress={onSave}>
          {saving ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.saveButtonText}>Save</Text>
          )}
        </TouchableOpacity>
      </View>
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

interface Props {
  displayName: string;
  onChangeDisplayName: (text: string) => void;
  onSaveDisplayName: () => void;
  savingDisplayName: boolean;
  displayNameError: string | null;
  username: string;
  onChangeUsername: (text: string) => void;
  onSaveUsername: () => void;
  savingUsername: boolean;
  usernameError: string | null;
}

export function AccountSection({
  displayName,
  onChangeDisplayName,
  onSaveDisplayName,
  savingDisplayName,
  displayNameError,
  username,
  onChangeUsername,
  onSaveUsername,
  savingUsername,
  usernameError,
}: Props): React.JSX.Element {
  return (
    <View>
      <EditableField
        label="Display name"
        value={displayName}
        onChangeText={onChangeDisplayName}
        onSave={onSaveDisplayName}
        saving={savingDisplayName}
        error={displayNameError}
        autoCapitalize="words"
      />
      <EditableField
        label="Username"
        value={username}
        onChangeText={onChangeUsername}
        onSave={onSaveUsername}
        saving={savingUsername}
        error={usernameError}
        autoCapitalize="none"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  field: {marginBottom: 16},
  label: {fontSize: 13, fontWeight: '600', color: '#555', marginBottom: 6},
  row: {flexDirection: 'row', alignItems: 'center'},
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    marginRight: 8,
  },
  saveButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#2e7d32',
    minWidth: 64,
    alignItems: 'center',
  },
  saveButtonDisabled: {backgroundColor: '#a5c9a8'},
  saveButtonText: {color: '#fff', fontWeight: '700'},
  error: {color: '#c62828', fontSize: 13, marginTop: 6},
});
