import { CheckCircle2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { HumanRequestCard } from "@/features/decisions/HumanRequestCard";
import { useAttention } from "@/hooks/queries";

export function AttentionPage() {
  const { data: requests, isLoading } = useAttention();

  return (
    <AppShell title="Attention Queue">
      <ScrollArea className="h-full p-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-3">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}

          {requests?.map((r) => <HumanRequestCard key={r.id} request={r} showContext />)}

          {requests && requests.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-24 text-center text-muted-foreground">
              <CheckCircle2 className="h-8 w-8 text-status-completed" />
              <p className="text-sm">Nothing needs you right now.</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </AppShell>
  );
}
