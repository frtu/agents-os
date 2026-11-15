# Worker brief — phase {{PHASE_ID}}, lane `{{LANE_ID}}` (EXTERNAL DELIVERABLE)

Produce one document **outside the wiki** that applies a lens (a review skill, a template) to the
knowledge built in phases 1–2. **The original artifact under review is never modified.**

**Vault dir:** {{VAULT}}  ·  **Date:** {{DATE}}

## 1. Inputs
- The artifact to review or improve, and the supporting sources (read-only):
{{SOURCES}}
- Reference pages to rely on (read these before anything else):
{{SIBLING_SLUGS}}

## 2. Lens and lane instructions
{{INSTRUCTIONS}}

If the instructions name a skill, read its `SKILL.md` in full, then load only the references it
says to load for this case. An interactive mode (one that pauses for the author's defence) runs
**non-interactively** here: list the questions under an "Unresolved" section instead of waiting.

## 3. Your contract
**Write exactly:**
{{CREATES}}

**Write scope:**
{{WRITE_SCOPE}}

**Never touch:**
{{FORBIDDEN}}

## 4. Deliverable rules
- **BLUF:** the bottom line, the verdict and the single biggest fix come first.
- **Point to the evidence:** every recommendation points to a wiki page (`↳ [[slug]]`).
- **Never invent facts:** a missing fact is written `[need input: …]`.
- **Quote the original:** when critiquing a line, quote it exactly.
- **Credit honestly:** if a team built something, say "led the team that …".
- **Clean your own prose:** if a word-level clarity skill exists, run its checks on your own text.
- **End with three sections:** Unresolved (questions the author must answer), Verdict (one line), and References.

## 5. Hand-back (required)
Write `{{MANIFEST_PATH}}` with `{"lane", "created": [{path, hook}], "updated": [], "gaps": []}`.
Leave `portal_section` empty, since output files are not listed in the portal.
Reply with: the path, the bottom line, and the top 5 findings. Do not stage or commit.
