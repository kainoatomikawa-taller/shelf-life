/**
 * Client-side model of a recorded post-cook rating.
 */

export interface Rating {
  readonly id: string;
  readonly userId: string;
  readonly recipeId: string;
  readonly stars: number;
  readonly quickTags: string[];
  readonly madeItAt: string;
}
