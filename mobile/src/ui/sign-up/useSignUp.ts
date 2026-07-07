/**
 * Drives the sign-up form: holds the field values, runs client-side
 * validation on submit, and calls AuthApi. Server errors (e.g. username
 * taken, email in use) are surfaced verbatim since they're actionable,
 * unlike login's deliberately generic failure message.
 */

import {useCallback, useState} from 'react';
import {AuthApi} from '../../data/AuthApi';
import type {AuthUser} from '../../domain/Auth';
import {
  hasNoFieldErrors,
  validateSignUpFields,
  type SignUpFieldErrors,
} from '../../domain/SignUpValidation';

const api = new AuthApi();

export function useSignUp(onSuccess: (user: AuthUser) => void) {
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<SignUpFieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const canSubmit =
    name.trim().length > 0 &&
    username.trim().length > 0 &&
    email.trim().length > 0 &&
    password.length > 0 &&
    confirmPassword.length > 0 &&
    !submitting;

  const submit = useCallback(async () => {
    if (!canSubmit) {
      return;
    }
    setServerError(null);

    const errors = validateSignUpFields({
      name,
      username,
      email,
      password,
      confirmPassword,
    });
    setFieldErrors(errors);
    if (!hasNoFieldErrors(errors)) {
      return;
    }

    setSubmitting(true);
    try {
      const user = await api.signUp({
        name: name.trim(),
        username: username.trim(),
        email: email.trim(),
        password,
      });
      onSuccess(user);
    } catch (e) {
      setServerError(e instanceof Error ? e.message : 'Sign up failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [canSubmit, name, username, email, password, confirmPassword, onSuccess]);

  return {
    name,
    setName,
    username,
    setUsername,
    email,
    setEmail,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    fieldErrors,
    submitting,
    serverError,
    canSubmit,
    submit,
  };
}
