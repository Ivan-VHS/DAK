#ifndef DUCKOS_X86_64_CPU_H
#define DUCKOS_X86_64_CPU_H

#include <stdint.h>

enum {
    DUCKOS_CPU_FEATURE_SSE2 = UINT32_C(1) << 0,
    DUCKOS_CPU_FEATURE_SSE42 = UINT32_C(1) << 1,
    DUCKOS_CPU_FEATURE_AES = UINT32_C(1) << 2,
    DUCKOS_CPU_FEATURE_AVX = UINT32_C(1) << 3,
    DUCKOS_CPU_FEATURE_AVX2 = UINT32_C(1) << 4,
    DUCKOS_CPU_FEATURE_AVX512F = UINT32_C(1) << 5,
    DUCKOS_CPU_FEATURE_FMA = UINT32_C(1) << 6,
    DUCKOS_CPU_FEATURE_XSAVE = UINT32_C(1) << 7,
    DUCKOS_CPU_FEATURE_OSXSAVE = UINT32_C(1) << 8,
    DUCKOS_CPU_FEATURE_INVARIANT_TSC = UINT32_C(1) << 9,
    DUCKOS_CPU_FEATURE_VMX = UINT32_C(1) << 10,
    DUCKOS_CPU_FEATURE_SVM = UINT32_C(1) << 11,
    DUCKOS_CPU_FEATURE_HYPERVISOR = UINT32_C(1) << 12
};

typedef struct {
    char vendor[13];
    uint32_t signature;
    uint32_t family;
    uint32_t model;
    uint32_t stepping;
    uint32_t initial_apic_id;
    uint32_t logical_processors_per_package;
    uint32_t physical_cores_per_package;
    uint32_t smt_threads_per_core;
    uint32_t max_basic_leaf;
    uint32_t max_extended_leaf;
    uint64_t xcr0;
    uint32_t features;
} duckos_x86_64_cpu_info;

int duckos_x86_64_cpu_probe(duckos_x86_64_cpu_info *out);

#endif
