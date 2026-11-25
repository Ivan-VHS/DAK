# DuckOS x86_64 CPU exception handling

**Status:** experimental kernel foundation. The CPU exception IDT is installed during Stage 1 boot; this is not yet a complete interrupt subsystem.

## Scope

DuckOS installs a 256-entry x86_64 Interrupt Descriptor Table. The first 32 entries are populated with CPU exception handlers. Other entries remain absent until the kernel owns interrupt-controller setup and routing.

Each populated entry is a present ring-0 interrupt gate (`0x8E`) whose code selector is read from the currently active `CS`. This deliberately avoids assuming that the bootloader's GDT uses a particular selector value. The gate builder is a privileged-instruction-free C11 contract and is tested on the host.

The kernel disables maskable interrupts with `cli` before installing the IDT. It does not execute `sti`.

## Exception entry and frame contract

`kernel/arch/x86_64/exceptions.S` provides stubs for vectors 0 through 31. Exceptions that do not push an error code receive a synthetic zero slot; exceptions that do push an error code retain the processor-supplied value. Both paths then push the vector number and enter one common stub.

The current error-code vectors are:

`8, 10, 11, 12, 13, 14, 17, 21, 29, 30`.

The common stub saves general-purpose registers in the order declared by `duckos_x86_exception_frame`, clears the direction flag, aligns the temporary call stack for the x86_64 System V ABI, and calls the non-returning kernel diagnostic handler.

The frame layout is covered by host tests. Its fixed offsets are:

| Field | Byte offset |
|---|---:|
| `r15` | 0 |
| `rax` | 112 |
| `vector` | 120 |
| `error_code` | 128 |
| `rip` | 136 |
| `cs` | 144 |
| `rflags` | 152 |
| Total | 160 |

## Failure reporting

The diagnostic handler keeps maskable interrupts disabled and writes the exception vector, name, error code, instruction pointer, code selector and flags to COM1. For page faults (`#PF`, vector 14), it also reads `CR2` to report the faulting linear address.

When a valid 32-bit RGB framebuffer is available, the handler draws a red panic banner and a halt message. It then enters the existing `cli; hlt` loop. Exceptions are fatal at this stage: there is no scheduler or process context to resume.

## Build and verification

The host contract suite checks:

- the 16-byte IDT gate layout and every field offset;
- reconstruction of a full 64-bit handler address from its descriptor;
- interrupt-gate attributes, selector and IST bounds;
- fail-closed behavior for null handlers, null gate pointers and invalid selectors;
- the exact C exception-frame size and field offsets expected by the assembly stub.

The freestanding ISO build compiles the C gate builder and IDT initializer, assembles the exception stubs, and links them into the kernel ELF. The BIOS and UEFI QEMU test now requires the serial marker:

```text
exceptions=0..31 idt=loaded maskable_interrupts=disabled
```

That marker proves the kernel reached the code after `lidt`; the current test does not deliberately inject a CPU exception or claim that every exception path has been exercised in the emulator.

## Deliberate limitations

- The bootloader-provided GDT remains active. DuckOS does not yet install its own GDT.
- No TSS or Interrupt Stack Table (IST) is configured. The double-fault handler therefore still depends on the current kernel stack and is not a guaranteed recovery path for a corrupted stack.
- PIC/APIC initialization, IRQ remapping, timer interrupts, keyboard IRQs and external interrupt dispatch are not enabled.
- Maskable interrupts stay disabled. No `sti`, preemption, context switching or user-mode entry is performed.
- The stubs are fatal diagnostic handlers, not resumable exception handlers.
- No syscall gate, `syscall/sysret` setup or Ring 3 transition is present.

The next safe order is to establish an owned GDT and TSS, provide dedicated IST stacks for at least double fault and NMI, add guarded exception smoke tests, then implement interrupt-controller setup and timer/keyboard routing. Only after those gates should the kernel enable maskable interrupts.
