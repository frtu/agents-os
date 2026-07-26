import { useEffect } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * A minimal right-side drawer. No Radix; just a fixed overlay + panel.
 */
export function Sheet({
  open,
  onClose,
  children,
  side = "right",
  className,
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  side?: "right" | "left";
  className?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <div className={cn("fixed inset-0 z-50", open ? "pointer-events-auto" : "pointer-events-none")} aria-hidden={!open}>
      <div
        onClick={onClose}
        className={cn("absolute inset-0 bg-black/40 transition-opacity", open ? "opacity-100" : "opacity-0")}
      />
      <div
        role="dialog"
        className={cn(
          "absolute top-0 flex h-full w-full max-w-xl flex-col border-border bg-background shadow-xl transition-transform duration-200",
          side === "right" ? "right-0 border-l" : "left-0 border-r",
          open ? "translate-x-0" : side === "right" ? "translate-x-full" : "-translate-x-full",
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function SheetHeader({
  title,
  description,
  onClose,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border p-4">
      <div className="min-w-0">
        <div className="truncate text-base font-semibold">{title}</div>
        {description && <div className="mt-0.5 text-sm text-muted-foreground">{description}</div>}
      </div>
      <button onClick={onClose} className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
