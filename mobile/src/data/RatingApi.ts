/**
 * Thin API client for a user's rating history. Bearer-authenticated — the
 * backend derives the caller's identity from the verified Supabase access
 * token rather than a client-supplied id.
 */

import {API_BASE_URL} from './config';
import type {Rating} from '../domain/Rating';

interface RatingResponse {
  id: string;
  user_id: string;
  recipe_id: string;
  stars: number;
  quick_tags: string[];
  made_it_at: string;
}

function toDomain(dto: RatingResponse): Rating {
  return {
    id: dto.id,
    userId: dto.user_id,
    recipeId: dto.recipe_id,
    stars: dto.stars,
    quickTags: dto.quick_tags,
    madeItAt: dto.made_it_at,
  };
}

export class RatingApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  /** Returns an empty list for a user who hasn't completed onboarding yet. */
  async list(accessToken: string): Promise<Rating[]> {
    const res = await fetch(`${this.baseUrl}/ratings`, {
      headers: {Authorization: `Bearer ${accessToken}`},
    });
    if (res.status === 404) {
      return [];
    }
    if (!res.ok) {
      throw new Error(`Failed to load ratings: ${res.status}`);
    }
    const data = (await res.json()) as RatingResponse[];
    return data.map(toDomain);
  }
}
