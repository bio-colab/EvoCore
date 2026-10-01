# EvoCore v0.2.0 — Autonomous Scientific Discovery Linux Appliance

> **Release Tag**: `v0.2.0`  
> **Release Name**: EvoCore v0.2.0: Autonomous Laboratory Edition  
> **Target Commit / Branch**: `main`

---

## 🚀 Overview

We are proud to announce the first public release of **EvoCore (v0.2.0)** — an immutable, specialized micro-kernel Linux operating environment engineered specifically for reproducible evolutionary algorithms, symbolic mathematics, and scientific law discovery.

EvoCore was born from **[Darwin-Evolab](https://github.com/bio-colab/darwin-evolab)** to serve as its sovereign computational body: an operating appliance that boots purely into RAM, executes registered scientific experiments without human intervention, validates physical invariants, and produces signed evidence manifests.

---

## 🌟 Highlights & New Capabilities

- **Embedded Python 3.9 & NumPy 1.21**:
  Integrated a streamlined CPython 3.9.21 runtime and vectorized NumPy directly into a 26 MB compressed payload appended to `core.gz`.
- **Stokes-Newton Drag Force Physics Benchmark**:
  Out of the box, EvoCore executes evolutionary searches across 35 generations and 1,050 evaluations in RAM, discovering high-accuracy candidates (Brown-Lawler formula, $E_{\text{gap}} < 0.27\%$) while passing strict aerodynamic monotonicity and asymptotic limit gates.
- **Cryptographic Evidence Attestation**:
  Every experiment produces a cryptographically signed `evidence_manifest.json` containing:
  - `environment_sha256`: SHA-256 fingerprint of the kernel, CPU, and runtime.
  - `specification_sha256`: Canonical hash of the scientific problem specification.
  - `solution_sha256`: Mathematical fingerprint of the discovered formula and gates.
- **Four Distinct Operating Modes**:
  1. `Laboratory Mode (GUI)`: Live ASCII telemetry dashboard with physical gate tracking.
  2. `Headless Lab Runner`: Silent in-memory discovery with automatic host export and ACPI power-off.
  3. `Research Shell`: Interactive terminal with Darwin-Evolab and Python preloaded.
  4. `Full ISO CD-ROM Boot`: Bootable on bare-metal hardware and hypervisors.
- **Cross-Platform One-Click Launchers**:
  Native Windows Command Prompt (`run_evocore.bat`) and PowerShell (`run_evocore.ps1`) launchers with UTF-8 bilingual interfaces.

---

## 📦 Verified Artifacts & SHA-256 Hashes

| Artifact | Size | SHA-256 Checksum |
|---|---|---|
| `vmlinuz` | 6.1 MB | `ca30b6d7c0a279841c3237acd1d47705a7d392b186f0f7e80ff5d0dcca5dbfa1` |
| `core.gz` | 42.1 MB | `cd93447474af13723321685764d8a1db666c04f98144ae9d8e579737976e33ca` |
| `EvoCore-minimal.iso` | 69.1 MB | `aad99e83e770584d2f96987636e9e44c31e1aeee794ec66ffef1fe86a1a01f40` |

---

## 🔗 Links & Attribution
- **Parent Research Engine**: [Darwin-Evolab](https://github.com/bio-colab/darwin-evolab)
- **Official Repository**: [bio-colab/EvoCore](https://github.com/bio-colab/EvoCore)
- **License**: MIT License © 2026 bio-colab
