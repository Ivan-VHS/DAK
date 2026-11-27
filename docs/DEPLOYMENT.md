# Dak release and deployment tooling

This document describes the release-packaging and deployment-planning tools added to the Dak repository.

## What is implemented

The Python toolchain now provides:

- deterministic component-bundle packaging from a validated system manifest;
- component re-hashing while packaging, to detect a file changing during the copy;
- a SHA-256 inventory covering release metadata and payload files;
- optional Ed25519 signing of release metadata using OpenSSL;
- archive verification, including path, entry-type, size, component hash and checksum validation;
- optional Ed25519 signature verification against a separately supplied public key;
- non-destructive GPT layout planning for EFI, A/B system slots, recovery and user data;
- USB, PXE, UEFI HTTP Boot/iPXE and cloud deployment-plan descriptions;
- machine-readable JSON schemas for release metadata and deployment plans.

The toolchain does **not** currently write raw disks, install an operating system, create a bootable ISO, generate a real firmware-compatible EFI executable, convert cloud disk images, configure DHCP/TFTP/HTTP servers, or prove bootability on hardware.

## Commands

Validate a system manifest and all referenced component files:

```sh
python -m dakos validate-manifest system-manifest.json build/rootfs
```

Build an unsigned component bundle:

```sh
python -m dakos build-release system-manifest.json build/rootfs Dak-0.2.0.tar.gz
```

Create an Ed25519 key pair for release signing. Keep the private key offline or in the release secret store; publish only the public key:

```sh
openssl genpkey -algorithm ED25519 -out release-private.pem
openssl pkey -in release-private.pem -pubout -out release-public.pem
```

Build and verify a signed release:

```sh
python -m dakos build-release system-manifest.json build/rootfs Dak-0.2.0.tar.gz --signing-key release-private.pem
python -m dakos verify-release Dak-0.2.0.tar.gz --public-key release-public.pem
```

Generate a USB partition layout without touching a drive:

```sh
python -m dakos deployment-plan system-manifest.json build/rootfs --target usb --output usb-layout.json
```

Generate a network-boot handoff plan:

```sh
python -m dakos deployment-plan system-manifest.json build/rootfs \
  --target pxe --base-url https://boot.example.test/dakos --secure-boot \
  --output pxe-plan.json
```

Generate a UEFI HTTP Boot/iPXE handoff plan by selecting `--target http`. Generate a cloud deployment description by selecting `--target cloud`.

## Release bundle structure

```text
dakos-release/
├── manifest.json
├── release.json
├── release.json.sig       # only when --signing-key is supplied
├── SHA256SUMS
├── README.txt
└── payload/
    └── ...                # component files from the validated manifest
```

The manifest is canonicalized before its SHA-256 digest is placed in `release.json`. With signing enabled, the Ed25519 signature covers `release.json`, which in turn binds the manifest digest. The verifier then checks the manifest's component hashes and the archive checksum inventory. The verification public key must come from a trusted source; a key shipped inside the same archive would not establish trust.

## Deployment plan boundaries

The planner produces a GPT map with:

- `efi`;
- `dak_system_a`;
- `dak_system_b`;
- `dak_recovery`;
- `dak_data`.

This is a proposed layout, not an installer. The A/B labels reserve two system slots but do not yet switch boot entries, confirm a healthy boot, or perform rollback. Those actions require the native Dak Boot Manager, a real kernel/initramfs/root filesystem image, and target-specific integration tests.

For PXE and HTTP targets the planner emits an iPXE handoff script and the expected component/manifest URLs. It does not publish those files, configure a boot server, implement DHCP/TFTP, or perform cryptographic verification in a firmware boot chain. The plan explicitly assigns manifest verification to the future native bootloader. HTTPS transport is required when the plan requests secure network transport, but HTTPS alone is not UEFI Secure Boot.

The `secure_boot.ready` field remains `false` until firmware trust enrollment, signed EFI artifacts, revocation policy, and native signature enforcement are implemented and tested. The cloud format list is a declaration of intended output formats (`raw`, `qcow2`, `vhdx`); no disk conversion is performed by this release planner.

## Test and validation

Run:

```sh
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
npm test
```

The deployment tests cover reproducible bundles, payload tampering, Ed25519 signing and verification, A/B layout planning, HTTPS iPXE handoff planning, URL validation and non-destructive behavior.

## Remaining native OS work

A bootable production Dak still requires a freestanding Reaper compiler/backend or another explicitly selected native kernel toolchain, a native kernel entry point, firmware-facing bootloader, physical memory and interrupt setup, process/runtime enforcement, filesystem and init, compositor, signed driver loading, installer, image assembly and real UEFI/BIOS/VM/hardware testing. The release tools intentionally report these as unimplemented instead of producing misleading ISO/USB/Cloud artifacts.
