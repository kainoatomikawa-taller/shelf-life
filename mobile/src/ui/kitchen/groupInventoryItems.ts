/**
 * Grouping for the Kitchen list (§5.2): perishables can be grouped either
 * by storage location or by urgency; the separate pantry/spices view
 * groups by category instead.
 */

import {
  isLongLivedCategory,
  storageLocationLabel,
  STORAGE_LOCATIONS,
  type IngredientCategory,
} from '../../domain/Ingredient';
import {
  freshnessStatusLabel,
  URGENCY_ORDER,
  type InventoryItem,
} from '../../domain/InventoryItem';

export type GroupBy = 'location' | 'urgency';

export interface Section {
  readonly title: string;
  readonly data: readonly InventoryItem[];
}

export function splitPerishablesFromLongLived(items: readonly InventoryItem[]): {
  perishables: InventoryItem[];
  longLived: InventoryItem[];
} {
  const perishables: InventoryItem[] = [];
  const longLived: InventoryItem[] = [];
  for (const item of items) {
    (isLongLivedCategory(item.ingredientCategory) ? longLived : perishables).push(
      item,
    );
  }
  return {perishables, longLived};
}

export function groupPerishables(
  items: readonly InventoryItem[],
  groupBy: GroupBy,
): Section[] {
  if (groupBy === 'location') {
    return STORAGE_LOCATIONS.map(location => ({
      title: storageLocationLabel(location),
      data: items.filter(item => item.storageLocation === location),
    })).filter(section => section.data.length > 0);
  }

  return URGENCY_ORDER.map(status => ({
    title: freshnessStatusLabel(status),
    data: items.filter(item => item.freshnessStatus === status),
  })).filter(section => section.data.length > 0);
}

const LONG_LIVED_CATEGORY_LABELS: Record<Extract<IngredientCategory, 'pantry' | 'spice'>, string> = {
  pantry: 'Pantry',
  spice: 'Spices',
};

export function groupLongLived(items: readonly InventoryItem[]): Section[] {
  return (['pantry', 'spice'] as const)
    .map(category => ({
      title: LONG_LIVED_CATEGORY_LABELS[category],
      data: items.filter(item => item.ingredientCategory === category),
    }))
    .filter(section => section.data.length > 0);
}
