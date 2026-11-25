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

    .limine_requests : ALIGN(8)
    {
        KEEP(*(.limine_requests_start))
        KEEP(*(.limine_requests))
        KEEP(*(.limine_requests_end))
    } :requests

    .text : ALIGN(0x1000) AT(ADDR(.text) - KERNEL_VMA + KERNEL_PHYS)
    {
        *(.text .text.*)
    } :text

    .rodata : ALIGN(0x1000) AT(ADDR(.rodata) - KERNEL_VMA + KERNEL_PHYS)
    {
        *(.rodata .rodata.*)
    } :rodata

    .data : ALIGN(0x1000) AT(ADDR(.data) - KERNEL_VMA + KERNEL_PHYS)
    {
        *(.data .data.*)
    } :data

    .bss (NOLOAD) : ALIGN(0x1000) AT(ADDR(.bss) - KERNEL_VMA + KERNEL_PHYS)
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
