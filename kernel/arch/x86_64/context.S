.section .text
.code64
.global duckos_x86_64_context_switch
.type duckos_x86_64_context_switch, @function
duckos_x86_64_context_switch:
    pushfq
    pushq %rbx
    pushq %rbp
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    pushq %rdi
    movq %rsp, (%rdi)
    movq %rsi, %rsp
    popq %rdi
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbp
    popq %rbx
    popfq
    ret
.size duckos_x86_64_context_switch, .-duckos_x86_64_context_switch
.section .note.GNU-stack,"",@progbits
