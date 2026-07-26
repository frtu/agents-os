import type { RealtimeConnection, RealtimeMessage } from "@/realtime/types";
import { mockServer } from "@/api/mock/server";

/** How often the simulated backend advances running executions. */
const TICK_MS = 2500;

/**
 * A RealtimeConnection backed by the in-browser mock server. It fans out the
 * server's emitted messages and drives execution progress on an interval.
 */
export function createMockStream(): RealtimeConnection {
  const listeners = new Set<(msg: RealtimeMessage) => void>();
  let unsubscribeServer: (() => void) | null = null;
  let timer: ReturnType<typeof setInterval> | null = null;

  return {
    start() {
      if (unsubscribeServer) return;
      mockServer.ensureSeeded();
      unsubscribeServer = mockServer.subscribe((msg) => {
        listeners.forEach((l) => l(msg));
      });
      timer = setInterval(() => mockServer.tick(), TICK_MS);
    },
    stop() {
      unsubscribeServer?.();
      unsubscribeServer = null;
      if (timer) clearInterval(timer);
      timer = null;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
