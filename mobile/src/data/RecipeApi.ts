/**
 * Thin API client for fetching a single recipe's full detail.
 */

import {API_BASE_URL} from './config';
import type {
  IngredientRole,
  RecipeDetail,
  RecipeDetailIngredient,
} from '../domain/RecipeDetail';
import type {Difficulty} from '../domain/RecipeCard';

interface RecipeDetailIngredientResponse {
  ingredient_id: string;
  ingredient_name: string;
  role: IngredientRole;
}

interface RecipeDetailResponse {
  id: string;
  name: string;
  time_minutes: number;
  difficulty: Difficulty;
  cuisine_tags: string[];
  ingredients: RecipeDetailIngredientResponse[];
  steps: string[];
}

function toIngredient(
  dto: RecipeDetailIngredientResponse,
): RecipeDetailIngredient {
  return {
    ingredientId: dto.ingredient_id,
    ingredientName: dto.ingredient_name,
    role: dto.role,
  };
}

function toDomain(dto: RecipeDetailResponse): RecipeDetail {
  return {
    id: dto.id,
    name: dto.name,
    timeMinutes: dto.time_minutes,
    difficulty: dto.difficulty,
    cuisineTags: dto.cuisine_tags,
    ingredients: dto.ingredients.map(toIngredient),
    steps: dto.steps,
  };
}

export class RecipeApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async getDetail(recipeId: string): Promise<RecipeDetail> {
    const res = await fetch(`${this.baseUrl}/recipes/${recipeId}`);
    if (!res.ok) {
      throw new Error(`Failed to load recipe: ${res.status}`);
    }
    return toDomain((await res.json()) as RecipeDetailResponse);
  }
}
