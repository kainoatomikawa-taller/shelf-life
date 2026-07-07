/**
 * Thin client for username/password login. Delegates to the
 * "login-with-username" Supabase edge function (Supabase Auth is
 * email-based, so username lookup happens server-side) and, on success,
 * stores the returned session via the Supabase client SDK.
 */

import {supabase} from './supabaseClient';
import type {AuthUser} from '../domain/Auth';

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
}
