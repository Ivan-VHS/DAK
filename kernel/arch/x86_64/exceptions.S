.section .text
.extern dak_x86_exception_dispatch

.macro DAK_ISR_NO_ERROR number
    .global dak_x86_isr_\number
    .type dak_x86_isr_\number, @function
dak_x86_isr_\number:
    pushq $0
    pushq $\number
    jmp dak_x86_exception_common
.endm

.macro DAK_ISR_ERROR number
    .global dak_x86_isr_\number
    .type dak_x86_isr_\number, @function
dak_x86_isr_\number:
    pushq $\number
    jmp dak_x86_exception_common
.endm

# CPU-supplied error-code vectors: 8, 10-14, 17, 21, 29 and 30.
DAK_ISR_NO_ERROR 0
DAK_ISR_NO_ERROR 1
DAK_ISR_NO_ERROR 2
DAK_ISR_NO_ERROR 3
DAK_ISR_NO_ERROR 4
DAK_ISR_NO_ERROR 5
DAK_ISR_NO_ERROR 6
DAK_ISR_NO_ERROR 7
DAK_ISR_ERROR    8
DAK_ISR_NO_ERROR 9
DAK_ISR_ERROR    10
DAK_ISR_ERROR    11
DAK_ISR_ERROR    12
DAK_ISR_ERROR    13
DAK_ISR_ERROR    14
DAK_ISR_NO_ERROR 15
DAK_ISR_NO_ERROR 16
DAK_ISR_ERROR    17
DAK_ISR_NO_ERROR 18
DAK_ISR_NO_ERROR 19
DAK_ISR_NO_ERROR 20
DAK_ISR_ERROR    21
DAK_ISR_NO_ERROR 22
DAK_ISR_NO_ERROR 23
DAK_ISR_NO_ERROR 24
DAK_ISR_NO_ERROR 25
DAK_ISR_NO_ERROR 26
DAK_ISR_NO_ERROR 27
DAK_ISR_NO_ERROR 28
DAK_ISR_ERROR    29
DAK_ISR_ERROR    30
DAK_ISR_NO_ERROR 31

.type dak_x86_exception_common, @function
dak_x86_exception_common:
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
    call dak_x86_exception_dispatch

1:
    cli
    hlt
    jmp 1b

.section .note.GNU-stack,"",@progbits
