"""In-process SimulationEngine: the MVP WorkflowEngine adapter. It stands in for
Temporal — advancing running executions over time, raising Human Requests,
producing Artifacts, and emitting realtime events — so the whole control plane is
exercisable without a durable engine. All runtime state transitions live here."""
from __future__ import annotations

import random

from app.domain.enums import (
    ArtifactType,
    CapabilityExecutionStatus as CapStatus,
    DecisionKind,
    ExecutionStrategy,
    HumanRequestType,
    Priority,
    ProviderExecutionStatus as ProvStatus,
    StoryExecutionStatus as ExecStatus,
    TaskExecutionStatus as TaskStatus,
    TaskPlanningStatus,
    TimelineEventCategory as Cat,
)
from app.domain.events import MessageType
from app.domain.models import (
    CapabilityExecution,
    Decision,
    HumanRequest,
    HumanRequestOption,
    ProviderExecution,
    Story,
    StoryExecution,
    Task,
    TaskExecution,
)
from app.infra.store import Store, now, uid


class ExecutionNotFound(Exception):
    pass


class HumanRequestNotFound(Exception):
    pass


class SimulationEngine:
    def __init__(self, store: Store) -> None:
        self.store = store

    # -- catalog helpers ---------------------------------------------------
    def _cap_name(self, cap_id: str | None) -> str:
        cap = self.store.capabilities.get(cap_id) if cap_id else None
        return cap.name if cap else "Capability"

    def _provider_for(self, cap_id: str | None) -> tuple[str, str]:
        cap = self.store.capabilities.get(cap_id) if cap_id else None
        prov_id = cap.supported_providers[0] if cap and cap.supported_providers else "prov_anthropic"
        prov = self.store.providers.get(prov_id)
        return prov_id, (prov.name if prov else "Anthropic")

    # -- construction (seed + start) --------------------------------------
    def instantiate_execution(
        self, story: Story, task_rows: list[Task], state: str
    ) -> StoryExecution:
        exec_id = uid("sexec")
        task_execs: list[TaskExecution] = []
        for i, t in enumerate(task_rows):
            if state == "completed":
                status = TaskStatus.COMPLETED
            elif state == "running":
                status = TaskStatus.RUNNING if i == 0 else TaskStatus.CREATED
            else:  # blocked
                status = TaskStatus.COMPLETED if i == 0 else TaskStatus.WAITING_DECISION

            prov_id, prov_name = self._provider_for(t.capability_id)
            cap_status = (
                CapStatus.COMPLETED if status == TaskStatus.COMPLETED
                else CapStatus.RUNNING if status == TaskStatus.RUNNING
                else CapStatus.WAITING if status == TaskStatus.WAITING_DECISION
                else CapStatus.PENDING
            )
            prov_status = (
                ProvStatus.SUCCEEDED if status == TaskStatus.COMPLETED
                else ProvStatus.RUNNING if status == TaskStatus.RUNNING
                else ProvStatus.SCHEDULED
            )
            cexec = CapabilityExecution(
                id=uid("cexec"), task_execution_id="", capability_id=t.capability_id,
                capability_name=self._cap_name(t.capability_id),
                strategy=ExecutionStrategy.SINGLE_PROVIDER, status=cap_status,
                provider_executions=[
                    ProviderExecution(
                        id=uid("pexec"), capability_execution_id="",
                        provider_id=prov_id, provider_name=prov_name, status=prov_status,
                        attempt=1,
                        started_at=None if status == TaskStatus.CREATED else now(-3_000_000),
                        ended_at=now(-600_000) if status == TaskStatus.COMPLETED else None,
                    )
                ],
            )
            task_execs.append(
                TaskExecution(
                    id=uid("texec"), story_execution_id=exec_id, task_id=t.id,
                    task_name=t.name, status=status, attempt=1,
                    started_at=None if status == TaskStatus.CREATED else now(-3_600_000),
                    completed_at=now(-600_000) if status == TaskStatus.COMPLETED else None,
                    capability_executions=[cexec],
                )
            )

        completed = sum(1 for t in task_execs if t.status == TaskStatus.COMPLETED)
        exec = StoryExecution(
            id=exec_id, story_id=story.id,
            status=(
                ExecStatus.COMPLETED if state == "completed"
                else ExecStatus.WAITING if state == "blocked"
                else ExecStatus.RUNNING
            ),
            progress=1.0 if state == "completed" else completed / max(len(task_execs), 1),
            started_at=now(-3_600_000),
            completed_at=now(-300_000) if state == "completed" else None,
            task_executions=task_execs,
        )
        self.store.executions[exec_id] = exec
        self.store.execution_by_story[story.id] = exec_id

        self.store.add_timeline(exec_id, "Execution Started", Cat.RUNTIME)
        if completed > 0:
            self.store.add_timeline(exec_id, "Task Completed", Cat.RUNTIME, f"{completed} task(s) completed")

        if state == "blocked":
            waiting = next((t for t in task_execs if t.status == TaskStatus.WAITING_DECISION), None)
            if waiting:
                self.raise_human_request(story, exec, waiting)
        if state == "completed":
            self.add_artifact(story.id, exec.id, ArtifactType.SPECIFICATION, f"{story.title} — final", "Anthropic")
        return exec

    def add_artifact(self, story_id: str, exec_id: str, type: ArtifactType, name: str, created_by: str) -> None:
        if type == ArtifactType.DIAGRAM:
            content = "graph TD\n  A[Client] --> B[API]\n  B --> C[(DB)]\n  B --> D[Temporal]"
        elif type == ArtifactType.SOURCE_CODE:
            content = "export function extract() {\n  return 'service';\n}"
        else:
            content = f"# {name}\n\nGenerated by {created_by}.\n\n- Point one\n- Point two\n- Point three\n"

        from app.domain.models import Artifact  # local import keeps module header tidy

        artifact = Artifact(
            id=uid("art"), execution_id=exec_id, story_id=story_id, type=type, name=name,
            version=1, created_by=created_by, created_at=now(), content=content,
            language="typescript" if type == ArtifactType.SOURCE_CODE else None,
        )
        self.store.artifacts_by_story.setdefault(story_id, []).insert(0, artifact)
        self.store.add_timeline(exec_id, "Artifact Produced", Cat.ARTIFACT, name)
        self.store.bus.emit(MessageType.ARTIFACT_PRODUCED, artifact.id, {"storyId": story_id})

    def raise_human_request(self, story: Story, exec: StoryExecution, task_exec: TaskExecution) -> None:
        init = self.store.initiative_for_story(story.id)
        req_type = random.choice([
            HumanRequestType.APPROVAL, HumanRequestType.CLARIFICATION,
            HumanRequestType.TOOL_PERMISSION, HumanRequestType.CHOOSE_OPTION,
        ])
        if req_type == HumanRequestType.APPROVAL:
            prompt = f'Approve the output of "{task_exec.task_name}" before continuing?'
        elif req_type == HumanRequestType.CLARIFICATION:
            prompt = f'Clarification needed for "{task_exec.task_name}": which audience should this target?'
        elif req_type == HumanRequestType.TOOL_PERMISSION:
            prompt = f'Allow "{task_exec.task_name}" to access the GitHub MCP server?'
        else:
            prompt = f'Choose an option for "{task_exec.task_name}".'

        options = (
            [HumanRequestOption(id="opt_a", label="Concise executive summary"),
             HumanRequestOption(id="opt_b", label="Detailed technical write-up")]
            if req_type == HumanRequestType.CHOOSE_OPTION else None
        )
        req = HumanRequest(
            id=uid("hreq"), execution_id=exec.id,
            initiative_id=init.id if init else "", initiative_title=init.title if init else "",
            story_id=story.id, story_title=story.title, type=req_type, prompt=prompt,
            options=options, status="Visible",
            priority=Priority.HIGH if req_type == HumanRequestType.APPROVAL else Priority.MEDIUM,
            created_at=now(),
        )
        self.store.human_requests[req.id] = req
        task_exec.status = TaskStatus.WAITING_DECISION
        exec.status = ExecStatus.WAITING
        self.store.add_timeline(exec.id, "Approval Requested", Cat.DECISION, prompt)
        self.store.bus.emit(MessageType.DECISION_REQUESTED, req.id, {"executionId": exec.id})
        self.store.bus.emit(MessageType.ATTENTION_UPDATED, req.id)
        self.store.push_notification("HumanRequest", f"Action needed: {story.title}")

    # -- commands (WorkflowEngine port + extras) --------------------------
    def mark_task_ready(self, task_id: str) -> None:
        t = self.store.tasks.get(task_id)
        if t:
            t.status = TaskPlanningStatus.READY

    def start_story(self, story_id: str) -> StoryExecution:
        story = self.store.stories.get(story_id)
        if not story:
            raise ExecutionNotFound(story_id)
        task_rows = self._story_tasks(story_id)
        for t in task_rows:
            t.status = TaskPlanningStatus.READY
        story.status = "Ready"

        existing = self.store.execution_by_story.get(story_id)
        if existing:
            self.store.executions.pop(existing, None)

        self.instantiate_execution(story, task_rows, "running")
        exec_id = self.store.execution_by_story[story_id]
        exec = self.store.executions[exec_id]
        for i, te in enumerate(exec.task_executions):
            te.status = TaskStatus.RUNNING if i == 0 else TaskStatus.CREATED
        exec.status = ExecStatus.RUNNING
        exec.progress = 0.0
        self.store.add_timeline(exec.id, "Story Started", Cat.RUNTIME)
        self.store.bus.emit(MessageType.STORY_UPDATED, story_id)
        self.store.bus.emit(MessageType.EXECUTION_UPDATED, exec.id)
        return exec

    def start_task(self, task_id: str) -> None:
        t = self.store.tasks.get(task_id)
        if not t:
            return
        exec_id = self.store.execution_by_story.get(t.story_id)
        if not exec_id:
            return
        exec = self.store.executions[exec_id]
        te = next((x for x in exec.task_executions if x.task_id == task_id), None)
        if te and te.status == TaskStatus.CREATED:
            te.status = TaskStatus.RUNNING
            te.started_at = now()
            exec.status = ExecStatus.RUNNING
            self.store.add_timeline(exec.id, "Capability Started", Cat.RUNTIME, te.task_name)
            self.store.bus.emit(MessageType.EXECUTION_UPDATED, exec.id)

    def cancel(self, execution_id: str) -> None:
        exec = self.store.executions.get(execution_id)
        if not exec:
            return
        exec.status = ExecStatus.CANCELLED
        for t in exec.task_executions:
            if t.status in (TaskStatus.RUNNING, TaskStatus.WAITING_DECISION, TaskStatus.CREATED):
                t.status = TaskStatus.CANCELLED
        for r in self.store.human_requests.values():
            if r.execution_id == execution_id and r.status != "Closed":
                r.status = "Closed"
        self.store.add_timeline(execution_id, "Execution Cancelled", Cat.RUNTIME)
        self.store.bus.emit(MessageType.EXECUTION_UPDATED, execution_id)
        self.store.bus.emit(MessageType.STORY_UPDATED, exec.story_id)
        self.store.bus.emit(MessageType.ATTENTION_UPDATED, execution_id)

    def retry(self, execution_id: str) -> None:
        exec = self.store.executions.get(execution_id)
        if not exec:
            return
        story = self.store.stories.get(exec.story_id)
        if not story:
            return
        task_rows = self._story_tasks(story.id)
        self.store.executions.pop(execution_id, None)
        self.start_story(story.id)
        new_exec_id = self.store.execution_by_story[story.id]
        self.store.add_timeline(new_exec_id, "Retry Scheduled", Cat.RUNTIME, f"retry of {len(task_rows)} task(s)")

    def signal(self, execution_id: str, signal: str, payload: dict | None = None) -> None:
        """Generic port hook — decisions route through apply_decision instead."""
        # No-op for the simulation MVP; kept to satisfy the WorkflowEngine port.

    def apply_decision(
        self, human_request_id: str, decision: DecisionKind,
        comment: str | None = None, selected_option: str | None = None,
    ) -> Decision:
        req = self.store.human_requests.get(human_request_id)
        if not req:
            raise HumanRequestNotFound(human_request_id)

        record = Decision(
            id=uid("dec"), human_request_id=human_request_id, decision=decision,
            selected_option=selected_option, comment=comment,
            user="you@leader", created_at=now(),
        )
        self.store.decisions[record.id] = record
        req.status = "Closed"

        exec = self.store.executions.get(req.execution_id)
        if exec:
            waiting = next((t for t in exec.task_executions if t.status == TaskStatus.WAITING_DECISION), None)
            if decision in (DecisionKind.ABORT, DecisionKind.REJECT):
                terminal = TaskStatus.CANCELLED if decision == DecisionKind.ABORT else TaskStatus.FAILED
                if waiting:
                    waiting.status = terminal
                exec.status = ExecStatus.CANCELLED if decision == DecisionKind.ABORT else ExecStatus.FAILED
                self.store.add_timeline(exec.id, "Decision Received", Cat.DECISION, str(decision))
            else:
                if waiting:
                    waiting.status = TaskStatus.RUNNING
                    if waiting.capability_executions:
                        waiting.capability_executions[0].status = CapStatus.RUNNING
                exec.status = ExecStatus.RUNNING
                label = ""
                if selected_option and req.options:
                    opt = next((o for o in req.options if o.id == selected_option), None)
                    label = f": {opt.label}" if opt else ""
                self.store.add_timeline(exec.id, "Decision Received", Cat.DECISION, f"{decision}{label}")
            self.store.bus.emit(MessageType.DECISION_APPLIED, req.id, {"executionId": exec.id})
            self.store.bus.emit(MessageType.EXECUTION_UPDATED, exec.id)
            self.store.bus.emit(MessageType.STORY_UPDATED, exec.story_id)
        self.store.bus.emit(MessageType.ATTENTION_UPDATED, req.id)
        return record

    def dismiss_notification(self, notification_id: str) -> None:
        for n in self.store.notifications:
            if n.id == notification_id:
                n.read = True
                break

    # -- background simulation --------------------------------------------
    def tick(self) -> None:
        for exec in list(self.store.executions.values()):
            if exec.status != ExecStatus.RUNNING:
                continue
            story = self.store.stories.get(exec.story_id)
            if not story:
                continue

            active = next((t for t in exec.task_executions if t.status == TaskStatus.RUNNING), None)
            if not active:
                nxt = next((t for t in exec.task_executions if t.status == TaskStatus.CREATED), None)
                if nxt:
                    nxt.status = TaskStatus.RUNNING
                    nxt.started_at = now()
                    if nxt.capability_executions:
                        nxt.capability_executions[0].status = CapStatus.RUNNING
                        if nxt.capability_executions[0].provider_executions:
                            nxt.capability_executions[0].provider_executions[0].status = ProvStatus.RUNNING
                    self.store.add_timeline(exec.id, "Capability Started", Cat.RUNTIME, nxt.task_name)
                    self.store.bus.emit(MessageType.EXECUTION_UPDATED, exec.id)
                continue

            if random.random() < 0.22:
                self.raise_human_request(story, exec, active)
                self.store.bus.emit(MessageType.EXECUTION_UPDATED, exec.id)
                self.store.bus.emit(MessageType.STORY_UPDATED, story.id)
                continue

            active.status = TaskStatus.COMPLETED
            active.completed_at = now()
            if active.capability_executions:
                cap = active.capability_executions[0]
                cap.status = CapStatus.COMPLETED
                if cap.provider_executions:
                    cap.provider_executions[0].status = ProvStatus.SUCCEEDED
                    cap.provider_executions[0].ended_at = now()
            self.store.add_timeline(exec.id, "Task Completed", Cat.RUNTIME, active.task_name)

            cap_id = self.store.tasks[active.task_id].capability_id if active.task_id in self.store.tasks else None
            prov_name = (
                active.capability_executions[0].provider_executions[0].provider_name
                if active.capability_executions and active.capability_executions[0].provider_executions
                else "Anthropic"
            )
            if cap_id == "cap_write_md":
                self.add_artifact(story.id, exec.id, ArtifactType.MARKDOWN, f"{active.task_name} — draft", prov_name)
            elif cap_id == "cap_diagram":
                self.add_artifact(story.id, exec.id, ArtifactType.DIAGRAM, active.task_name, "Anthropic")
            elif cap_id == "cap_code":
                self.add_artifact(story.id, exec.id, ArtifactType.SOURCE_CODE, active.task_name, "Claude Code")

            completed = sum(1 for t in exec.task_executions if t.status == TaskStatus.COMPLETED)
            exec.progress = completed / len(exec.task_executions)
            if completed == len(exec.task_executions):
                exec.status = ExecStatus.COMPLETED
                exec.completed_at = now()
                self.store.add_timeline(exec.id, "Execution Completed", Cat.RUNTIME)
                self.store.push_notification("Completed", f"Completed: {story.title}")
            self.store.bus.emit(MessageType.EXECUTION_UPDATED, exec.id)
            self.store.bus.emit(MessageType.STORY_UPDATED, story.id)

    # -- shared query helper ----------------------------------------------
    def _story_tasks(self, story_id: str) -> list[Task]:
        return sorted(
            (t for t in self.store.tasks.values() if t.story_id == story_id),
            key=lambda t: t.order,
        )
