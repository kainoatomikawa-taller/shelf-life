/**
 * Hook that loads pantry items for the current user.
 */

import {useCallback, useEffect, useState} from 'react';
import {PantryApi} from '../data/PantryApi';
import type {PantryItem} from '../domain/PantryItem';

const api = new PantryApi();

export function usePantryItems(ownerId: string) {
  const [items, setItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await api.list(ownerId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [ownerId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {items, loading, error, refresh};
}
