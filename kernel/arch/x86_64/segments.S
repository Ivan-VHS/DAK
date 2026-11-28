.section .text
.global duckos_x86_gdt_load
.type duckos_x86_gdt_load, @function
duckos_x86_gdt_load:
    lgdt (%rdi)

    /* Reload CS through a far return before installing the new data selectors. */
    pushq $0x08
    leaq .Lduckos_gdt_cs_reload(%rip), %rax
    pushq %rax
    lretq

.Lduckos_gdt_cs_reload:
    movw $0x10, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %ss
    xorw %ax, %ax
    movw %ax, %fs
    movw %ax, %gs

    movw %si, %ax
    ltr %ax
    ret
.size duckos_x86_gdt_load, .-duckos_x86_gdt_load

.section .note.GNU-stack,"",@progbits
