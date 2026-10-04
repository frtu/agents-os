import { useEffect, useState } from "react";
import { realtime, type RealtimeMessage } from "@/realtime";

interface Entry extends RealtimeMessage {
  receivedAt: string;
  n: number;
}

const MAX_EVENTS = 200;

/** Live, newest-first realtime messages (spec 001 FR-12). */
export function EventLog() {
  const [events, setEvents] = useState<Entry[]>([]);

  useEffect(() => {
    let n = 0;
    return realtime.subscribe((msg) => {
      n += 1;
      const entry = { ...msg, receivedAt: new Date().toLocaleTimeString(), n };
      setEvents((prev) => [entry, ...prev].slice(0, MAX_EVENTS));
    });
  }, []);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{events.length} event{events.length === 1 ? "" : "s"}</span>
        <button type="button" className="hover:text-foreground" onClick={() => setEvents([])}>
          clear
        </button>
      </div>
      {events.length === 0 && <p className="text-xs text-muted-foreground">Waiting for realtime messages…</p>}
      <ul className="flex flex-col gap-1">
        {events.map((e) => (
          <li key={e.n} className="rounded-md border border-border px-2 py-1.5 text-xs">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{e.type}</span>
              <span className="text-muted-foreground">{e.receivedAt}</span>
            </div>
            <div className="truncate font-mono text-[11px] text-muted-foreground">
              {e.aggregateId} · #{e.sequence}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
