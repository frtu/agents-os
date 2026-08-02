import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Plus, Send, Sparkles, X } from "lucide-react";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useUiStore } from "@/store/ui";
import { useCreateStory, useDraftStory } from "@/hooks/mutations";

const PRIORITY_OPTIONS = [
  { value: 0, label: "High" },
  { value: 1, label: "Medium" },
  { value: 2, label: "Low" },
];

const inputClass =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary";

function RequiredMark() {
  return <span className="text-status-blocked"> *</span>;
}

export function CreateStorySheet() {
  const panel = useUiStore((s) => s.panel);
  const closePanel = useUiStore((s) => s.closePanel);
  const open = panel.kind === "createStory";
  const initiativeId = panel.kind === "createStory" ? panel.initiativeId : undefined;
  const epicId = panel.kind === "createStory" ? panel.epicId : undefined;

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(1);
  const [criteria, setCriteria] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  // Reset the form each time the drawer opens (possibly for a new initiative).
  useEffect(() => {
    if (open) {
      setTitle("");
      setDescription("");
      setPriority(1);
      setCriteria([]);
      setMessage("");
    }
  }, [open]);

  const draft = useDraftStory();
  const create = useCreateStory(initiativeId ?? "");

  const chatRef = useRef<HTMLTextAreaElement>(null);
  useLayoutEffect(() => {
    const el = chatRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [message, open]);

  const send = () => {
    if (!message.trim() || !initiativeId) return;
    draft.mutate(
      { initiativeId, message: message.trim() },
      {
        onSuccess: (d) => {
          setTitle(d.title);
          setDescription(d.description);
          setPriority(d.priority);
          setCriteria(d.acceptanceCriteria);
        },
      },
    );
  };

  const submit = () => {
    if (!title.trim() || !epicId) return;
    create.mutate(
      {
        epicId,
        title: title.trim(),
        description: description.trim(),
        priority,
        acceptanceCriteria: criteria.map((c) => c.trim()).filter(Boolean),
      },
      { onSuccess: () => closePanel() },
    );
  };

  return (
    <Sheet open={open} onClose={closePanel}>
      <SheetHeader
        title="New Story"
        description="Describe the work below, or fill the form directly."
        onClose={closePanel}
      />

      <ScrollArea className="min-h-0 flex-1 p-4">
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">
              Title<RequiredMark />
            </span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be done"
              className={inputClass}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Description</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional context"
              rows={3}
              className={`${inputClass} resize-none`}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Priority</span>
            <select
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className={inputClass}
            >
              {PRIORITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium text-muted-foreground">Acceptance criteria</span>
            {criteria.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  value={c}
                  onChange={(e) =>
                    setCriteria((prev) => prev.map((v, j) => (j === i ? e.target.value : v)))
                  }
                  placeholder={`Criterion ${i + 1}`}
                  className={inputClass}
                />
                <button
                  onClick={() => setCriteria((prev) => prev.filter((_, j) => j !== i))}
                  aria-label="Remove criterion"
                  className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
            <Button
              size="sm"
              variant="outline"
              className="self-start"
              onClick={() => setCriteria((prev) => [...prev, ""])}
            >
              <Plus className="h-3.5 w-3.5" />
              Add criterion
            </Button>
          </div>
        </div>
      </ScrollArea>

      <div className="border-t border-border p-4">
        <Button
          className="mb-3 w-full"
          onClick={submit}
          disabled={!title.trim() || create.isPending}
        >
          Create Story
        </Button>

        <div className="relative">
          <textarea
            ref={chatRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Describe the story and let AI prefill the form…"
            rows={1}
            className={`${inputClass} resize-none pr-12`}
          />
          <Button
            size="icon"
            onClick={send}
            disabled={!message.trim() || draft.isPending}
            aria-label="Send"
            className="absolute bottom-2 right-2 h-8 w-8"
          >
            {draft.isPending ? <Sparkles className="h-4 w-4 animate-pulse" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </Sheet>
  );
}
