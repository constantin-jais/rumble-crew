**English** · [Français](README.fr.md)

> [!NOTE]
> **Reserved · future home of Missions** — rebuilt in the canonical base repository [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai) ([multi-repo topology, ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).
> This repository will reopen as the real application repository when the owner activates it, consuming the base as a versioned dependency. The foundations described below are **being built now** — with links to the code that already exists.

# Missions

**The authority that governs bounded agent missions.** A requester proposes a mission — a bounded piece of work handed to agents; two independent reviewer agents approve the same immutable plan; Missions authorizes it; an orchestrator executes it; and the result is validated by quorum before it counts. **Reported activity stays distinct from validated results.**

Missions is the couche-2 (Polaris) human authority over agent orchestration: it decides what is allowed, records the evidence, and never lets an agent's claim of work stand as a validated result on its own.

## Why it's different

- **Two-agent quorum.** No single identity — human or agent — authorizes its own work. Two eligible reviewers, distinct from every contributor, approve the same **immutable plan digest**, then the same **immutable result digest**.
- **Reported ≠ validated.** What an agent reports it did is kept separate from what has been quorum-validated. Observation never silently becomes truth.
- **Immutable digests.** Authorization binds to an exact plan digest; a changed result requires fresh reviews. Past evidence is never rewritten.
- **Human control gate retained.** Protected canonical contracts, auth, migrations, releases and deployments keep an additional human control gate on top of the agent quorum.
- **Deny by default.** An unknown or self-reviewing reviewer, a stale digest, or an expired authorization is refused, fail-closed.

## Status — spec-published, foundations under construction

Missions is being rebuilt from locked contracts. It is **not released yet**; the v1 authority baseline already exists and is proven in the base repository:

| Foundation                                      | State      | Evidence                                                                                                                                                      |
| ----------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **v1 domain state machine**                     | ✅ built   | Mission lifecycle as a pure state machine ([#151](https://github.com/libre-ai/libre-ai/pull/151))                                                             |
| **Tenant-scoped RLS persistence**               | ✅ built   | Append-only, row-level-security isolation ([#152](https://github.com/libre-ai/libre-ai/pull/152))                                                             |
| **Authorization matrix**                        | ✅ built   | App-side authorization conformant to the missions-v1 contract ([#153](https://github.com/libre-ai/libre-ai/pull/153))                                         |
| **Accessible cockpit**                          | ✅ built   | Server-rendered, keyboard-accessible read view ([#154](https://github.com/libre-ai/libre-ai/pull/154))                                                        |
| **Command service**                             | ✅ built   | Composes authorization → domain → persistence ([#155](https://github.com/libre-ai/libre-ai/pull/155))                                                         |
| **Adversarial write-path qualification**        | ✅ built   | Release qualification of the write path ([#157](https://github.com/libre-ai/libre-ai/pull/157))                                                               |
| **Orchestration contracts + engine brick**      | ✅ present | `mission-record.v2`, `orchestrator-control/event`, `agent-review-quorum` schemas + golden vectors (quorum, transitions, digests); `crates/agent-orchestrator` |
| **v2 two-agent quorum**                         | ⏳ next    | Contract locked, unimplemented: agent-signed reviews, reviewer isolation, nonce/expiry                                                                        |
| **Orchestrator event binding + decision gates** | ⏳ next    | Accept orchestrator-signed events; block/resume on human decision requests                                                                                    |
| **Agent Board** — operational projection        | ⏳ next    | The read-only dashboard (fleet, task board, live progress) that projects Missions events                                                                      |

This repository is public and reserved. **Benchmark target:** managed-agents platforms (e.g. Multica) — reached through governed authorization and quorum evidence rather than raw task throughput.

## How it works

1. **Propose / review** — a requester creates a mission from an accepted planning handoff; a deterministic plan body is reviewed blindly by two eligible agents on the same digest.
2. **Authorize / observe** — Missions verifies the plan quorum and emits an **expiring authorization**; the orchestrator reports causal events while an operator may pause or cancel within policy.
3. **Validate** — the result is approved by a second quorum on the immutable result digest before it counts as validated; reported activity that never reached quorum is never promoted to truth.

## Architecture — built from interoperable bricks

Missions is the authority of the couche-2 human surface. Around it, each brick is independently versioned and interoperable (the multi-repo target of [ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)).

| Brick                                          | Role                                 | Interface it exposes / consumes                                                                         |
| ---------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| **Missions** (`apps/missions`)                 | The authority — control plane        | Proposes, reviews, authorizes, validates; emits authorization + mission events                          |
| **Agent Board** (`apps/agent-board`, ⏳)       | The projection — observability plane | Read-only view of Missions events: fleet, task board, live progress; never writes mission state         |
| **Orchestrator** (`crates/agent-orchestrator`) | The execution engine                 | Plans, executes, enforces budget, reports causal events; consumes an expiring authorization             |
| **Contracts**                                  | Locked interoperability surface      | `mission-record.v2`, `orchestrator-control/event.v1`, `agent-review-quorum.v1` schemas + golden vectors |

The authority (Missions) **writes** the state of truth; the board **reads** it to make the fleet observable; the orchestrator **runs** the work between them. The board holds no authority — it cannot authorize, only display.

## Where the work happens

All active development is in the base repository, under:

- `apps/missions` — the authority (domain, authorization, persistence, cockpit, command service)
- `crates/agent-orchestrator` — the execution engine
- `contracts/` — the locked schemas, orchestration contracts and golden vectors
- [`docs/apps/missions.md`](https://github.com/libre-ai/libre-ai/blob/main/docs/apps/missions.md) — the Missions authority brief
- [`docs/apps/agent-board.md`](https://github.com/libre-ai/libre-ai/blob/main/docs/apps/agent-board.md) — the Agent Board projection brief

To follow progress or contribute, open issues and pull requests in [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai). This repository stays reserved until activation.

## License

EUPL-1.2.
