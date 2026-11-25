.section .text
.extern duckos_x86_exception_dispatch

.macro DUCKOS_ISR_NO_ERROR number
    .global duckos_x86_isr_\number
    .type duckos_x86_isr_\number, @function
duckos_x86_isr_\number:
    pushq $0
    pushq $\number
    jmp duckos_x86_exception_common
.endm

.macro DUCKOS_ISR_ERROR number
    .global duckos_x86_isr_\number
    .type duckos_x86_isr_\number, @function
duckos_x86_isr_\number:
    pushq $\number
    jmp duckos_x86_exception_common
.endm

# CPU-supplied error-code vectors: 8, 10-14, 17, 21, 29 and 30.\nDUCKOS_ISR_NO_ERROR 0
DUCKOS_ISR_NO_ERROR 1
DUCKOS_ISR_NO_ERROR 2
DUCKOS_ISR_NO_ERROR 3
DUCKOS_ISR_NO_ERROR 4
DUCKOS_ISR_NO_ERROR 5
DUCKOS_ISR_NO_ERROR 6
DUCKOS_ISR_NO_ERROR 7
DUCKOS_ISR_ERROR    8
DUCKOS_ISR_NO_ERROR 9
DUCKOS_ISR_ERROR    10
DUCKOS_ISR_ERROR    11
DUCKOS_ISR_ERROR    12
DUCKOS_ISR_ERROR    13
DUCKOS_ISR_ERROR    14
DUCKOS_ISR_NO_ERROR 15
DUCKOS_ISR_NO_ERROR 16
DUCKOS_ISR_ERROR    17
DUCKOS_ISR_NO_ERROR 18
DUCKOS_ISR_NO_ERROR 19
DUCKOS_ISR_NO_ERROR 20
DUCKOS_ISR_ERROR    21
DUCKOS_ISR_NO_ERROR 22
DUCKOS_ISR_NO_ERROR 23
DUCKOS_ISR_NO_ERROR 24
DUCKOS_ISR_NO_ERROR 25
DUCKOS_ISR_NO_ERROR 26
DUCKOS_ISR_NO_ERROR 27
DUCKOS_ISR_NO_ERROR 28
DUCKOS_ISR_ERROR    29
DUCKOS_ISR_ERROR    30
DUCKOS_ISR_NO_ERROR 31

.type duckos_x86_exception_common, @function
duckos_x86_exception_common:
    cld
    pushq %rax
    pushq %rbx
    pushq %rcx
    pushq %rdx
    pushq %rbp
    pushq %rsi
    pushq %rdi
    pushq %r8
    pushq %r9
    pushq %r10
    pushq %r11
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15

    movq %rsp, %rdi
    andq $-16, %rsp
    call duckos_x86_exception_dispatch

1:
    cli
    hlt
    jmp 1b

.section .note.GNU-stack,"",@progbits
