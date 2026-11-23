#include "duckos/kernel.h"
#include "duckos/syscall.h"

void duckos_int80_handle_frame(DuckOsInt80Frame *frame) {
    if (frame == NULL) return;
    frame->rax = (uint64_t)duckos_syscall_dispatch(
        frame->rax,
        frame->rdi,
        frame->rsi,
        frame->rdx,
        frame->r10,
        frame->r8,
        frame->r9
    );
}
