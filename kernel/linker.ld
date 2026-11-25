OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)

KERNEL_VMA = 0xffffffff80000000;
KERNEL_PHYS = 0x00200000;

PHDRS
{
    requests PT_LOAD FLAGS(4);
    text PT_LOAD FLAGS(5);
    rodata PT_LOAD FLAGS(4);
    data PT_LOAD FLAGS(6);
}

SECTIONS
{
    . = KERNEL_VMA;
    __kernel_start = .;

    .limine_requests ALIGN(8) : AT(KERNEL_PHYS)
    {
        KEEP(*(.limine_requests_start))
        KEEP(*(.limine_requests))
        KEEP(*(.limine_requests_end))
    } :requests

    .text ALIGN(0x1000) : AT(KERNEL_PHYS + (ADDR(.text) - KERNEL_VMA))
    {
        *(.text .text.*)
    } :text

    .rodata ALIGN(0x1000) : AT(KERNEL_PHYS + (ADDR(.rodata) - KERNEL_VMA))
    {
        *(.rodata .rodata.*)
    } :rodata

    .data ALIGN(0x1000) : AT(KERNEL_PHYS + (ADDR(.data) - KERNEL_VMA))
    {
        *(.data .data.*)
    } :data

    .bss ALIGN(0x1000) (NOLOAD) : AT(KERNEL_PHYS + (ADDR(.bss) - KERNEL_VMA))
    {
        *(COMMON)
        *(.bss .bss.*)
    } :data

    . = ALIGN(0x1000);
    __kernel_end = .;

    /DISCARD/ :
    {
        *(.comment)
        *(.eh_frame .eh_frame.*)
        *(.note .note.*)
    }
}

ASSERT(ADDR(.limine_requests) == KERNEL_VMA, "Limine requests must begin at the kernel VMA");
ASSERT(LOADADDR(.limine_requests) == KERNEL_PHYS, "kernel physical base mismatch");
ASSERT((__kernel_end - __kernel_start) > 0, "empty kernel image");
