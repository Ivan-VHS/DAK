.section .text
.code64
.global duckos_int80_entry
.type duckos_int80_entry,@function
.extern duckos_int80_handle_frame
duckos_int80_entry:
    cld
    pushq %rax
    pushq %rbx
    pushq %rcx
    pushq %rdx
    pushq %rsi
    pushq %rdi
    pushq %rbp
    pushq %r8
    pushq %r9
    pushq %r10
    pushq %r11
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15

    movq %rsp, %rdi
    movq %rsp, %r12
    andq $-16, %rsp
    call duckos_int80_handle_frame
    movq %r12, %rsp

    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %r11
    popq %r10
    popq %r9
    popq %r8
    popq %rbp
    popq %rdi
    popq %rsi
    popq %rdx
    popq %rcx
    popq %rbx
    popq %rax
    iretq
.size duckos_int80_entry, .-duckos_int80_entry

.global duckos_int80_unhandled
.type duckos_int80_unhandled,@function
duckos_int80_unhandled:
    cli
1:
    hlt
    jmp 1b
.size duckos_int80_unhandled, .-duckos_int80_unhandled

.section .note.GNU-stack,"",@progbits
