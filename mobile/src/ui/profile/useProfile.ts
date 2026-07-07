/**
 * Loads a user's taste profile and keeps it in sync with the backend: every
 * edit is saved immediately (not batched behind a "Save" button) so that
 * safety-critical fields like allergies and diet take effect right away.
 */

import {useCallback, useEffect, useState} from 'react';
import {UserApi} from '../../data/UserApi';
import {getAccessToken} from '../../data/supabaseClient';
import {
  DEFAULT_FLAVOR_PROFILE,
  DEFAULT_ONBOARDING_ANSWERS,
  toOnboardingAnswers,
  type FlavorProfile,
  type OnboardingAnswers,
} from '../../domain/UserProfile';

const api = new UserApi();

export function useProfile() {
  const [answers, setAnswers] = useState<OnboardingAnswers | null>(null);
  const [tasteVector, setTasteVector] = useState<FlavorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);
      try {
        const accessToken = await getAccessToken();
        if (!accessToken) {
          throw new Error('Not signed in');
        }
        const profile = await api.getProfile(accessToken);
        if (cancelled) {
          return;
        }
        if (profile) {
          setAnswers(toOnboardingAnswers(profile));
          setTasteVector(profile.tasteVector);
        } else {
          setAnswers(DEFAULT_ONBOARDING_ANSWERS);
          setTasteVector(DEFAULT_FLAVOR_PROFILE);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Unknown error');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const save = useCallback(async (next: OnboardingAnswers) => {
    setSaving(true);
    setError(null);
    try {
      const accessToken = await getAccessToken();
      if (!accessToken) {
        throw new Error('Not signed in');
      }
      const profile = await api.submitOnboarding(accessToken, next);
      setTasteVector(profile.tasteVector);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setSaving(false);
    }
  }, []);

  const updateAnswers = useCallback(
    (partial: Partial<OnboardingAnswers>) => {
      if (!answers) {
        return;
      }
      const next = {...answers, ...partial};
      setAnswers(next);
      void save(next);
    },
    [answers, save],
  );

  return {answers, tasteVector, loading, saving, error, updateAnswers};
}
