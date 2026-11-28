#ifndef DUCKOS_X86_64_GDT_H
#define DUCKOS_X86_64_GDT_H

#ifdef __cplusplus
extern "C" {
#endif

/* Installs one bootstrap CPU's owned GDT and TSS with dedicated IST stacks. */
int duckos_x86_gdt_init(void);

#ifdef __cplusplus
}
#endif

#endif
