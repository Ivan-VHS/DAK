# Cross-repository Java ecosystem capability adaptation

This map records how mature Java ecosystem practices are adapted across the
Ivan-VHS repositories. It deliberately does not add Spring Boot, Quarkus,
Micronaut, Hibernate or Netty as dependencies to projects whose contracts do
not need a JVM, SQL store or network server.

## Repository matrix

| Repository | Native stack and role | Adapted capabilities | Explicitly not claimed |
|---|---|---|---|
| [DuckOS](https://github.com/Ivan-VHS/DuckOS/tree/feature/java-ecosystem-capability-adaptation) | C11 foundation, Python build/control tools, JavaScript Mora shell | Strict service profiles, dependency-first planning, resource quotas, liveness/readiness, retry/backoff and circuit-breaker parameters | No service process is started, no port is bound, no kernel capability is enforced by the planner |
| [Reaper](https://github.com/Ivan-VHS/Reaper/tree/feature/polyglot-source-profiles) | Python language implementation and native C compiler | Bounded plugin dispatch, local health metrics, source-profile and structured diagnostic contracts | No hard interruption of synchronous Python handlers, no HTTP server/OTLP exporter/SQL persistence |
| [OPlague](https://github.com/Ivan-VHS/OPlague/tree/feature/java-ecosystem-capability-adaptation) | Python read-only hardware/package evidence workbench | Bounded plugin inputs/outputs, per-plugin admission, observed deadlines and readiness metrics | No driver installation, no remote control plane, no force-kill timeout |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample/tree/feature/java-ecosystem-capability-adaptation) | C++20/Qt offline audio generation | Per-request render budgets, execution correlation, plugin health and timing evidence | No distributed renderer, real-time plugin host, forced interruption or database |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki/tree/feature/java-ecosystem-capability-adaptation) | C11 processor workstation and C ABI | Typed/paginated metric query, capability/type predicates and explicit result counts | No ORM, network backend or distributed data engine |

## Capability mapping

| Java framework family | Portable property reused | Projects |
|---|---|---|
| Spring Framework / Boot | Explicit composition, configuration boundaries, lifecycle and health | All projects, through native constructs |
| Quarkus / Micronaut | Preflight validation, static metadata, build-time checks and bounded startup contracts | DuckOS, Reaper, OPlague, VentuSample, Pytyliki |
| Jakarta EE / MicroProfile | Versioned schemas, capability contracts, health/readiness interfaces | DuckOS, Reaper, OPlague, VentuSample, Pytyliki |
| Vert.x / Netty | Explicit concurrency and queue models; event-loop discipline only where asynchronous I/O exists | DuckOS planning; no event-loop networking is added elsewhere |
| Javalin / HTTP stacks | Route/transport separation | Not introduced: none of these changes creates a web service |
| Hibernate / Spring Data | Persistence lifecycle and transaction discipline | Existing in-memory/file/native transactions are retained; no relational DB is added |
| jOOQ / MyBatis | Typed query predicates and explicit pagination | Pytyliki metric registry |
| Resilience4j / Spring Cloud | Bounded admission, backoff, circuit-breaker policy and execution budgets | DuckOS, Reaper, OPlague, VentuSample |
| Actuator / OpenTelemetry | Health state, counters, durations and correlation fields | Reaper, OPlague, VentuSample; other projects retain local reports |
| Spark / Flink / Kafka Streams | Explicit stream/batch boundaries and checkpoint awareness | Not introduced: current workloads are local/bounded |
| Apache Camel | Explicit adapters and versioned cross-project message/file contracts | Existing federation and file/ABI integrations; no generic ESB is added |

## Shared engineering rules

1. **No framework by name alone.** Every adaptation maps to a concrete public
   parameter, invariant, status, test or versioned contract.
2. **Backward compatibility.** Existing C ABI and metric search entrypoints,
   Reaper syntax defaults, plugin IDs and existing file schemas remain stable.
3. **Bounded inputs and outputs.** Size, queue, concurrency, timeout, memory
   and collection limits are explicit and validated before expensive work.
4. **Honest deadline semantics.** A synchronous handler can be timed and its
   late result rejected, but it cannot be safely pre-empted without cooperative
   cancellation or process isolation.
5. **Readiness is scoped.** A registry-ready result is not a claim that an OS,
   device, external runtime, network dependency or GUI is healthy.
6. **No hidden side effects.** Static plans do not launch services; inspection
   does not install drivers; offline DSP does not become real-time playback.
7. **One contract across the dependency graph.** When schemas, IDs or API
   versions change, tests and consumers in the peer repositories must be
   updated in the same coordinated change.

## Validation status

The branches contain implementation and regression-test changes. The
connector session did not execute the full CMake, Python or Qt test suites
locally. GitHub Actions must pass on the current branch heads before merge.
These branches are proposed changes; none is merged to `main` by this plan.
