export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const CSRF_COOKIE_NAME =
  import.meta.env.VITE_CSRF_COOKIE_NAME ?? "careerpilot_csrf_token";

export const CSRF_HEADER_NAME =
  import.meta.env.VITE_CSRF_HEADER_NAME ?? "X-CSRF-Token";
