/**
 * Read-only view of the derived taste vector — the record of how the
 * user's ratings history has shaped their flavor preferences over time.
 * Never editable directly: it only moves as recipes are rated (§4.6).
 */

import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import type {FlavorDimension, FlavorProfile} from '../../../domain/UserProfile';

const DIMENSION_LABELS: Record<FlavorDimension, string> = {
  sweetness: 'Sweetness',
  saltiness: 'Saltiness',
  sourness: 'Sourness',
  bitterness: 'Bitterness',
  spiciness: 'Spiciness',
  umami: 'Umami',
};

const DIMENSIONS = Object.keys(DIMENSION_LABELS) as FlavorDimension[];

interface Props {
  tasteVector: FlavorProfile;
}

export function TasteVectorHistory({tasteVector}: Props): React.JSX.Element {
  return (
    <View>
      {DIMENSIONS.map(dimension => {
        const value = tasteVector[dimension];
        return (
          <View key={dimension} style={styles.row}>
            <Text style={styles.label}>{DIMENSION_LABELS[dimension]}</Text>
            <View style={styles.track}>
              <View style={[styles.fill, {width: `${value * 100}%`}]} />
            </View>
          </View>
        );
      })}
      <Text style={styles.hint}>
        Updates automatically as you rate recipes — it isn't something you set
        directly.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {marginBottom: 12},
  label: {fontSize: 13, color: '#333', marginBottom: 4},
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: '#eee',
    overflow: 'hidden',
  },
  fill: {height: 8, borderRadius: 4, backgroundColor: '#2e7d32'},
  hint: {fontSize: 12, color: '#888', marginTop: 8, fontStyle: 'italic'},
});
