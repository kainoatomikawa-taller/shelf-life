/**
 * A single Discover recipe card (§5.4): what you'd need to shop for, shown
 * as an ingredients-on-hand count.
 */

import React from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {difficultyLabel} from '../../domain/RecipeCard';
import {
  haveCountText,
  type DiscoverRecipeCard,
} from '../../domain/DiscoverRecipeCard';

interface Props {
  card: DiscoverRecipeCard;
  onPress: (recipeId: string) => void;
}

export function DiscoverRecipeCardView({
  card,
  onPress,
}: Props): React.JSX.Element {
  const isComplete = card.haveCount >= card.totalCount;

  return (
    <TouchableOpacity style={styles.card} onPress={() => onPress(card.id)}>
      <Text style={styles.name}>{card.name}</Text>
      <Text style={styles.meta}>
        {card.timeMinutes} min · {difficultyLabel(card.difficulty)}
      </Text>
      <View style={[styles.badge, isComplete && styles.badgeComplete]}>
        <Text style={styles.badgeText}>{haveCountText(card)}</Text>
      </View>
    </TouchableOpacity>
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
  badge: {
    alignSelf: 'flex-start',
    borderRadius: 14,
    paddingVertical: 5,
    paddingHorizontal: 10,
    backgroundColor: '#fff3e0',
  },
  badgeComplete: {backgroundColor: '#eef5ee'},
  badgeText: {fontSize: 12, fontWeight: '600'},
});
