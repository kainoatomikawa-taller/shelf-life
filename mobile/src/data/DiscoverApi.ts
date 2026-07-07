/**
 * Thin API client for the Discover feed (§5.4): For You / Explore tabs of
 * recipes the user could cook if they shopped.
 */

import {API_BASE_URL} from './config';
import type {
  DiscoverRecipeCard,
  DiscoverTab,
} from '../domain/DiscoverRecipeCard';
import type {Difficulty} from '../domain/RecipeCard';

interface DiscoverRecipeCardResponse {
  id: string;
  name: string;
  time_minutes: number;
  difficulty: Difficulty;
  cuisine_tags: string[];
  have_count: number;
  total_count: number;
}

function toDomain(dto: DiscoverRecipeCardResponse): DiscoverRecipeCard {
  return {
    id: dto.id,
    name: dto.name,
    timeMinutes: dto.time_minutes,
    difficulty: dto.difficulty,
    cuisineTags: dto.cuisine_tags,
    haveCount: dto.have_count,
    totalCount: dto.total_count,
  };
}

export class DiscoverApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async getFeed(userId: string, tab: DiscoverTab): Promise<DiscoverRecipeCard[]> {
    const params = new URLSearchParams({user_id: userId, tab});
    const res = await fetch(`${this.baseUrl}/discover/feed?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to load Discover feed: ${res.status}`);
    }
    const data = (await res.json()) as DiscoverRecipeCardResponse[];
    return data.map(toDomain);
  }
}
