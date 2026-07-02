# Rumble Crew

**Layer:** Rumble — Product  
**Role:** agentic teamwork workspace  
**Mission:** make human/agent collaboration visible, assignable, reviewable, and trustworthy.

---

## Stack role

- **Layer:** Rumble — Product.
- **Role:** agentic teamwork workspace.
- **Mission:** make human/agent collaboration visible, assignable, reviewable, and trustworthy.
- **Maturity:** `contract-first`.
- **Scale-ready:** no — specs exist, but the runtime is not present locally.
- **Current increment:** P0 specs.
- **Learning value:** human/agent tasks, approvals, evidence, run recovery, and operational transparency.
- **Next quality step:** define the `AgentTaskRequest` lifecycle and human approval policy.

See the ecosystem cockpit in [`constantin-jais/ecosystem/status.md`](https://github.com/constantin-jais/constantin-jais/blob/main/ecosystem/status.md).

## Dogfooding

This repository is part of the forge dogfooding loop: the ecosystem should use its own tools to make specs, maturity, contracts, releases, and product documentation observable.

Current visible evidence:

- the repository documents task, status, blocker, approval, and evidence boundaries;
- README maturity notes make the lack of local runtime explicit;
- specs frame the dogfooding loop before operational team-board claims are made.

Expected next evidence:

- publish example AgentTaskRequest lifecycle outputs;
- add fixture-backed approval and evidence checks.

Dogfooding claims should stay backed by visible commands, fixtures, CI workflows, generated reports, or linked docs.

## Contributing

See:

- [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines;
- [ROADMAP.md](ROADMAP.md) for current contribution priorities;
- [issue templates](.github/ISSUE_TEMPLATE/) for bugs, docs issues, fixture/example requests, and design discussions.

## Usable today

The README and specs define the product boundary for making agentic work visible: tasks, statuses, blockers, approvals, and evidence presentation.

## Not scale-ready yet

There is no local runtime yet, so it should not be presented as an operational team board or production collaboration product.

## Next product milestone

Specify the `AgentTaskRequest` lifecycle with explicit human approval and recovery semantics.

## Purpose

`rumble-crew` is built around the idea of agents as teammates: agents can receive tasks, report progress, raise blockers, reuse skills, and appear on a board next to humans.

In this ecosystem, `rumble-crew` is the product surface for agentic teamwork. It does not execute the work itself; it makes work understandable and governable.

## Owns

- Human/agent board UX: issues, assignments, statuses, blockers, reviews, and approvals.
- Agent profiles, team/squad views, skill visibility, and activity timelines.
- Workspace-level collaboration and operational transparency.
- Presentation of execution evidence produced by Bolt/Wrench/Gear.

## Does Not Own

- Actual orchestration, routing, and execution policy: belongs to `cos-matic`.
- Tool inspection/validation evidence: belongs to Wrench.
- Client-platform primitives, tokens, accessibility, and native/web adapters: belong to Portal.
- Agent runtime substrate, artifacts, and distribution: belongs to Gear.
- Generic project management unrelated to agentic work.

## Allowed Dependencies

- Consumes plans, runs, incidents, gates, and execution state from Bolt.
- Presents evidence emitted by Wrench and Gear.
- Uses Portal when building shared client surfaces for agent/human collaboration.
- Can write user decisions, approvals, comments, and assignments back into orchestration flows.

## Product Vision Challenge

`rumble-crew` must not become a clone of a project-management tool. Its sharp value is trustable collaboration with agents: who is doing what, why, with which evidence, and under whose approval.
