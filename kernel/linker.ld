ENTRY(_start)

SECTIONS
{
    . = 0x00100000;
    __kernel_start = .;

    .multiboot ALIGN(8) :
    {
        KEEP(*(.multiboot))
    }

    .text ALIGN(0x1000) :
    {
        *(.text.boot)
        *(.text .text.*)
    }

    .rodata ALIGN(0x1000) :
    {
        *(.rodata.boot)
        *(.rodata .rodata.*)
    }

    .data ALIGN(0x1000) :
    {
        *(.data .data.*)
    }

    .bss ALIGN(0x1000) (NOLOAD) :
    {
        *(COMMON)
        *(.bss.boot)
        *(.bss .bss.*)
    }

    . = ALIGN(0x1000);
    __kernel_end = .;

    /DISCARD/ :
    {
        *(.comment)
        *(.note*)
        *(.eh_frame*)
        *(.eh_frame_hdr*)
    }
}
