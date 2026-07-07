/**
 * Hook that loads the full detail view for a single recipe.
 */

import {useCallback, useEffect, useState} from 'react';
import {RecipeApi} from '../../data/RecipeApi';
import type {RecipeDetail} from '../../domain/RecipeDetail';

const api = new RecipeApi();

export function useRecipeDetail(recipeId: string) {
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRecipe(await api.getDetail(recipeId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [recipeId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {recipe, loading, error, refresh};
}
