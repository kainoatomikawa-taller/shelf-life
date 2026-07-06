/**
 * Step 5 — Adventurousness. How far to stray from familiar recipes when
 * ranking recommendations.
 */

import React from 'react';
import {View} from 'react-native';
import type {OnboardingAnswers} from '../../../domain/UserProfile';
import {SliderScale} from '../components/SliderScale';

interface Props {
  answers: OnboardingAnswers;
  onChange: (partial: Partial<OnboardingAnswers>) => void;
}

export function AdventurousnessStep({answers, onChange}: Props): React.JSX.Element {
  return (
    <View>
      <SliderScale
        label="How adventurous do you want your recipes to be?"
        lowLabel="Stick to the familiar"
        highLabel="Surprise me"
        value={answers.adventurousness}
        onChange={value => onChange({adventurousness: value})}
      />
    </View>
  );
}
