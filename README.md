# NeuroLIF-SKY130

**Transistor-Level Leaky Integrate-and-Fire Neuron with Weighted Synaptic Input and Physical Verification in SKY130**

NeuroLIF-SKY130 is a pre-silicon neuromorphic IC-design project implementing a transistor-level leaky integrate-and-fire (LIF) neuron using SKY130 1.8 V CMOS devices.

The project covers the complete path from transistor-level circuit development and weighted-synapse characterization to physical layout, design-rule checking, independent geometry-based connectivity verification and layout-versus-schematic comparison.

The final released core contains **17 MOS transistors**, exposes **8 external pins** and has been closed with **zero SKY130 DRC violations** and a successful **KLayout LVS match**.

![Final routed NeuroLIF-SKY130 neuron](figures/layout/klayout_full_neuron_final.png)

---

## Highlights

| Item | Result |
|---|---|
| Technology | SKY130 1.8 V CMOS |
| Neuron model | Leaky integrate-and-fire |
| MOS devices | 17 |
| PFET / NFET | 8 / 9 |
| External pins | 8 |
| Logical conductor nets | 14 |
| Weighted synapse | 2-bit, 0/1/2/3 unit-current encoding |
| Membrane capacitor | External ideal 5 pF |
| Nominal Schmitt hysteresis | ~199.9 mV |
| PVT validation | 27 / 27 defined operating points passed |
| Deterministic variation | 13 / 13 cases passed |
| Official SKY130 DRC | PASS, 0 violations |
| Connectivity/topology audit | PASS |
| Cross-net shorts | None detected |
| Floating conductor nets | None detected |
| KLayout LVS | PASS, netlists match |
| Extracted MOS count | 17 / 17 |

---

## Architecture

The final neuron consists of:

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

The physical core is composed of:

```text
7-MOS weighted synapse
1-MOS membrane leak
6-MOS Schmitt detector
2-MOS output inverter
1-MOS reset
--------------------------
17 MOS total
```

The membrane capacitor is deliberately external to the physical core.

Nominal simulation uses:

```text
Cmem = 5 pF
```

More detail is provided in:

```text
docs/architecture.md
docs/circuit_design.md
```

---

## Weighted Electronic Synapse

The final synapse uses three identical PMOS unit-current cells.

Two digital inputs, `GATE_W0` and `GATE_W1`, implement four synaptic states:

| Code | Active unit cells | Relative weight |
|---|---:|---:|
| `00` | 0 | 0× |
| `01` | 1 | 1× |
| `10` | 2 | 2× |
| `11` | 3 | 3× |

Nominal delivered currents are:

| Weight | Current |
|---|---:|
| `00` | ~0.002 nA |
| `01` | ~103.734 nA |
| `10` | ~207.470 nA |
| `11` | ~311.206 nA |

The measured ratios are approximately:

```text
10 / 01 = 2.0000
11 / 01 = 3.0000
```

### Why identical unit cells?

During characterization, a single PMOS with twice the unit width did not produce twice the unit current under the tested implementation and bias conditions:

```text
Unit PMOS current       ≈ 103.738 nA
Single 2×-wide PMOS     ≈ 98.196 nA
Two identical unit PMOS ≈ 207.476 nA
```

The final 2× state therefore uses two identical unit devices in parallel.

This is an implementation-specific observation. It is not intended as a general claim that MOS current cannot scale with device width.

![Final weighted-synapse layout](figures/layout/klayout_weighted_synapse.png)

### Membrane Dynamics versus Synaptic Weight

The transistor-level transient response shows how the synaptic weight changes the membrane-voltage dynamics.

- `00` (0×): no firing; the membrane voltage decays below threshold
- `01` (1×): lowest nonzero synaptic drive and lowest nonzero firing rate
- `10` (2×): stronger synaptic drive and higher firing rate
- `11` (3×): strongest synaptic drive and highest firing rate

The dashed line marks the nominal rising Schmitt threshold:

```text
VTH_UP = 1.023948 V
```

The plotted waveforms are the original transistor-level simulation results; the added annotation area does not modify the waveform data.

![Membrane dynamics versus synaptic weight](figures/membrane_dynamics_vs_synaptic_weight_exact.png)

---

## Membrane, Leak and Threshold Detection

`VMEM` is the neuron state variable.

Synaptic current charges the external membrane capacitor while an NMOS leak transistor provides a continuously controllable discharge path.

Nominal leak-device dimensions:

```text
W = 0.42 µm
L = 1.00 µm
```

The leak strength is controlled externally through `VLEAK`.

Threshold detection uses a corrected six-transistor CMOS Schmitt topology.

The final simulated switching points are approximately:

```text
VTH_UP     = 1.023948 V
VTH_DOWN   = 0.824096 V
Hysteresis = 199.852 mV
```

The approximately 200 mV hysteresis window provides distinct rising and falling switching thresholds around the membrane transition.

---

## Spike Generation and Reset

The Schmitt stage generates the internal signal:

```text
VRAW
```

A CMOS inverter converts `VRAW` into the positive-going external signal:

```text
SPIKE
```

The reset transistor is:

```text
MN_RST VMEM SPIKE VSS VSS
```

When `SPIKE` rises, the reset NMOS discharges `VMEM` toward `VSS`.

A dedicated refractory-delay circuit is not included in this revision.

---

## Nominal Functional Response

The final nominal transistor-level simulation produced:

| Weight | Spike count | Firing rate |
|---|---:|---:|
| `00` | 0 | 0 Hz |
| `01` | 16 | 42.1 kHz |
| `10` | 39 | 102.6 kHz |
| `11` | 65 | 171.1 kHz |

Under nominal conditions, the firing response increases monotonically with synaptic weight.

---

## Robustness Characterization

The frozen transistor-level validation includes:

```text
Post-patch nominal validation       PASS
Functional numerical convergence   PASS
PVT operating points                27 / 27 PASS
Deterministic variation cases       13 / 13 PASS
```

### PVT acceptance criterion

A PVT operating point is considered passing when:

- the simulation completes successfully
- weight `00` remains silent
- weight `11` generates at least one valid output spike
- firing response is nondecreasing with increasing synaptic weight

Therefore, **27 / 27 PASS does not mean that intermediate weights `01` and `10` necessarily fire at every PVT corner**.

The deterministic 13-case variation study is not presented as a Monte Carlo mismatch analysis.

Frozen result summaries are available under:

```text
results/nominal/
results/synapse/
results/pvt/
results/variation/
```

Clean result-analysis notebooks are provided under:

```text
notebooks/
```

---

## Physical Implementation

The physical design was implemented in KLayout using the open SKY130 technology environment.

Frozen development environment:

```text
KLayout      0.30.12
Python       3.11.9
gdsfactory   8.4.0
kfactory     0.17.8
```

The physical implementation uses a dedicated seven-device MOS primitive library with explicit single-finger devices:

```text
nf = 1
interdig = 0
```

![SKY130 MOS primitive library](figures/layout/klayout_primitive_library.png)

The final full-neuron layout is shown below with the relevant KLayout layer view.

![Final neuron with KLayout layers](figures/layout/klayout_full_neuron_with_layers.png)

### Canonical physical artifact

```text
layout/neuron/neurolif_full_neuron_final_routed_v1.gds
```

Top cell:

```text
NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1
```

SHA-256:

```text
74fcc1478c50e2fd590d333e576c99fd1fec03d72c43f3679c15fd50e8d9a6de
```

The canonical GDS is treated as frozen.

A separate labelled derivative is used only for LVS extraction:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

---

## Physical Verification

Physical closure uses three complementary verification mechanisms.

### 1. Official SKY130 DRC

The final routed GDS was checked using the official SKY130 KLayout DRC deck.

Result:

```text
PASS
0 violations
```

![Final DRC result](figures/verification/klayout_final_drc_zero.png)

### 2. Independent geometry-based connectivity audit

A separate geometry-level audit checks:

- 17 expected MOS devices
- 14 intended logical conductor nets
- M1/VIA1/M2 connectivity
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

### 3. KLayout LVS

The labelled LVS derivative was extracted and compared against the intended 17-MOS reference schematic.

Final result:

```text
MOS total = 17 / 17
PFET      = 8 / 8
NFET      = 9 / 9

OFFICIAL RESULT:
NETLISTS MATCH
```

KLayout reported:

```text
INFO : Congratulations! Netlists match.
```

![Final LVS result](figures/verification/klayout_final_lvs_match.png)

Detailed evidence is preserved under:

```text
verification/neuron/
verification/synapse/
```

The machine-readable reports, logs, extracted netlists and JSON verification records are the primary verification evidence; screenshots are supporting presentation material.

---

## Why DRC Was Not Treated as Sufficient

During development, one intermediate VDD-routed layout passed DRC while an intended `MN_FB` electrical connection was still missing.

A later VRAW routing attempt also produced an unintended `VRAW`-to-`VSS` MET1 short that was isolated by the independent geometry audit.

These cases motivated the final verification strategy:

```text
DRC
 +
independent geometry/connectivity audit
 +
LVS
```

rather than relying on DRC alone.

---

## External Interface

The final core exposes eight top-level pins:

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

## Repository Structure

```text
NeuroLIF-SKY130/
│
├── circuit/       # reference and LVS schematics
├── docs/          # architecture, circuit, physical design and verification
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

Technical documentation:

```text
docs/architecture.md
docs/circuit_design.md
docs/physical_design.md
docs/verification.md
docs/reproducibility.md
```

---

## Reproducibility

The repository provides curated workflows for final verification and result inspection.

The following use the current public repository structure:

```text
public result-analysis notebooks
final standalone DRC runner
final standalone LVS runner
full-neuron connectivity audit
```

Final DRC runner:

```text
scripts/klayout/run_final_drc.py
```

Final LVS runner:

```text
scripts/klayout/run_final_lvs.py
```

Full-neuron connectivity audit:

```text
scripts/verification/neuron/
audit_full_neuron_connectivity_v1.py
```

The repository also preserves the successful physical-design lineage.

However, some historical intermediate GDS files and manifests are intentionally not included in the curated public release. The repository therefore should not be interpreted as a complete one-command reconstruction of every historical routing stage from a fresh clone.

See:

```text
docs/reproducibility.md
```

for the exact reproducibility boundary and frozen tool versions.

---

## Research Context

Neuromorphic silicon circuits use transistor-level physical dynamics to implement neuron-like state integration, thresholding and spike generation.

NeuroLIF-SKY130 is positioned as an educational open-PDK implementation of these ideas, with emphasis on transistor-level circuit behavior, weighted synaptic input, physical layout and reproducible verification.

The project is not presented as a new general neuron model or as a fabricated neuromorphic processor.

---

## References

1. C. Mead, “Neuromorphic Electronic Systems,” *Proceedings of the IEEE*, vol. 78, no. 10, pp. 1629–1636, 1990. DOI: 10.1109/5.58356.

2. G. Indiveri et al., “Neuromorphic Silicon Neuron Circuits,” *Frontiers in Neuroscience*, vol. 5, art. 73, 2011. DOI: 10.3389/fnins.2011.00073.

3. SkyWater Technology / Google, *SkyWater SKY130 Open Source PDK Documentation*.

---

## Scope and Limitations

NeuroLIF-SKY130 is a **pre-silicon educational neuromorphic circuit-design project**.

The repository supports claims of:

- transistor-level LIF-neuron simulation
- weighted-synapse characterization
- nominal functional validation
- defined PVT and deterministic-variation validation
- physical-layout implementation
- zero-violation official SKY130 DRC
- independent geometry/connectivity verification
- successful KLayout LVS

The repository does **not** claim:

- fabricated silicon
- tapeout
- measured post-silicon performance
- commercial manufacturing signoff
- Monte Carlo mismatch validation
- parasitic-extracted post-layout transient simulation

PEX and post-layout simulation remain possible future extensions.

---

## License

This repository is released under the MIT License.

See:

```text
LICENSE
```

for the complete license text.

---

## Citation

A machine-readable citation record is provided in:

```text
CITATION.cff
```

If this repository is used in academic or research work, please cite the project using that record.
