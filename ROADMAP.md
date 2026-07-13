# Roadmap

This is a contribution map, not a startup roadmap or a delivery promise. It shows where help is useful while keeping scope explicit.

## Now

- make dogfooding evidence visible through commands, fixtures, CI checks, generated reports, or linked docs;
- stabilize product boundary docs;
- maintain the tested `MissionRecord v1` schema, transition engine and approval fixtures; the card represents a mission, never an agent;
- keep optimistic revision, immutable updates and human verdict gates fail-closed;
- document known projection and persistence gaps;
- keep spec and docs checks green when present.

## Next

- add a local read-only board projection consuming the complete transition-engine lifecycle;
- improve refusal, error, blocker, recovery and abandonment vocabulary from real use;
- extend contract tests only when a new transition is justified;
- prepare the first alpha-quality local mission-governance proof with a simulated Agent Factory adapter.

## Later

- broader integrations with Agent Factory, Proof Kit and Artifact Supply through explicit contracts;
- provenance for agentic mission evidence;
- hosted team usage only when tenancy, audit, and permission boundaries are explicit.
