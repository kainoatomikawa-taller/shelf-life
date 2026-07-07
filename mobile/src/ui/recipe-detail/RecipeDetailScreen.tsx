/**
 * Full detail view for a single recipe: complete ingredient list (essential
 * and optional), time, and step-by-step procedure. Reached by tapping a
 * card in Discover or Cook Now.
 */

import React from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {difficultyLabel} from '../../domain/RecipeCard';
import {useRecipeDetail} from './useRecipeDetail';

interface Props {
  recipeId: string;
  onBack: () => void;
}

export function RecipeDetailScreen({
  recipeId,
  onBack,
}: Props): React.JSX.Element {
  const {recipe, loading, error} = useRecipeDetail(recipeId);

  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={onBack} style={styles.backButton}>
        <Text style={styles.backText}>‹ Back</Text>
      </TouchableOpacity>

      {loading && <ActivityIndicator style={styles.spinner} />}
      {error && <Text style={styles.error}>{error}</Text>}

      {!loading && !error && recipe && (
        <ScrollView style={styles.scroll}>
          <Text style={styles.title}>{recipe.name}</Text>
          <Text style={styles.meta}>
            {recipe.timeMinutes} min · {difficultyLabel(recipe.difficulty)}
          </Text>

          <Text style={styles.sectionTitle}>Ingredients</Text>
          {recipe.ingredients.map(ingredient => (
            <View key={ingredient.ingredientId} style={styles.ingredientRow}>
              <Text style={styles.ingredientName}>
                {ingredient.ingredientName}
              </Text>
              {ingredient.role === 'optional' && (
                <Text style={styles.optionalTag}>optional</Text>
              )}
            </View>
          ))}

          <Text style={styles.sectionTitle}>Procedure</Text>
          {recipe.steps.map((step, index) => (
            <View key={index} style={styles.stepRow}>
              <Text style={styles.stepNumber}>{index + 1}.</Text>
              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 20, paddingTop: 12, paddingBottom: 0},
  backButton: {marginBottom: 12, alignSelf: 'flex-start'},
  backText: {color: '#2e7d32', fontWeight: '600', fontSize: 15},
  spinner: {marginTop: 24},
  error: {color: '#c62828', marginTop: 12},
  scroll: {flex: 1},
  title: {fontSize: 24, fontWeight: '700', marginBottom: 4},
  meta: {fontSize: 14, color: '#666', marginBottom: 20},
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    marginTop: 12,
    marginBottom: 8,
  },
  ingredientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  ingredientName: {fontSize: 15, color: '#222'},
  optionalTag: {
    fontSize: 11,
    fontWeight: '600',
    color: '#999',
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    paddingVertical: 2,
    paddingHorizontal: 6,
  },
  stepRow: {flexDirection: 'row', gap: 8, marginBottom: 10},
  stepNumber: {fontSize: 15, fontWeight: '700', color: '#2e7d32'},
  stepText: {fontSize: 15, color: '#222', flex: 1, lineHeight: 21},
});
