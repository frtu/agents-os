import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { realtime } from "@/realtime";
import type { RealtimeMessage } from "@/realtime/types";
import { qk } from "@/hooks/queryKeys";

/**
 * Bridges the realtime stream to the TanStack Query cache: each server message
 * invalidates the affected projections so queries refetch. The stream is never
 * a second source of truth (see specs/api/realtime.md).
 */
export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();

  useEffect(() => {
    const handle = (msg: RealtimeMessage) => {
      switch (msg.type) {
        case "StoryUpdated":
          qc.invalidateQueries({ queryKey: qk.boards });
          break;
        case "ExecutionUpdated":
          qc.invalidateQueries({ queryKey: qk.execution(msg.aggregateId) });
          qc.invalidateQueries({ queryKey: qk.boards });
          break;
        case "TimelineUpdated":
          qc.invalidateQueries({ queryKey: qk.timeline(msg.aggregateId) });
          break;
        case "DecisionRequested":
        case "AttentionUpdated":
          qc.invalidateQueries({ queryKey: qk.attention });
          qc.invalidateQueries({ queryKey: qk.boards });
          break;
        case "DecisionApplied": {
          const executionId = (msg.payload?.executionId as string) ?? msg.aggregateId;
          qc.invalidateQueries({ queryKey: qk.execution(executionId) });
          qc.invalidateQueries({ queryKey: qk.decisions(executionId) });
          qc.invalidateQueries({ queryKey: qk.attention });
          break;
        }
        case "ArtifactProduced": {
          const storyId = msg.payload?.storyId as string | undefined;
          if (storyId) qc.invalidateQueries({ queryKey: qk.artifacts(storyId) });
          break;
        }
        case "NotificationCreated":
          qc.invalidateQueries({ queryKey: qk.notifications });
          break;
      }
    };

    const unsubscribe = realtime.subscribe(handle);
    realtime.start();
    return () => {
      unsubscribe();
      realtime.stop();
    };
  }, [qc]);

  return <>{children}</>;
}
