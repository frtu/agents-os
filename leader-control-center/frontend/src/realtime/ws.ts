import type { RealtimeConnection, RealtimeMessage } from "@/realtime/types";

const WS_URL = import.meta.env.VITE_WS_URL ?? "/api/v1/stream";
const RECONNECT_MS = 3000;

function resolveWsUrl(url: string): string {
  if (url.startsWith("ws://") || url.startsWith("wss://")) return url;
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${url.startsWith("/") ? url : `/${url}`}`;
}

/** WebSocket-backed RealtimeConnection per specs/api/realtime.md. */
export function createWebSocketStream(): RealtimeConnection {
  const listeners = new Set<(msg: RealtimeMessage) => void>();
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let closedByClient = false;

  function connect() {
    socket = new WebSocket(resolveWsUrl(WS_URL));

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as RealtimeMessage;
        listeners.forEach((l) => l(msg));
      } catch {
        /* ignore malformed frames */
      }
    };

    socket.onclose = () => {
      socket = null;
      if (!closedByClient) {
        reconnectTimer = setTimeout(connect, RECONNECT_MS);
      }
    };

    socket.onerror = () => socket?.close();
  }

  return {
    start() {
      if (socket) return;
      closedByClient = false;
      connect();
    },
    stop() {
      closedByClient = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = null;
      socket?.close();
      socket = null;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
