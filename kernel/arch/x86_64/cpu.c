#include "cpu.h"

#include <stddef.h>

static void zero_bytes(void *memory, size_t size) {
    unsigned char *bytes = (unsigned char *)memory;
    for (size_t i = 0U; i < size; ++i) bytes[i] = 0U;
}

#if defined(_MSC_VER) && (defined(_M_X64) || defined(_M_IX86))
#include <intrin.h>
static void cpuid_query(uint32_t leaf, uint32_t subleaf,
                        uint32_t *a, uint32_t *b,
                        uint32_t *c, uint32_t *d) {
    int registers[4] = {0, 0, 0, 0};
    __cpuidex(registers, (int)leaf, (int)subleaf);
    *a = (uint32_t)registers[0];
    *b = (uint32_t)registers[1];
    *c = (uint32_t)registers[2];
    *d = (uint32_t)registers[3];
}
static uint64_t xgetbv_zero(void) {
    return (uint64_t)_xgetbv(0);
}
#elif defined(__x86_64__) || defined(__i386__)
static void cpuid_query(uint32_t leaf, uint32_t subleaf,
                        uint32_t *a, uint32_t *b,
                        uint32_t *c, uint32_t *d) {
    __asm__ volatile ("cpuid"
        : "=a"(*a), "=b"(*b), "=c"(*c), "=d"(*d)
        : "a"(leaf), "c"(subleaf));
}
static uint64_t xgetbv_zero(void) {
    uint32_t low;
    uint32_t high;
    __asm__ volatile ("xgetbv" : "=a"(low), "=d"(high) : "c"(0U));
    return ((uint64_t)high << 32) | (uint64_t)low;
}
#else
int duckos_x86_64_cpu_probe(duckos_x86_64_cpu_info *out) {
    if (out == NULL) return 0;
    unsigned char *bytes = (unsigned char *)out;
    for (size_t i = 0U; i < sizeof(*out); ++i) bytes[i] = 0U;
    return 0;
}
#endif

#if defined(_MSC_VER) && (defined(_M_X64) || defined(_M_IX86))
#define DUCKOS_X86_CPUID_AVAILABLE 1
#elif defined(__x86_64__) || defined(__i386__)
#define DUCKOS_X86_CPUID_AVAILABLE 1
#endif

#if defined(DUCKOS_X86_CPUID_AVAILABLE)
static uint32_t max_value(uint32_t left, uint32_t right) {
    return left > right ? left : right;
}

int duckos_x86_64_cpu_probe(duckos_x86_64_cpu_info *out) {
    if (out == NULL) return 0;
    zero_bytes(out, sizeof(*out));

    uint32_t a = 0U, b = 0U, c = 0U, d = 0U;
    cpuid_query(0U, 0U, &a, &b, &c, &d);
    out->max_basic_leaf = a;
    for (uint32_t i = 0U; i < 4U; ++i) {
        out->vendor[i] = (char)((b >> (i * 8U)) & 0xffU);
        out->vendor[4U + i] = (char)((d >> (i * 8U)) & 0xffU);
        out->vendor[8U + i] = (char)((c >> (i * 8U)) & 0xffU);
    }
    out->vendor[12] = '\0';

    cpuid_query(UINT32_C(0x80000000), 0U, &a, &b, &c, &d);
    out->max_extended_leaf = a;

    if (out->max_basic_leaf >= 1U) {
        cpuid_query(1U, 0U, &a, &b, &c, &d);
        out->signature = a;
        out->stepping = a & 0x0fU;
        const uint32_t base_model = (a >> 4) & 0x0fU;
        const uint32_t base_family = (a >> 8) & 0x0fU;
        const uint32_t extended_model = (a >> 16) & 0x0fU;
        const uint32_t extended_family = (a >> 20) & 0xffU;
        out->family = base_family == 0x0fU
            ? base_family + extended_family : base_family;
        out->model = (base_family == 0x06U || base_family == 0x0fU)
            ? base_model | (extended_model << 4) : base_model;
        out->initial_apic_id = (b >> 24) & 0xffU;
        out->logical_processors_per_package = (b >> 16) & 0xffU;
        if (out->logical_processors_per_package == 0U)
            out->logical_processors_per_package = 1U;

        if ((d & (UINT32_C(1) << 26)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_SSE2;
        if ((c & (UINT32_C(1) << 20)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_SSE42;
        if ((c & (UINT32_C(1) << 25)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_AES;
        if ((c & (UINT32_C(1) << 26)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_XSAVE;
        if ((c & (UINT32_C(1) << 27)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_OSXSAVE;
        if ((c & (UINT32_C(1) << 28)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_AVX;
        if ((c & (UINT32_C(1) << 12)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_FMA;
        if ((c & (UINT32_C(1) << 5)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_VMX;
        if ((c & (UINT32_C(1) << 31)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_HYPERVISOR;
    }

    if (out->max_basic_leaf >= 7U) {
        cpuid_query(7U, 0U, &a, &b, &c, &d);
        if ((b & (UINT32_C(1) << 5)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_AVX2;
        if ((b & (UINT32_C(1) << 16)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_AVX512F;
    }

    if ((out->features & DUCKOS_CPU_FEATURE_OSXSAVE) != 0U) {
        out->xcr0 = xgetbv_zero();
        const uint64_t avx_state = UINT64_C(0x06);
        const uint64_t avx512_state = UINT64_C(0xe6);
        if ((out->xcr0 & avx_state) != avx_state)
            out->features &= ~(DUCKOS_CPU_FEATURE_AVX |
                               DUCKOS_CPU_FEATURE_AVX2 |
                               DUCKOS_CPU_FEATURE_AVX512F |
                               DUCKOS_CPU_FEATURE_FMA);
        else if ((out->xcr0 & avx512_state) != avx512_state)
            out->features &= ~DUCKOS_CPU_FEATURE_AVX512F;
    } else {
        out->features &= ~(DUCKOS_CPU_FEATURE_AVX |
                           DUCKOS_CPU_FEATURE_AVX2 |
                           DUCKOS_CPU_FEATURE_AVX512F |
                           DUCKOS_CPU_FEATURE_FMA);
    }

    if (out->max_basic_leaf >= UINT32_C(0x1f) ||
        out->max_basic_leaf >= UINT32_C(0x0b)) {
        const uint32_t topology_leaf =
            out->max_basic_leaf >= UINT32_C(0x1f) ? UINT32_C(0x1f) : UINT32_C(0x0b);
        uint32_t smt_count = 0U;
        uint32_t package_logical_count = 0U;
        for (uint32_t subleaf = 0U; subleaf < 8U; ++subleaf) {
            cpuid_query(topology_leaf, subleaf, &a, &b, &c, &d);
            const uint32_t level_type = (c >> 8) & 0xffU;
            const uint32_t level_count = b & 0xffffU;
            if (level_type == 0U || level_count == 0U) break;
            if (level_type == 1U) smt_count = level_count;
            if (level_type == 2U) package_logical_count = level_count;
            out->initial_apic_id = d;
        }
        if (package_logical_count != 0U)
            out->logical_processors_per_package = package_logical_count;
        if (smt_count == 0U) smt_count = 1U;
        out->smt_threads_per_core = smt_count;
    }

    if (out->max_basic_leaf >= 4U) {
        cpuid_query(4U, 0U, &a, &b, &c, &d);
        const uint32_t cores = ((a >> 26) & 0x3fU) + 1U;
        if (cores != 0U) out->physical_cores_per_package = cores;
    }
    if (out->max_extended_leaf >= UINT32_C(0x80000008)) {
        cpuid_query(UINT32_C(0x80000008), 0U, &a, &b, &c, &d);
        const uint32_t amd_cores = (c & 0xffU) + 1U;
        out->physical_cores_per_package =
            max_value(out->physical_cores_per_package, amd_cores);
    }
    if (out->physical_cores_per_package == 0U)
        out->physical_cores_per_package = 1U;
    if (out->smt_threads_per_core == 0U) {
        const uint32_t logical = out->logical_processors_per_package;
        const uint32_t cores = out->physical_cores_per_package;
        out->smt_threads_per_core = logical >= cores ? logical / cores : 1U;
    }

    if (out->max_extended_leaf >= UINT32_C(0x80000001)) {
        cpuid_query(UINT32_C(0x80000001), 0U, &a, &b, &c, &d);
        if ((c & (UINT32_C(1) << 2)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_SVM;
    }
    if (out->max_extended_leaf >= UINT32_C(0x80000007)) {
        cpuid_query(UINT32_C(0x80000007), 0U, &a, &b, &c, &d);
        if ((d & (UINT32_C(1) << 8)) != 0U)
            out->features |= DUCKOS_CPU_FEATURE_INVARIANT_TSC;
    }

    return 1;
}
#endif
