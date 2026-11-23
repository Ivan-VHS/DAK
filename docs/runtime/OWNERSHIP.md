# DuckOS runtime values and ownership

## Scope

The first runtime slice builds on the existing 16-byte \`DuckValue\` representation.
It adds C17 operations for scalar tags, owned UTF-8 byte strings, dynamic arrays,
and array iterators. It is a host-buildable runtime library, not a kernel service
or a process-wide heap.

The public value layout remains unchanged:

| Field | Width | Meaning |
| --- | ---: | --- |
| \`payload\` | 8 bytes | Scalar bits or a runtime object pointer |
| \`kind\` | 4 bytes | Value tag |
| \`flags\` | 4 bytes | Reserved; must be zero in this runtime slice |

## Value tags

| Tag | Name | Payload |
| ---: | --- | --- |
| 0 | \`DUCK_VALUE_UNIT\` | zero |
| 1 | \`DUCK_VALUE_I64\` | signed integer bits |
| 2 | \`DUCK_VALUE_BOOL\` | zero or one |
| 3 | \`DUCK_VALUE_STRING\` | pointer to a managed string |
| 4 | \`DUCK_VALUE_ARRAY\` | pointer to a managed dynamic array |
| 5 | \`DUCK_VALUE_ITERATOR\` | pointer to an array iterator |

The DABI64 frame layout, register contract, and 16-byte value layout do not
change. The existing scalar compiler entry path and
\`duck_dabi64_validate_i64_arguments\` remain intentionally restricted to
\`i64\`; adding runtime tags does not imply that the Reaper native backend can
yet lower string or collection expressions.

## Ownership rules

Every heap-backed \`DuckValue\` is a strong reference. \`duck_value_clone\`
retains the referenced object; \`duck_value_move\` transfers a reference and
resets its source to \`unit\`; \`duck_value_drop\` releases a reference and
resets the slot. Scalar values are copied without allocation.

Objects use atomic reference counts. The allocator is supplied by the embedding
kernel or host and is copied into each object header. The allocator context must
outlive every object allocated through it. Allocations must satisfy normal C
object alignment.

Strings own an exact byte sequence and append a trailing NUL for C interop.
Their length is measured in bytes, not Unicode code points. The constructor does
not normalize or validate UTF-8; callers that expose text to user interfaces or
filesystems must validate the encoding at that boundary.

Arrays own cloned values. \`array_get\` returns a new strong reference.
Appending an iterator is rejected in this initial slice. Nested arrays are
allowed, but indirect cycles are rejected before insertion so reference
counting can reclaim all objects deterministically. The graph walk is bounded
by \`DUCK_RUNTIME_MAX_ARRAY_GRAPH\`; a larger graph is rejected rather than
traversed without a bound.

Iterators retain their source array and use a live view: appends made before the
next read may be observed. The source array must remain valid, which is ensured
by the iterator's retained reference. Mutation is single-writer; reference
count operations are atomic, but array mutation itself is not a concurrent
container API.

## Error and failure behaviour

Runtime operations return \`DuckRuntimeStatus\`. On allocation failure, an array
keeps its previous contents and length. Out-of-range reads do not modify the
array. A failed clone does not replace the destination. Forged pointers cannot
be made memory-safe by tag checks alone; callers must pass values produced by
this runtime or validated at a trusted ABI boundary.

The allocator is deliberately injected. The host tests use \`malloc\`/\`free\`;
DuckOS can later bind the same API to its kernel heap without changing value
semantics.

## Not implemented here

This slice does not provide cycle collection, maps, slices, byte buffers,
string builders, Unicode normalization, file or console I/O, a scheduler,
syscalls, ELF loading, or process startup. It does not yet connect the Reaper
\`each\` syntax or string/collection expressions to DABI64 machine-code
emission. Those are separate integration steps.
