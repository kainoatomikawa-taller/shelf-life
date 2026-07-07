/**
 * Thin client for username/password login and sign-up. Delegates to the
 * "login-with-username" / "sign-up-with-username" Supabase edge functions
 * (Supabase Auth is email-based, so username handling happens server-side)
 * and, on success, stores the returned session via the Supabase client SDK.
 */

import {FunctionsHttpError} from '@supabase/supabase-js';
import {supabase} from './supabaseClient';
import type {AuthUser, SignUpRequest} from '../domain/Auth';

interface LoginResponse {
  session: {
    access_token: string;
    refresh_token: string;
  };
  user: {
    id: string;
    username: string;
  };
}

type SignUpResponse = LoginResponse;

const SIGN_UP_FAILED = 'Sign up failed. Please try again.';

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

export class AuthApi {
  async login(username: string, password: string): Promise<AuthUser> {
    const {data, error} = await supabase.functions.invoke<LoginResponse>(
      'login-with-username',
      {body: {username, password}},
    );
    if (error || !data) {
      throw new Error('Invalid username or password');
    }

    const {error: sessionError} = await supabase.auth.setSession({
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token,
    });
    if (sessionError) {
      throw new Error('Invalid username or password');
    }

    return {id: data.user.id, username: data.user.username};
  }

  async signUp(fields: SignUpRequest): Promise<AuthUser> {
    const {data, error} = await supabase.functions.invoke<SignUpResponse>(
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

    return {id: data.user.id, username: data.user.username};
  }
}
