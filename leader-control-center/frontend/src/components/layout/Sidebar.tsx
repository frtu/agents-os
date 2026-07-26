import { NavLink } from "react-router-dom";
import { LayoutGrid, Inbox, Boxes } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAttention } from "@/hooks/queries";

const nav = [
  { to: "/", label: "Board", icon: LayoutGrid, end: true },
  { to: "/attention", label: "Attention", icon: Inbox, end: false },
];

export function Sidebar() {
  const { data: attention } = useAttention();
  const attentionCount = attention?.length ?? 0;

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-card">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <Boxes className="h-5 w-5 text-primary" />
        <span className="text-sm font-semibold leading-tight">Leader Control Center</span>
      </div>
      <nav className="flex flex-col gap-1 p-2">
        {nav.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
              )
            }
          >
            <span className="flex items-center gap-2">
              <Icon className="h-4 w-4" />
              {label}
            </span>
            {label === "Attention" && attentionCount > 0 && (
              <span className="rounded-full bg-status-blocked px-1.5 py-0.5 text-[10px] font-semibold text-white">
                {attentionCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto p-3 text-[11px] text-muted-foreground">
        Supervising durable AI work.
      </div>
    </aside>
  );
}
