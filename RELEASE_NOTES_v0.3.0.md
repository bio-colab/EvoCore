# EvoCore v0.3.0 — The Sovereign Autonomous Scientific Appliance Release Notes

We are thrilled to announce **EvoCore v0.3.0**, marking a foundational architectural leap in autonomous scientific computing, hermetic operating appliances, and deep cryptographic attestation.

---

## 🌟 Major Highlights & What's New

### 1. Sovereign Command-Line Interface (`evocore`)
EvoCore is now packaged as a sovereign, first-class executable and Python library:
```bash
pip install -e .
```
- Available directly from the terminal via the `evocore` command.
- Modular subcommand architecture:
  - `evocore info`: Full hardware, QEMU discovery, and appliance build artifact telemetry.
  - `evocore build`: Declarative appliance ISO and initramfs remastering from profile.
  - `evocore run`: Multi-mode QEMU executor (`lab`, `research`, `iso`).
  - `evocore evidence`: Verification, inspection, bundling, and unpacking of scientific proofs.
  - `evocore profile`: Discover, inspect, and validate declarative appliance profiles.
  - `evocore repl`: Interactive terminal shell with prompt auto-completion and command history.

### 2. Agent-Native Dual-Mode Contract (`--json` vs Human TUI)
Every command in `evocore` strictly adheres to a dual-mode communication contract:
- **Human TUI (Default)**: Visual tables, status markers (`[OK]`, `[*]`, `[!]`), and real-time execution dashboards.
- **Machine Contract (`--json`)**: Deterministic, pure JSON emitted strictly to `stdout`, completely free from ANSI color codes, banner text, or log pollution.
- **Deterministic Exit Codes (0-7)**:
  - `0`: Success
  - `1`: General Error
  - `2`: Invalid Arguments / Schema Validation Failure
  - `3`: QEMU Hypervisor Not Found
  - `4`: Missing Artifact (Kernel, Initrd, ISO, Manifest)
  - `5`: Attestation / Tamper Verification Failure
  - `6`: Execution Timeout
  - `7`: Remastering / Build Failure

### 3. Deep Forensic Attestation & Merkle Rootfs Integrity
Elevating reproducibility to formal cryptographic guarantees:
- **Merkle Rootfs Hash (`rootfs_merkle_root`)**: Computes recursive SHA-256 Merkle root across all filesystem inodes and byte contents inside the RAM initramfs.
- **Composite Attestation Ledger**:
  `sha256(vmlinuz_sha256 | initrd_sha256 | rootfs_merkle_root | spec_sha256 | solution_sha256)`
- **Sealed Evidence Capsules (`.evobundle`)**: Self-verifying, compressed evidence archives containing the execution logs, verified solution AST, specification, and cryptographic hashes.

### 4. Interactive REPL Shell (`evocore repl`)
A rich, standalone interactive console powered by `prompt_toolkit`:
- Live command auto-completion (`build`, `run`, `evidence verify`, `profile list`).
- Persistent command history and session management.

### 5. Automated Verification & Testing
- Comprehensive test suite expanded to **22 unit tests** spanning CLI runner tests, Merkle root tree calculations, tamper detection, `.evobundle` roundtrips, and backward compatibility.
- 100% test pass rate across Linux and Windows.

---

## 📦 Getting Started with v0.3.0

```bash
# Clone the repository
git clone https://github.com/bio-colab/EvoCore.git
cd EvoCore

# Install package
pip install -e ".[test]"

# Inspect environment and hypervisor status
evocore info

# Run headless experiment and seal evidence capsule
evocore run --mode lab --headless --bundle

# Verify the resulting sealed evidence capsule
evocore evidence verify output/experiment_*.evobundle --json
```

---

## 👥 Contributors & Lineage
EvoCore is developed by the **Darwin-Evolab Team** at [bio-colab](https://github.com/bio-colab).
Licensed under the [MIT License](LICENSE).
