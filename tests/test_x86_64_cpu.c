#include "cpu.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    duckos_x86_64_cpu_info info;
    assert(duckos_x86_64_cpu_probe(&info));
    assert(info.vendor[0] != '\0');
    assert(info.max_basic_leaf >= 1U);
    assert(info.logical_processors_per_package >= 1U);
    assert(info.physical_cores_per_package >= 1U);
    assert(info.smt_threads_per_core >= 1U);
    printf("x86_64 CPU probe: %.12s family=%u model=%u stepping=%u logical=%u cores=%u features=0x%x\n",
           info.vendor, info.family, info.model, info.stepping,
           info.logical_processors_per_package,
           info.physical_cores_per_package, info.features);
    return 0;
}
