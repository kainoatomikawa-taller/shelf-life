/**
 * Thin API client for the Cook Now feed (§5.3): For You / Explore tabs of
 * recipes the user can cook right now.
 */

import {API_BASE_URL} from './config';
import type {
  CookNowTab,
  Difficulty,
  RecipeBadges,
  RecipeCard,
  SubstitutionSuggestion,
} from '../domain/RecipeCard';

interface SubstitutionSuggestionResponse {
  from_ingredient_id: string;
  from_ingredient_name: string;
  to_ingredient_id: string;
  to_ingredient_name: string;
  disclosure: string;
  ratio_note: string | null;
  confidence: number;
}

interface RecipeBadgesResponse {
  expiring_ingredient_name: string | null;
  low_stock_ingredient_name: string | null;
  substitution_count: number;
}

interface RecipeCardResponse {
  id: string;
  name: string;
  time_minutes: number;
  difficulty: Difficulty;
  cuisine_tags: string[];
  badges: RecipeBadgesResponse;
  substitutions: SubstitutionSuggestionResponse[];
}

function toSubstitution(
  dto: SubstitutionSuggestionResponse,
): SubstitutionSuggestion {
  return {
    fromIngredientId: dto.from_ingredient_id,
    fromIngredientName: dto.from_ingredient_name,
    toIngredientId: dto.to_ingredient_id,
    toIngredientName: dto.to_ingredient_name,
    disclosure: dto.disclosure,
    ratioNote: dto.ratio_note,
    confidence: dto.confidence,
  };
}

function toBadges(dto: RecipeBadgesResponse): RecipeBadges {
  return {
    expiringIngredientName: dto.expiring_ingredient_name,
    lowStockIngredientName: dto.low_stock_ingredient_name,
    substitutionCount: dto.substitution_count,
  };
}

function toDomain(dto: RecipeCardResponse): RecipeCard {
  return {
    id: dto.id,
    name: dto.name,
    timeMinutes: dto.time_minutes,
    difficulty: dto.difficulty,
    cuisineTags: dto.cuisine_tags,
    badges: toBadges(dto.badges),
    substitutions: dto.substitutions.map(toSubstitution),
  };
}

export class CookNowApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async getFeed(userId: string, tab: CookNowTab): Promise<RecipeCard[]> {
    const params = new URLSearchParams({user_id: userId, tab});
    const res = await fetch(`${this.baseUrl}/cook-now/feed?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to load Cook Now feed: ${res.status}`);
    }
    const data = (await res.json()) as RecipeCardResponse[];
    return data.map(toDomain);
  }
}
