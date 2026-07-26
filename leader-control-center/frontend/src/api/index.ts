import type { ApiClient } from "@/api/types";
import { mockClient } from "@/api/mock/mockClient";
import { httpClient } from "@/api/http";

export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== "false";

/** The single API client the app talks to. Mock by default; HTTP when disabled. */
export const api: ApiClient = USE_MOCKS ? mockClient : httpClient;

export type { ApiClient, DecisionInput } from "@/api/types";
