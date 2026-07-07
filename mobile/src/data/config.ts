/**
 * Client configuration. The API base URL can be overridden at build time.
 */

export const API_BASE_URL =
  process.env.SHELF_LIFE_API_URL ?? 'http://localhost:8000';

export const SUPABASE_URL =
  process.env.SHELF_LIFE_SUPABASE_URL ?? 'http://localhost:54321';

export const SUPABASE_ANON_KEY = process.env.SHELF_LIFE_SUPABASE_ANON_KEY ?? '';
