/**
 * Thin API client for submitting a user's onboarding taste profile.
 * Maps between the client's camelCase domain model and the backend's
 * snake_case contract.
 */

import {API_BASE_URL} from './config';
import type {OnboardingAnswers, UserProfile} from '../domain/UserProfile';

interface UserProfileResponse {
  id: string;
  allergies: string[];
  diet_type: UserProfile['dietType'];
  liked_cuisines: string[];
  flavor_profile: UserProfile['flavorProfile'];
  skill_level: UserProfile['skillLevel'];
  typical_time_available_minutes: number;
  equipment: string[];
  budget_sensitivity: UserProfile['budgetSensitivity'];
  adventurousness: number;
  taste_vector: UserProfile['tasteVector'];
}

function toDomain(dto: UserProfileResponse): UserProfile {
  return {
    id: dto.id,
    allergies: dto.allergies,
    dietType: dto.diet_type,
    likedCuisines: dto.liked_cuisines,
    flavorProfile: dto.flavor_profile,
    skillLevel: dto.skill_level,
    typicalTimeAvailableMinutes: dto.typical_time_available_minutes,
    equipment: dto.equipment,
    budgetSensitivity: dto.budget_sensitivity,
    adventurousness: dto.adventurousness,
    tasteVector: dto.taste_vector,
  };
}

export class UserApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  async submitOnboarding(
    userId: string,
    answers: OnboardingAnswers,
  ): Promise<UserProfile> {
    const res = await fetch(
      `${this.baseUrl}/users/${encodeURIComponent(userId)}/profile`,
      {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          allergies: answers.allergies,
          diet_type: answers.dietType,
          liked_cuisines: answers.likedCuisines,
          flavor_profile: answers.flavorProfile,
          skill_level: answers.skillLevel,
          typical_time_available_minutes: answers.typicalTimeAvailableMinutes,
          equipment: answers.equipment,
          budget_sensitivity: answers.budgetSensitivity,
          adventurousness: answers.adventurousness,
        }),
      },
    );
    if (!res.ok) {
      throw new Error(`Failed to submit onboarding: ${res.status}`);
    }
    return toDomain((await res.json()) as UserProfileResponse);
  }
}
