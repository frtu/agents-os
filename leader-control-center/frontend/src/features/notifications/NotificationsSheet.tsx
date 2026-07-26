import { BellOff } from "lucide-react";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn, timeAgo } from "@/lib/utils";
import { useNotifications } from "@/hooks/queries";
import { useDismissNotification } from "@/hooks/mutations";
import { useUiStore } from "@/store/ui";

export function NotificationsSheet() {
  const open = useUiStore((s) => s.notificationsOpen);
  const setOpen = useUiStore((s) => s.setNotificationsOpen);
  const { data: notifications } = useNotifications();
  const dismiss = useDismissNotification();

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
                n.read ? "opacity-60" : "bg-card",
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm">{n.message}</p>
                {!n.read && (
                  <Button size="sm" variant="ghost" onClick={() => dismiss.mutate(n.id)}>
                    Dismiss
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
