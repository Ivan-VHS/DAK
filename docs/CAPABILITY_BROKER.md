# DuckOS native capability broker

**Status:** C11 authorization primitive implemented and host-tested against Reaper's canonical operation catalogue. The booted kernel does not yet call it from syscall or IPC dispatch.

## Authority source

The broker consumes \`ReaperSystemOperationInfo\` from the pinned Reaper submodule. Each operation's declared required capability and domain are the single source of truth. Unknown operations fail closed.

Root grants are issued only by a configured authority principal and are bounded by an explicit root ceiling. There is no default grant. Task identity is a pair of kernel task ID and generation, so reuse of a numeric task ID does not reuse the old identity.

## Token and resource model

Each grant is represented by a bounded table slot and an opaque 64-bit token made from a slot index and generation. A stale token cannot resolve after revocation and reuse of that slot.

A grant contains:
- grantor and grantee task-generation identities;
- an explicit Reaper capability bitmask;
- a resource domain;
- either global service scope or one object ID plus object generation;
- an optional parent token for delegated grants.

Object-scoped grants are checked against both resource ID and generation. A stale/recycled window, surface, display lease or GPU object therefore does not inherit a prior grant.

## Admission

The broker authorizes only when all checks pass:
1. The operation exists in the Reaper registry.
2. The token resolves to a live generation.
3. The authenticated current task matches the grant's grantee.
4. Every required capability bit is present.
5. The operation domain and object identity match an object-scoped grant.
6. Every parent token in the delegation chain remains active and grants to the child grantor.

Administrative display-mode changes, session unlock requests and GPU reset use their own capability bits and are denied by ordinary read/render grants.

## Delegation and revocation

Delegation is explicit. The parent grant must include \`DUCKOS_CAPABILITY_BROKER_DELEGATE\`; a child can receive only a subset of parent rights and cannot widen an object-scoped grant to another object or to global scope.

A parent token remains in every descendant's ancestry. Revoking that parent makes descendants fail authorization without walking or mutating the entire table. A grantee may revoke its own token; the configured authority may revoke any live token.

## Kernel boundary

The API is internal to kernel/service code. The caller principal must be read from the current scheduler task structure, never accepted from a user payload. The owning service must serialize broker calls under its kernel lock.

This PR provides the actual authorization algorithm and revocable capability-token store, but does not yet integrate it into an execution path: DuckOS still lacks a process scheduler, ring-3 tasks, a syscall handler, a kernel endpoint registry and privileged desktop services. Until those exist and call this broker, the running Stage 1 image does not enforce these grants against applications.

## Tests

\`duckos-capability-broker\` checks root-only issuance, task-generation identity, object scoping, domain matching, display/GPU administrative separation, explicit attenuation, attempted rights escalation, ancestor revocation, stale token rejection, unknown operation denial and table exhaustion.
