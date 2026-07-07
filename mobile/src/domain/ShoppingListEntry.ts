/**
 * Client-side model of a Shopping List tab entry.
 */

export interface ShoppingListEntry {
  readonly id: string;
  readonly ingredientId: string;
  readonly ingredientName: string;
  readonly checked: boolean;
  readonly quantityNeededAmount: number | null;
  readonly quantityNeededUnit: string | null;
}
