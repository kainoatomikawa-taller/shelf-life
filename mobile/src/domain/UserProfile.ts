/**
 * Client-side model of a user's taste profile, collected during onboarding.
 * Mirrors the backend's hard-constraint / soft-preference split (§4.6):
 * allergies and diet type are safety-critical, everything else only
 * personalizes ranking.
 */

export type DietType =
  | 'omnivore'
  | 'vegetarian'
  | 'vegan'
  | 'pescatarian'
  | 'keto'
  | 'paleo'
  | 'gluten_free'
  | 'dairy_free'
  | 'halal'
  | 'kosher';

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced';

export type BudgetSensitivity = 'low' | 'medium' | 'high';

export type FlavorDimension =
  | 'sweetness'
  | 'saltiness'
  | 'sourness'
  | 'bitterness'
  | 'spiciness'
  | 'umami';

export type FlavorProfile = Record<FlavorDimension, number>;

export const DEFAULT_FLAVOR_PROFILE: FlavorProfile = {
  sweetness: 0.5,
  saltiness: 0.5,
  sourness: 0.5,
  bitterness: 0.5,
  spiciness: 0.5,
  umami: 0.5,
};

export interface OnboardingAnswers {
  readonly allergies: string[];
  readonly dietType: DietType;
  readonly likedCuisines: string[];
  readonly flavorProfile: FlavorProfile;
  readonly skillLevel: SkillLevel;
  readonly typicalTimeAvailableMinutes: number;
  readonly equipment: string[];
  readonly budgetSensitivity: BudgetSensitivity;
  readonly adventurousness: number;
}

export const DEFAULT_ONBOARDING_ANSWERS: OnboardingAnswers = {
  allergies: [],
  dietType: 'omnivore',
  likedCuisines: [],
  flavorProfile: DEFAULT_FLAVOR_PROFILE,
  skillLevel: 'beginner',
  typicalTimeAvailableMinutes: 30,
  equipment: [],
  budgetSensitivity: 'medium',
  adventurousness: 0.5,
};

export interface UserProfile {
  readonly id: string;
  readonly allergies: string[];
  readonly dietType: DietType;
  readonly likedCuisines: string[];
  readonly flavorProfile: FlavorProfile;
  readonly skillLevel: SkillLevel;
  readonly typicalTimeAvailableMinutes: number;
  readonly equipment: string[];
  readonly budgetSensitivity: BudgetSensitivity;
  readonly adventurousness: number;
  readonly tasteVector: FlavorProfile;
}
