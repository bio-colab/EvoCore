# Contributing to EvoCore

Thank you for your interest in contributing to **EvoCore: Darwin-Evolab Autonomous Scientific Linux Appliance**!

EvoCore bridges operating systems engineering with autonomous evolutionary algorithms. Whether you are adding new scientific evaluators, optimizing micro-kernel boot latency, or improving declarative remastering profiles, your contributions are welcome.

---

## 🧭 Principles of Contribution

1. **Hermetic & Reproducible**:
   Every change must preserve strict bit-for-bit reproducibility. Non-deterministic behavior, unpinned random seeds in testing, or host-polluting side effects are strictly rejected.
2. **Minimal Footprint**:
   EvoCore is a micro-appliance. Keep payload sizes strictly scrutinized. Avoid introducing unnecessary runtime dependencies into the base image.
3. **Scientific Attestation**:
   Any new experiment runner must adhere to the `evidence_manifest.json` contract, producing cryptographic signatures (`environment_sha256`, `specification_sha256`, `solution_sha256`).

---

## 🛠️ Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/bio-colab/EvoCore.git
   cd EvoCore
   ```

2. **Run the Test Suite**:
   ```bash
   pytest tests/test_evoforge.py -v
   ```

3. **Build the Appliance**:
   ```bash
   python evoforge.py build --profile minimal
   ```

---

## 📋 Pull Request Guidelines

1. **Branch Naming**:
   - `feat/feature-name` for new capabilities.
   - `fix/bug-description` for bug fixes.
   - `profile/new-domain` for new declarative experiment profiles.
2. **Verify Tests**:
   Ensure all automated unit and integration tests pass before submitting your PR.
3. **Documentation**:
   Update `README.md` or profile specifications if introducing new flags, boot parameters, or profiles.

---

## ⚖️ Code of Conduct
We are committed to providing a welcoming, rigorous, and respectful scientific environment. Scientific debate must be grounded in mathematical evidence and reproducible code.
