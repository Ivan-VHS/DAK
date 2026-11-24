# Service execution profiles and Java-ecosystem capability adaptation

DuckOS borrows proven *contracts and operational practices* from Java service
frameworks without importing a JVM runtime into the operating-system core.
The current implementation is a validator and static planner, not a process
supervisor: it never launches services, binds ports, loads modules or grants
capabilities.

## Profile contract

Each service is described by `duckos.service-profile.v1`:

- **Runtime:** native C11, native C++, Python, Node.js, JVM, JVM Native Image,
  or the Reaper runtime. The label is descriptive; it does not install a runtime.
- **Execution model:** blocking, worker-pool, event-loop, stream, or batch.
- **Admission limits:** concurrency, queue depth, timeout, input/output bytes
  and reserved memory.
- **Health:** explicit liveness/readiness requirements and bounded probe timing.
- **Resilience:** finite retry count, capped exponential backoff and optional
  circuit-breaker state parameters.
- **Dependencies/capabilities:** unique IDs resolved by a deterministic,
  dependency-first topological plan.

Unknown fields are rejected so a misspelled option cannot silently fall back
to a permissive default. Numeric limits reject booleans, NaN/infinity and
out-of-range values. Aggregate startup plans enforce global concurrency,
queue and memory budgets. Serialized profiles are finite JSON and are capped at 256 KiB by default.

## CLI

Create a JSON document with a top-level `services` array, then run:

```sh
duckos service-plan service-profiles.json
duckos service-plan service-profiles.json --max-concurrency 2048 --max-memory-bytes 8589934592 --max-profile-bytes 131072
```

The output includes the stable startup order, normalized profiles, retry
schedule and aggregate budget. It explicitly reports
`services_started=false`, `processes_spawned=false` and
`network_ports_bound=false`.

## Java framework crosswalk

| Java ecosystem concept | DuckOS adaptation |
|---|---|
| Spring Boot configuration / profiles | Strict versioned JSON service profiles with explicit defaults |
| Spring Boot Actuator / MicroProfile Health | Required liveness/readiness definitions in the service contract |
| Quarkus / Micronaut build-time metadata | Preflight validation and deterministic static dependency planning |
| Vert.x execution model | Explicit worker-pool/event-loop/stream/batch labels and capacity parameters |
| Resilience4j / Spring Cloud circuit breakers | Bounded retry/backoff and circuit-breaker parameters |
| Jakarta CDI / service contracts | Versioned module ABI, capability IDs and dependency graph |
| OpenTelemetry | Reserved correlation/telemetry contract direction; no telemetry exporter is claimed by this planner |
| Hibernate / jOOQ | Not applicable to the service planner; no database or ORM is introduced |
| Netty / Javalin | No HTTP listener is added; native transport work remains a separate subsystem |

## Operational semantics

- The planner is deterministic and side-effect free.
- A retry schedule is advisory; no retry actually runs.
- A declared circuit breaker is a policy contract, not a running breaker.
- A memory reservation is a plan-time budget, not an OS-enforced allocation.
- Runtime selection does not imply runtime installation, compatibility or isolation.
- Dependency order is not proof that each service is bootable or healthy.

## Extension path

A future native supervisor should consume this validated profile rather than
inventing a second configuration format. Before implementation it must add
process identity, readiness evidence, cancellation, bounded shutdown, restart
state persistence, privilege/capability enforcement, telemetry provenance and
crash-recovery tests. Until those exist, this document and CLI describe
planning only.
