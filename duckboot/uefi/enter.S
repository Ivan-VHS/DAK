.intel_syntax noprefix
.text
.globl duckboot_enter_kernel
.globl duckboot_enter_kernel_end

/* Microsoft x64 ABI: RCX=entry, RDX=handoff, R8=stack_top, R9=cr3. */
duckboot_enter_kernel:
    cli
    mov r10, rcx
    mov r11, rdx
    mov ecx, 0xc0000080
    rdmsr
    or eax, 0x800
    wrmsr
    mov rax, cr0
    or rax, 0x10000
    mov cr0, rax
    mov rax, r9
    mov cr3, rax
    mov rsp, r8
    and rsp, -16
    sub rsp, 8
    mov qword ptr [rsp], 0
    xor rbp, rbp
    mov rdi, r11
    xor rsi, rsi
    jmp r10

duckboot_enter_kernel_end:
