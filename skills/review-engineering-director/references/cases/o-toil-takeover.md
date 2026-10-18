---
case: O
name: Taking over another team's toil
shape: You are asked to absorb a manual ops loop (alert relay, capacity bumps) currently run by a "messenger" team; the draft is accept-as-is or refuse.
heuristics: [19, 17]
guide: ../guides/team-load-and-delegation.md
---

# Case O — Taking over another team's toil

- **Before:** *"We'll take over the capacity alerts from next sprint."*
- **Common approach:** accept the loop as it is, or refuse it.
- **Why this one diverges:** "my maybe becomes yes after asking". You cannot negotiate the conditions until you have seen the real process.
- **Interrogation:** *"What are the thresholds, increment sizes and re-alert cadence today?"* *"Who keeps the incident risk?"* (19). *"Where is the last reversible step?"*
- **What surfaces:** small increments every few weeks (a micro-optimization staircase), a human relaying alerts, and nobody owning the long-term shape.
- **Distilled (what to do):** own short and long term, control the increment size (a larger buffer to buy time to automate), and leave incident risk with the original owner. Scope it tightly. Automate up to the last reversible step; destructive actions stay human, with auto-proceed after N days of no objection. Delegate to a junior who ramped up well; seniors review the design. The end state is a system that shifts responsibility to the domains.
- **Lesson:** don't become the new messenger. Do ops enough to know how to do dev.
