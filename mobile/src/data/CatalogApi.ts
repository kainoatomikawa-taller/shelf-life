/**
 * Thin API client for the ingredient catalog search box on the add-item
 * screen (§5.2). Backs alias-aware search, e.g. "scallion" -> "Green
 * Onions" (AC1).
 */

import {API_BASE_URL} from './config';
import type {IngredientCategory, IngredientSummary, StorageLocation} from '../domain/Ingredient';

interface IngredientSummaryResponse {
  id: string;
  name: string;
  aliases: string[];
  category: IngredientCategory;
  default_storage_location: StorageLocation;
}

function toDomain(dto: IngredientSummaryResponse): IngredientSummary {
  return {
    id: dto.id,
    name: dto.name,
    aliases: dto.aliases,
    category: dto.category,
    defaultStorageLocation: dto.default_storage_location,
  };
}

export class CatalogApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async searchIngredients(
    query: string,
    limit = 20,
  ): Promise<IngredientSummary[]> {
    if (!query.trim()) {
      return [];
    }
    const params = new URLSearchParams({query, limit: String(limit)});
    const res = await fetch(`${this.baseUrl}/catalog/ingredients?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to search ingredients: ${res.status}`);
    }
    const data = (await res.json()) as IngredientSummaryResponse[];
    return data.map(toDomain);
  }
}
