<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>🦆 Duck — Reaper 优先的操作系统项目</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native Mora](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20Mora)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **以 Reaper 为核心的系统基础、本机桌面外壳和本地优先工具生态；每条实现边界都清晰可见。**

**项目状态:** 实验阶段 · x86_64 Stage 1 已通过 QEMU 验证 · **版本:** Stage 1 boot foundation · **README 标准:** Psychoporter 666 v1.0 · **审阅日期:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Duck system architecture overview" width="100%"></p>

## 快速导航

[🚀 Demo: Browser reference preview](mora/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## 目标与范围

Duck 是一个以 Reaper 为优先的实验性操作系统项目。当前工作刻意分为内核启动基础、Reaper 策略契约和面向主机操作系统的 Mora 原生桌面应用三个独立方向。

## 功能

- x86_64 Stage 1 路径验证 Limine 固件交接和 Boot Info v1，分配早期 4 KiB 物理帧，输出 DUCKOS_BOOT_OK stage=1 后停机。QEMU BIOS 与 UEFI 检查均已通过。
- Reaper 提供参考策略契约路线，包括 40 项 Core Subsystem MVP 契约。内核原生强制执行仍待实现。
- Mora 具有基于 Qt 6 Widgets 的本机桌面应用，窗口由主机操作系统管理，并带有本地应用目录。Stage 1 内核不会启动它。
- mora/index.html 保留为浏览器参考预览。它不是原生合成器，也不是内核桌面。

## 系统结构图

~~~mermaid
flowchart TB
  subgraph BOOT["x86_64 Stage 1 — QEMU verified"]
    L["Limine handoff"] --> B["Boot Info v1"]
    B --> F["Early 4 KiB frame"]
    F --> M["Serial marker / halt"]
  end
  subgraph POLICY["Reaper policy contracts"]
    R["Reference contracts"] --> T["Contract tests"]
    T -.-> N["Native enforcement pending"]
  end
  subgraph HOST["Mora host desktop — separate from kernel"]
    Q["Qt 6 Widgets"] --> W["Host-managed windows"]
    H["Browser reference preview"]
  end
  BOOT -.->|"desktop integration pending"| HOST
~~~

## 构建原生 Mora

发布镜像构建面向 Linux x86_64，需要 Git/子模块、GCC/G++、CMake、作为构建工具的 Python 3、Node.js 22、Qt 6 Widgets、xorriso、curl、tar、QEMU 和 OVMF。

~~~sh
cmake -S . -B build/mora-native -DCMAKE_BUILD_TYPE=Release -DDUCKOS_BUILD_NATIVE_MORA=ON
cmake --build build/mora-native --target duckos_mora_native --parallel
ctest --test-dir build/mora-native --output-on-failure
~~~

Qt 桌面目标为可选项；未检测到 Qt 6 Widgets 时将跳过。Mora 作为宿主操作系统的原生应用运行，不由 Stage 1 内核启动。

## 浏览器参考预览

Linux:
~~~sh
./scripts/run-mora.sh
npm test
~~~
Windows PowerShell:
~~~powershell
.\scripts\run-mora.ps1
npm test
~~~

浏览器外壳仅用于参考展示，并非原生合成器，也不代表已与内核集成。

## 构建发布镜像

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/Duck-Release-x86_64.iso
~~~

发布管线验证仓库固定版本，运行项目构建和测试，生成 SHA-256 清单并组装 BIOS/UEFI 混合 ISO。该 ISO 是源码与工具预览，不是完整可安装操作系统。

## 内核状态与后续层

| Layer | Status |
|---|---|
| Limine 固件交接与 Boot Info v1 | 已实现；通过 QEMU 验证 |
| 早期物理帧分配 | Stage 1 路径已实现 |
| Reaper Core Subsystem MVP | 40 项参考契约；原生强制执行待实现 |
| 页表与地址空间 | 待实现 |
| 中断、定时器和抢占式调度器 | 待实现 |
| 进程模型与系统调用 ABI | 待实现 |
| 内核强制能力与零拷贝 IPC | 待实现 |
| PCI/USB/ACPI 与隔离驱动运行时 | 待实现 |
| 文件系统、服务管理器、安装程序和持久会话 | 待实现 |
| 原生合成器、GPU 与音频栈 | 待实现 |

当前内核阶段在验证固件交接并完成早期物理帧分配后停机。尚未提供进程隔离、驱动加载、存储、网络、持久会话或内核强制沙箱。Mora 目录条目不会执行清单命令，也不会授予硬件权限。

## 架构目标

x86_64 是面向 Intel 和 AMD 的主要目标。Elbrus 保留为单独兼容路线；这不代表已有 Elbrus 编译器后端、启动镜像或物理硬件测试矩阵。

## 源码联邦与完整性

当前源码集合的固定版本记录在 `federation/repositories.v1.json` 中。请使用以下命令初始化其中指定的确切版本：

~~~sh
git submodule update --init --recursive
~~~

关联项目仍是独立仓库，分别拥有各自的权利人、许可证、契约和发布周期：

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample)

## 文档

- [架构](docs/ARCHITECTURE.md)
- [实现状态](docs/IMPLEMENTATION_STATUS.md)
- [可启动镜像](docs/BOOTABLE_IMAGE.md)
- [内核子系统 MVP](docs/CORE_MVP_V1.md)
- [生态集成](docs/ECOSYSTEM_INTEGRATION.md)
- [项目演进阶梯](docs/PROJECT_EVOLUTION_LADDER.md)
- [Reaper 原生集成](docs/REAPER_INTEGRATION.md)
- [文档索引](docs/README.md)

实现状态台账、可启动镜像指南和项目演进阶梯是已交付及待完成系统层的权威记录。

## 许可证与法律状态

仓库根目录没有 LICENSE 文件或许可证声明。不得假定采用 MIT、Apache-2.0 或拥有重新分发权。分发前必须由权利人选择并批准许可证条款。

不得超出适用许可证授权范围重新分发打包内容或第三方材料。Git submodule 固定版本仅记录源码修订，不会改变权属或许可证条款。

## 工程原则

根据源码、测试、Schema、构建产物和 CI 证据描述行为。目录或路线图不是实现证明。浏览器偏好不是内核强制执行；PE 检查不是进程执行；校验和不是作者身份的证明。

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>
