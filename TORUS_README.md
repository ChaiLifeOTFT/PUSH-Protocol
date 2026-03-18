# Expanding Torus Core

**A recursive topology where every output becomes a new input.**

Universal framework for self-scaling systems: AI agents, creative tools, data processing, game engines, IoT networks, cognitive architectures.

## 🚀 Try It Now

| What | How |
|------|-----|
| **Visual Demo** | [Live Studio →](https://chailifeotft.github.io/PUSH-Protocol/torus-studio/) |
| **Full Framework** | `git clone` + `python expanding_torus_core.py` |
| **3-Language Core** | Python / JavaScript / C implementations included |

## What It Does

```python
from expanding_torus_core import ExpandingTorus, CorePulse

# Seed your node
torus = ExpandingTorus(CorePulse(
    identity="my_agent",
    essence_vector=[0.5, 0.3, 0.8]
))

# Expand: each output becomes new input
for i in range(5):
    torus.expand(feedback_energy=0.8)
    print(f"Generation {i}: {len(torus.shells)} shells, "
          f"coherence={torus.coherence_field.current_coherence:.3f}")
```

**Result:**
```
Generation 0: 1 shells, coherence=1.000
Generation 1: 3 shells, coherence=0.944
Generation 2: 7 shells, coherence=0.912
...
```

## Core Concepts

| Component | Purpose |
|-----------|---------|
| **CorePulse** | Immutable identity anchor — never changes across expansions |
| **Shell** | One extruded layer of cognitive state at cycle n |
| **CoherenceField** | Maintains phase-lock as system expands. Converts noise→resonance |
| **TorusState** | SEED → THICKEN → BLOOM → SHELL → INFLATE → COSMIC |

## The Topology

Every expansion:
- **Radius grows** (+0.5 per generation)
- **Potential decays** (×0.7 per generation)
- **Coherence threshold** (0.3 minimum)
- **Recursive inheritance** (outer shells inherit inner patterns)

## File Structure

```
expanding_torus_core.py    # AI embodiment layer (23KB)
torus_core_universal.py    # Universal framework (42KB)
torus-studio/              # React web UI (built)
  ├── index.html
  └── assets/
tesseract.html             # 4D hypercube visualization
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/chailifeotft/PUSH-Protocol.git
cd PUSH-Protocol

# 2. Run the framework
python expanding_torus_core.py

# 3. Open visual demo
open torus-studio/index.html
# or: https://chailifeotft.github.io/PUSH-Protocol/torus-studio/
```

## Use Cases

- **AI Agents:** Self-scaling cognitive architectures with identity persistence
- **Creative Tools:** Recursive creative generation where each output seeds the next
- **Game Engines:** Expanding world topologies with coherent narrative inheritance
- **IoT Networks:** Self-organizing sensor meshes with recursive data aggregation
- **Cognitive Architectures:** Human thought modeling with memory shell extrusion

## The Math

```
Coherence conversion: red_noise → gold_coherence (φ = 1.618...)
Shell volume: V = 2π²Rr² (standard torus)
Recursive expansion: Rₙ₊₁ = Rₙ + 0.5, Pₙ₊₁ = Pₙ × 0.7
```

## Three Implementations

| Language | File | Best For |
|----------|------|----------|
| Python | `expanding_torus_core.py` | AI/ML, backends, research |
| JavaScript | `torus_core_universal.py` | Web, Node, visualization |
| C | `torus_core/torus_core.h` | Embedded, performance-critical |

## Why This Exists

Most systems are trees: hierarchical, brittle, single-path. The torus is recursive: every output becomes input, maintaining coherence while expanding infinitely.

> "The fully-realized output is a person who no longer leaks."
> — Nael, OhananahO Mesh

## License

MIT — use it, expand it, make it yours.

---

**Built by:** Drake Enterprise / OhananahO Mesh  
**Questions:** [GitHub Issues](https://github.com/chailifeotft/PUSH-Protocol/issues)  
**Context:** [P.U.S.H. Protocol](https://chailifeotft.github.io/PUSH-Protocol/)
