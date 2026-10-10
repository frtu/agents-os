# People Page Templates — extracted examples

> Reference only. The skill extracts the template **live** from the target
> vault's `wiki/people/members/` pages; these snapshots show what the
> extraction typically yields and the two-tier ref pattern.

Core vault named : `{core-people}`=`management`

## Tier 1 — canonical member page

Skeleton observed in `{core-people}/vault/wiki/people/members/` (e.g.
 `fred-tu.md`):

```markdown
---
Category: member
Tags:
  - member
  - leader
  - {domain}
Source links:
  - "[[source-{slug}|{Source Title}]]"
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Full Name}

**Role:** {Title} @ {Company}
**Site:** {Location}

## Current Profile

{One-paragraph current scope, role line, key ownership.}

## Role

| Attribute | Value |
| --------- | ----- |
| Role      | …     |
| Location  | …     |
| Since     | …     |

## {Evidence sections — e.g. "How X operates", "Operating signals"}
{Only what sources support; quote or closely paraphrase.}

## Related

- [[page]] — relationship context
- [[Workspaces/{other-vault}/vault/wiki/people/members/{slug}-ref-{topic}|{Name} — {topic} view ({other-vault})]]
```

## Tier 2 — workspace-scoped ref page (topic vault)

Skeleton observed in `cost-optimisation/.../fred-tu-ref-cost.md`:

```markdown
---
Category: wiki
Aliases: [{slug}, {Full Name}, {slug}-ref-{topic}]
Tags: [member, {topic}, …]
Source links:
  - "[[source-{slug}|{Source Title}]]"
  - "[[Workspaces/{core-people}/vault/wiki/people/members/{slug}|{Name} (management)]]"
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Full Name}

> Reference to [[Workspaces/{core-people}/vault/wiki/people/members/{slug}|{Name}]]
> in the `{core-people}` workspace. This page captures the **{topic} view only**;
> leadership profile lives there.

{One-paragraph role-in-this-topic.}

## Role in {topic}

| Attribute | Value |
|-----------|-------|
| … | … |

## What {first name} {did/owns here}

- {Evidence-backed bullets, each traceable to the source page.}

## Note on evidence

{Source type, diarization reliability, what not to extend beyond this scope.}
```

## Gap marker (evidence exists for nothing in a section)

```markdown
## {Section Name}

> No evidence in current sources. Fill from {next expected source}.
```
