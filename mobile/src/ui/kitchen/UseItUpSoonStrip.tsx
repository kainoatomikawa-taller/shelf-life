/**
 * "Use it up soon" strip (§5.2): a top-of-Kitchen shelf for items in Use
 * soon / Use now, each one tap away from matching Cook Now recipes — the
 * point where inventory meets recipes.
 */

import React from 'react';
import {ScrollView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {freshnessStatusColor, freshnessStatusLabel} from '../../domain/InventoryItem';
import type {InventoryItem} from '../../domain/InventoryItem';

interface Props {
  items: readonly InventoryItem[];
  onCookNow: (item: InventoryItem) => void;
}

export function UseItUpSoonStrip({items, onCookNow}: Props): React.JSX.Element | null {
  if (items.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Use it up soon</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}>
        {items.map(item => (
          <TouchableOpacity
            key={item.id}
            style={styles.card}
            onPress={() => onCookNow(item)}>
            <View style={styles.statusRow}>
              <View
                style={[
                  styles.dot,
                  {backgroundColor: freshnessStatusColor(item.freshnessStatus)},
                ]}
              />
              <Text style={styles.statusLabel}>
                {freshnessStatusLabel(item.freshnessStatus)}
              </Text>
            </View>
            <Text style={styles.name} numberOfLines={1}>
              {item.ingredientName}
            </Text>
            <Text style={styles.cookNowLink}>Cook Now →</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {marginBottom: 16},
  title: {fontSize: 13, fontWeight: '700', color: '#666', marginBottom: 8},
  scrollContent: {gap: 10, paddingRight: 8},
  card: {
    width: 132,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#eee',
    backgroundColor: '#fafafa',
    padding: 12,
  },
  statusRow: {flexDirection: 'row', alignItems: 'center', marginBottom: 6},
  dot: {width: 8, height: 8, borderRadius: 4, marginRight: 6},
  statusLabel: {fontSize: 11, color: '#555', fontWeight: '600'},
  name: {fontSize: 15, fontWeight: '700', marginBottom: 10},
  cookNowLink: {fontSize: 12, color: '#2e7d32', fontWeight: '700'},
});
