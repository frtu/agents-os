import { BellOff } from "lucide-react";
import type { NotificationStatus } from "@/types/domain";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn, timeAgo } from "@/lib/utils";
import { useNotifications } from "@/hooks/queries";
import {
  useAckNotification,
  useCloseNotification,
  useOpenNotification,
} from "@/hooks/mutations";
import { useUiStore } from "@/store/ui";

// The single forward action available from each open state.
const nextAction: Record<Exclude<NotificationStatus, "CLOSED">, string> = {
  UNREAD: "Open",
  READ: "Acknowledge",
  ACKED: "Close",
};

export function NotificationsSheet() {
  const open = useUiStore((s) => s.notificationsOpen);
  const setOpen = useUiStore((s) => s.setNotificationsOpen);
  const { data: notifications } = useNotifications();
  const openNotification = useOpenNotification();
  const ackNotification = useAckNotification();
  const closeNotification = useCloseNotification();

  const advance = (id: string, status: NotificationStatus) => {
    if (status === "UNREAD") openNotification.mutate(id);
    else if (status === "READ") ackNotification.mutate(id);
    else if (status === "ACKED") closeNotification.mutate(id);
  };

  return (
    <Sheet open={open} onClose={() => setOpen(false)} className="max-w-md">
      <SheetHeader title="Notifications" onClose={() => setOpen(false)} />
      <ScrollArea className="min-h-0 flex-1 p-4">
        <div className="flex flex-col gap-2">
          {notifications?.map((n) => (
            <div
              key={n.id}
              className={cn(
                "rounded-md border border-border p-3",
                n.status === "UNREAD" ? "bg-card" : "opacity-60",
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm">{n.message}</p>
                {n.status !== "CLOSED" && (
                  <Button size="sm" variant="ghost" onClick={() => advance(n.id, n.status)}>
                    {nextAction[n.status]}
                  </Button>
                )}
              </div>
              <span className="text-xs text-muted-foreground">{timeAgo(n.createdAt)}</span>
            </div>
          ))}
          {notifications && notifications.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-16 text-center text-muted-foreground">
              <BellOff className="h-6 w-6" />
              <p className="text-sm">No notifications.</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </Sheet>
  );
}
