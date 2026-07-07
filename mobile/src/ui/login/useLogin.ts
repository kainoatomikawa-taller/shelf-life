/**
 * Drives the login form: holds username/password input, submits to
 * AuthApi, and surfaces a generic error on any failure so we never leak
 * whether a username exists or which credential was wrong.
 */

import {useCallback, useState} from 'react';
import {AuthApi} from '../../data/AuthApi';
import type {AuthUser} from '../../domain/Auth';

const GENERIC_ERROR = 'Incorrect username or password. Please try again.';

const api = new AuthApi();

export function useLogin(onSuccess: (user: AuthUser) => void) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    username.trim().length > 0 && password.length > 0 && !submitting;

  const submit = useCallback(async () => {
    if (!canSubmit) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const user = await api.login(username.trim(), password);
      onSuccess(user);
    } catch {
      setError(GENERIC_ERROR);
    } finally {
      setSubmitting(false);
    }
  }, [canSubmit, username, password, onSuccess]);

  return {
    username,
    setUsername,
    password,
    setPassword,
    submitting,
    error,
    canSubmit,
    submit,
  };
}
