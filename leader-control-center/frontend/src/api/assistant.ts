import type { StoryDraft } from "@/types/domain";

// The local leader-assistant REST service. In dev, "/assistant" is proxied to
// http://localhost:7860 by vite (see vite.config.ts) to avoid CORS.
const ASSISTANT_URL = import.meta.env.VITE_ASSISTANT_URL ?? "/assistant";

const DRAFT_INSTRUCTIONS =
  "You are drafting a single agile user story for a software initiative. " +
  "Based on the description below, return ONLY a JSON object (no prose, no " +
  "markdown code fences) with exactly these keys:\n" +
  '- "title": string, a concise story title\n' +
  '- "description": string, a short description of the work\n' +
  '- "priority": number, 0 = High, 1 = Medium, 2 = Low\n' +
  '- "acceptanceCriteria": string[], testable acceptance criteria\n\n' +
  "Description:\n";

interface AgentResponse {
  reply: string;
  session_id: string | null;
}

/** Extract the first JSON object from an LLM reply, tolerating code fences. */
function extractJson(text: string): string | null {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const body = fenced ? fenced[1] : text;
  const start = body.indexOf("{");
  const end = body.lastIndexOf("}");
  if (start === -1 || end === -1 || end < start) return null;
  return body.slice(start, end + 1);
}

const PRIORITY_WORDS: Record<string, number> = { high: 0, medium: 1, low: 2 };

function coercePriority(value: unknown): number {
  if (typeof value === "number" && [0, 1, 2].includes(value)) return value;
  if (typeof value === "string") {
    const mapped = PRIORITY_WORDS[value.trim().toLowerCase()];
    if (mapped !== undefined) return mapped;
    const n = Number(value);
    if ([0, 1, 2].includes(n)) return n;
  }
  return 1;
}

function parseStoryDraft(reply: string): StoryDraft {
  const json = extractJson(reply);
  let obj: Record<string, unknown> = {};
  if (json) {
    try {
      obj = JSON.parse(json) as Record<string, unknown>;
    } catch {
      /* fall through to defaults / raw reply */
    }
  }

  return {
    title: typeof obj.title === "string" ? obj.title : "",
    // If the agent didn't produce JSON, surface its prose as the description
    // so the user still gets something useful to edit.
    description:
      typeof obj.description === "string"
        ? obj.description
        : json
          ? ""
          : reply.trim(),
    priority: coercePriority(obj.priority),
    acceptanceCriteria: Array.isArray(obj.acceptanceCriteria)
      ? obj.acceptanceCriteria.filter((c): c is string => typeof c === "string")
      : [],
  };
}

/** Draft a story by asking the local leader-assistant agent. */
export async function draftStoryViaAssistant(input: {
  initiativeId: string;
  message: string;
}): Promise<StoryDraft> {
  const res = await fetch(`${ASSISTANT_URL}/api/agent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: DRAFT_INSTRUCTIONS + input.message }),
  });

  if (!res.ok) {
    throw new Error(`Assistant request failed: ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as AgentResponse;
  return parseStoryDraft(data.reply ?? "");
}
