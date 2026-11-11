import { createApiClient } from "@driftless/api-client";

/** Single API client for the app. Auth headers are added here once SSO lands (S10). */
export const api = createApiClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api/v1" });
