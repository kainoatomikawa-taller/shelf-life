/**
 * Domain model for a pantry item on the client.
 * Mirrors the backend contract but expresses client-side freshness helpers.
 */

export type Unit =
  | 'piece'
  | 'gram'
  | 'kilogram'
  | 'milliliter'
  | 'liter'
  | 'pack';

export type FreshnessStatus = 'fresh' | 'expiring_soon' | 'expired';

export interface PantryItem {
  readonly id: string;
  readonly ownerId: string;
  readonly name: string;
  readonly amount: number;
  readonly unit: Unit;
  readonly expirationDate: string; // ISO date (YYYY-MM-DD)
  readonly freshnessStatus: FreshnessStatus;
  readonly daysUntilExpiration: number;
}

export function freshnessColor(status: FreshnessStatus): string {
  switch (status) {
    case 'fresh':
      return '#2e7d32';
    case 'expiring_soon':
      return '#f9a825';
    case 'expired':
      return '#c62828';
  }
}
