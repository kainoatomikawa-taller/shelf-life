/**
 * Client-side model of a user's public profile (username + display name),
 * fetched from the backend's bearer-authenticated /profiles endpoints.
 */

export interface Profile {
  readonly id: string;
  readonly username: string;
  readonly displayName: string;
  readonly createdAt: string;
}
