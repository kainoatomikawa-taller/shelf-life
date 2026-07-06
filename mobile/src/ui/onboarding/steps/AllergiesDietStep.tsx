/**
 * Step 1 — Allergies & diet. Framed explicitly as a safety question: this is
 * the data the app uses to guarantee a recipe is never served if it
 * conflicts with an allergy or diet restriction.
 */

import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import type {DietType, OnboardingAnswers} from '../../../domain/UserProfile';
import {ChipToggleGroup} from '../components/ChipToggleGroup';
import {TagInput} from '../components/TagInput';

const COMMON_ALLERGIES = [
  'peanuts',
  'tree nuts',
  'dairy',
  'eggs',
  'gluten',
  'shellfish',
  'soy',
  'fish',
  'sesame',
];

const DIET_TYPES: DietType[] = [
  'omnivore',
  'vegetarian',
  'vegan',
  'pescatarian',
  'keto',
  'paleo',
  'gluten_free',
  'dairy_free',
  'halal',
  'kosher',
];

function dietLabel(diet: string): string {
  return diet.replace('_', ' ');
}

interface Props {
  answers: OnboardingAnswers;
  onChange: (partial: Partial<OnboardingAnswers>) => void;
}

export function AllergiesDietStep({answers, onChange}: Props): React.JSX.Element {
  const toggleAllergy = (allergen: string) => {
    const has = answers.allergies.includes(allergen);
    onChange({
      allergies: has
        ? answers.allergies.filter(a => a !== allergen)
        : [...answers.allergies, allergen],
    });
  };

  return (
    <View>
      <Text style={styles.sectionLabel}>Any allergies we must never ignore?</Text>
      <ChipToggleGroup
        options={COMMON_ALLERGIES}
        selected={answers.allergies}
        onToggle={toggleAllergy}
      />
      <View style={styles.spacer} />
      <TagInput
        tags={answers.allergies.filter(a => !COMMON_ALLERGIES.includes(a))}
        onAdd={tag => onChange({allergies: [...answers.allergies, tag.toLowerCase()]})}
        onRemove={tag =>
          onChange({allergies: answers.allergies.filter(a => a !== tag)})
        }
        placeholder="Other allergy..."
      />

      <View style={styles.spacerLarge} />
      <Text style={styles.sectionLabel}>Do you follow a specific diet?</Text>
      <ChipToggleGroup
        options={DIET_TYPES}
        selected={[answers.dietType]}
        onToggle={diet => onChange({dietType: diet as DietType})}
        labelFor={dietLabel}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 10},
  spacer: {height: 16},
  spacerLarge: {height: 28},
});
