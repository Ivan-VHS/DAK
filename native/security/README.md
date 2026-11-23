# DuckOS agent sandbox

duck-sandbox.py launches a command through Bubblewrap with a private PID, IPC, UTS and network namespace (via --unshare-all), a read-only /usr, a fresh /tmp and /run, and one explicitly mounted workspace. It clears the child environment, refuses to run as root, applies CPU/address-space/file-size/process/file-descriptor limits, and has no unsandboxed fallback.

Example:

    python3 native/security/duck-sandbox.py \
      --workspace ./agent-work \
      --wall-seconds 180 \
      --cpu-seconds 60 \
      --memory-mib 2048 \
      -- python3 agent.py --task inspect

Use --read-only when the agent only needs to inspect files. Workspace write access is explicit and limited to that directory.

## Security boundary

This is a Linux-host development sandbox, not a security boundary implemented by the DuckOS kernel. It depends on the host kernel's namespaces, Bubblewrap, filesystem permissions and resource limits. The wrapper deliberately fails closed if Bubblewrap is missing or cannot create the requested namespaces.

The current policy does not ship a custom seccomp allowlist, syscall broker, GPU access, device access, network proxy, signed agent package format or remote attestation. It is suitable for reducing accidental access by development agents, not for executing hostile code with high-value secrets. Keep secrets outside the workspace and keep the host kernel and Bubblewrap updated.
