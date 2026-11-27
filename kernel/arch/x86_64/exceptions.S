.section .text
.extern dakos_x86_exception_dispatch

.macro DAKOS_ISR_NO_ERROR number
    .global dakos_x86_isr_\number
    .type dakos_x86_isr_\number, @function
dakos_x86_isr_\number:
    pushq $0
    pushq $\number
    jmp dakos_x86_exception_common
.endm

.macro DAKOS_ISR_ERROR number
    .global dakos_x86_isr_\number
    .type dakos_x86_isr_\number, @function
dakos_x86_isr_\number:
    pushq $\number
    jmp dakos_x86_exception_common
.endm

# CPU-supplied error-code vectors: 8, 10-14, 17, 21, 29 and 30.
DAKOS_ISR_NO_ERROR 0
DAKOS_ISR_NO_ERROR 1
DAKOS_ISR_NO_ERROR 2
DAKOS_ISR_NO_ERROR 3
DAKOS_ISR_NO_ERROR 4
DAKOS_ISR_NO_ERROR 5
DAKOS_ISR_NO_ERROR 6
DAKOS_ISR_NO_ERROR 7
DAKOS_ISR_ERROR    8
DAKOS_ISR_NO_ERROR 9
DAKOS_ISR_ERROR    10
DAKOS_ISR_ERROR    11
DAKOS_ISR_ERROR    12
DAKOS_ISR_ERROR    13
DAKOS_ISR_ERROR    14
DAKOS_ISR_NO_ERROR 15
DAKOS_ISR_NO_ERROR 16
DAKOS_ISR_ERROR    17
DAKOS_ISR_NO_ERROR 18
DAKOS_ISR_NO_ERROR 19
DAKOS_ISR_NO_ERROR 20
DAKOS_ISR_ERROR    21
DAKOS_ISR_NO_ERROR 22
DAKOS_ISR_NO_ERROR 23
DAKOS_ISR_NO_ERROR 24
DAKOS_ISR_NO_ERROR 25
DAKOS_ISR_NO_ERROR 26
DAKOS_ISR_NO_ERROR 27
DAKOS_ISR_NO_ERROR 28
DAKOS_ISR_ERROR    29
DAKOS_ISR_ERROR    30
DAKOS_ISR_NO_ERROR 31

.type dakos_x86_exception_common, @function
dakos_x86_exception_common:
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
    call dakos_x86_exception_dispatch

1:
    cli
    hlt
    jmp 1b

.section .note.GNU-stack,"",@progbits
