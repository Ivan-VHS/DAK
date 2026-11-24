#ifndef DUCKOS_KERNEL_SECURITY_API_H
#define DUCKOS_KERNEL_SECURITY_API_H

#include "security.h"

/*
 * Internal kernel-only interface. Do not expose this entry point via a
 * userspace syscall until the kernel has caller authentication/capabilities.
 * Early boot is single-writer; SMP callers must add a kernel lock.
 */
void duckos_kernel_security_init(void);
duckos_security_status duckos_kernel_security_submit(
    const duckos_security_event_v1 *event,
    duckos_security_evaluation_v1 *evaluation
);

#endif
