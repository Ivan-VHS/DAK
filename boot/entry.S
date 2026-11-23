.section .multiboot,"a"
.align 8
.global multiboot2_header
multiboot2_header:
    .long 0xe85250d6
    .long 0
    .long 24
    .long 0x17adaf12
    .short 0
    .short 0
    .long 8

.section .text.boot,"ax"
.code32
.global _start
.type _start,@function
_start:
    cli
    cld
    movl %eax, boot_magic
    movl %ebx, boot_info
    movl $boot_stack_top, %esp

    /* Initial identity map: first 1 GiB using 2 MiB pages. */
    movl $boot_pml4, %eax
    movl $boot_pdpt, %ebx
    orl $0x3, %ebx
    movl %ebx, (%eax)
    movl $0, 4(%eax)

    movl $boot_pdpt, %eax
    movl $boot_pd, %ebx
    orl $0x3, %ebx
    movl %ebx, (%eax)
    movl $0, 4(%eax)

    movl $boot_pd, %edi
    xorl %ecx, %ecx
1:
    movl %ecx, %eax
    shll $21, %eax
    orl $0x83, %eax
    movl %eax, (%edi)
    movl $0, 4(%edi)
    addl $8, %edi
    incl %ecx
    cmpl $512, %ecx
    jne 1b

    movl $boot_pml4, %eax
    movl %eax, %cr3

    /* PAE, OSFXSR and OSXMMEXCPT. */
    movl %cr4, %eax
    orl $0x620, %eax
    movl %eax, %cr4

    /* Long mode and NX support. */
    movl $0xc0000080, %ecx
    rdmsr
    orl $0x900, %eax
    wrmsr

    /* Enable protected mode, monitor coprocessor and paging; clear EM. */
    movl %cr0, %eax
    orl $0x80000003, %eax
    andl $0xfffffffb, %eax
    movl %eax, %cr0

    lgdt boot_gdt_pointer
    ljmp $0x08, $long_mode_start

.code64
long_mode_start:
    movw $0x10, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %ss
    xorw %ax, %ax
    movw %ax, %fs
    movw %ax, %gs

    leaq boot_stack_top(%rip), %rsp
    andq $-16, %rsp
    xorq %rbp, %rbp

    movl boot_magic(%rip), %edi
    movl boot_info(%rip), %esi
    call duckos_kernel_main

2:
    cli
    hlt
    jmp 2b
.size _start, .-_start

.section .rodata.boot,"a"
.align 8
boot_gdt:
    .quad 0x0000000000000000
    .quad 0x00af9a000000ffff
    .quad 0x00cf92000000ffff
boot_gdt_end:
boot_gdt_pointer:
    .word boot_gdt_end - boot_gdt - 1
    .long boot_gdt

.section .bss.boot,"aw",@nobits
.align 8
boot_magic:
    .skip 4
boot_info:
    .skip 4
.align 16
boot_stack_bottom:
    .skip 16384
boot_stack_top:

.align 4096
.global boot_pml4
boot_pml4:
    .skip 4096
.align 4096
.global boot_pdpt
boot_pdpt:
    .skip 4096
.align 4096
.global boot_pd
boot_pd:
    .skip 4096
