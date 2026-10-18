---
case: I
name: It doesn't work despite green tests
shape: A stakeholder keeps saying the product isn't ready; the team's response is more tests, more dashboards, more tools.
heuristics: [22, 1, 3]
guide: ../guides/stakeholder-trust-and-sign-off.md
---

# Case I — "It doesn't work" despite green tests

- **Before:** a status update listing hundreds of passing tests and a new quality dashboard with dozens of columns.
- **Common approach:** add more tooling and more data.
- **Why this one diverges:** it is a trust gap, not a tooling gap. Naive questions showed that an intermediary had rewritten the stakeholder's cases, so her actual cases were never run. Her complaint was legitimate. Developer-centric tools made her back away.
- **Interrogation:** *"Were *her* cases run, verbatim?"* *"What concrete evidence would remove her fear?"* (22). *"Which number on this board changes her decision?"* (1).
- **What surfaces:** one-way communication; an intermediary hiding behind the platform team; a ritual (grooming) that had decayed into status talk.
- **Distilled (what to do):** human → process → tools. Demo her case working, together. Give each step owner a definition of done and add a triage tree that routes each failure. Measure against the committed bar and hide unreliable numbers. Escalate the connection gap to her manager.
- **Lesson:** trust is earned by seeing it work, not by the volume of evidence.
