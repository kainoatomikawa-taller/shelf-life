/**
 * Drives the forgot-password form: holds a single username-or-email input
 * and submits it to the "forgot-password" edge function via AuthApi. Always
 * lands on the same confirmation state regardless of whether the identifier
 * matched an account, so the flow never reveals account existence.
 */

import {useCallback, useState} from 'react';
import {AuthApi} from '../../data/AuthApi';

const GENERIC_ERROR = 'Something went wrong. Please try again.';

const api = new AuthApi();

export function useForgotPassword() {
  const [identifier, setIdentifier] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const canSubmit = identifier.trim().length > 0 && !submitting;

  const submit = useCallback(async () => {
    if (!canSubmit) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await api.requestPasswordReset(identifier.trim());
      setSubmitted(true);
    } catch {
      setError(GENERIC_ERROR);
    } finally {
      setSubmitting(false);
    }
  }, [canSubmit, identifier]);

  return {
    identifier,
    setIdentifier,
    submitting,
    error,
    submitted,
    canSubmit,
    submit,
  };
}
