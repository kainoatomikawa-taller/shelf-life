/**
 * Client-side model of the user authenticated via the login-with-username
 * edge function.
 */

export interface AuthUser {
  id: string;
  username: string;
}

/** Fields submitted to the sign-up-with-username edge function. */
export interface SignUpRequest {
  name: string;
  username: string;
  email: string;
  password: string;
}
