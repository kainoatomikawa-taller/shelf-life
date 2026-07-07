/**
 * Resolves whether there's a valid Supabase session on launch (the SDK
 * already auto-refreshes it from AsyncStorage) and, if so, loads the
 * signed-in user's data: preferences (also used to decide whether
 * onboarding is done), ratings, and shopping list. Inventory is
 * deliberately not fetched here — KitchenScreen is the default landing
 * tab and loads it via its own hook the moment it mounts, so fetching it
 * again here would just be a redundant network call.
 *
 * Also reacts to the SDK signing the user out (e.g. a refresh token that
 * finally expired) so the app falls back to the login flow instead of
 * getting stuck showing stale state.
 */

import {useCallback, useEffect, useRef, useState} from 'react';
import {AuthApi} from '../data/AuthApi';
import {RatingApi} from '../data/RatingApi';
import {ShoppingListApi} from '../data/ShoppingListApi';
import {UserApi} from '../data/UserApi';
import {getAccessToken, supabase} from '../data/supabaseClient';
import type {AuthUser} from '../domain/Auth';

const authApi = new AuthApi();
const userApi = new UserApi();
const ratingApi = new RatingApi();
const shoppingListApi = new ShoppingListApi();

export function useAppSession() {
  const [checkingSession, setCheckingSession] = useState(true);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [onboarded, setOnboarded] = useState(false);
  const mounted = useRef(true);

  const loadForUser = useCallback(async (user: AuthUser) => {
    const accessToken = await getAccessToken();
    let profile = null;
    if (accessToken) {
      const [profileResult] = await Promise.allSettled([
        userApi.getProfile(accessToken),
        ratingApi.list(accessToken),
        shoppingListApi.list(accessToken),
      ]);
      profile = profileResult.status === 'fulfilled' ? profileResult.value : null;
    }
    if (!mounted.current) {
      return;
    }
    setOnboarded(profile !== null);
    setAuthUser(user);
  }, []);

  useEffect(() => {
    mounted.current = true;
    (async () => {
      try {
        const user = await authApi.getCurrentUser();
        if (user) {
          await loadForUser(user);
        }
      } finally {
        if (mounted.current) {
          setCheckingSession(false);
        }
      }
    })();
    return () => {
      mounted.current = false;
    };
  }, [loadForUser]);

  useEffect(() => {
    const {
      data: {subscription},
    } = supabase.auth.onAuthStateChange(event => {
      if (event === 'SIGNED_OUT') {
        setAuthUser(null);
        setOnboarded(false);
      }
    });
    return () => subscription.unsubscribe();
  }, []);

  const signIn = useCallback(
    (user: AuthUser) => {
      void loadForUser(user);
    },
    [loadForUser],
  );

  /** Keeps the app-wide identity (e.g. greetings) in sync after the
   * Profile screen edits display_name/username. */
  const updateIdentity = useCallback(
    (partial: Partial<Pick<AuthUser, 'username' | 'name'>>) => {
      setAuthUser(prev => (prev ? {...prev, ...partial} : prev));
    },
    [],
  );

  return {checkingSession, authUser, onboarded, setOnboarded, signIn, updateIdentity};
}
