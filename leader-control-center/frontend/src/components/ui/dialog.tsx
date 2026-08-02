import { useEffect } from "react";
import { cn } from "@/lib/utils";

/**
 * A minimal centered modal. No Radix; just a fixed overlay + panel, Escape to
 * close. Mirrors the dependency-light approach of sheet.tsx.
 */
export function Dialog({
  open,
  onClose,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div onClick={onClose} className="absolute inset-0 bg-black/40" />
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          "relative z-10 w-full max-w-md rounded-lg border border-border bg-background p-5 shadow-xl",
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}
