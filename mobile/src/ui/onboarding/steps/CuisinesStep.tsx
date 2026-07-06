/**
 * Step 2 — Liked cuisines & dishes. Both feed the taste profile's
 * `likedCuisines` list, which the ranking step (§4.6) treats as a soft
 * preference, never an eligibility filter.
 */

import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import type {OnboardingAnswers} from '../../../domain/UserProfile';
import {ChipToggleGroup} from '../components/ChipToggleGroup';
import {TagInput} from '../components/TagInput';

const COMMON_CUISINES = [
  'italian',
  'mexican',
  'chinese',
  'japanese',
  'indian',
  'thai',
  'french',
  'mediterranean',
  'korean',
  'american',
  'vietnamese',
  'middle eastern',
];

interface Props {
  answers: OnboardingAnswers;
  onChange: (partial: Partial<OnboardingAnswers>) => void;
}

export function CuisinesStep({answers, onChange}: Props): React.JSX.Element {
  const toggleCuisine = (cuisine: string) => {
    const has = answers.likedCuisines.includes(cuisine);
    onChange({
      likedCuisines: has
        ? answers.likedCuisines.filter(c => c !== cuisine)
        : [...answers.likedCuisines, cuisine],
    });
  };

  return (
    <View>
      <Text style={styles.sectionLabel}>Cuisines you enjoy</Text>
      <ChipToggleGroup
        options={COMMON_CUISINES}
        selected={answers.likedCuisines}
        onToggle={toggleCuisine}
      />

      <View style={styles.spacerLarge} />
      <Text style={styles.sectionLabel}>Specific dishes you love</Text>
      <TagInput
        tags={answers.likedCuisines.filter(c => !COMMON_CUISINES.includes(c))}
        onAdd={tag =>
          onChange({likedCuisines: [...answers.likedCuisines, tag.toLowerCase()]})
        }
        onRemove={tag =>
          onChange({likedCuisines: answers.likedCuisines.filter(c => c !== tag)})
        }
        placeholder="e.g. pad thai, tacos al pastor..."
      />
    </View>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 10},
  spacerLarge: {height: 28},
});
