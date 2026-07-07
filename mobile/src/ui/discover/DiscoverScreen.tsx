/**
 * Discover (§5.4): For You / Explore tabs of recipes the user could cook if
 * they shopped, each card showing how many ingredients they already have.
 */

import React, {useState} from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {SingleSelectChips} from '../add-item/components/SingleSelectChips';
import {RecipeDetailScreen} from '../recipe-detail/RecipeDetailScreen';
import type {DiscoverTab} from '../../domain/DiscoverRecipeCard';
import {DiscoverRecipeCardView} from './DiscoverRecipeCardView';
import {useDiscoverFeed} from './useDiscoverFeed';

interface Props {
  userId: string;
}

const TABS: readonly DiscoverTab[] = ['for_you', 'explore'];

function tabLabel(tab: DiscoverTab): string {
  return tab === 'for_you' ? 'For You' : 'Explore';
}

export function DiscoverScreen({userId}: Props): React.JSX.Element {
  const [tab, setTab] = useState<DiscoverTab>('for_you');
  const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
  const {cards, loading, error} = useDiscoverFeed(userId, tab);

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
      <Text style={styles.title}>Discover</Text>

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
            <DiscoverRecipeCardView card={item} onPress={setSelectedRecipeId} />
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>
              No recipes to discover yet — check back once the catalog grows.
            </Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 20, paddingTop: 12, paddingBottom: 0},
  title: {fontSize: 28, fontWeight: '700', marginBottom: 16},
  spinner: {marginTop: 24},
  error: {color: '#c62828', marginTop: 12},
  list: {flex: 1, marginTop: 16},
  empty: {color: '#666', marginTop: 24, textAlign: 'center'},
});
