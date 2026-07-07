/**
 * Supabase client singleton. Session tokens are persisted via AsyncStorage
 * so a signed-in user stays signed in across app restarts.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import {createClient} from '@supabase/supabase-js';
import {SUPABASE_ANON_KEY, SUPABASE_URL} from './config';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});

/**
 * Reads the current (SDK-refreshed, if needed) access token for
 * bearer-authenticated calls to our backend. Returns null if there's no
 * signed-in session.
 */
export async function getAccessToken(): Promise<string | null> {
  const {data} = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
