/**
 * Thin client for the /profiles endpoints. Unlike the rest of this app's
 * API clients, these calls are bearer-authenticated — the backend derives
 * the caller's identity from the verified Supabase access token rather
 * than a client-supplied id.
 */

import {API_BASE_URL} from './config';
import type {Profile} from '../domain/Profile';

interface ProfileResponse {
  id: string;
  username: string;
  display_name: string;
  created_at: string;
}

function toDomain(dto: ProfileResponse): Profile {
  return {
    id: dto.id,
    username: dto.username,
    displayName: dto.display_name,
    createdAt: dto.created_at,
  };
}

export class ProfileApi {
  constructor(private readonly baseUrl: string = API_BASE_URL) {}

  /** Returns null if the signed-in account has no profile yet. */
  async getMine(accessToken: string): Promise<Profile | null> {
    const res = await fetch(`${this.baseUrl}/profiles/me`, {
      headers: {Authorization: `Bearer ${accessToken}`},
    });
    if (res.status === 404) {
      return null;
    }
    if (!res.ok) {
      throw new Error(`Failed to load profile: ${res.status}`);
    }
    return toDomain((await res.json()) as ProfileResponse);
  }

  /**
   * Creates the caller's profile. A 409 means either this account already
   * has one (benign — resolved by re-fetching it) or the username is taken
   * by someone else (surfaced as an error).
   */
  async create(
    accessToken: string,
    username: string,
    displayName: string,
  ): Promise<Profile> {
    const res = await fetch(`${this.baseUrl}/profiles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({username, display_name: displayName}),
    });
    if (res.status === 409) {
      const existing = await this.getMine(accessToken);
      if (existing) {
        return existing;
      }
      throw new Error('That username is already taken.');
    }
    if (!res.ok) {
      throw new Error(`Failed to create profile: ${res.status}`);
    }
    return toDomain((await res.json()) as ProfileResponse);
  }

  /**
   * Edits display_name and/or username on the Profile screen. Username
   * changes are unlimited with no cooldown; a 409 means the requested
   * username is already taken by someone else.
   */
  async update(
    accessToken: string,
    fields: {username?: string; displayName?: string},
  ): Promise<Profile> {
    const res = await fetch(`${this.baseUrl}/profiles/me`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        username: fields.username,
        display_name: fields.displayName,
      }),
    });
    if (res.status === 409) {
      throw new Error('That username is already taken.');
    }
    if (!res.ok) {
      throw new Error(`Failed to update profile: ${res.status}`);
    }
    return toDomain((await res.json()) as ProfileResponse);
  }
}
