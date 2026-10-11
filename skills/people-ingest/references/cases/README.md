# Worked Vault Cases — index

How real vaults organized their `wiki/people/` knowledge base. Generic on purpose —
pattern-match the structure, not the company specifics. **Load the matching case file only when
the vault's scale or source mix fits its shape** — don't read them all up front.

| Case | Shape to match | File |
| ---- | -------------- | ---- |
| A | Large dual-track engineering org (500+ eng): full ladder with dimensions, skills, processes, personas | `a-eng-prod-large-enterprise.md` |

Each case file carries: **Context** (org shape and sources) → **Information structure** (the
directory layout and what each layer answers) → **Articulations** (what links to what, and why) →
**Generic patterns** (the transferable core) → **Anti-patterns** (what to avoid).

## Adaptation guidance (applies to every case)

Scale drives the shape of the tree, not the layer structure. Cut tracks and levels freely, but
keep the role → dimension → skill → process → step → member chain and the articulation rules.

| Org size | Shape to aim for |
|----------|------------------|
| < 50 eng | Single track, 3–4 levels, no dimension pages; skills keep depth tables with Junior/Mid/Senior only; personas may not exist |
| 50–500 eng | Dual track optional; 4–6 IC levels; 3–4 dimension pages; management levels mirror the IC top levels; personas for the 2–3 core delivery roles |
| 500+ eng | Full case shape: dual track with overlapping top levels, per-track dimension sets, intermediate tiers where jumps got wide, persona per delivery role, matrix artifact page |

## Growing the case library

When you hit a **new vault organization shape** during an ingest — one that recurs and isn't
captured above — capture it here so future runs reuse it, **without touching SKILL.md**:

1. Confirm it's genuinely new (not a scale variant of an existing case — check the table above
   first) and worth reusing.
2. Write a new file `{next-letter}-{short-name}.md` in this folder, following the same frontmatter
   (`case`, `name`, `shape`, `source`) and Context → Information structure → Articulations →
   Generic patterns → Anti-patterns structure. Do not repeat the adaptation table.
3. Add one row to the index table above.
4. Keep it **generic** — no real company names, levels or values; genericize the specifics into a
   reusable structure.
