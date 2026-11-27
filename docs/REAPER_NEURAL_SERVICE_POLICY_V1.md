# DuckOS Reaper Neural Service Admission Policy v1

**Canonical neural model contract:** Reaper, reaper.neural-network.v1  
**DuckOS adapter:** duckos/ai/neural_service.rpr  
**Status:** executable user-space admission policy model

## Request envelope

The ten-field Reaper list has this fixed order:

1. dak.neural-service-request.v1;
2. caller-selected request identity;
3. model schema, currently reaper.neural-network.v1;
4. workload mode: inference or offline_batch;
5. target: user_cpu only;
6. input vector width;
7. output vector width;
8. model memory reservation in bytes;
9. caller-declared operation-step budget;
10. explicit effect list.

## Admission rules

| Property | Limit |
|---|---:|
| Input / output width | 1–512 |
| Model reservation | 1–16 MiB |
| Step budget | 1–65,536 |
| Workload mode | inference or offline_batch |
| Execution target | user_cpu |
| Permitted effect | compute only |

The policy returns ALLOW or DENY with the accepted byte and step budgets. Unknown schemas, malformed dimensions, oversized requests, kernel targets and effects other than compute are denied.

## Security and maturity boundary

This module validates a request descriptor only. It does not allocate the requested memory, spawn a process, schedule work, grant capabilities, execute model inference, or enforce kernel-level CPU and memory quotas. A production scheduler must consume this contract through an independently implemented and tested user-space service boundary.

The adapter deliberately denies network, filesystem, MMIO, DMA, IRQ and kernel effects. It does not add drivers or firmware access.

## Verification

The Reaper contract workflow runs this file and requires the marker DAK_REAPER_NEURAL_SERVICE:PASS. The fixture covers accepted inference and offline-batch requests, plus denied kernel, network, oversized-memory and excessive-step requests.
