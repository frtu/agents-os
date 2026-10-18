---
case: K
name: Stakeholder dictates the HOW
shape: A request phrased as a solution ("give me a global score", "use syntax X", "set it to 1000") that the team is about to build or refuse literally.
heuristics: [16, 20, 2]
guide: ../guides/stakeholder-trust-and-sign-off.md
---

# Case K — Stakeholder dictates the HOW

- **Before:** a ticket: *"Expose a single global relevance score per result."*
- **Common approach:** build it, or refuse it.
- **Why this one diverges:** the literal HOW hurts the requester. Raw scores invite "why 97 vs 80?", and hand-tuning derails optimization. But a real need is buried inside.
- **Interrogation:** *"For what? For whom?"* (16). *"What would they do with it on day one?"*
- **What surfaces:** the need is explainability. End users need to see why something matched. Internal teams need a debug view of the factors.
- **Distilled (what to do):** "Let me come back with a consolidated answer." Turn the need into a contract: stakeholders add test cases, the platform optimizes across all of them, and progress is shown as a time series. Show outcomes, not engine internals. Pushback phrasing: "Tell me the WHAT, we'll figure out the HOW together."
- **Lesson:** extract the WHAT from the HOW, even when the conclusion is wrong. An exec's HOW is a way to express direction.
