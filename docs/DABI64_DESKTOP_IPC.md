# DuckOS DABI64 Desktop IPC foundation

**Status:** C11 endpoint queue and shared Reaper wire validator/catalogue are implemented and host-tested. Syscall delivery, scheduler identity, endpoint registry, kernel locking/wakeups and desktop services are not yet connected.

## Shared ABI source

DuckOS consumes DABI64 Desktop Host v1 from the pinned Reaper specialist submodule at projects/reaper. CMake compiles the Reaper system operation catalogue and DABI64 validators into the DuckOS desktop IPC foundation target. This prevents a second local copy of the request/response layout and operation identifiers.

The upstream ABI contract is tracked in Reaper PR #331. This DuckOS PR is dependent on that PR and must not merge ahead of it.

## Endpoint model

A desktop IPC endpoint connects exactly two kernel principals: an owner and a peer. A principal is a task identifier plus a generation value, so a recycled task ID cannot silently inherit a previous endpoint identity.

Each endpoint owns two independent bounded queues:
- owner-to-peer requests and events;
- peer-to-owner requests and events.

All storage slots are supplied by trusted kernel/service code. A user process never supplies queue pointers or storage addresses. Each slot stores exact DABI64 frame bytes plus sender/receiver identity, sequence, request ID and operation metadata.

## Admission rules

The C11 endpoint primitive:
1. Requires non-zero endpoint identity and distinct owner/peer task-generation pairs.
2. Rejects null, undersized, oversized or overlapping slot buffers.
3. Accepts desktop operation IDs only and validates DABI64 v1 request headers through the Reaper library.
4. Requires sequence numbers to increase exactly by one per sender; rejected/full sends do not consume sequence numbers.
5. Copies complete frames into kernel/service-owned slots and derives recipients from endpoint membership.
6. Returns backpressure when a queue is full and preserves queued messages when a receiver's buffer is too small.
7. Delivers only to the endpoint's recorded receiver principal and reports sender metadata.
8. Allows only the owner principal to close an endpoint; close clears queued frame bytes.

The endpoint primitive does not itself check operation capabilities. The kernel capability broker must run before a service executes an accepted operation.

## Concurrency and syscall boundary

Endpoint operations are not internally lock-free or self-synchronizing. The owning kernel service must serialize access with its lock and must not call these functions from competing CPUs or interrupt contexts without that protection.

The current API takes a principal record because no scheduler-owned task object is available yet. This record is intended for internal kernel callers only. A future syscall adapter must resolve identity from the current task structure and must never copy PID, generation or capability claims from user memory into the principal.

The current Stage 1 boot path has no user address spaces, ring-3 entry, syscall handler, task scheduler or blocking IPC wakeups. The endpoint queue is a tested foundation component, not a user-visible IPC service.

## Tests

The native CTest target duckos-dabi64-ipc-foundation verifies endpoint storage, principal generation and peer checks, DABI64 frame validation, desktop-operation allowlisting, bidirectional delivery, sequence replay rejection, full/empty backpressure, non-destructive small-buffer receive, owner-only close and clearing of consumed frame bytes.
