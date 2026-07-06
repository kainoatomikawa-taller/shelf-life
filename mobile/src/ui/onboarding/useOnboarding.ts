/**
 * Drives the 5-step onboarding flow: holds the in-progress answers, moves
 * between steps, and persists the final taste profile via UserApi.
 */

import {useCallback, useState} from 'react';
import {UserApi} from '../../data/UserApi';
import {
  DEFAULT_ONBOARDING_ANSWERS,
  type OnboardingAnswers,
} from '../../domain/UserProfile';

export const TOTAL_ONBOARDING_STEPS = 5;

const api = new UserApi();

export function useOnboarding(userId: string, onComplete: () => void) {
  const [answers, setAnswers] = useState<OnboardingAnswers>(
    DEFAULT_ONBOARDING_ANSWERS,
  );
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateAnswers = useCallback((partial: Partial<OnboardingAnswers>) => {
    setAnswers(prev => ({...prev, ...partial}));
  }, []);

  const finish = useCallback(
    async (finalAnswers: OnboardingAnswers) => {
      setSubmitting(true);
      setError(null);
      try {
        await api.submitOnboarding(userId, finalAnswers);
        onComplete();
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unknown error');
      } finally {
        setSubmitting(false);
      }
    },
    [userId, onComplete],
  );

  const advance = useCallback(
    (currentAnswers: OnboardingAnswers) => {
      if (stepIndex < TOTAL_ONBOARDING_STEPS - 1) {
        setStepIndex(stepIndex + 1);
      } else {
        void finish(currentAnswers);
      }
    },
    [stepIndex, finish],
  );

  const continueStep = useCallback(() => {
    advance(answers);
  }, [advance, answers]);

  const skipStep = useCallback(
    (defaultsForStep: Partial<OnboardingAnswers>) => {
      const resetAnswers = {...answers, ...defaultsForStep};
      setAnswers(resetAnswers);
      advance(resetAnswers);
    },
    [advance, answers],
  );

  return {
    answers,
    stepIndex,
    updateAnswers,
    continueStep,
    skipStep,
    submitting,
    error,
  };
}
