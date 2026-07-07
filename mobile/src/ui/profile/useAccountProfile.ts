/**
 * Drives the Profile screen's editable display_name and username (§6).
 * Each field saves independently on an explicit action rather than on
 * every keystroke, since a username save round-trips a uniqueness check
 * that shouldn't fire on every character typed. Username changes are
 * unlimited with no cooldown — every save just re-runs the check.
 */

import {useCallback, useEffect, useState} from 'react';
import {ProfileApi} from '../../data/ProfileApi';
import {getAccessToken} from '../../data/supabaseClient';
import type {AuthUser} from '../../domain/Auth';
import {validateUsername} from '../../domain/SignUpValidation';

const SESSION_EXPIRED = 'Your session has expired. Please log in again.';

const api = new ProfileApi();

export function useAccountProfile(
  authUser: AuthUser,
  onUpdated: (partial: Partial<Pick<AuthUser, 'username' | 'name'>>) => void,
) {
  const [username, setUsername] = useState(authUser.username);
  const [displayName, setDisplayName] = useState(authUser.name);
  const [savingUsername, setSavingUsername] = useState(false);
  const [savingDisplayName, setSavingDisplayName] = useState(false);
  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [displayNameError, setDisplayNameError] = useState<string | null>(null);

  useEffect(() => {
    setUsername(authUser.username);
    setDisplayName(authUser.name);
  }, [authUser.username, authUser.name]);

  const saveDisplayName = useCallback(async () => {
    const next = displayName.trim();
    if (!next || next === authUser.name) {
      setDisplayName(authUser.name);
      return;
    }
    setSavingDisplayName(true);
    setDisplayNameError(null);
    try {
      const token = await getAccessToken();
      if (!token) {
        throw new Error(SESSION_EXPIRED);
      }
      const profile = await api.update(token, {displayName: next});
      setDisplayName(profile.displayName);
      onUpdated({name: profile.displayName});
    } catch (e) {
      setDisplayName(authUser.name);
      setDisplayNameError(
        e instanceof Error ? e.message : 'Failed to save display name.',
      );
    } finally {
      setSavingDisplayName(false);
    }
  }, [displayName, authUser.name, onUpdated]);

  const saveUsername = useCallback(async () => {
    const next = username.trim();
    if (!next || next.toLowerCase() === authUser.username) {
      setUsername(authUser.username);
      return;
    }
    const formatError = validateUsername(next);
    if (formatError) {
      setUsernameError(formatError);
      return;
    }
    setSavingUsername(true);
    setUsernameError(null);
    try {
      const token = await getAccessToken();
      if (!token) {
        throw new Error(SESSION_EXPIRED);
      }
      const profile = await api.update(token, {username: next});
      setUsername(profile.username);
      onUpdated({username: profile.username});
    } catch (e) {
      setUsername(authUser.username);
      setUsernameError(
        e instanceof Error ? e.message : 'Failed to save username.',
      );
    } finally {
      setSavingUsername(false);
    }
  }, [username, authUser.username, onUpdated]);

  return {
    username,
    setUsername,
    displayName,
    setDisplayName,
    savingUsername,
    savingDisplayName,
    usernameError,
    displayNameError,
    saveUsername,
    saveDisplayName,
  };
}
