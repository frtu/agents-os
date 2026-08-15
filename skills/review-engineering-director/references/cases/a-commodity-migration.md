---
case: A
name: The commodity migration that wasn't
shape: Commodity-looking work (migration, upgrade, refactor) claimed by category or by output count.
heuristics: [3, 7, 14]
---

# Case A — The commodity migration that wasn't

- **Before:** *"Led migration of service X to framework Y — 40 MRs merged."*
- **Interrogation:** Everyone migrates; the category is worth ~zero (heuristic 7). And MR count is output, not outcome (3). *"What made this migration different from the textbook one? What constraint did the standard playbook not cover?"* (14)
- **What surfaces:** it had to run with zero downtime under a constraint the standard case never faces — an unusual data shape, a dual-write window, an irreversible cutover.
- **Distilled:** *"Migrated X with zero downtime under [the unusual constraint the playbook doesn't handle], removing [the specific pain]."*
- **Lesson:** the differential (14) and the pain removed (3) carry the bullet — never the category or the MR count.
