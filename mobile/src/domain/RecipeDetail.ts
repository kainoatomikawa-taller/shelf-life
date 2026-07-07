/**
 * Domain model for a recipe's full detail view: every ingredient (essential
 * or optional) and the step-by-step procedure, shown once a user taps into
 * a Discover or Cook Now card.
 */

import type {Difficulty} from './RecipeCard';

export type IngredientRole = 'essential' | 'optional';

export interface RecipeDetailIngredient {
  readonly ingredientId: string;
  readonly ingredientName: string;
  readonly role: IngredientRole;
}

export interface RecipeDetail {
  readonly id: string;
  readonly name: string;
  readonly timeMinutes: number;
  readonly difficulty: Difficulty;
  readonly cuisineTags: readonly string[];
  readonly ingredients: readonly RecipeDetailIngredient[];
  readonly steps: readonly string[];
}
