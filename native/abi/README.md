# Driver ABI v1

The public C header is include/duckos/driver.h. It establishes fixed-width fields, explicit structure sizes, major/minor negotiation, capability flags and stable numeric status values.

## Compatibility rules

1. A driver declares the ABI major it was built against. A major mismatch is a hard rejection.
2. A minor version may add fields only to the end of a structure. Consumers must check struct_size before reading optional fields.
3. Reserved fields must be zero. Unknown capability bits and operation codes must be ignored or rejected safely.
4. Kernel addresses are never accepted from untrusted user space as raw pointers. buffer_token is an opaque handle that a future kernel implementation must validate against the calling process.
5. Driver callbacks run in kernel context and must not block indefinitely. Cancellation, DMA mapping, IRQ delivery, IOMMU policy and hot-unplug semantics require separate reviewed specifications.

## Honest implementation status

This is the ABI header and compatibility contract only. The current bring-up kernel has no ELF module loader, symbol resolver, device model, syscall table, interrupt subsystem, DMA API or driver manager. No third-party kernel module can be loaded yet. OPlague remains a read-only host/device inventory project until those kernel facilities exist.
