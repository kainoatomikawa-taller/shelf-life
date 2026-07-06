/**
 * Domain model for a Cook Now feed card (§5.3): a recipe that's currently
 * cookable — every essential ingredient is on hand or has a valid swap —
 * annotated with the badges that explain why it's surfaced.
 */

export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

export type CookNowTab = 'for_you' | 'explore';

export interface SubstitutionSuggestion {
  readonly fromIngredientId: string;
  readonly fromIngredientName: string;
  readonly toIngredientId: string;
  readonly toIngredientName: string;
  readonly disclosure: string;
  readonly ratioNote: string | null;
  readonly confidence: number;
}

export interface RecipeBadges {
  readonly expiringIngredientName: string | null;
  readonly lowStockIngredientName: string | null;
  readonly substitutionCount: number;
}

export interface RecipeCard {
  readonly id: string;
  readonly name: string;
  readonly timeMinutes: number;
  readonly difficulty: Difficulty;
  readonly cuisineTags: readonly string[];
  readonly badges: RecipeBadges;
  readonly substitutions: readonly SubstitutionSuggestion[];
}

export function difficultyLabel(difficulty: Difficulty): string {
  switch (difficulty) {
    case 'beginner':
      return 'Beginner';
    case 'intermediate':
      return 'Intermediate';
    case 'advanced':
      return 'Advanced';
  }
}

export function expiringBadgeText(ingredientName: string): string {
  return `Uses ${ingredientName} — use it soon!`;
}

export function substitutionsBadgeText(count: number): string {
  return count === 1 ? '1 substitution' : `${count} substitutions`;
}

export function lowStockBadgeText(ingredientName: string): string {
  return `You're low on ${ingredientName}`;
}
