# Guide — Platform boundaries and partner negotiations

**Load when:** a partner team wants to co-build, consolidate or "unify"; defining what the platform owns; a consumer asks for custom features; adoption by another team. Case: H.

## Default moves

1. **Sequence: WHAT (layer) → WHEN → WHO contributes.** "Solve the technical problem first, cut the cake later", but privately the cake matters.
2. **Platform owns the HOW and the runtime; partners own content, experience and the last mile.** "I want the usage, not the maintenance." If nobody maintains content, bootstrap it yourself, but keep the door open to other maintainers.
3. **One coarse, extensible API with an opaque payload.** Add intelligence behind it later. Externally say "not on the timeline yet", never "we don't do X".
4. **Build the critical, complex part first.** Groundwork alone gets you replaced.
5. **Decide who maintains it before you build.** Guard the funding ratio.
6. **Verify the sponsor in the room.** Build from both ends: the team bottom-up, the leader with the peer leader.
7. **Answer a question with a question:** "What did you build? Show me a sample."
8. **Generic over custom:** no per-customer tagging. If the extra work is about 10% over what exists, do it; if it is much more, it goes to the backlog. Prefer the finer generic grain everyone will need.
9. **Cheapest convenience ladder:** one-time export → monthly batch → self-service. Share the query, don't build the tool.
10. **Partnership → product.** If teams must ticket or chat you, the abstraction failed. Aim for API and self-service.

## Questions to fire

- "Who owns the unified thing, by name?"
- "If we deliver only this layer, can they build the rest without us?"
- "Why are they coming to us: robustness, risk offload, mandate?"
- "Is this a yes to the part we agree with, or to everything in their head?"

## Traps

- Saying yes to a compound ask. Acknowledge only the part you agree with ("let me look into it").
- Committing to an interface before you must. Every move should keep future options open.
- Doing another team's job, such as their frontend or their testing. Time-box a feasibility check, then hand it back.
- Sharing capabilities you are still building "so they can track us".
