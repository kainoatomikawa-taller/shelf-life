/**
 * A row of one-tap chips for a single-select choice, e.g. storage location
 * or quantity state (§5.2) — unlike ChipToggleGroup, picking a chip always
 * replaces the current selection rather than toggling membership.
 */

import React from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';

interface Props<T extends string> {
  options: readonly T[];
  selected: T;
  onSelect: (option: T) => void;
  labelFor: (option: T) => string;
}

export function SingleSelectChips<T extends string>({
  options,
  selected,
  onSelect,
  labelFor,
}: Props<T>): React.JSX.Element {
  return (
    <View style={styles.wrap}>
      {options.map(option => {
        const isSelected = option === selected;
        return (
          <TouchableOpacity
            key={option}
            onPress={() => onSelect(option)}
            style={[styles.chip, isSelected && styles.chipSelected]}>
            <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
              {labelFor(option)}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {flexDirection: 'row', flexWrap: 'wrap', gap: 8},
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
  },
  chipSelected: {backgroundColor: '#2e7d32', borderColor: '#2e7d32'},
  chipText: {color: '#333', fontSize: 14},
  chipTextSelected: {color: '#fff', fontWeight: '600'},
});
