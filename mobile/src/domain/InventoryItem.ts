/**
 * Domain model for an inventory item on the client — the result of adding
 * an item via the add-item screen (§5.2).
 */

import type {IngredientCategory, QuantityState, StorageLocation} from './Ingredient';

export type FreshnessDateType = 'package' | 'est-from-purchase' | 'est-unknown';

export type FreshnessDisplayStatus =
  | 'fresh'
  | 'use_soon'
  | 'use_now'
  | 'past_estimate_check_it';

export interface SpoilageCheckTip {
  readonly smell: string;
  readonly look: string;
  readonly texture: string;
}

export interface InventoryItem {
  readonly id: string;
  readonly userId: string;
  readonly ingredientId: string;
  readonly ingredientName: string;
  readonly ingredientCategory: IngredientCategory;
  readonly quantityState: QuantityState;
  readonly storageLocation: StorageLocation;
  readonly purchaseDate: string | null;
  readonly printedPackageDate: string | null;
  readonly isFrozen: boolean;
  readonly computedFreshnessDate: string;
  readonly freshnessDateType: FreshnessDateType;
  readonly freshnessDateLabel: string;
  readonly freshnessDateTooltip: string;
  readonly freshnessStatus: FreshnessDisplayStatus;
  readonly spoilageCheckTip: SpoilageCheckTip | null;
  readonly addedAt: string;
  readonly notes: string | null;
}

/** Most urgent first — the default sort/group order for the "by urgency"
 * view of the Kitchen list (§5.2). */
export const URGENCY_ORDER: readonly FreshnessDisplayStatus[] = [
  'past_estimate_check_it',
  'use_now',
  'use_soon',
  'fresh',
];

export function freshnessStatusColor(status: FreshnessDisplayStatus): string {
  switch (status) {
    case 'fresh':
      return '#2e7d32';
    case 'use_soon':
      return '#f9a825';
    case 'use_now':
      return '#ef6c00';
    case 'past_estimate_check_it':
      return '#c62828';
  }
}

export function freshnessStatusLabel(status: FreshnessDisplayStatus): string {
  switch (status) {
    case 'fresh':
      return 'Fresh';
    case 'use_soon':
      return 'Use soon';
    case 'use_now':
      return 'Use now';
    case 'past_estimate_check_it':
      return 'Past estimate — check it';
  }
}
