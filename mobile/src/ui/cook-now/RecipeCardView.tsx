/**
 * A single Cook Now recipe card (§5.3): expiring / substitution / low-stock
 * badges, with the substitution badge revealing its swap(s) on tap (AC3).
 */

import React, {useState} from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {
  difficultyLabel,
  expiringBadgeText,
  lowStockBadgeText,
  substitutionsBadgeText,
  type RecipeCard,
} from '../../domain/RecipeCard';

interface Props {
  card: RecipeCard;
}

export function RecipeCardView({card}: Props): React.JSX.Element {
  const [swapsRevealed, setSwapsRevealed] = useState(false);
  const {badges} = card;
  const hasSubstitutions = badges.substitutionCount > 0;

  return (
    <View style={styles.card}>
      <Text style={styles.name}>{card.name}</Text>
      <Text style={styles.meta}>
        {card.timeMinutes} min · {difficultyLabel(card.difficulty)}
      </Text>

      <View style={styles.badgeRow}>
        {badges.expiringIngredientName && (
          <View style={[styles.badge, styles.expiringBadge]}>
            <Text style={styles.badgeText}>
              {expiringBadgeText(badges.expiringIngredientName)}
            </Text>
          </View>
        )}
        {badges.lowStockIngredientName && (
          <View style={[styles.badge, styles.lowStockBadge]}>
            <Text style={styles.badgeText}>
              {lowStockBadgeText(badges.lowStockIngredientName)}
            </Text>
          </View>
        )}
        {hasSubstitutions && (
          <TouchableOpacity
            style={[styles.badge, styles.substitutionBadge]}
            onPress={() => setSwapsRevealed(prev => !prev)}>
            <Text style={styles.badgeText}>
              {substitutionsBadgeText(badges.substitutionCount)}{' '}
              {swapsRevealed ? '▲' : '▼'}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {hasSubstitutions && swapsRevealed && (
        <View style={styles.swapList}>
          {card.substitutions.map(swap => (
            <View key={swap.fromIngredientId} style={styles.swapRow}>
              <Text style={styles.swapTitle}>
                Use {swap.toIngredientName} instead of {swap.fromIngredientName}
              </Text>
              {swap.ratioNote && (
                <Text style={styles.swapDetail}>Ratio: {swap.ratioNote}</Text>
              )}
              <Text style={styles.swapDetail}>{swap.disclosure}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#eee',
    backgroundColor: '#fff',
    padding: 14,
    marginBottom: 12,
  },
  name: {fontSize: 17, fontWeight: '700', marginBottom: 2},
  meta: {fontSize: 13, color: '#666', marginBottom: 10},
  badgeRow: {flexDirection: 'row', flexWrap: 'wrap', gap: 6},
  badge: {
    borderRadius: 14,
    paddingVertical: 5,
    paddingHorizontal: 10,
  },
  badgeText: {fontSize: 12, fontWeight: '600'},
  expiringBadge: {backgroundColor: '#fff3e0'},
  lowStockBadge: {backgroundColor: '#fce4ec'},
  substitutionBadge: {backgroundColor: '#eef5ee'},
  swapList: {
    marginTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 10,
    gap: 8,
  },
  swapRow: {gap: 2},
  swapTitle: {fontSize: 13, fontWeight: '700', color: '#2e7d32'},
  swapDetail: {fontSize: 12, color: '#666'},
});
