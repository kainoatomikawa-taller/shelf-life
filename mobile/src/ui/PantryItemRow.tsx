import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import {freshnessColor, type PantryItem} from '../domain/PantryItem';

interface Props {
  item: PantryItem;
}

export function PantryItemRow({item}: Props): React.JSX.Element {
  return (
    <View style={styles.row}>
      <View
        style={[styles.dot, {backgroundColor: freshnessColor(item.freshnessStatus)}]}
      />
      <View style={styles.info}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.meta}>
          {item.amount} {item.unit} · expires {item.expirationDate}
        </Text>
      </View>
      <Text style={styles.days}>
        {item.daysUntilExpiration >= 0
          ? `${item.daysUntilExpiration}d`
          : 'expired'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {flexDirection: 'row', alignItems: 'center', paddingVertical: 12},
  dot: {width: 12, height: 12, borderRadius: 6, marginRight: 12},
  info: {flex: 1},
  name: {fontSize: 16, fontWeight: '600'},
  meta: {fontSize: 12, color: '#666', marginTop: 2},
  days: {fontSize: 14, color: '#333'},
});
