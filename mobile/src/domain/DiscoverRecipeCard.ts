/**
 * Domain model for a Discover feed card (§5.4): a recipe the user could
 * cook if they shopped, annotated with how many of its ingredients they
 * already have.
 */

import type {Difficulty} from './RecipeCard';

export type DiscoverTab = 'for_you' | 'explore';

export interface DiscoverRecipeCard {
  readonly id: string;
  readonly name: string;
  readonly timeMinutes: number;
  readonly difficulty: Difficulty;
  readonly cuisineTags: readonly string[];
  readonly haveCount: number;
  readonly totalCount: number;
}

export function haveCountText(card: DiscoverRecipeCard): string {
  return `Have ${card.haveCount} of ${card.totalCount} ingredients`;
}
