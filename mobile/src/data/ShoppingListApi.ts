/**
 * Thin API client for the Shopping List tab. Bearer-authenticated — the
 * backend derives the caller's identity from the verified Supabase access
 * token rather than a client-supplied id.
 */

import {API_BASE_URL} from './config';
import type {ShoppingListEntry} from '../domain/ShoppingListEntry';

interface ShoppingListEntryResponse {
  id: string;
  ingredient_id: string;
  ingredient_name: string;
  checked: boolean;
  quantity_needed_amount: number | null;
  quantity_needed_unit: string | null;
}

function toDomain(dto: ShoppingListEntryResponse): ShoppingListEntry {
  return {
    id: dto.id,
    ingredientId: dto.ingredient_id,
    ingredientName: dto.ingredient_name,
    checked: dto.checked,
    quantityNeededAmount: dto.quantity_needed_amount,
    quantityNeededUnit: dto.quantity_needed_unit,
  };
}

export class ShoppingListApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async list(accessToken: string): Promise<ShoppingListEntry[]> {
    const res = await fetch(`${this.baseUrl}/shopping-list`, {
      headers: {Authorization: `Bearer ${accessToken}`},
    });
    if (!res.ok) {
      throw new Error(`Failed to load shopping list: ${res.status}`);
    }
    const data = (await res.json()) as ShoppingListEntryResponse[];
    return data.map(toDomain);
  }
}
