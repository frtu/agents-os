---
case: J
name: Sign-off sprawl
shape: An exec requires every function (product, engineering, compliance, security) to sign; the plan is a dense matrix, or the platform becomes the human proxy for go/no-go.
heuristics: [22, 19, 7]
guide: ../guides/stakeholder-trust-and-sign-off.md
---

# Case J — Sign-off sprawl

- **Before:** a launch plan with a full matrix (every signer × every dataset × every rule), and the platform team listed as go/no-go owner.
- **Common approach:** collect every signature, or push back on the exec.
- **Why this one diverges:** "all must sign" is how execs express fear. Fighting it loses, and the dense version never closes. **Fear is solved by tangible data.**
- **Interrogation:** *"What single question does each signer answer?"* *"Why does the platform own go/no-go?"* (19). *"Which domains are ready to test the process?"*
- **What surfaces:** most rules are boilerplate covered by company defaults. Some rules match an already-approved model. Only exotic logic needs a real review.
- **Distilled (what to do):** a sparse matrix tiered by risk. Defaults cover the majority; role rules go to the role owner; custom logic goes to its developer. Make sign-off cheap ("here is the only delta"). Use contract-first transparency: a board by bucket (security / functional / quality) with owner and strictness. Phase 1, engineers populate the board; phase 2, directors sign and own it. Start with 2–3 ready domains.
- **Lesson:** platform = transparency; leaders = decision. "If they sign, they're responsible."
