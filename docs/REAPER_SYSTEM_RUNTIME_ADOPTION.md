# Reaper System Runtime ABI adoption contract

**Consumer:** DAKOS  
**Provider:** Reaper System Runtime ABI v1  
**Status:** integration contract; no privileged adapter is claimed by this document.

## Purpose

DAKOS is the intended first OS provider for Reaper's process, thread, synchronization, filesystem, clock, networking and cryptographic host operations. The adapter belongs on the DAKOS side of the existing process and trust boundary. Reaper must not bypass the host policy broker with raw syscalls.

The native Reaper ABI is defined in include/reaper/system.h and implemented as the reaper_system library. It contributes 42 versioned operation IDs across seven domains. The adapter must match ABI version 1 and use only the capabilities explicitly granted by DAKOS.

## Provider architecture

The target call path is:

~~~text
DAKOS application / Reaper task
          |
          v
Reaper typed operation + required effect
          |
          v
ReaperSystemHost (ABI v1)
          |
          v
DAKOS ReaperSystemDispatch adapter
          |
          v
DAKOS capability broker / service boundary
          |
          v
reviewed kernel or user-space service implementation
~~~

The actual provider should be split into small domain adapters rather than one unrestricted dispatcher. Each adapter receives only the subsystem interfaces it needs. The system ABI is not itself a kernel syscall table.

## Capability mapping

| Reaper operation domain | DAKOS-owned service |
|---|---|
| Process | Process broker, executable manifest validation and child lifecycle |
| Thread | Scheduler-facing task/thread service and bounded join semantics |
| Synchronization | Kernel or runtime mutex, semaphore and event primitives |
| Filesystem | VFS handles rooted in an approved mount or directory capability |
| Clock/timers | Monotonic clock, timer queue and deadline service |
| Networking | Network service with endpoint policy and bounded socket handles |
| Cryptography | Trusted OS crypto/entropy provider; no insecure fallback |

## Default-deny policy

- Process inspection may be granted to a task only for its own identity and explicitly authorized children.
- Process spawn/signal/exit are not implicitly granted. Spawn consumes structured argv/environment data and a validated executable capability; it never invokes a shell.
- Thread creation and priority changes are scoped to the calling task and scheduler policy.
- Synchronization objects are task-owned unless a separate sharing capability is designed and reviewed.
- Filesystem access is handle-based and rooted. Reject parent traversal, symlink escape, stale handles and operations outside the granted mount.
- Network access is disabled unless a manifest and policy broker grant it. Enforce address/port policy, deadlines and message-size limits.
- Entropy must come from the platform's cryptographically secure source. Failure is fatal to the requesting operation; never fall back to a time-seeded PRNG.
- Device, MMIO, DMA, IRQ, port-I/O, firmware and driver-installation permissions are outside System Runtime ABI v1. They remain separate reviewed driver capabilities.

## Platform priority and compatibility

The primary development, build and qualification target is x86-64 on modern Intel and AMD processors. Keep architecture-neutral operation IDs and host contracts. Preserve the Elbrus architecture abstraction and a separately tested backend; do not remove its target metadata or compatibility path as part of the x86-64 priority.

## Integration gates

1. Pin the Reaper ABI version and operation catalogue in DAKOS's dependency/federation record.
2. Implement a no-op or fake provider first; test each operation's required capability before dispatch.
3. Add host-specific payload schemas with explicit sizes, version fields, endianness and handle kinds. Never infer payload layout from a name.
4. Implement real provider operations only where the corresponding DAKOS subsystem exists and has its own tests.
5. Add deny-by-default tests for missing grants, forged/stale handles, invalid lengths, path traversal, shell metacharacters, out-of-scope process IDs and denied network endpoints.
6. Keep the existing Reaper source-check bridge separate. A user-space static check or Studio launch does not mean the kernel adapter is installed.
7. Mark each service implemented, adapter-dependent, experimental or planned using source and test evidence.

## Acceptance

DAKOS may claim an operation is available only when:
- a concrete provider function exists;
- policy and handle validation execute before side effects;
- fake-host tests and target integration tests cover success and denial;
- cancellation/deadline and error mapping are defined;
- the feature is built and tested for its declared target.

Until those gates pass, this file is a forward-compatible integration contract only.