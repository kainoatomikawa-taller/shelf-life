/**
 * Thin API client for adding an inventory item from the add-item screen
 * (§5.2). Only ownerId/ingredientId are required — every other field is
 * skippable and left undefined so the backend applies its smart defaults.
 */

import {API_BASE_URL} from './config';
import type {QuantityState, StorageLocation} from '../domain/Ingredient';
import type {
  FreshnessDateType,
  FreshnessDisplayStatus,
  InventoryItem,
} from '../domain/InventoryItem';

interface InventoryItemResponse {
  id: string;
  user_id: string;
  ingredient_id: string;
  ingredient_name: string;
  quantity_state: QuantityState;
  storage_location: StorageLocation;
  purchase_date: string | null;
  printed_package_date: string | null;
  is_frozen: boolean;
  computed_freshness_date: string;
  freshness_date_type: FreshnessDateType;
  freshness_status: FreshnessDisplayStatus;
  added_at: string;
  notes: string | null;
}

function toDomain(dto: InventoryItemResponse): InventoryItem {
  return {
    id: dto.id,
    userId: dto.user_id,
    ingredientId: dto.ingredient_id,
    ingredientName: dto.ingredient_name,
    quantityState: dto.quantity_state,
    storageLocation: dto.storage_location,
    purchaseDate: dto.purchase_date,
    printedPackageDate: dto.printed_package_date,
    isFrozen: dto.is_frozen,
    computedFreshnessDate: dto.computed_freshness_date,
    freshnessDateType: dto.freshness_date_type,
    freshnessStatus: dto.freshness_status,
    addedAt: dto.added_at,
    notes: dto.notes,
  };
}

export interface AddInventoryItemPayload {
  userId: string;
  ingredientId: string;
  quantityState?: QuantityState;
  storageLocation?: StorageLocation;
  purchaseDate?: string;
  printedPackageDate?: string;
  isFrozen?: boolean;
}

export class InventoryApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async add(payload: AddInventoryItemPayload): Promise<InventoryItem> {
    const res = await fetch(`${this.baseUrl}/inventory-items`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        user_id: payload.userId,
        ingredient_id: payload.ingredientId,
        quantity_state: payload.quantityState ?? null,
        storage_location: payload.storageLocation ?? null,
        purchase_date: payload.purchaseDate ?? null,
        printed_package_date: payload.printedPackageDate ?? null,
        is_frozen: payload.isFrozen ?? false,
      }),
    });
    if (!res.ok) {
      throw new Error(`Failed to add inventory item: ${res.status}`);
    }
    return toDomain((await res.json()) as InventoryItemResponse);
  }

  async list(userId: string): Promise<InventoryItem[]> {
    const res = await fetch(
      `${this.baseUrl}/inventory-items?user_id=${encodeURIComponent(userId)}`,
    );
    if (!res.ok) {
      throw new Error(`Failed to load inventory items: ${res.status}`);
    }
    const data = (await res.json()) as InventoryItemResponse[];
    return data.map(toDomain);
  }
}
