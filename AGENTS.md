# AGENTS.md

Canonical agent-context surface for this repository. `CLAUDE.md` is a minimal adapter that imports this file.

## Purpose

Missions is the authority that governs bounded agent missions: a requester proposes a mission, two independent reviewer agents approve the same immutable plan digest, Missions authorizes it, an orchestrator executes it, and the result is validated by quorum before it counts. Reported activity stays distinct from validated results.

## Scope / Non-scope

- **Reserved home.** This repository is the public reserved home of Missions. The product is being rebuilt in the canonical base repository [`libre-ai/libre-ai`](https://github.com/libre-ai/libre-ai) (multi-repo topology, [ADR-0008](https://github.com/libre-ai/libre-ai/blob/main/docs/adr/0008-multi-repo-target-topology-and-brand.md)); it reopens as the real application repository when the owner activates it.
- This repository carries the tested `MissionRecord v1` contract surface: `schemas/mission-record.v1.schema.json`, fixtures under `fixtures/mission-record/`, and a dependency-free validator and transition engine under `scripts/`.
- Non-scope: new product development in this repository until activation; the card represents a mission, never an agent (ROADMAP).

## Commands

Verified against `scripts/` and `.github/workflows/hygiene.yml` (stdlib-only Python, no dependencies):

- `python3 scripts/validate_mission_contracts.py` — semantic validation of MissionRecord v1 fixtures against the schema.
- `python3 -m unittest discover scripts/tests -v` — unit tests for the contract validator and the fail-closed transition engine (`scripts/mission_runtime.py`).

## CI gates

- `hygiene` (`.github/workflows/hygiene.yml`) — runs the contract validation and unit tests above.
- `Context hygiene` (`.github/workflows/context-hygiene.yml`).

## Links

- [README](README.md) · [Français](README.fr.md)
- [docs/product-readiness.md](docs/product-readiness.md) — canonical readiness cockpit
- [schemas/mission-record.v1.schema.json](schemas/mission-record.v1.schema.json)
- [ROADMAP.md](ROADMAP.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md)
