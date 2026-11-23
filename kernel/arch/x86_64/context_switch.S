.section .text
.code64
.global duckos_context_switch
.type duckos_context_switch,@function
duckos_context_switch:
    pushq %rbp
    pushq %rbx
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    movq %rsp, (%rdi)
    movq %rsi, %rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbx
    popq %rbp
    ret
.size duckos_context_switch, .-duckos_context_switch

.section .note.GNU-stack,"",@progbits
