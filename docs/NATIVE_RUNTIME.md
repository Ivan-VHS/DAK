# Native Mora runtime and host services

## What is now native

DuckOS now has a native X11 desktop target in `native/mora-x11.c`, built as `duckos-compositor`. It owns the X11 window-manager selection, redirects top-level windows with X Composite, composites the redirected window surfaces through XRender, tracks damage, creates a title frame, focuses windows, updates basic EWMH properties, supports title dragging and handles Alt+F4 / Alt+F9. The `--check` mode verifies the X11 extension stack without taking over the display.

This is a real X11 process, not the previous browser window simulation. It is an initial X11 backend only: it is not a Wayland compositor, DRM/KMS driver, Vulkan renderer, multi-GPU manager or a full modern desktop compositor. It has no GPU shader pipeline, vsync scheduler, screen capture or polished resize/multi-monitor support. Do not start it on a desktop session that already has another window manager.

## Native host broker

`duckos.host` is a local userspace service with two transports:

- Unix domain socket: obtains the peer UID through Linux `SO_PEERCRED` and checks capability grants for that UID.
- Optional loopback HTTP bridge: binds only to `127.0.0.1` or `::1`, checks the Host header and exact allowed Origin, requires a bearer token, stores only SHA-256 token digests and limits request size and command surface.

The broker has a versioned JSON-RPC envelope. A caller cannot supply an executable or arbitrary command line to a process start method. The only launch targets are entries in `duckos/host/native-apps.json`. Child sessions run in independent POSIX process groups; when the broker is privileged, it drops the child to the requesting UID, primary group and home directory before execution. Stop sends SIGTERM and then bounded SIGKILL escalation. This is a userspace supervisor, not a kernel scheduler, namespace sandbox or cgroup resource boundary.

The capability policy lives in an administrator-owned JSON file. UIDs receive explicit grants, app manifests can require additional grants, and the root broker does not silently launch another user's application as root. Kernel module loading is a separate root-only operation with a fixed category/module allowlist.

## System terminal

The terminal exposes named read-only diagnostics, not a generic shell:

- `system`, `date`, `uptime`, `memory`, `storage`, `processes`, `network`, `home`.

Each name maps to a fixed argv array. No shell parser, pipes, redirection, variable expansion or arbitrary executable path is accepted. Execution has a five-second timeout, bounded output and runs as the requesting UID when the host broker is privileged.

## Driver integration

The broker can inventory Linux kernel modules through `modinfo` and `/proc/modules`, and can use the existing read-only PCI/USB host inventory. It can load a module only when all of these are true:

1. The caller has the explicit `driver.load` capability.
2. The broker is running with effective UID 0.
3. The module belongs to the compiled-in graphics/audio/network/device allowlist.
4. `modprobe` is present and reports success.

This reuses the host distribution's driver stack. DuckOS does not yet ship its own GPU, HDA, Wi-Fi, Ethernet, USB or NVMe drivers; it does not build or sign new kernel modules, implement a driver isolation boundary or guarantee a particular vendor device works.

## Reaper bridge

The host bridge imports `reaper.runtime.Interpreter` from the installed Reaper Python package and runs a small, fixed set of DuckOS `.rpr` policies under strict execution limits. Exposed contracts are capability membership, desktop command authorization, session transitions and window transitions.

Set `PYTHONPATH` to the Reaper checkout (or install Reaper in the same Python environment) to enable live evaluation. Without it, `duckos host reaper` reports `not-installed` and does not pretend that a contract was run. This is a real interpreter integration, not a second hard-coded copy of the policy.

## Mora browser connection

Mora can connect to the loopback HTTP bridge. The token is entered once per browser tab and held only in `sessionStorage`. The client refuses non-loopback endpoints, sends bearer-authenticated JSON-RPC requests, and does not expose arbitrary terminal or executable input to the page.

Example host setup (run as administrator, replacing UID 1000 with the desktop user's UID):

```sh
sudo duckos host policy-init --path /etc/duckos/host-policy.json --uid 1000 \
  --grant host.read --grant session.read --grant session.spawn --grant session.stop \
  --grant terminal.safe --grant driver.inspect --grant driver.load \
  --grant reaper.evaluate --grant desktop.start --grant display.manage

sudo duckos host token-create --path /etc/duckos/bridge-tokens.json --uid 1000
sudo duckos host serve --socket /run/duckos/host.sock \
  --policy /etc/duckos/host-policy.json --http-host 127.0.0.1 --http-port 8765 \
  --token-file /etc/duckos/bridge-tokens.json \
  --origin http://127.0.0.1:8760 --origin http://localhost:8760
```

The token-create command prints a random token exactly once. Only the digest is kept on disk. Copy the printed value into the Mora connection prompt. Keep both configuration files root-owned and mode 0600.

## Boot and image status

`packaging/live-build` and `tools/build-live-image.sh` define a reproducible Debian Live image build, including Xorg, the native X11 compositor, Mora, the host broker, a DuckOS X session entry and optional Reaper sources. The output is a bootable DuckOS userspace image that uses the distribution's Linux kernel. It is **not** a self-hosted DuckOS kernel image.

A native DuckOS boot still requires a freestanding Reaper compiler/backend, UEFI entry point, physical memory manager, page tables, interrupt controllers, context-switching scheduler, syscall ABI, device discovery, signed driver loading, filesystem and hardware-backed conformance tests. The existing `.rpr` boot/scheduler/memory/IPC files are policy contracts and are not relabelled as these mechanisms.

## Verification

```sh
python -m unittest discover -s tests -v
npm test
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
xvfb-run -a ./build/duckos-compositor --check
```

The CI job builds the C target against the X11 extension development packages and negotiates the extension stack under Xvfb. That verifies the compositor's build and X11 startup path; it does not substitute for testing on the target GPU, audio codec, network adapter or UEFI firmware.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve existing third-party and contributor notices.
