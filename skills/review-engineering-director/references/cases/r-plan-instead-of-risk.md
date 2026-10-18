---
case: R
name: Action plan delivered where a risk assessment was asked
shape: Leaders ask "should we go?" on a risky migration; the doc answers with a detailed execution plan.
heuristics: [15, 20, 13]
guide: ../guides/exec-review-and-demo.md
template: ../templates/risk-assessment.md
---

# Case R — Action plan delivered where a risk assessment was asked

- **Before:** a 10-page migration plan with phases, owners and dates, sent to leaders who asked for a risk evaluation.
- **Common approach:** be thorough and show the plan.
- **Why this one diverges:** "Leaders don't care about action; they care what happens if it goes wrong." Their biggest fear is an irreversible, half-finished migration.
- **Interrogation:** *"What decision does this doc drive: go, no-go, or go-with-conditions?"* *"What happens to the business if it stalls halfway?"* (20).
- **What surfaces:** technical facts that never reached business language ("deletes don't propagate"), an undefined term ("zero downtime"), and a driver pushing changes into every domain with unclear requirements.
- **Distilled (what to do):** remove the action plan. Go deeper on risks and predictions. Translate each risk into a business consequence with a sampled case, and frame it from neighboring teams' point of view. Let domain owners answer their risks. Stay the consulting expert while the program driver chases.
- **Lesson:** match the altitude of the ask.
