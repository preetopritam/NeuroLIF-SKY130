<div align="center">

# NeuroLIF-SKY130

### Transistor-Level Leaky Integrate-and-Fire Neuron  
### Weighted Synaptic Input · SKY130 Physical Design · DRC · Connectivity Audit · LVS

[![Technology](https://img.shields.io/badge/PDK-SKY130-1565C0)](#physical-implementation)
[![KLayout](https://img.shields.io/badge/KLayout-0.30.12-455A64)](#physical-implementation)
[![DRC](https://img.shields.io/badge/DRC-0%20violations-2E7D32)](#physical-verification)
[![LVS](https://img.shields.io/badge/LVS-Netlists%20Match-2E7D32)](#physical-verification)
[![MOS](https://img.shields.io/badge/MOS-17%2F17-00695C)](#highlights)
[![PVT](https://img.shields.io/badge/PVT-27%2F27%20PASS-2E7D32)](#robustness-characterization)
[![License](https://img.shields.io/badge/License-MIT-37474F)](#license)

**Pre-silicon educational neuromorphic IC design using the open SKY130 PDK**

</div>

---

NeuroLIF-SKY130 implements a transistor-level **leaky integrate-and-fire (LIF) neuron** using SKY130 1.8 V CMOS devices.

The project covers the complete design path from transistor-level circuit development and weighted-synapse characterization to physical layout, official SKY130 DRC, independent geometry-based connectivity verification and KLayout LVS.

The released core contains **17 MOS transistors**, exposes **8 external pins**, passes the official SKY130 DRC with **0 violations**, and matches the intended 17-MOS reference schematic under LVS.

<p align="center">
  <img src="figures/layout/klayout_full_neuron_final.png" alt="Final routed NeuroLIF-SKY130 neuron" width="900">
</p>

<p align="center">
  <em>Final routed NeuroLIF-SKY130 physical core in KLayout.</em>
</p>

---

## Project at a Glance

| Item | Status |
|---|---|
| Circuit | Transistor-level LIF neuron with weighted synaptic input |
| Technology | SKY130 1.8 V CMOS |
| Core size | 17 MOS: 8 PFET + 9 NFET |
| Synaptic weight | 2-bit, 0× / 1× / 2× / 3× |
| Membrane capacitor | External ideal 5 pF |
| Transistor-level simulation | Completed |
| Nominal functional validation | PASS |
| PVT characterization | 27 / 27 defined operating points PASS |
| Deterministic variation | 13 / 13 cases PASS |
| Physical layout | Completed |
| Official SKY130 DRC | PASS, 0 violations |
| Connectivity/topology audit | PASS |
| KLayout LVS | PASS, netlists match |
| Extracted MOS count | 17 / 17 |
| Tapeout | Not performed |
| Fabricated silicon | Not available |
| Monte Carlo mismatch | Not performed |
| Parasitic-extracted transient simulation | Not performed |

---

## Highlights

| Metric | Result |
|---|---:|
| Technology | SKY130 1.8 V CMOS |
| Neuron model | Leaky integrate-and-fire |
| MOS devices | **17** |
| PFET / NFET | **8 / 9** |
| External pins | **8** |
| Logical conductor nets | **14** |
| Synaptic encoding | **0× / 1× / 2× / 3×** |
| Membrane capacitor | External ideal **5 pF** |
| Nominal Schmitt hysteresis | **199.852 mV** |
| PVT validation | **27 / 27** defined operating points passed |
| Deterministic variation | **13 / 13** cases passed |
| Official SKY130 DRC | **PASS — 0 violations** |
| Connectivity/topology audit | **PASS** |
| Cross-net shorts | **None detected** |
| Floating conductor nets | **None detected** |
| KLayout LVS | **PASS — Netlists match** |
| Extracted MOS count | **17 / 17** |

---

# Circuit Design

## Architecture

The final signal path is:

```text
Reference current
      |
      v
PMOS current mirror
      |
      v
2-bit weighted synapse
      |
      v
     VMEM
      |
      +-------> NMOS leak controlled by VLEAK
      |
      v
6T CMOS Schmitt detector
      |
      v
     VRAW
      |
      v
CMOS output inverter
      |
      v
    SPIKE
      |
      +-------> NMOS reset
                    |
                    v
                   VMEM
```

### Physical transistor composition

| Block | MOS count |
|---|---:|
| Weighted synapse | 7 |
| Membrane leak | 1 |
| Schmitt detector | 6 |
| Output inverter | 2 |
| Reset | 1 |
| **Total** | **17** |

The membrane capacitor is deliberately external to the physical core.

Nominal transistor-level simulations use:

```text
Cmem = 5 pF
```

Detailed architecture and circuit documentation:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/circuit_design.md`](docs/circuit_design.md)

---

## Weighted Electronic Synapse

The final 2-bit synapse uses **three identical PMOS unit-current cells**.

Two digital controls, `GATE_W0` and `GATE_W1`, produce four synaptic states:

| Code | Active unit cells | Logical weight | Nominal delivered current |
|---|---:|---:|---:|
| `00` | 0 | 0× | ~0.002 nA |
| `01` | 1 | 1× | ~103.734 nA |
| `10` | 2 | 2× | ~207.470 nA |
| `11` | 3 | 3× | ~311.206 nA |

> **Note:** `00` represents the nominal **0× synaptic state**. The transistor-level simulation shows a residual off-state current of approximately **0.002 nA (~2 pA)** rather than mathematically zero current.

Measured current ratios:

```text
10 / 01 = 2.0000
11 / 01 = 3.0000
```

### Why identical unit cells?

Direct characterization showed that, for the tested SKY130 device configuration and bias conditions, a single PMOS with twice the unit width did not produce twice the unit current:

```text
Unit PMOS current       ≈ 103.738 nA
Single 2×-wide PMOS     ≈ 98.196 nA
Two identical unit PMOS ≈ 207.476 nA
```

The final 2× state therefore uses **two identical unit PMOS devices in parallel**.

This is an implementation-specific result and is not presented as a general statement about MOS-current scaling with transistor width.

<p align="center">
  <img src="figures/layout/klayout_weighted_synapse.png" alt="Weighted synapse layout" width="780">
</p>

<p align="center">
  <em>Final routed 7-MOS weighted-synapse block.</em>
</p>

---

## Membrane Dynamics versus Synaptic Weight

The transistor-level transient response shows how synaptic weight changes the membrane-voltage dynamics:

- `00` — no firing; membrane voltage remains below threshold
- `01` — lowest nonzero synaptic drive and firing rate
- `10` — stronger drive and higher firing rate
- `11` — strongest drive and highest firing rate

The dashed line marks the nominal rising Schmitt threshold:

```text
VTH_UP = 1.023948 V
```

<p align="center">
  <img src="figures/membrane_dynamics_vs_synaptic_weight_exact.png" alt="Membrane dynamics versus synaptic weight" width="900">
</p>

<p align="center">
  <em>
    Original transistor-level VMEM waveforms for all four synaptic-weight states.
    The waveform data are unchanged; presentation annotations were added outside the original plot region.
  </em>
</p>

---

## Membrane, Leak and Threshold Detection

`VMEM` is the principal neuron state variable.

Synaptic current charges the external membrane capacitor while an NMOS leak transistor provides a controllable discharge path.

### Leak device

```text
W = 0.42 µm
L = 1.00 µm
```

Leak strength is externally controlled through `VLEAK`.

### Schmitt detector

Threshold detection uses a corrected six-transistor CMOS Schmitt topology.

Final transistor-level switching points:

```text
VTH_UP     = 1.023948 V
VTH_DOWN   = 0.824096 V
Hysteresis = 199.852 mV
```

The approximately **200 mV hysteresis window** provides distinct rising and falling switching thresholds around the membrane transition.

---

## Spike Generation and Reset

The Schmitt detector generates the internal signal:

```text
VRAW
```

A CMOS inverter produces the externally available positive-going signal:

```text
SPIKE
```

The reset transistor is:

```text
MN_RST VMEM SPIKE VSS VSS
```

When `SPIKE` rises, the reset NMOS discharges `VMEM` toward `VSS`, initiating the next integrate-and-fire cycle.

A dedicated refractory-delay circuit is not included in the current revision.

---

## Nominal Functional Response

| Weight | Spike count | Firing rate |
|---|---:|---:|
| `00` | 0 | 0 Hz |
| `01` | 16 | 42.1 kHz |
| `10` | 39 | 102.6 kHz |
| `11` | 65 | 171.1 kHz |

Under nominal conditions, firing activity increases monotonically with the number of active synaptic unit cells.

---

## Key Design Parameters

| Parameter | Value |
|---|---:|
| Supply voltage | 1.80 V |
| Reference current | 100 nA nominal |
| Membrane capacitor | 5 pF |
| Rising threshold | 1.023948 V |
| Falling threshold | 0.824096 V |
| Hysteresis | 199.852 mV |
| Weight-01 current | ~103.734 nA |
| Weight-10 current | ~207.470 nA |
| Weight-11 current | ~311.206 nA |
| NMOS logic width | 1.00 µm |
| PMOS logic width | 2.00 µm |
| Logic-channel length | 0.15 µm |
| Feedback-device width | 0.42 µm |
| Feedback-device length | 0.30 µm |
| Mirror/synapse PMOS width | 0.84 µm |
| Mirror/synapse PMOS length | 0.50 µm |
| Leak NMOS width | 0.42 µm |
| Leak NMOS length | 1.00 µm |
| Reset NMOS width | 1.20 µm |
| Reset NMOS length | 0.15 µm |

---

## Robustness Characterization

```text
Post-patch nominal validation       PASS
Functional numerical convergence   PASS
PVT operating points                27 / 27 PASS
Deterministic variation cases       13 / 13 PASS
```

### PVT acceptance criterion

Each PVT operating point passes when:

1. the simulation completes successfully
2. weight `00` remains silent
3. weight `11` generates at least one valid output spike
4. firing response remains nondecreasing with increasing synaptic weight

Therefore:

> **27 / 27 PASS does not imply that intermediate weights `01` and `10` generate spikes at every individual PVT corner.**

The deterministic 13-case variation study is not presented as a Monte Carlo mismatch analysis.

### Frozen simulation results

```text
results/
├── nominal/
├── synapse/
├── pvt/
└── variation/
```

Clean result-analysis notebooks are available under:

```text
notebooks/
```

---

# Physical Design

## Physical Implementation

The physical implementation was developed in KLayout using the open SKY130 technology environment.

### Frozen development environment

| Tool | Version |
|---|---|
| KLayout | 0.30.12 |
| Python | 3.11.9 |
| gdsfactory | 8.4.0 |
| kfactory | 0.17.8 |

The project uses a dedicated seven-device MOS primitive library.

All final MOS primitives use:

```text
nf = 1
interdig = 0
```

<p align="center">
  <img src="figures/layout/klayout_primitive_library.png" alt="SKY130 MOS primitive library" width="720">
</p>

<p align="center">
  <em>Single-finger SKY130 MOS primitive library used by the physical-design flow.</em>
</p>

### Final routed core with layer view

<p align="center">
  <img src="figures/layout/klayout_full_neuron_with_layers.png" alt="Final neuron with KLayout layers" width="900">
</p>

### Canonical physical artifact

```text
layout/neuron/neurolif_full_neuron_final_routed_v1.gds
```

Top cell:

```text
NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1
```

Canonical SHA-256:

```text
74fcc1478c50e2fd590d333e576c99fd1fec03d72c43f3679c15fd50e8d9a6de
```

The canonical physical GDS is treated as frozen.

A separate labelled derivative is used only for LVS extraction:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

---

## Tool Flow and Transferability

The project uses an open-source SKY130-oriented workflow rather than a commercial analog-IC environment.

### Current flow

```text
Transistor-level circuit definition
            |
            v
        ngspice
            |
            v
Nominal / weighted-synapse / PVT /
deterministic-variation characterization
            |
            v
Python + gdsfactory + kfactory
            |
            v
KLayout physical implementation
            |
            +------> Official SKY130 DRC
            |
            +------> Geometry/connectivity audit
            |
            +------> KLayout LVS
```

The project demonstrates experience with the underlying IC-design concepts of:

- transistor-level schematic definition
- device sizing and biasing
- transient simulation
- PVT evaluation
- physical device placement
- custom routing
- body and well connectivity
- layout-rule verification
- connectivity verification
- schematic-to-layout equivalence checking

These concepts transfer directly to industry-standard analog/mixed-signal IC workflows.

The repository does **not** claim commercial Cadence Virtuoso or Spectre experience. A natural future extension is to reproduce the same design methodology in an industry-standard schematic, simulation and layout environment.

---

# Verification

## Physical Verification

The final core is closed using three complementary verification mechanisms:

```text
Official SKY130 DRC
        +
Independent geometry/connectivity audit
        +
KLayout LVS
```

---

### 1. Official SKY130 DRC

Final result:

```text
PASS
0 violations
```

<p align="center">
  <img src="figures/verification/klayout_final_drc_zero.png" alt="Final DRC result" width="850">
</p>

---

### 2. Independent Geometry-Based Connectivity Audit

The audit independently checks:

- 17 expected MOS devices
- 14 intended logical conductor nets
- M1 / VIA1 / M2 connectivity
- weighted-synapse topology
- Schmitt, buffer, leak and reset topology
- PMOS NWELL/body connectivity
- NMOS substrate/body connectivity
- cross-net shorts
- unexplained floating conductor networks

Final result:

```text
17 MOS devices           VERIFIED
14 logical nets          VERIFIED

Cross-net shorts         NONE DETECTED
Floating conductor nets  NONE DETECTED
Body/well connectivity   VERIFIED
```

---

### 3. KLayout LVS

The labelled LVS derivative was extracted and compared against the intended 17-MOS reference schematic.

```text
MOS total = 17 / 17
PFET      = 8 / 8
NFET      = 9 / 9

OFFICIAL RESULT:
NETLISTS MATCH
```

Authoritative KLayout result:

```text
INFO : Congratulations! Netlists match.
```

<p align="center">
  <img src="figures/verification/klayout_final_lvs_match.png" alt="Final LVS result" width="850">
</p>

---

### Verification Summary

| Check | Result |
|---|---|
| Official SKY130 DRC | **PASS** |
| DRC violations | **0** |
| Geometry connectivity audit | **PASS** |
| Logical conductor nets | **14 / 14** |
| Cross-net shorts | **None detected** |
| Floating conductor nets | **None detected** |
| Body/well connectivity | **PASS** |
| Official KLayout LVS | **PASS** |
| LVS comparison | **Netlists match** |
| Extracted MOS | **17 / 17** |
| External pins | **8 / 8** |

Detailed evidence:

```text
verification/neuron/
verification/synapse/
```

Machine-readable logs, databases, extracted netlists and JSON verification records are the primary verification evidence. Screenshots are supporting presentation material.

---

## Why DRC Alone Was Not Treated as Sufficient

During development, one intermediate VDD-routed layout was DRC-clean while an intended `MN_FB` VDD connection was still missing.

A later VRAW route also created an unintended `VRAW`-to-`VSS` MET1 short that was isolated by the independent geometry audit.

These cases motivated the final verification strategy:

```text
DRC
 +
independent geometry/connectivity audit
 +
LVS
```

rather than relying on design-rule checking alone.

---

# Neuromorphic ASIC Relevance

## Relevance to Neuromorphic ASIC Research

NeuroLIF-SKY130 demonstrates a compact transistor-level neuromorphic signal-processing chain rather than only a behavioral neuron model.

The project combines:

- CMOS leaky integrate-and-fire dynamics
- electronically weighted synaptic input
- transistor-level membrane integration and leakage
- hysteretic threshold detection
- spike generation
- spike-controlled membrane reset
- custom SKY130 physical layout
- official DRC
- independent connectivity verification
- LVS against a transistor-level reference schematic

The current implementation focuses on a **single physically verified neuron core**.

The same design methodology can be extended to multi-neuron and multi-synapse systems in which:

- synaptic-weight programming
- bias-current distribution
- supply integrity
- routing congestion
- device mismatch
- leakage
- area
- power
- inter-neuron spike routing

become system-level design constraints.

The project therefore serves as a foundation for further work in:

- neuromorphic ASICs
- spiking-neural hardware
- mixed-signal Edge-AI circuits
- event-driven computation
- synapse/neuron arrays

It is not presented as a complete neuromorphic accelerator.

---

## Scalability and Next Steps

The current release closes one 17-MOS neuron core at the transistor and physical-design levels.

Natural next steps are:

### 1. Parasitic-Extracted Post-Layout Simulation

Extract routing and device parasitics from the final physical layout and repeat transient simulations to quantify changes in:

- membrane charging rate
- Schmitt switching thresholds
- spike timing
- reset behavior
- firing rate

---

### 2. Statistical Mismatch Characterization

Extend the existing PVT and deterministic-variation validation with Monte Carlo mismatch analysis.

Relevant quantities include:

- threshold spread
- firing-rate variation
- synaptic current variation
- device mismatch
- neuron-to-neuron variability

---

### 3. Multi-Synapse Integration

Extend the present weighted input into several independently controlled synaptic branches feeding the same membrane node.

This would introduce new design concerns such as:

- input fan-in
- current summation
- routing density
- weight-control distribution
- accumulated leakage

---

### 4. Neuron-Array Implementation

Tile the verified neuron cell into a small multi-neuron array.

Array-level work would require:

- shared bias distribution
- supply routing
- regular cell placement
- spike-routing strategy
- local and global interconnect planning
- area and power evaluation

---

### 5. Higher-Resolution Synaptic Weighting

The current circuit uses a 2-bit effective weighting scheme:

```text
0×
1×
2×
3×
```

A future implementation could investigate:

- higher-resolution digital weighting
- locally stored weight states
- alternative current-steering structures
- programmable synaptic devices

---

### 6. Edge-AI / Neuromorphic Integration

The verified neuron and synapse cells could be evaluated as building blocks for larger event-driven processing structures.

Possible directions include:

- spiking-neural arrays
- event-driven inference hardware
- neuromorphic sensory processing
- mixed-signal Edge-AI systems
- compute-in-memory-adjacent architectures

These are future research directions rather than claims of the present implementation.

---

### 7. Industry-Standard ASIC-Flow Migration

The same design could be reproduced in an industry-standard analog IC workflow using equivalent stages:

```text
schematic capture
       |
       v
transistor-level simulation
       |
       v
custom layout
       |
       v
DRC / LVS
       |
       v
parasitic extraction
       |
       v
post-layout simulation
```

The purpose would be to transfer the circuit methodology demonstrated here into larger-scale analog/mixed-signal ASIC development.

---

## External Interface

| Pin | Function |
|---|---|
| `VDD` | 1.8 V supply |
| `VSS` | Ground |
| `VBIAS` | PMOS current-mirror bias |
| `GATE_W0` | 1× synaptic-weight control |
| `GATE_W1` | 2× synaptic-weight control |
| `VLEAK` | Leak bias |
| `VMEM` | Membrane node / external capacitor terminal |
| `SPIKE` | Neuron spike output |

---

# Repository

## Repository Structure

```text
NeuroLIF-SKY130/
│
├── circuit/       # reference and LVS schematics
├── docs/          # detailed technical documentation
├── figures/       # layout, simulation and verification figures
├── layout/        # canonical GDS/OASIS artifacts
├── notebooks/     # clean result-analysis notebooks
├── results/       # frozen simulation summaries
├── scripts/       # physical construction and verification scripts
├── verification/  # DRC, connectivity and LVS evidence
│
├── CITATION.cff
├── LICENSE
└── README.md
```

### Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/circuit_design.md`](docs/circuit_design.md)
- [`docs/physical_design.md`](docs/physical_design.md)
- [`docs/verification.md`](docs/verification.md)
- [`docs/reproducibility.md`](docs/reproducibility.md)

---

## Reproducibility

The curated repository supports inspection and reproduction of the final verification workflow.

### Final DRC

```text
scripts/klayout/run_final_drc.py
```

### Final LVS

```text
scripts/klayout/run_final_lvs.py
```

### Full-Neuron Connectivity Audit

```text
scripts/verification/neuron/
audit_full_neuron_connectivity_v1.py
```

The repository also preserves the successful physical-design lineage.

Some historical intermediate GDS files and manifests are intentionally omitted from the curated release. The repository therefore should not be interpreted as a complete one-command replay of every historical routing stage from a fresh clone.

See:

[`docs/reproducibility.md`](docs/reproducibility.md)

for the exact reproducibility boundary and frozen tool versions.

---

## Validation Status and Limitations

### Completed

- transistor-level LIF-neuron simulation
- weighted-synapse characterization
- nominal transient validation
- numerical convergence validation
- 27-point defined PVT validation
- 13-case deterministic-variation validation
- custom physical-layout implementation
- official SKY130 DRC
- independent geometry/connectivity audit
- KLayout LVS
- 17/17 MOS extraction consistency

### Not completed

- parasitic-extracted transient simulation
- Monte Carlo mismatch analysis
- full-chip padframe
- ESD structures
- seal ring
- package-level design
- fabricated-silicon measurement
- tapeout

The project should therefore be interpreted as a **pre-silicon transistor-level and physical-design research/educational artifact**, not a production-ready taped-out IC.

---

## Research Context

Neuromorphic silicon circuits use transistor-level physical dynamics to implement neuron-like state integration, thresholding and spike generation.

NeuroLIF-SKY130 is an educational open-PDK implementation focused on:

- transistor-level neuron behavior
- weighted electronic synaptic input
- membrane integration and leak
- hysteretic threshold detection
- spike generation and reset
- physical layout
- reproducible verification

The project is **not presented as a new general neuron model, a fabricated neuromorphic processor or a tapeout-ready full chip**.

---

## References

1. C. Mead, “Neuromorphic Electronic Systems,” *Proceedings of the IEEE*, vol. 78, no. 10, pp. 1629–1636, 1990. DOI: `10.1109/5.58356`.

2. G. Indiveri et al., “Neuromorphic Silicon Neuron Circuits,” *Frontiers in Neuroscience*, vol. 5, art. 73, 2011. DOI: `10.3389/fnins.2011.00073`.

3. SkyWater Technology / Google, *SkyWater SKY130 Open Source PDK Documentation*.

---

## Scope and Limitations

NeuroLIF-SKY130 is a **pre-silicon educational neuromorphic circuit-design project**.

### Supported claims

- transistor-level LIF-neuron simulation
- weighted-synapse characterization
- nominal functional validation
- defined PVT validation
- deterministic-variation validation
- physical-layout implementation
- official SKY130 DRC with zero violations
- independent geometry/connectivity verification
- successful KLayout LVS

### Not claimed

- fabricated silicon
- tapeout
- measured post-silicon performance
- commercial manufacturing signoff
- Monte Carlo mismatch validation
- parasitic-extracted post-layout transient simulation

PEX and post-layout simulation remain possible future extensions.

---

## License

Released under the **MIT License**.

See [`LICENSE`](LICENSE).

---

## Citation

A machine-readable citation record is provided in [`CITATION.cff`](CITATION.cff).

If this repository is used in academic or research work, please cite the project using that record.
