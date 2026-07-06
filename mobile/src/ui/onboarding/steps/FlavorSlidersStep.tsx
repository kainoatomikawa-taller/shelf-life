/**
 * Step 3 — Flavor sliders. Seeds the derived taste vector (§4.6); each
 * dimension ranges from "less" to "more" around a neutral midpoint.
 */

import React from 'react';
import {View} from 'react-native';
import type {
  FlavorDimension,
  OnboardingAnswers,
} from '../../../domain/UserProfile';
import {SliderScale} from '../components/SliderScale';

const DIMENSIONS: Array<{
  key: FlavorDimension;
  label: string;
  low: string;
  high: string;
}> = [
  {key: 'sweetness', label: 'Sweetness', low: 'Less sweet', high: 'More sweet'},
  {key: 'saltiness', label: 'Saltiness', low: 'Less salty', high: 'More salty'},
  {key: 'sourness', label: 'Sourness', low: 'Less sour', high: 'More sour'},
  {
    key: 'bitterness',
    label: 'Bitterness',
    low: 'Less bitter',
    high: 'More bitter',
  },
  {key: 'spiciness', label: 'Spiciness', low: 'Mild', high: 'Fiery'},
  {key: 'umami', label: 'Umami', low: 'Less umami', high: 'More umami'},
];

interface Props {
  answers: OnboardingAnswers;
  onChange: (partial: Partial<OnboardingAnswers>) => void;
}

export function FlavorSlidersStep({answers, onChange}: Props): React.JSX.Element {
  return (
    <View>
      {DIMENSIONS.map(dimension => (
        <SliderScale
          key={dimension.key}
          label={dimension.label}
          lowLabel={dimension.low}
          highLabel={dimension.high}
          value={answers.flavorProfile[dimension.key]}
          onChange={value =>
            onChange({
              flavorProfile: {...answers.flavorProfile, [dimension.key]: value},
            })
          }
        />
      ))}
    </View>
  );
}
