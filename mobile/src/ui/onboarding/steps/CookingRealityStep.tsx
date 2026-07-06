/**
 * Step 4 — Cooking reality check: skill, time, equipment, and budget. All
 * soft preferences used to bias which recipes rank higher, never to exclude
 * one outright.
 */

import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import type {
  BudgetSensitivity,
  OnboardingAnswers,
  SkillLevel,
} from '../../../domain/UserProfile';
import {ChipToggleGroup} from '../components/ChipToggleGroup';

const SKILL_LEVELS: SkillLevel[] = ['beginner', 'intermediate', 'advanced'];

const TIME_OPTIONS = [15, 30, 45, 60, 90];

const EQUIPMENT_OPTIONS = [
  'oven',
  'stovetop',
  'microwave',
  'blender',
  'slow cooker',
  'air fryer',
  'grill',
  'food processor',
];

const BUDGET_LEVELS: BudgetSensitivity[] = ['low', 'medium', 'high'];

interface Props {
  answers: OnboardingAnswers;
  onChange: (partial: Partial<OnboardingAnswers>) => void;
}

export function CookingRealityStep({answers, onChange}: Props): React.JSX.Element {
  const toggleEquipment = (item: string) => {
    const has = answers.equipment.includes(item);
    onChange({
      equipment: has
        ? answers.equipment.filter(e => e !== item)
        : [...answers.equipment, item],
    });
  };

  return (
    <View>
      <Text style={styles.sectionLabel}>Cooking skill</Text>
      <ChipToggleGroup
        options={SKILL_LEVELS}
        selected={[answers.skillLevel]}
        onToggle={level => onChange({skillLevel: level as SkillLevel})}
      />

      <View style={styles.spacerLarge} />
      <Text style={styles.sectionLabel}>Typical time available</Text>
      <ChipToggleGroup
        options={TIME_OPTIONS.map(String)}
        selected={[String(answers.typicalTimeAvailableMinutes)]}
        onToggle={minutes =>
          onChange({typicalTimeAvailableMinutes: Number(minutes)})
        }
        labelFor={minutes => `${minutes} min`}
      />

      <View style={styles.spacerLarge} />
      <Text style={styles.sectionLabel}>Equipment you have</Text>
      <ChipToggleGroup
        options={EQUIPMENT_OPTIONS}
        selected={answers.equipment}
        onToggle={toggleEquipment}
      />

      <View style={styles.spacerLarge} />
      <Text style={styles.sectionLabel}>Budget sensitivity</Text>
      <ChipToggleGroup
        options={BUDGET_LEVELS}
        selected={[answers.budgetSensitivity]}
        onToggle={level => onChange({budgetSensitivity: level as BudgetSensitivity})}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {fontSize: 14, fontWeight: '600', color: '#333', marginBottom: 10},
  spacerLarge: {height: 28},
});
