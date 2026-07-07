/**
 * Client-side model of the user authenticated via the login-with-username
 * edge function.
 */

export interface AuthUser {
  id: string;
  username: string;
}
