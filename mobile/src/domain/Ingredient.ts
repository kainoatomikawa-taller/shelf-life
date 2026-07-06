/**
 * Domain model for a catalog ingredient on the client — the result shape
 * for the add-item screen's search box (§5.2).
 */

export type StorageLocation = 'fridge' | 'counter' | 'freezer' | 'pantry';

export type QuantityState = 'in' | 'low' | 'out';

export type IngredientCategory =
  | 'perishable_fridge'
  | 'perishable_counter'
  | 'frozen'
  | 'pantry'
  | 'spice';

export interface IngredientSummary {
  readonly id: string;
  readonly name: string;
  readonly aliases: readonly string[];
  readonly category: IngredientCategory;
  readonly defaultStorageLocation: StorageLocation;
}

export const STORAGE_LOCATIONS: readonly StorageLocation[] = [
  'fridge',
  'counter',
  'freezer',
  'pantry',
];

export const QUANTITY_STATES: readonly QuantityState[] = ['in', 'low', 'out'];

export function storageLocationLabel(location: StorageLocation): string {
  switch (location) {
    case 'fridge':
      return 'Fridge';
    case 'counter':
      return 'Counter';
    case 'freezer':
      return 'Freezer';
    case 'pantry':
      return 'Pantry';
  }
}

export function quantityStateLabel(state: QuantityState): string {
  switch (state) {
    case 'in':
      return 'In stock';
    case 'low':
      return 'Running low';
    case 'out':
      return 'Out';
  }
}

/** The alias that matched the search query, if the match wasn't on the
 * canonical name — lets the UI confirm "scallion" resolved to "Green
 * Onions" (§5.2 AC1). */
export function matchedAlias(
  ingredient: IngredientSummary,
  query: string,
): string | null {
  const q = query.trim().toLowerCase();
  if (!q || ingredient.name.toLowerCase() === q) {
    return null;
  }
  return ingredient.aliases.find(alias => alias.toLowerCase() === q) ?? null;
}
