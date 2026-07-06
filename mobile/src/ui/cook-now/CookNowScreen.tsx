/**
 * Cook Now (§5.2) — recipe matching isn't built yet, so this is a minimal
 * landing spot for the "Use it up soon" strip's shortcut: it shows which
 * ingredient the results would be filtered by once Cook Now exists, rather
 * than fabricating recipe data.
 */

import React from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';

interface Props {
  filterIngredientName: string;
  onBack: () => void;
}

export function CookNowScreen({
  filterIngredientName,
  onBack,
}: Props): React.JSX.Element {
  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={onBack} style={styles.backButton}>
        <Text style={styles.backText}>‹ Kitchen</Text>
      </TouchableOpacity>

      <Text style={styles.title}>Cook Now</Text>

      <View style={styles.filterChip}>
        <Text style={styles.filterChipText}>Using: {filterIngredientName}</Text>
      </View>

      <View style={styles.emptyState}>
        <Text style={styles.emptyTitle}>Recipe matching is coming soon</Text>
        <Text style={styles.emptyBody}>
          Once Cook Now is ready, this will show recipes that use your{' '}
          {filterIngredientName}, so it doesn't go to waste.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 20, paddingTop: 12},
  backButton: {marginBottom: 12, alignSelf: 'flex-start'},
  backText: {color: '#2e7d32', fontWeight: '600', fontSize: 15},
  title: {fontSize: 28, fontWeight: '700', marginBottom: 16},
  filterChip: {
    alignSelf: 'flex-start',
    backgroundColor: '#eef5ee',
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 14,
    marginBottom: 24,
  },
  filterChipText: {color: '#2e7d32', fontWeight: '600', fontSize: 13},
  emptyState: {
    backgroundColor: '#fafafa',
    borderRadius: 12,
    padding: 20,
  },
  emptyTitle: {fontSize: 16, fontWeight: '700', marginBottom: 8},
  emptyBody: {fontSize: 14, color: '#666', lineHeight: 20},
});
