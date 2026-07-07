/**
 * Hook that loads one tab of the Cook Now feed for the current user.
 */

import {useCallback, useEffect, useState} from 'react';
import {CookNowApi} from '../../data/CookNowApi';
import {getAccessToken} from '../../data/supabaseClient';
import type {CookNowTab, RecipeCard} from '../../domain/RecipeCard';

const api = new CookNowApi();

export function useCookNowFeed(tab: CookNowTab) {
  const [cards, setCards] = useState<RecipeCard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const accessToken = await getAccessToken();
      if (!accessToken) {
        throw new Error('Not signed in');
      }
      setCards(await api.getFeed(accessToken, tab));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {cards, loading, error, refresh};
}
