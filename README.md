> [!WARNING]
> **Frozen on 2026-07-16 — reserved as the future home of Agent Board ([monorepo ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).**
> Agent Board is being rebuilt from locked contracts in the canonical base repository [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai) (target: `apps/missions`). This repository will reopen as the real product repository when the owner activates it. Everything below describes the pre-freeze state and no longer reflects the current architecture or roadmap.

<p align="center">
  <img src=".github/assets/repository-card.svg" alt="Libre AI Agent Board, represented by missions moving through visible columns and approval gates." width="100%">
</p>

# Libre AI Agent Board

A future human decision surface for agentic missions, blockers, approvals and evidence.

## Status

| | |
| --- | --- |
| Maturity | **Contract-first** |
| Works today | tested `MissionRecord v1` contract and a side-effect-free local transition engine |
| Not available | there is no local board, persistence, agent execution or hosted collaboration product |
| Historical ID | `rumble-crew` may remain in historical references only |

Readiness cockpit: [docs/product-readiness.md](docs/product-readiness.md).

This repository intentionally avoids presenting a specification as an operational product.

## Product boundary

Agent Board is intended to make agentic work understandable and governable:

- one card represents a mission, never an agent profile;
- the mission states its intent, scope, risk and acceptance conditions;
- current status, blockers and required human decisions stay visible;
- reported activity remains distinct from verified outcomes;
- every approval, refusal and transition retains an author and a reason.

It does **not** execute or route agents, inspect tools, store generic artifacts, profile agents, or replace a general project-management suite. Agent Factory owns orchestration and execution; Agent Board owns the human decision surface connected through explicit contracts.

## Contract proof

`MissionRecord v1` makes the first lifecycle boundary executable. It keeps scope, risk, acceptance conditions, approvals, blockers, reported activity, submitted result and human verdict distinct. High and critical missions require approval by a human other than the requester; activity alone can never satisfy a result.

```bash
python3 scripts/validate_mission_contracts.py
python3 -m unittest discover scripts/tests -v
```

The contract and positive/negative fixtures live under `schemas/` and `fixtures/mission-record/`. `scripts/mission_runtime.py` applies optimistic-revision transitions to an immutable copy and validates the resulting record. Its tests cover start, declared activity, block, recovery, result submission, human acceptance, pre-execution refusal, stale writes and forbidden service verdicts. It does not persist data, execute or route an agent. See the canonical local cockpit: [docs/product-readiness.md](docs/product-readiness.md).

## Next evidence

The next milestone is a local read-only board projection consuming the transition engine across proposal, approval, blocked execution, recovery, result submission and human acceptance or refusal. Product availability should not be announced before that projection exists.

## Contributing

Start with:

- [Roadmap](ROADMAP.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Contributions should improve observable contracts and evidence rather than add speculative platform scope.

## License

[MIT](LICENSE).
