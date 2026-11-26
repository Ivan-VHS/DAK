# Reaper-VHS GPU subsystem v1

**Status:** Reaper-language contracts and regression tests added. Native PCI enumeration, GPU page tables, DMA/IOMMU operations, compression, migration, device control and dashboard UI are not delivered by these contracts.

## Purpose

Reaper-VHS defines one versioned policy boundary for GPU discovery, memory ownership, device isolation, resource residency, compression metadata, oversubscription, thermal policy, recovery and diagnostics. The implementation is written in `.rpr` and included in the DuckOS core Reaper contract suite.

The code does not contain a Python implementation. The current repository's broad Reaper execution path remains its reference runtime; the Reaper native C17 compiler is a partial subset and cannot yet compile this subsystem to freestanding machine code. Passing these checks proves the Reaper policy logic, not hardware operation.

## R0–R10 delivery

| Stage | Reaper module contract | Delivered in this change | Still required for native hardware |
|---|---|---|---|
| R0 | Versioned GPU ABI | ABI v1.0 gate and stable descriptor shapes | Freeze generated headers, ABI compatibility tests and native compiler support |
| R1 | PCI/PCIe discovery | PCI location/device validation, display-class check, vendor classification and BAR descriptor validation | PCI config-space enumeration, BAR sizing/reservation, ACPI routing and tested Intel/AMD/NVIDIA driver adapters |
| R2 | Physical/virtual memory | GPU address range, page alignment, permissions, backing tier and VRAM budget checks | Physical allocator integration, GPU page tables, TLB invalidation, VRAM object allocator and reclaim |
| R3 | DMA + IOMMU | DMA descriptor, direction, alignment, lifecycle and isolated-domain admission contracts | IOMMU page tables, DMA mapping/unmapping, cache maintenance, invalidation and device teardown |
| R4 | GPU context + GPUVM | Context ownership, domain matching, capabilities and mapping admission | GPU command queues, hardware contexts, GPUVM page-table management and fences |
| R5 | VRAM residency | Buffer descriptor, pinning, migration preconditions and deterministic residency decisions | Actual VRAM/system-RAM copies, eviction worker, synchronization and device-specific migration |
| R6 | VHS-Codec | Versioned block metadata, raw/compressed selection, output caps and integrity-result admission | Real LZ4/Zstd/zero/constant codec implementation, checksum engine and GPU texture path |
| R7 | HyperSwap | Fault/oversubscription admission, backing/queue checks and explicit-staging fallback | Hardware fault-and-replay qualification, page-fault handler, transfer queues and working-set controller |
| R8 | Telemetry + Power Governor | Bounded telemetry, qualified-clock ceiling, thermal actions and stable-profile fallback decisions | Sensor collection, vendor power APIs, signed limits, watchdog and measured hardware qualification |
| R9 | Security Guard | Owner/domain/capability checks, same-domain immutable dedup policy and recovery decisions | Kernel-enforced isolation, IOMMU/GPUVM enforcement, secure reset and audit integration |
| R10 | Dashboard | Snapshot validation, alert classification and physical VRAM residency metric | Native DuckOS dashboard, live sensor source, time-series store and accessibility-tested UI |

## ABI data shapes

All fields are positional arrays in v1.0 so the existing Reaper parser can validate them without relying on unsupported struct/native-compiler features. Integers are byte counts unless the name specifies another unit.

- PCI device: `[segment, bus, slot, function, vendor_id, device_id, class_code, bar_count]`.
- BAR: `[index, base, size, kind, prefetchable]`.
- GPU page: `[gpu_virtual, backing_physical, bytes, permissions, owner_context, pinned, tier]`.
- DMA map: `[iova, physical, bytes, direction, domain_id, alignment, state]`.
- GPU context: `[context_id, owner_pid, iommu_domain, vram_limit, queue_limit, state, grants]`.
- GPUVM map: `[context_id, domain_id, gpu_virtual, object_id, bytes, permissions, owner_pid]`.
- Buffer: `[object_id, context_id, bytes, tier, pin_count, priority, access]`.
- VHS-Codec block: `[codec, original_bytes, encoded_bytes, checksum_u32, format_version, block_bytes]`.
- Telemetry: `[temperature_mC, power_mW, clock_MHz, utilization_basis_points, resident_vram_bytes, total_vram_bytes, error_count, monotonic_timestamp]`.
- Dashboard: `[vram_total, vram_resident, host_backing, compressed_backing, temperature_mC, clock_MHz, utilization_basis_points, faults, pending_migrations, power_mW]`.

The exact accepted values and status strings are defined in `duckos/graphics/reaper_vhs.rpr`; tests are in `core_mvp_tests.rpr`.

## Safety rules

1. A PCI device classified as a GPU is not assumed to have a working driver.
2. GPU virtual address space, resident VRAM, host backing and compressed storage are separate measurements. They must never be summed and labelled physical VRAM.
3. DMA requires a validated descriptor, an isolated IOMMU domain and an explicit capability. The current contract does not call an IOMMU.
4. GPU contexts are bound to an owner and domain. Cross-context or cross-domain mappings fail closed.
5. Pinned buffers cannot be evicted or migrated by the policy.
6. Compression is admitted only when output bounds, codec version and checksum metadata are valid. The contract does not compress bytes.
7. Transparent oversubscription requires an explicitly supported fault-and-replay capability and sufficient host backing. Otherwise the caller must stage resources explicitly.
8. Frequency requests stay within a qualified stable ceiling. This v1 contract never requests a voltage increase.
9. Device reset is only a policy request after contexts have quiesced and reset support is declared.
10. Any missing telemetry or invalid descriptor is an error/unknown state, not a healthy reading.

## Verification

The R0–R10 assertions are appended to `core_mvp_tests.rpr`. Existing DuckOS CI statically checks every `.rpr` module and executes the complete core contract suite through both Reaper tree-walk and VM engines.

A hardware stage can be marked delivered only after the corresponding native kernel/driver source, negative tests, emulator or hardware-in-the-loop evidence and supported-device matrix are present.
