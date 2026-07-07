/**
 * Hook that loads one tab of the Discover feed for the current user.
 */

import {useCallback, useEffect, useState} from 'react';
import {DiscoverApi} from '../../data/DiscoverApi';
import type {DiscoverRecipeCard, DiscoverTab} from '../../domain/DiscoverRecipeCard';

const api = new DiscoverApi();

export function useDiscoverFeed(userId: string, tab: DiscoverTab) {
  const [cards, setCards] = useState<DiscoverRecipeCard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCards(await api.getFeed(userId, tab));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [userId, tab]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {cards, loading, error, refresh};
}
