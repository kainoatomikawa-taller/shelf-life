/**
 * A discrete 5-point scale (0, 0.25, 0.5, 0.75, 1) standing in for a
 * continuous slider — avoids pulling in a native gesture dependency while
 * keeping the same "low to high" interaction the spec calls a slider.
 */

import React from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';

const STEPS = [0, 0.25, 0.5, 0.75, 1] as const;

interface Props {
  label: string;
  lowLabel: string;
  highLabel: string;
  value: number;
  onChange: (value: number) => void;
}

export function SliderScale({
  label,
  lowLabel,
  highLabel,
  value,
  onChange,
}: Props): React.JSX.Element {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.track}>
        {STEPS.map(step => {
          const isSelected = Math.abs(step - value) < 0.01;
          return (
            <TouchableOpacity
              key={step}
              accessibilityRole="button"
              accessibilityLabel={`${label}: ${step}`}
              onPress={() => onChange(step)}
              style={[styles.dot, isSelected && styles.dotSelected]}
            />
          );
        })}
      </View>
      <View style={styles.endLabels}>
        <Text style={styles.endLabel}>{lowLabel}</Text>
        <Text style={styles.endLabel}>{highLabel}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {marginBottom: 20},
  label: {fontSize: 15, fontWeight: '600', marginBottom: 10},
  track: {flexDirection: 'row', justifyContent: 'space-between'},
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
  },
  dotSelected: {backgroundColor: '#2e7d32', borderColor: '#2e7d32'},
  endLabels: {flexDirection: 'row', justifyContent: 'space-between', marginTop: 6},
  endLabel: {fontSize: 12, color: '#888'},
});
