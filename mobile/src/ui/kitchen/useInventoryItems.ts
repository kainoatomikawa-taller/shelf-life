/**
 * Loads a user's inventory items and exposes the Kitchen list's per-item
 * quick actions (§5.2 AC2): one-tap Mark Low / Mark Out, used-it-up,
 * delete, and edit dates. Each action updates local state from the
 * server's response (or removal) rather than re-fetching the whole list.
 */

import {useCallback, useEffect, useState} from 'react';
import {InventoryApi} from '../../data/InventoryApi';
import {getAccessToken} from '../../data/supabaseClient';
import type {QuantityState} from '../../domain/Ingredient';
import type {InventoryItem} from '../../domain/InventoryItem';

const api = new InventoryApi();

async function requireAccessToken(): Promise<string> {
  const token = await getAccessToken();
  if (!token) {
    throw new Error('Not signed in');
  }
  return token;
}

export function useInventoryItems() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await api.list(await requireAccessToken()));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const setQuantityState = useCallback(
    async (itemId: string, quantityState: QuantityState) => {
      try {
        const accessToken = await requireAccessToken();
        const updated = await api.updateQuantityState(
          accessToken,
          itemId,
          quantityState,
        );
        setItems(current =>
          current.map(item => (item.id === itemId ? updated : item)),
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unknown error');
      }
    },
    [],
  );

  const editDates = useCallback(
    async (
      itemId: string,
      dates: {purchaseDate?: string; printedPackageDate?: string},
    ) => {
      try {
        const accessToken = await requireAccessToken();
        const updated = await api.updateDates(accessToken, itemId, dates);
        setItems(current =>
          current.map(item => (item.id === itemId ? updated : item)),
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unknown error');
      }
    },
    [],
  );

  const remove = useCallback(async (itemId: string) => {
    try {
      const accessToken = await requireAccessToken();
      await api.remove(accessToken, itemId);
      setItems(current => current.filter(item => item.id !== itemId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    }
  }, []);

  return {items, loading, error, refresh, setQuantityState, editDates, remove};
}
