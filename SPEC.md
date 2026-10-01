# EvoCore v0.1 — Darwin-Evolab Experimental Operating Environment
### Architecture, Invariants, and Appliance Specification

> **Document Identifier:** `EVOCORE-SPEC-0.1`  
> **Status:** Prototype Architecture & Engineering Charter  
> **Base Upstream:** Tiny Core Linux (CorePure64 / Core)  
> **Scope:** Strictly Local / Specialized Research Appliance  

---

## 1. Executive Summary & Epistemic Scope

`EvoCore` is an immutable, ephemeral, RAM-booted operating system distribution derived from Tiny Core Linux. It is **not** a general-purpose Linux distribution designed to host desktop applications; rather, it is a dedicated **Scientific Measurement Instrument and Evolutionary Execution Appliance**.

When an evaluation engine evolves arbitrary code, neural parameters, digital circuits, or algebraic expressions, executing them on standard operating systems carries two severe risks:
1. **Environmental Drift & Non-Reproducibility:** Minor differences in `glibc`, Python point releases, CPU scheduler policies, or background system services alter execution timings, floating-point rounding, and test outputs.
2. **Side-Effect Pollution:** Arbitrary mutated code may crash filesystems, spawn fork-bombs, allocate unbounded RAM, or overwrite local directories.

`EvoCore` solves both problems at the bare-metal level:
* **100% RAM Execution:** The entire system boots into RAM (`rootfs`). The underlying disk is never touched or mounted read-write without explicit provenance authorization.
* **Cryptographic Attestation:** Every experiment run in `EvoCore` generates an immutable provenance manifest binding the Linux kernel hash, initramfs hash, extension hashes, dataset hash, random seed, and output genome.
* **Two Operating Modes:**
  - **Laboratory Mode (Default):** Unattended execution. Boot -> Hardware Audit -> Run Target Experiment -> Emit Cryptographic Evidence Bundle -> Safe Shutdown.
  - **Research Mode:** Interactive terminal for live exploration, REPL debugging, and manual steering.

---

## 2. Layered Architecture

`EvoCore` maintains a strict separation of concerns across four decoupled layers:

```text
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ Layer 4: Provenance & Cryptographic Attestation                         │
 │          manifest.json, dataset.hash, environment.hash, genome.hash     │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ Layer 3: Domain Extension Layer (.tcz modular packages)                 │
 │          evocore-math.tcz (NumPy, SciPy, SymPy, Z3)                     │
 │          evocore-eda.tcz (Yosys, Verilator, ngspice)                    │
 │          evocore-code.tcz (libcst, pytest, git)                         │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ Layer 2: EvoCore Supervisor & Runtime Layer                             │
 │          /opt/evocore/supervisor.py, /opt/bootlocal.sh, /etc/issue       │
 │          Hardware detector, kernel cmdline parser, evidence emitter     │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ Layer 1: Immutable Micro-Kernel & RootFS Layer                          │
 │          Linux vmlinuz64 + Busybox + CPIO initramfs (evocore.gz)        │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Boot Pipeline & Supervisor Contract

Tiny Core initializes through `/linuxrc` -> `/sbin/init` -> `/etc/init.d/tc-config` -> `/opt/bootsync.sh` -> `/opt/bootlocal.sh`.

`EvoCore` hooks cleanly into `/opt/bootlocal.sh` without modifying upstream kernel or init binaries:

```text
BIOS / UEFI Boot
       ↓
ISOLINUX / SYSLINUX Bootloader (isolinux.cfg)
       ↓
vmlinuz (Kernel) + evocore.gz (Initramfs)
       ↓
tc-config (Micro-OS initialization in RAM)
       ↓
/opt/bootlocal.sh
       ↓
/opt/evocore/supervisor.py
       ├── Read /proc/cmdline (evomode=lab | evomode=research)
       ├── Load profile & extensions (.tcz)
       ├── If Mode == Laboratory:
       │     1. Execute /opt/evocore/experiment.json
       │     2. Compute SHA-256 signatures of inputs, kernel, and output
       │     3. Write evidence_manifest.json to persistence target
       │     4. Power off machine (if requested)
       └── If Mode == Research:
             Drop to interactive /bin/sh with Evolab environment pre-loaded
```

---

## 4. Declarative Build Profiles (EvoForge)

ISOs are produced deterministically by the `evoforge` build engine using declarative profiles:

1. **`minimal`**: Minimal appliance (< 35 MB ISO). Core Python runtime, Busybox, and the Darwin-Evolab kernel. Capable of discrete logic synthesis, Stokes-Newton hydrodynamic regression, and algorithmic optimization.
2. **`symbolic`**: Scientific appliance (< 85 MB ISO). Adds NumPy, SciPy, SymPy, and Z3 SMT solver for formal mathematical verification and complex dimensional regression.
3. **`eda`**: Silicon design appliance (< 140 MB ISO). Adds Yosys open synthesis suite, Verilator C++ simulator, and ngspice transistor simulator for Sky130 CMOS analog and digital circuit synthesis.

---

## 5. Security, Sandboxing, & Non-Persistence

1. **Ephemeral State:** Every boot starts from an identical bit-stream in RAM. Any corruption, crash, or memory overflow is erased upon power cycle.
2. **Local Isolation:** Work on `EvoCore` is strictly local. All build artifacts, ISOs, and unpacked root filesystems are excluded from version control repositories (`.gitignore`).
3. **Evidence Persistence:** Results are exported exclusively through structured output adapters (USB partition, network HTTP/SSH sink, or attached block device).
