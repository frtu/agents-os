"""Seed catalog + planning data, mirroring the frontend mock so the two backends
present an identical demo. Execution instantiation for pre-seeded runtime states
is delegated to the SimulationEngine (runtime logic lives in one place)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.models import (
    AcceptanceCriteria,
    Capability,
    Initiative,
    Provider,
    Story,
    Task,
)
from app.infra.store import EpicRow, Store, now, uid

if TYPE_CHECKING:  # avoid import cycle; engine imports the store, not vice versa
    from app.workflow.simulation import SimulationEngine


_PROVIDERS = [
    ("prov_anthropic", "Anthropic", "llm"),
    ("prov_openai", "OpenAI", "llm"),
    ("prov_gemini", "Google Gemini", "llm"),
    ("prov_claude_code", "Claude Code", "llm"),
    ("prov_github_mcp", "GitHub MCP", "mcp"),
    ("prov_human", "Human", "human"),
]

_CAPABILITIES = [
    ("cap_research", "Research", "Gather and synthesize information", "Topic", "Research Notes", ["prov_anthropic", "prov_openai", "prov_gemini"]),
    ("cap_write_md", "Write Markdown", "Author a Markdown document", "Markdown Specification", "Markdown Document", ["prov_anthropic", "prov_openai"]),
    ("cap_diagram", "Generate Diagram", "Produce a diagram", "Diagram Spec", "Diagram", ["prov_anthropic", "prov_gemini"]),
    ("cap_review", "Review", "Review content against criteria", "Document", "Review", ["prov_anthropic", "prov_human"]),
    ("cap_review_arch", "Review Architecture", "Assess an architecture proposal", "Proposal", "Assessment", ["prov_anthropic", "prov_human"]),
    ("cap_code", "Generate Code", "Generate source code", "Spec", "Source Code", ["prov_claude_code", "prov_openai"]),
    ("cap_summarize", "Summarize", "Summarize long content", "Document", "Summary", ["prov_anthropic", "prov_openai"]),
]

# initiative -> stories -> tasks; `state` drives runtime instantiation.
_INITIATIVES = [
    {
        "id": "init_promo",
        "title": "Promotion to Staff Engineer",
        "description": "Prepare a complete, executive-quality promotion package.",
        "stories": [
            {
                "id": "story_packet",
                "title": "Write promotion document",
                "description": "Executive-quality promotion narrative with metrics.",
                "status": "Ready", "priority": 1, "state": "running",
                "criteria": ["Executive quality", "Less than three pages", "Ready for manager review"],
                "tasks": [
                    ("Research past impact", "cap_research", "Ready"),
                    ("Draft narrative", "cap_write_md", "Ready"),
                    ("Review for tone", "cap_review", "Ready"),
                ],
            },
            {
                "id": "story_diagrams",
                "title": "Generate architecture diagrams",
                "description": "Diagrams showcasing systems led.",
                "status": "Ready", "priority": 2, "state": "blocked",
                "criteria": ["Consistent style", "Covers 3 systems"],
                "tasks": [
                    ("Collect system inventory", "cap_research", "Ready"),
                    ("Produce diagrams", "cap_diagram", "Ready"),
                ],
            },
            {
                "id": "story_achievements",
                "title": "Update achievements log",
                "description": "Refresh the running achievements document.",
                "status": "Ready", "priority": 3, "state": "ready",
                "criteria": ["All quarters covered"],
                "tasks": [("Summarize quarter", "cap_summarize", "Ready")],
            },
        ],
    },
    {
        "id": "init_modernize",
        "title": "Platform Modernization",
        "description": "Modernize the core platform and migrate services.",
        "stories": [
            {
                "id": "story_arch",
                "title": "Create architecture proposal",
                "description": "Target architecture for the modernized platform.",
                "status": "Ready", "priority": 1, "state": "completed",
                "criteria": ["Cost analysis included", "Risks documented"],
                "tasks": [
                    ("Research current state", "cap_research", "Ready"),
                    ("Draft proposal", "cap_write_md", "Ready"),
                    ("Review architecture", "cap_review_arch", "Ready"),
                ],
            },
            {
                "id": "story_migrate",
                "title": "Build migration strategy",
                "description": "Phased migration plan with rollback.",
                "status": "Ready", "priority": 2, "state": "running",
                "criteria": ["Zero-downtime path", "Rollback per phase"],
                "tasks": [
                    ("Analyze dependencies", "cap_research", "Ready"),
                    ("Write migration plan", "cap_write_md", "Ready"),
                ],
            },
            {
                "id": "story_poc",
                "title": "Prototype service extraction",
                "description": "Extract one service as a proof of concept.",
                "status": "Draft", "priority": 3, "state": "todo",
                "criteria": ["Runs in staging"],
                "tasks": [("Scaffold service", "cap_code", "Draft")],
            },
        ],
    },
    {
        "id": "init_ai",
        "title": "AI Adoption",
        "description": "Roll out AI tooling across the org.",
        "stories": [
            {
                "id": "story_guidelines",
                "title": "Draft AI usage guidelines",
                "description": "Company guidelines for responsible AI use.",
                "status": "Ready", "priority": 1, "state": "blocked",
                "criteria": ["Legal reviewed", "One page"],
                "tasks": [
                    ("Research policies", "cap_research", "Ready"),
                    ("Write guidelines", "cap_write_md", "Ready"),
                ],
            },
            {
                "id": "story_training",
                "title": "Prepare enablement material",
                "description": "Onboarding deck and examples.",
                "status": "Ready", "priority": 2, "state": "ready",
                "criteria": ["Covers top 5 workflows"],
                "tasks": [("Summarize workflows", "cap_summarize", "Ready")],
            },
        ],
    },
]


def seed(store: Store, engine: "SimulationEngine") -> None:
    if store.seeded:
        return

    for pid, name, ptype in _PROVIDERS:
        store.providers[pid] = Provider(id=pid, name=name, type=ptype)

    for cid, name, desc, inputs, outputs, provs in _CAPABILITIES:
        store.capabilities[cid] = Capability(
            id=cid, name=name, description=desc,
            inputs=inputs, outputs=outputs, supported_providers=provs,
        )

    for order, spec in enumerate(_INITIATIVES):
        store.initiatives[spec["id"]] = Initiative(
            id=spec["id"], portfolio_id="portfolio_default",
            title=spec["title"], description=spec["description"], status="Ready",
            order=order,
            created_at=now(-86_400_000), updated_at=now(),
        )
        epic_id = f"epic_{spec['id']}"
        store.epics[epic_id] = EpicRow(epic_id, spec["id"], spec["title"])

        for s in spec["stories"]:
            story = Story(
                id=s["id"], epic_id=epic_id, title=s["title"],
                description=s["description"], priority=s["priority"], status=s["status"],
                acceptance_criteria=[
                    AcceptanceCriteria(id=uid("ac"), description=c) for c in s["criteria"]
                ],
                created_at=now(-86_400_000), updated_at=now(),
            )
            store.stories[s["id"]] = story

            task_rows: list[Task] = []
            for i, (tname, cap_id, tstatus) in enumerate(s["tasks"]):
                task = Task(
                    id=uid("task"), story_id=s["id"], name=tname,
                    planning_mode="Structured", status=tstatus, order=i,
                    dependencies=[], capability_id=cap_id,
                    created_at=now(-86_400_000), updated_at=now(),
                )
                store.tasks[task.id] = task
                task_rows.append(task)

            if s["state"] not in ("todo", "ready"):
                engine.instantiate_execution(story, task_rows, s["state"])

    store.seeded = True
