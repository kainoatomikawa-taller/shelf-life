/**
 * Pure client-side validation rules for the sign-up form. These check
 * shape only — uniqueness (username taken / email in use) can only be
 * decided server-side and comes back as a sign-up edge function error.
 */

const USERNAME_PATTERN = /^[a-zA-Z0-9_]{3,20}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export interface SignUpFields {
  readonly name: string;
  readonly username: string;
  readonly email: string;
  readonly password: string;
  readonly confirmPassword: string;
}

export interface SignUpFieldErrors {
  readonly name?: string;
  readonly username?: string;
  readonly email?: string;
  readonly password?: string;
  readonly confirmPassword?: string;
}

export function validateName(name: string): string | undefined {
  return name.trim().length > 0 ? undefined : 'Enter your name.';
}

export function validateUsername(username: string): string | undefined {
  if (!USERNAME_PATTERN.test(username)) {
    return '3-20 characters: letters, numbers, and underscores only.';
  }
  return undefined;
}

export function validateEmail(email: string): string | undefined {
  return EMAIL_PATTERN.test(email) ? undefined : 'Enter a valid email address.';
}

export function validatePasswordStrength(password: string): string | undefined {
  if (password.length < 8) {
    return 'Use at least 8 characters.';
  }
  if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password)) {
    return 'Include at least one letter and one number.';
  }
  return undefined;
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): string | undefined {
  return password === confirmPassword ? undefined : 'Passwords do not match.';
}

export function validateSignUpFields(fields: SignUpFields): SignUpFieldErrors {
  return {
    name: validateName(fields.name),
    username: validateUsername(fields.username),
    email: validateEmail(fields.email),
    password: validatePasswordStrength(fields.password),
    confirmPassword: validateConfirmPassword(fields.password, fields.confirmPassword),
  };
}

export function hasNoFieldErrors(errors: SignUpFieldErrors): boolean {
  return Object.values(errors).every(message => message === undefined);
}
