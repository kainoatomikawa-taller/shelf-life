/**
 * Thin API client for the Shelf Life backend.
 * Maps backend snake_case responses to the client's PantryItem domain model.
 */

import {API_BASE_URL} from './config';
import type {PantryItem, Unit} from '../domain/PantryItem';

interface PantryItemResponse {
  id: string;
  owner_id: string;
  name: string;
  amount: number;
  unit: Unit;
  expiration_date: string;
  freshness_status: PantryItem['freshnessStatus'];
  days_until_expiration: number;
}

function toDomain(dto: PantryItemResponse): PantryItem {
  return {
    id: dto.id,
    ownerId: dto.owner_id,
    name: dto.name,
    amount: dto.amount,
    unit: dto.unit,
    expirationDate: dto.expiration_date,
    freshnessStatus: dto.freshness_status,
    daysUntilExpiration: dto.days_until_expiration,
  };
}

export interface AddPantryItemPayload {
  ownerId: string;
  name: string;
  amount: number;
  unit: Unit;
  expirationDate: string;
}

export class PantryApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async list(ownerId: string): Promise<PantryItem[]> {
    const res = await fetch(
      `${this.baseUrl}/pantry-items?owner_id=${encodeURIComponent(ownerId)}`,
    );
    if (!res.ok) {
      throw new Error(`Failed to load pantry items: ${res.status}`);
    }
    const data = (await res.json()) as PantryItemResponse[];
    return data.map(toDomain);
  }

  async add(payload: AddPantryItemPayload): Promise<PantryItem> {
    const res = await fetch(`${this.baseUrl}/pantry-items`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        owner_id: payload.ownerId,
        name: payload.name,
        amount: payload.amount,
        unit: payload.unit,
        expiration_date: payload.expirationDate,
      }),
    });
    if (!res.ok) {
      throw new Error(`Failed to add pantry item: ${res.status}`);
    }
    return toDomain((await res.json()) as PantryItemResponse);
  }
}
