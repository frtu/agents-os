import type { RealtimeConnection } from "@/realtime/types";
import { USE_MOCKS } from "@/api";
import { createMockStream } from "@/realtime/mockStream";
import { createWebSocketStream } from "@/realtime/ws";

/** The single realtime connection for the app. Mock by default; WS when disabled. */
export const realtime: RealtimeConnection = USE_MOCKS ? createMockStream() : createWebSocketStream();

export type { RealtimeConnection, RealtimeMessage, RealtimeMessageType } from "@/realtime/types";
