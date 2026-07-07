/**
 * The 5-step onboarding flow (§5.1): allergies/diet, liked cuisines &
 * dishes, flavor sliders, cooking reality check, and adventurousness. Every
 * step can be skipped — skipping keeps that step's field at its domain
 * default rather than blocking progress.
 */

import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import {
  DEFAULT_FLAVOR_PROFILE,
  type OnboardingAnswers,
} from '../../domain/UserProfile';
import {AdventurousnessStep} from './steps/AdventurousnessStep';
import {AllergiesDietStep} from './steps/AllergiesDietStep';
import {CookingRealityStep} from './steps/CookingRealityStep';
import {CuisinesStep} from './steps/CuisinesStep';
import {FlavorSlidersStep} from './steps/FlavorSlidersStep';
import {StepShell} from './components/StepShell';
import {TOTAL_ONBOARDING_STEPS, useOnboarding} from './useOnboarding';

interface StepConfig {
  title: string;
  subtitle: string;
  banner?: string;
  resetDefaults: Partial<OnboardingAnswers>;
  continueLabel: string;
  Content: React.ComponentType<{
    answers: OnboardingAnswers;
    onChange: (partial: Partial<OnboardingAnswers>) => void;
  }>;
}

const STEPS: StepConfig[] = [
  {
    title: 'Allergies & diet',
    subtitle: "We'll use this to personalize your recipes.",
    banner:
      'For your safety: a recipe that conflicts with an allergy or diet you list here will never be suggested to you, no matter how well it otherwise matches your taste.',
    resetDefaults: {allergies: [], dietType: 'omnivore'},
    continueLabel: 'Continue',
    Content: AllergiesDietStep,
  },
  {
    title: 'What do you love to eat?',
    subtitle:
      'Cuisines and dishes you crave help us recommend recipes you actually want to cook.',
    resetDefaults: {likedCuisines: []},
    continueLabel: 'Continue',
    Content: CuisinesStep,
  },
  {
    title: 'Dial in your flavor profile',
    subtitle: 'Nudge each slider toward how you like your food to taste.',
    resetDefaults: {flavorProfile: DEFAULT_FLAVOR_PROFILE},
    continueLabel: 'Continue',
    Content: FlavorSlidersStep,
  },
  {
    title: "Let's be realistic",
    subtitle:
      'Your skill, time, tools, and budget shape which recipes make sense for you.',
    resetDefaults: {
      skillLevel: 'beginner',
      typicalTimeAvailableMinutes: 30,
      equipment: [],
      budgetSensitivity: 'medium',
    },
    continueLabel: 'Continue',
    Content: CookingRealityStep,
  },
  {
    title: 'One last thing',
    subtitle: 'How far outside your comfort zone should we push?',
    resetDefaults: {adventurousness: 0.5},
    continueLabel: 'Finish',
    Content: AdventurousnessStep,
  },
];

interface Props {
  onComplete: () => void;
}

export function OnboardingScreen({onComplete}: Props): React.JSX.Element {
  const {answers, stepIndex, updateAnswers, continueStep, skipStep, submitting, error} =
    useOnboarding(onComplete);

  const step = STEPS[stepIndex];
  if (!step) {
    return <View />;
  }
  const {Content} = step;

  return (
    <StepShell
      stepNumber={stepIndex + 1}
      totalSteps={TOTAL_ONBOARDING_STEPS}
      title={step.title}
      subtitle={step.subtitle}
      banner={step.banner}
      continueLabel={step.continueLabel}
      submitting={submitting}
      onSkip={() => skipStep(step.resetDefaults)}
      onContinue={continueStep}>
      <Content answers={answers} onChange={updateAnswers} />
      {error && <Text style={styles.error}>{error}</Text>}
    </StepShell>
  );
}

const styles = StyleSheet.create({
  error: {color: '#c62828', marginTop: 12},
});
