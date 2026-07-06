/**
 * A row of tappable chips for multi-select or single-select choices.
 */

import React from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';

interface Props {
  options: readonly string[];
  selected: readonly string[];
  onToggle: (option: string) => void;
  labelFor?: (option: string) => string;
}

export function ChipToggleGroup({
  options,
  selected,
  onToggle,
  labelFor,
}: Props): React.JSX.Element {
  return (
    <View style={styles.wrap}>
      {options.map(option => {
        const isSelected = selected.includes(option);
        return (
          <TouchableOpacity
            key={option}
            onPress={() => onToggle(option)}
            style={[styles.chip, isSelected && styles.chipSelected]}>
            <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
              {labelFor ? labelFor(option) : option}
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
