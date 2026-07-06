/**
 * Free-text entry for adding arbitrary tags (e.g. a dish not in the curated
 * list), rendered alongside the tags already selected.
 */

import React, {useState} from 'react';
import {StyleSheet, Text, TextInput, TouchableOpacity, View} from 'react-native';

interface Props {
  tags: readonly string[];
  onAdd: (tag: string) => void;
  onRemove: (tag: string) => void;
  placeholder: string;
}

export function TagInput({
  tags,
  onAdd,
  onRemove,
  placeholder,
}: Props): React.JSX.Element {
  const [draft, setDraft] = useState('');

  const submit = () => {
    const trimmed = draft.trim();
    if (trimmed) {
      onAdd(trimmed);
    }
    setDraft('');
  };

  return (
    <View>
      <View style={styles.row}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          onSubmitEditing={submit}
          placeholder={placeholder}
          style={styles.input}
          returnKeyType="done"
        />
        <TouchableOpacity onPress={submit} style={styles.addButton}>
          <Text style={styles.addButtonText}>Add</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.tagWrap}>
        {tags.map(tag => (
          <TouchableOpacity
            key={tag}
            onPress={() => onRemove(tag)}
            style={styles.tag}>
            <Text style={styles.tagText}>{tag} ×</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {flexDirection: 'row', gap: 8, marginBottom: 10},
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  addButton: {
    paddingHorizontal: 16,
    justifyContent: 'center',
    backgroundColor: '#2e7d32',
    borderRadius: 8,
  },
  addButtonText: {color: '#fff', fontWeight: '600'},
  tagWrap: {flexDirection: 'row', flexWrap: 'wrap', gap: 8},
  tag: {
    backgroundColor: '#eef5ee',
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  tagText: {color: '#2e7d32', fontSize: 13},
});
