/**
 * Cook Now (§5.3): For You / Explore tabs of recipes the user can cook
 * right now, each ranked by a different algorithm — For You by
 * content-based taste/effort/freshness fit, Explore by popularity mixed
 * with the user's adventurousness. Cards carry badges explaining why a
 * recipe is surfaced, with tap-to-reveal substitution detail (AC3).
 */

import React, {useState} from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {SingleSelectChips} from '../add-item/components/SingleSelectChips';
import {RecipeDetailScreen} from '../recipe-detail/RecipeDetailScreen';
import type {CookNowTab} from '../../domain/RecipeCard';
import {RecipeCardView} from './RecipeCardView';
import {useCookNowFeed} from './useCookNowFeed';

interface Props {
  filterIngredientName?: string | null;
  onBack: () => void;
}

const TABS: readonly CookNowTab[] = ['for_you', 'explore'];

function tabLabel(tab: CookNowTab): string {
  return tab === 'for_you' ? 'For You' : 'Explore';
}

export function CookNowScreen({
  filterIngredientName,
  onBack,
}: Props): React.JSX.Element {
  const [tab, setTab] = useState<CookNowTab>('for_you');
  const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
  const {cards, loading, error} = useCookNowFeed(tab);

  if (selectedRecipeId) {
    return (
      <RecipeDetailScreen
        recipeId={selectedRecipeId}
        onBack={() => setSelectedRecipeId(null)}
      />
    );
  }

  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={onBack} style={styles.backButton}>
        <Text style={styles.backText}>‹ Kitchen</Text>
      </TouchableOpacity>

      <Text style={styles.title}>Cook Now</Text>

      {filterIngredientName && (
        <View style={styles.filterChip}>
          <Text style={styles.filterChipText}>
            Using: {filterIngredientName}
          </Text>
        </View>
      )}

      <SingleSelectChips
        options={TABS}
        selected={tab}
        onSelect={setTab}
        labelFor={tabLabel}
      />

      {loading && <ActivityIndicator style={styles.spinner} />}
      {error && <Text style={styles.error}>{error}</Text>}

      {!loading && !error && (
        <FlatList
          style={styles.list}
          data={cards}
          keyExtractor={card => card.id}
          renderItem={({item}) => (
            <RecipeCardView card={item} onPress={setSelectedRecipeId} />
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>
              No recipes you can cook right now — try restocking a few
              essentials.
            </Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 20, paddingTop: 12, paddingBottom: 0},
  backButton: {marginBottom: 12, alignSelf: 'flex-start'},
  backText: {color: '#2e7d32', fontWeight: '600', fontSize: 15},
  title: {fontSize: 28, fontWeight: '700', marginBottom: 16},
  filterChip: {
    alignSelf: 'flex-start',
    backgroundColor: '#eef5ee',
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 14,
    marginBottom: 12,
  },
  filterChipText: {color: '#2e7d32', fontWeight: '600', fontSize: 13},
  spinner: {marginTop: 24},
  error: {color: '#c62828', marginTop: 12},
  list: {flex: 1, marginTop: 16},
  empty: {color: '#666', marginTop: 24, textAlign: 'center'},
});
