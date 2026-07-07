/**
 * Thin client for username/password login, sign-up, and session restore.
 * Delegates to the "login-with-username" / "sign-up-with-username"
 * Supabase edge functions (Supabase Auth is email-based, so username
 * handling happens server-side) and, on success, stores the returned
 * session via the Supabase client SDK. Identity (username + display name)
 * is always resolved from the bearer-authenticated /profiles endpoints —
 * the single source of truth, used the same way whether the session was
 * just created or restored from a previous launch.
 */

import {FunctionsHttpError} from '@supabase/supabase-js';
import {ProfileApi} from './ProfileApi';
import {supabase} from './supabaseClient';
import type {AuthUser, SignUpRequest} from '../domain/Auth';
import type {Profile} from '../domain/Profile';

interface AuthEdgeFunctionResponse {
  session: {
    access_token: string;
    refresh_token: string;
  };
}

const LOGIN_FAILED = 'Incorrect username or password. Please try again.';
const SIGN_UP_FAILED = 'Sign up failed. Please try again.';
const RESET_REQUEST_FAILED = 'Something went wrong. Please try again.';

const profileApi = new ProfileApi();

async function extractErrorMessage(error: unknown, fallback: string): Promise<string> {
  if (error instanceof FunctionsHttpError) {
    const body = await error.context.json().catch(() => null);
    const message = body?.error ?? body?.message;
    if (typeof message === 'string' && message.length > 0) {
      return message;
    }
  }
  return fallback;
}

function toAuthUser(profile: Profile): AuthUser {
  return {id: profile.id, username: profile.username, name: profile.displayName};
}

export class AuthApi {
  async login(username: string, password: string): Promise<AuthUser> {
    const {data, error} = await supabase.functions.invoke<AuthEdgeFunctionResponse>(
      'login-with-username',
      {body: {username, password}},
    );
    if (error || !data) {
      throw new Error(LOGIN_FAILED);
    }

    const {error: sessionError} = await supabase.auth.setSession({
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token,
    });
    if (sessionError) {
      throw new Error(LOGIN_FAILED);
    }

    // Any failure here (including a missing profile) is folded into the
    // same generic message so we never leak which part of sign-in failed.
    try {
      const profile = await profileApi.getMine(data.session.access_token);
      if (!profile) {
        throw new Error(LOGIN_FAILED);
      }
      return toAuthUser(profile);
    } catch {
      throw new Error(LOGIN_FAILED);
    }
  }

  async signUp(fields: SignUpRequest): Promise<AuthUser> {
    const {data, error} = await supabase.functions.invoke<AuthEdgeFunctionResponse>(
      'sign-up-with-username',
      {body: fields},
    );
    if (error || !data) {
      throw new Error(await extractErrorMessage(error, SIGN_UP_FAILED));
    }

    const {error: sessionError} = await supabase.auth.setSession({
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token,
    });
    if (sessionError) {
      throw new Error(SIGN_UP_FAILED);
    }

    const profile = await profileApi.create(
      data.session.access_token,
      fields.username,
      fields.name,
      fields.email,
    );
    return toAuthUser(profile);
  }

  /**
   * Requests a password-reset email via the "forgot-password" edge
   * function, which accepts a username or an email. Username resolution
   * happens server-side (the client never learns whether the identifier
   * matched an account) — this always resolves on a successful call to the
   * function, regardless of whether a matching account exists, so the UI
   * can show one generic confirmation message without leaking account
   * existence.
   */
  async requestPasswordReset(identifier: string): Promise<void> {
    const {error} = await supabase.functions.invoke('forgot-password', {
      body: {identifier},
    });
    if (error) {
      throw new Error(await extractErrorMessage(error, RESET_REQUEST_FAILED));
    }
  }

  /**
   * Resolves the session the SDK already restored/refreshed from storage,
   * if any, into an AuthUser. Returns null when there's no session or its
   * profile can't be resolved (e.g. an incomplete sign-up) — either way,
   * the caller should fall back to the login flow.
   */
  async getCurrentUser(): Promise<AuthUser | null> {
    const {data, error} = await supabase.auth.getSession();
    if (error || !data.session) {
      return null;
    }

    try {
      const profile = await profileApi.getMine(data.session.access_token);
      return profile ? toAuthUser(profile) : null;
    } catch {
      return null;
    }
  }
}
