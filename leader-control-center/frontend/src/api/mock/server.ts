/**
 * In-memory mock backend. Backs both the mock ApiClient and the mock realtime
 * stream so the UI is fully usable before the FastAPI backend exists.
 *
 * It also simulates durable execution: running stories advance over time,
 * occasionally raise Human Requests, produce Artifacts, and emit realtime
 * messages — mirroring specs/domain/event-model.md.
 */
import type {
  Artifact,
  BoardColumn,
  Capability,
  Decision,
  HumanRequest,
  Initiative,
  InitiativeBoardView,
  Notification,
  Provider,
  Story,
  StoryCardView,
  StoryExecution,
  Task,
  TaskExecution,
  TimelineEvent,
} from "@/types/domain";
import type { DecisionInput } from "@/api/types";
import type { RealtimeMessage } from "@/realtime/types";
import { uid } from "@/lib/utils";

// --------------------------------------------------------------------------
// Internal mutable stores
// --------------------------------------------------------------------------

interface EpicRow {
  id: string;
  initiativeId: string;
  title: string;
}

const initiatives = new Map<string, Initiative>();
const epics = new Map<string, EpicRow>();
const stories = new Map<string, Story>();
const tasks = new Map<string, Task>();
const capabilities = new Map<string, Capability>();
const providers = new Map<string, Provider>();
const executions = new Map<string, StoryExecution>(); // by story execution id
const executionByStory = new Map<string, string>(); // storyId -> executionId
const humanRequests = new Map<string, HumanRequest>();
const decisions = new Map<string, Decision>();
const artifactsByStory = new Map<string, Artifact[]>();
const timelines = new Map<string, TimelineEvent[]>(); // by story execution id
const notifications: Notification[] = [];

let sequence = 1;
const listeners = new Set<(msg: RealtimeMessage) => void>();

function now(offsetMs = 0): string {
  return new Date(Date.now() + offsetMs).toISOString();
}

function resource<T extends { id: string }>(row: Omit<T, "version" | "createdAt" | "updatedAt">): T {
  return { ...row, version: 1, createdAt: now(-86_400_000), updatedAt: now() } as unknown as T;
}

function emit(type: RealtimeMessage["type"], aggregateId: string, payload?: Record<string, unknown>) {
  const msg: RealtimeMessage = { type, aggregateId, sequence: sequence++, payload };
  listeners.forEach((l) => l(msg));
}

function addTimeline(execId: string, type: string, category: TimelineEvent["category"], detail?: string) {
  const list = timelines.get(execId) ?? [];
  list.push({ id: uid("tl"), executionId: execId, type, category, detail, occurredAt: now() });
  timelines.set(execId, list);
  emit("TimelineUpdated", execId);
}

function pushNotification(type: string, message: string) {
  const n: Notification = { id: uid("ntf"), type, message, read: false, createdAt: now() };
  notifications.unshift(n);
  emit("NotificationCreated", n.id, { message });
}

// --------------------------------------------------------------------------
// Seed data
// --------------------------------------------------------------------------

function seedCapability(id: string, name: string, description: string, inputs: string, outputs: string, prov: string[]) {
  capabilities.set(id, { id, name, description, inputs, outputs, supportedProviders: prov });
}

function seed() {
  // Providers
  [
    { id: "prov_anthropic", name: "Anthropic", type: "llm" as const },
    { id: "prov_openai", name: "OpenAI", type: "llm" as const },
    { id: "prov_gemini", name: "Google Gemini", type: "llm" as const },
    { id: "prov_claude_code", name: "Claude Code", type: "llm" as const },
    { id: "prov_github_mcp", name: "GitHub MCP", type: "mcp" as const },
    { id: "prov_human", name: "Human", type: "human" as const },
  ].forEach((p) => providers.set(p.id, p));

  // Capability catalog
  seedCapability("cap_research", "Research", "Gather and synthesize information", "Topic", "Research Notes", ["prov_anthropic", "prov_openai", "prov_gemini"]);
  seedCapability("cap_write_md", "Write Markdown", "Author a Markdown document", "Markdown Specification", "Markdown Document", ["prov_anthropic", "prov_openai"]);
  seedCapability("cap_diagram", "Generate Diagram", "Produce a diagram", "Diagram Spec", "Diagram", ["prov_anthropic", "prov_gemini"]);
  seedCapability("cap_review", "Review", "Review content against criteria", "Document", "Review", ["prov_anthropic", "prov_human"]);
  seedCapability("cap_review_arch", "Review Architecture", "Assess an architecture proposal", "Proposal", "Assessment", ["prov_anthropic", "prov_human"]);
  seedCapability("cap_code", "Generate Code", "Generate source code", "Spec", "Source Code", ["prov_claude_code", "prov_openai"]);
  seedCapability("cap_summarize", "Summarize", "Summarize long content", "Document", "Summary", ["prov_anthropic", "prov_openai"]);

  // Initiatives (each backed by one Epic)
  const specs: Array<{
    id: string;
    title: string;
    description: string;
    stories: Array<{
      id: string;
      title: string;
      description: string;
      status: Story["status"];
      priority: number;
      criteria: string[];
      tasks: Array<{ name: string; capabilityId: string; status: Task["status"] }>;
      state: "todo" | "ready" | "running" | "blocked" | "completed";
    }>;
  }> = [
    {
      id: "init_promo",
      title: "Promotion to Staff Engineer",
      description: "Prepare a complete, executive-quality promotion package.",
      stories: [
        {
          id: "story_packet",
          title: "Write promotion document",
          description: "Executive-quality promotion narrative with metrics.",
          status: "Ready",
          priority: 1,
          criteria: ["Executive quality", "Less than three pages", "Ready for manager review"],
          state: "running",
          tasks: [
            { name: "Research past impact", capabilityId: "cap_research", status: "Ready" },
            { name: "Draft narrative", capabilityId: "cap_write_md", status: "Ready" },
            { name: "Review for tone", capabilityId: "cap_review", status: "Ready" },
          ],
        },
        {
          id: "story_diagrams",
          title: "Generate architecture diagrams",
          description: "Diagrams showcasing systems led.",
          status: "Ready",
          priority: 2,
          criteria: ["Consistent style", "Covers 3 systems"],
          state: "blocked",
          tasks: [
            { name: "Collect system inventory", capabilityId: "cap_research", status: "Ready" },
            { name: "Produce diagrams", capabilityId: "cap_diagram", status: "Ready" },
          ],
        },
        {
          id: "story_achievements",
          title: "Update achievements log",
          description: "Refresh the running achievements document.",
          status: "Ready",
          priority: 3,
          criteria: ["All quarters covered"],
          state: "ready",
          tasks: [{ name: "Summarize quarter", capabilityId: "cap_summarize", status: "Ready" }],
        },
      ],
    },
    {
      id: "init_modernize",
      title: "Platform Modernization",
      description: "Modernize the core platform and migrate services.",
      stories: [
        {
          id: "story_arch",
          title: "Create architecture proposal",
          description: "Target architecture for the modernized platform.",
          status: "Ready",
          priority: 1,
          criteria: ["Cost analysis included", "Risks documented"],
          state: "completed",
          tasks: [
            { name: "Research current state", capabilityId: "cap_research", status: "Ready" },
            { name: "Draft proposal", capabilityId: "cap_write_md", status: "Ready" },
            { name: "Review architecture", capabilityId: "cap_review_arch", status: "Ready" },
          ],
        },
        {
          id: "story_migrate",
          title: "Build migration strategy",
          description: "Phased migration plan with rollback.",
          status: "Ready",
          priority: 2,
          criteria: ["Zero-downtime path", "Rollback per phase"],
          state: "running",
          tasks: [
            { name: "Analyze dependencies", capabilityId: "cap_research", status: "Ready" },
            { name: "Write migration plan", capabilityId: "cap_write_md", status: "Ready" },
          ],
        },
        {
          id: "story_poc",
          title: "Prototype service extraction",
          description: "Extract one service as a proof of concept.",
          status: "Draft",
          priority: 3,
          criteria: ["Runs in staging"],
          state: "todo",
          tasks: [{ name: "Scaffold service", capabilityId: "cap_code", status: "Draft" }],
        },
      ],
    },
    {
      id: "init_ai",
      title: "AI Adoption",
      description: "Roll out AI tooling across the org.",
      stories: [
        {
          id: "story_guidelines",
          title: "Draft AI usage guidelines",
          description: "Company guidelines for responsible AI use.",
          status: "Ready",
          priority: 1,
          criteria: ["Legal reviewed", "One page"],
          state: "blocked",
          tasks: [
            { name: "Research policies", capabilityId: "cap_research", status: "Ready" },
            { name: "Write guidelines", capabilityId: "cap_write_md", status: "Ready" },
          ],
        },
        {
          id: "story_training",
          title: "Prepare enablement material",
          description: "Onboarding deck and examples.",
          status: "Ready",
          priority: 2,
          criteria: ["Covers top 5 workflows"],
          state: "ready",
          tasks: [{ name: "Summarize workflows", capabilityId: "cap_summarize", status: "Ready" }],
        },
      ],
    },
  ];

  specs.forEach((spec) => {
    initiatives.set(spec.id, resource<Initiative>({
      id: spec.id,
      portfolioId: "portfolio_default",
      title: spec.title,
      description: spec.description,
      status: "Ready",
    }) as Initiative);

    const epicId = `epic_${spec.id}`;
    epics.set(epicId, { id: epicId, initiativeId: spec.id, title: spec.title });

    spec.stories.forEach((s) => {
      const story = resource<Story>({
        id: s.id,
        epicId,
        title: s.title,
        description: s.description,
        priority: s.priority,
        status: s.status,
        acceptanceCriteria: s.criteria.map((c) => ({ id: uid("ac"), description: c })),
      }) as Story;
      stories.set(s.id, story);

      const taskRows: Task[] = s.tasks.map((t, i) =>
        resource<Task>({
          id: uid("task"),
          storyId: s.id,
          name: t.name,
          planningMode: "Structured",
          status: t.status,
          order: i,
          dependencies: [],
          capabilityId: t.capabilityId,
        }) as Task,
      );
      taskRows.forEach((t) => tasks.set(t.id, t));

      if (s.state !== "todo" && s.state !== "ready") {
        instantiateExecution(story, taskRows, s.state);
      }
    });
  });
}

function capName(id?: string): string {
  return (id && capabilities.get(id)?.name) || "Capability";
}

/** Create a Story Execution reflecting a desired initial state. */
function instantiateExecution(story: Story, taskRows: Task[], state: "running" | "blocked" | "completed") {
  const execId = uid("sexec");
  const taskExecs: TaskExecution[] = taskRows.map((t, i) => {
    let status: TaskExecution["status"] = "Created";
    if (state === "completed") status = "Completed";
    else if (state === "running") status = i === 0 ? "Running" : i === 1 ? "Created" : "Created";
    else if (state === "blocked") status = i === 0 ? "Completed" : "WaitingDecision";

    const provId = capabilities.get(t.capabilityId!)?.supportedProviders[0] ?? "prov_anthropic";
    return {
      id: uid("texec"),
      storyExecutionId: execId,
      taskId: t.id,
      taskName: t.name,
      status,
      attempt: 1,
      startedAt: status === "Created" ? undefined : now(-3_600_000),
      completedAt: status === "Completed" ? now(-600_000) : undefined,
      capabilityExecutions: [
        {
          id: uid("cexec"),
          taskExecutionId: "",
          capabilityId: t.capabilityId!,
          capabilityName: capName(t.capabilityId),
          strategy: "SingleProvider",
          status: status === "Completed" ? "Completed" : status === "Running" ? "Running" : status === "WaitingDecision" ? "Waiting" : "Pending",
          providerExecutions: [
            {
              id: uid("pexec"),
              capabilityExecutionId: "",
              providerId: provId,
              providerName: providers.get(provId)?.name ?? "Anthropic",
              status: status === "Completed" ? "Succeeded" : status === "Running" ? "Running" : "Scheduled",
              attempt: 1,
              startedAt: status === "Created" ? undefined : now(-3_000_000),
              endedAt: status === "Completed" ? now(-600_000) : undefined,
            },
          ],
        },
      ],
    };
  });

  const completed = taskExecs.filter((t) => t.status === "Completed").length;
  const exec: StoryExecution = {
    id: execId,
    storyId: story.id,
    status: state === "completed" ? "Completed" : state === "blocked" ? "Waiting" : "Running",
    progress: state === "completed" ? 1 : completed / taskExecs.length,
    startedAt: now(-3_600_000),
    completedAt: state === "completed" ? now(-300_000) : undefined,
    taskExecutions: taskExecs,
  };
  executions.set(execId, exec);
  executionByStory.set(story.id, execId);

  // Seed a timeline
  addTimeline(execId, "Execution Started", "Runtime");
  if (completed > 0) addTimeline(execId, "Task Completed", "Runtime", `${completed} task(s) completed`);

  // Blocked stories carry an open Human Request
  if (state === "blocked") {
    const waiting = taskExecs.find((t) => t.status === "WaitingDecision");
    if (waiting) raiseHumanRequest(story, exec, waiting);
  }

  // Completed stories carry an artifact
  if (state === "completed") {
    addArtifact(story.id, exec.id, "Specification", `${story.title} — final`, "Anthropic");
  }
}

function raiseHumanRequest(story: Story, exec: StoryExecution, taskExec: TaskExecution) {
  const init = initiativeForStory(story.id)!;
  const types: HumanRequest["type"][] = ["Approval", "Clarification", "ToolPermission", "ChooseOption"];
  const type = types[Math.floor(Math.random() * types.length)];
  const req: HumanRequest = {
    id: uid("hreq"),
    executionId: exec.id,
    initiativeId: init.id,
    initiativeTitle: init.title,
    storyId: story.id,
    storyTitle: story.title,
    type,
    prompt:
      type === "Approval"
        ? `Approve the output of "${taskExec.taskName}" before continuing?`
        : type === "Clarification"
          ? `Clarification needed for "${taskExec.taskName}": which audience should this target?`
          : type === "ToolPermission"
            ? `Allow "${taskExec.taskName}" to access the GitHub MCP server?`
            : `Choose an option for "${taskExec.taskName}".`,
    options:
      type === "ChooseOption"
        ? [
            { id: "opt_a", label: "Concise executive summary" },
            { id: "opt_b", label: "Detailed technical write-up" },
          ]
        : undefined,
    status: "Visible",
    priority: type === "Approval" ? "high" : "medium",
    createdAt: now(),
  };
  humanRequests.set(req.id, req);
  taskExec.status = "WaitingDecision";
  exec.status = "Waiting";
  addTimeline(exec.id, "Approval Requested", "Decision", req.prompt);
  emit("DecisionRequested", req.id, { executionId: exec.id });
  emit("AttentionUpdated", req.id);
  pushNotification("HumanRequest", `Action needed: ${story.title}`);
}

function addArtifact(storyId: string, execId: string, type: Artifact["type"], name: string, createdBy: string) {
  const list = artifactsByStory.get(storyId) ?? [];
  const content =
    type === "Diagram"
      ? "graph TD\n  A[Client] --> B[API]\n  B --> C[(DB)]\n  B --> D[Temporal]"
      : type === "SourceCode"
        ? "export function extract() {\n  return 'service';\n}"
        : `# ${name}\n\nGenerated by ${createdBy}.\n\n- Point one\n- Point two\n- Point three\n`;
  const artifact: Artifact = {
    id: uid("art"),
    executionId: execId,
    storyId,
    type,
    name,
    version: 1,
    createdBy,
    createdAt: now(),
    content,
    language: type === "SourceCode" ? "typescript" : undefined,
  };
  list.unshift(artifact);
  artifactsByStory.set(storyId, list);
  addTimeline(execId, "Artifact Produced", "Artifact", name);
  emit("ArtifactProduced", artifact.id, { storyId });
}

// --------------------------------------------------------------------------
// Projections
// --------------------------------------------------------------------------

function initiativeForStory(storyId: string): Initiative | undefined {
  const story = stories.get(storyId);
  if (!story) return undefined;
  const epic = epics.get(story.epicId);
  if (!epic) return undefined;
  return initiatives.get(epic.initiativeId);
}

function openRequestsForStory(storyId: string): number {
  let n = 0;
  humanRequests.forEach((r) => {
    if (r.storyId === storyId && r.status !== "Closed" && r.status !== "Resolved") n++;
  });
  return n;
}

function columnFor(story: Story, exec: StoryExecution | undefined, openReqs: number): BoardColumn {
  if (!exec) return story.status === "Ready" ? "Ready" : "Todo";
  if (openReqs > 0 || exec.status === "Waiting" || exec.status === "Failed") return "Blocked";
  if (exec.status === "Completed") return "Completed";
  if (exec.status === "Cancelled") return "Todo";
  return "Running";
}

function buildBoards(): InitiativeBoardView[] {
  const views: InitiativeBoardView[] = [];
  initiatives.forEach((initiative) => {
    const epic = [...epics.values()].find((e) => e.initiativeId === initiative.id);
    if (!epic) return;
    const cols: Record<BoardColumn, StoryCardView[]> = {
      Todo: [],
      Ready: [],
      Running: [],
      Blocked: [],
      Completed: [],
    };
    let openReqTotal = 0;
    [...stories.values()]
      .filter((s) => s.epicId === epic.id)
      .sort((a, b) => a.priority - b.priority)
      .forEach((story) => {
        const execId = executionByStory.get(story.id);
        const exec = execId ? executions.get(execId) : undefined;
        const openReqs = openRequestsForStory(story.id);
        openReqTotal += openReqs;
        const column = columnFor(story, exec, openReqs);
        cols[column].push({ story, column, execution: exec, openHumanRequests: openReqs });
      });
    views.push({ initiative, epicId: epic.id, columns: cols, openHumanRequests: openReqTotal });
  });
  return views;
}

// --------------------------------------------------------------------------
// Simulation tick
// --------------------------------------------------------------------------

function tick() {
  executions.forEach((exec) => {
    if (exec.status !== "Running") return;
    const story = stories.get(exec.storyId)!;

    const active = exec.taskExecutions.find((t) => t.status === "Running");
    if (!active) {
      // start the next created task
      const next = exec.taskExecutions.find((t) => t.status === "Created");
      if (next) {
        next.status = "Running";
        next.startedAt = now();
        next.capabilityExecutions[0].status = "Running";
        next.capabilityExecutions[0].providerExecutions[0].status = "Running";
        addTimeline(exec.id, "Capability Started", "Runtime", next.taskName);
        emit("ExecutionUpdated", exec.id);
      }
      return;
    }

    // ~25% chance to raise a human request while running
    if (Math.random() < 0.22) {
      raiseHumanRequest(story, exec, active);
      emit("ExecutionUpdated", exec.id);
      emit("StoryUpdated", story.id);
      return;
    }

    // Otherwise complete the active task
    active.status = "Completed";
    active.completedAt = now();
    active.capabilityExecutions[0].status = "Completed";
    active.capabilityExecutions[0].providerExecutions[0].status = "Succeeded";
    active.capabilityExecutions[0].providerExecutions[0].endedAt = now();
    addTimeline(exec.id, "Task Completed", "Runtime", active.taskName);

    // Produce an artifact for writing/diagram/code capabilities
    const capId = tasks.get(active.taskId)?.capabilityId;
    if (capId === "cap_write_md") addArtifact(story.id, exec.id, "Markdown", `${active.taskName} — draft`, active.capabilityExecutions[0].providerExecutions[0].providerName);
    else if (capId === "cap_diagram") addArtifact(story.id, exec.id, "Diagram", `${active.taskName}`, "Anthropic");
    else if (capId === "cap_code") addArtifact(story.id, exec.id, "SourceCode", `${active.taskName}`, "Claude Code");

    const completed = exec.taskExecutions.filter((t) => t.status === "Completed").length;
    exec.progress = completed / exec.taskExecutions.length;

    if (completed === exec.taskExecutions.length) {
      exec.status = "Completed";
      exec.completedAt = now();
      addTimeline(exec.id, "Execution Completed", "Runtime");
      pushNotification("Completed", `Completed: ${story.title}`);
    }
    emit("ExecutionUpdated", exec.id);
    emit("StoryUpdated", story.id);
  });
}

// --------------------------------------------------------------------------
// Public server API
// --------------------------------------------------------------------------

let seeded = false;
function ensureSeeded() {
  if (!seeded) {
    seed();
    seeded = true;
  }
}

export const mockServer = {
  ensureSeeded,

  subscribe(listener: (msg: RealtimeMessage) => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  tick,

  getBoards(): InitiativeBoardView[] {
    ensureSeeded();
    return buildBoards();
  },
  getStoryTasks(storyId: string): Task[] {
    return [...tasks.values()].filter((t) => t.storyId === storyId).sort((a, b) => a.order - b.order);
  },
  getExecution(execId: string): StoryExecution {
    const e = executions.get(execId);
    if (!e) throw new Error(`Execution not found: ${execId}`);
    return e;
  },
  getTimeline(execId: string): TimelineEvent[] {
    return [...(timelines.get(execId) ?? [])].reverse();
  },
  getArtifacts(storyId: string): Artifact[] {
    return artifactsByStory.get(storyId) ?? [];
  },
  getArtifact(id: string): Artifact {
    for (const list of artifactsByStory.values()) {
      const found = list.find((a) => a.id === id);
      if (found) return found;
    }
    throw new Error(`Artifact not found: ${id}`);
  },
  getAttention(): HumanRequest[] {
    return [...humanRequests.values()]
      .filter((r) => r.status !== "Closed" && r.status !== "Resolved")
      .sort((a, b) => {
        const rank = { high: 0, medium: 1, low: 2 } as const;
        if (rank[a.priority] !== rank[b.priority]) return rank[a.priority] - rank[b.priority];
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      });
  },
  getDecisions(execId: string): Decision[] {
    const reqIds = new Set([...humanRequests.values()].filter((r) => r.executionId === execId).map((r) => r.id));
    return [...decisions.values()].filter((d) => reqIds.has(d.humanRequestId));
  },
  getCapabilities(): Capability[] {
    ensureSeeded();
    return [...capabilities.values()];
  },
  getProviders(): Provider[] {
    ensureSeeded();
    return [...providers.values()];
  },
  getNotifications(): Notification[] {
    return notifications;
  },

  markTaskReady(taskId: string) {
    const t = tasks.get(taskId);
    if (t) t.status = "Ready";
  },

  startStory(storyId: string): StoryExecution {
    const story = stories.get(storyId)!;
    const taskRows = this.getStoryTasks(storyId);
    // mark tasks ready
    taskRows.forEach((t) => (t.status = "Ready"));
    story.status = "Ready";
    const existing = executionByStory.get(storyId);
    if (existing) executions.delete(existing);
    instantiateExecution(story, taskRows, "running");
    // Set first task running explicitly
    const execId = executionByStory.get(storyId)!;
    const exec = executions.get(execId)!;
    exec.taskExecutions.forEach((te, i) => (te.status = i === 0 ? "Running" : "Created"));
    exec.status = "Running";
    exec.progress = 0;
    addTimeline(exec.id, "Story Started", "Runtime");
    emit("StoryUpdated", storyId);
    emit("ExecutionUpdated", exec.id);
    return exec;
  },

  startTask(taskId: string) {
    const t = tasks.get(taskId);
    if (!t) return;
    const execId = executionByStory.get(t.storyId);
    if (!execId) return;
    const exec = executions.get(execId)!;
    const te = exec.taskExecutions.find((x) => x.taskId === taskId);
    if (te && te.status === "Created") {
      te.status = "Running";
      te.startedAt = now();
      exec.status = "Running";
      addTimeline(exec.id, "Capability Started", "Runtime", te.taskName);
      emit("ExecutionUpdated", exec.id);
    }
  },

  cancelExecution(execId: string) {
    const exec = executions.get(execId);
    if (!exec) return;
    exec.status = "Cancelled";
    exec.taskExecutions.forEach((t) => {
      if (t.status === "Running" || t.status === "WaitingDecision" || t.status === "Created") t.status = "Cancelled";
    });
    // close any open requests
    humanRequests.forEach((r) => {
      if (r.executionId === execId && r.status !== "Closed") r.status = "Closed";
    });
    addTimeline(execId, "Execution Cancelled", "Runtime");
    emit("ExecutionUpdated", execId);
    emit("StoryUpdated", exec.storyId);
    emit("AttentionUpdated", execId);
  },

  retryExecution(execId: string) {
    const exec = executions.get(execId);
    if (!exec) return;
    const story = stories.get(exec.storyId)!;
    const taskRows = this.getStoryTasks(story.id);
    executions.delete(execId);
    this.startStory(story.id);
    addTimeline(executionByStory.get(story.id)!, "Retry Scheduled", "Runtime", `retry of ${taskRows.length} task(s)`);
  },

  submitDecision(humanRequestId: string, input: DecisionInput): Decision {
    const req = humanRequests.get(humanRequestId);
    if (!req) throw new Error(`Human request not found: ${humanRequestId}`);
    const decision: Decision = {
      id: uid("dec"),
      humanRequestId,
      decision: input.decision,
      selectedOption: input.selectedOption,
      comment: input.comment,
      user: "you@leader",
      createdAt: now(),
    };
    decisions.set(decision.id, decision);
    req.status = "Closed";

    const exec = executions.get(req.executionId);
    if (exec) {
      const waiting = exec.taskExecutions.find((t) => t.status === "WaitingDecision");
      if (input.decision === "Abort" || input.decision === "Reject") {
        if (waiting) waiting.status = input.decision === "Abort" ? "Cancelled" : "Failed";
        exec.status = input.decision === "Abort" ? "Cancelled" : "Failed";
        addTimeline(exec.id, "Decision Received", "Decision", `${input.decision}`);
      } else {
        if (waiting) {
          waiting.status = "Running";
          waiting.capabilityExecutions[0].status = "Running";
        }
        exec.status = "Running";
        addTimeline(exec.id, "Decision Received", "Decision", `${input.decision}${input.selectedOption ? `: ${req.options?.find((o) => o.id === input.selectedOption)?.label}` : ""}`);
      }
      emit("DecisionApplied", req.id, { executionId: exec.id });
      emit("ExecutionUpdated", exec.id);
      emit("StoryUpdated", exec.storyId);
    }
    emit("AttentionUpdated", req.id);
    return decision;
  },

  dismissNotification(id: string) {
    const n = notifications.find((x) => x.id === id);
    if (n) n.read = true;
  },
};
