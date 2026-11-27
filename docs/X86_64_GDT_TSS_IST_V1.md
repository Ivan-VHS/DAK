# x86-64 GDT, TSS and IST bootstrap v1

**Status:** the bootstrap CPU now loads a DAKOS-owned GDT and 64-bit TSS before installing the CPU exception IDT. This is an architecture bring-up step, not a completed process or interrupt subsystem.

## GDT layout

The seven-entry GDT reserves these selectors:

| Selector | Entry | Descriptor | Purpose |
|---:|---:|---|---|
| 0x00 | 0 | null | required null descriptor |
| 0x08 | 1 | ring-0 long code | kernel CS |
| 0x10 | 2 | ring-0 data | kernel DS/ES/SS |
| 0x18 | 3 | ring-3 data | future user SS/DS |
| 0x20 | 4 | ring-3 long code | future user CS |
| 0x28 | 5–6 | 64-bit available TSS | task-state segment |

The user selectors include RPL 3: data 0x1b and code 0x23. Those descriptors reserve the ABI values; they do not enable Ring 3 execution.

## Bootstrap TSS

One static TSS is installed for the bootstrap processor:

- RSP0 points to a dedicated 32 KiB privilege-transition stack.
- IST1 points to a dedicated 16 KiB double-fault stack.
- IST2 points to a dedicated 16 KiB NMI stack.
- IST3 points to a dedicated 16 KiB page-fault stack.
- The I/O-map base equals the TSS size, so no I/O permission bitmap is exposed.

The TSS descriptor is 16 bytes and uses the available 64-bit TSS type. LTR loads selector 0x28 and the processor marks the descriptor busy.

## IDT exception routing

The bootstrap IDT assigns:

| Vector | Exception | IST |
|---:|---|---:|
| 2 | NMI | 2 |
| 8 | Double fault | 1 |
| 14 | Page fault | 3 |
| Other vectors 0–31 | Current stack | 0 |

The exception assembly saves a fixed 160-byte register/vector frame at the base of its stack. For IST entries, the processor also pushes the interrupted RSP/SS beyond that fixed frame. The current dispatcher only reports the exception and halts; IST routing makes these fatal diagnostics less dependent on a possibly damaged interrupted stack.

## Boot order

1. Disable maskable interrupts.
2. Initialize the serial diagnostic port.
3. Load the owned GDT and TSS.
4. Install exception IDT gates using the new kernel code selector and configured IST indices.
5. Validate the Limine handoff and continue the existing Stage 1 memory bootstrap.

PIC/APIC setup and maskable interrupts remain disabled.

## Tests and limitations

Host C tests verify TSS size/field offsets, descriptor encoding, TSS base/limit reconstruction and invalid descriptor input. IDT contract tests verify that double fault, NMI and page fault are assigned IST1, IST2 and IST3.

This is a single bootstrap CPU configuration. Per-CPU GDT/TSS setup, AP startup, guard pages, stack overflow detection, recoverable page faults, external interrupt routing, APIC timers and scheduler/context switching remain separate implementation gates. No Ring 3 entry, syscall transition or kernel/user isolation is claimed here.
