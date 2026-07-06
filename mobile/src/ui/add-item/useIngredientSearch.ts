/**
 * Debounced type-ahead search against the ingredient catalog (§5.2 AC1).
 * Debouncing avoids firing a request on every keystroke while the user is
 * still typing.
 */

import {useEffect, useRef, useState} from 'react';
import {CatalogApi} from '../../data/CatalogApi';
import type {IngredientSummary} from '../../domain/Ingredient';

const DEBOUNCE_MS = 250;

const api = new CatalogApi();

export function useIngredientSearch(query: string) {
  const [results, setResults] = useState<IngredientSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    const currentRequest = ++requestId.current;
    const timer = setTimeout(() => {
      api
        .searchIngredients(trimmed)
        .then(found => {
          if (requestId.current === currentRequest) {
            setResults(found);
            setError(null);
          }
        })
        .catch(e => {
          if (requestId.current === currentRequest) {
            setError(e instanceof Error ? e.message : 'Unknown error');
          }
        })
        .finally(() => {
          if (requestId.current === currentRequest) {
            setLoading(false);
          }
        });
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [query]);

  return {results, loading, error};
}
