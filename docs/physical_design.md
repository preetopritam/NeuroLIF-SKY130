# NeuroLIF-SKY130 Physical Design

## Overview

The NeuroLIF-SKY130 physical implementation was developed in KLayout using the open SKY130 technology.

The final core contains the complete routed 17-MOS neuron:

- 7-MOS weighted synapse
- 1 NMOS leak device
- 6-transistor Schmitt detector
- 2-transistor CMOS output buffer
- 1 NMOS reset device

The physical membrane capacitor is intentionally external to the core.

## Tool Environment

The final physical-design environment used:

```text
KLayout 0.30.12
Python 3.11.9
gdsfactory 8.4.0
kfactory 0.17.8
Technology: Efabless SKY130
```

The physical implementation uses the SKY130 technology installation available through KLayout.

## Canonical MOS Primitive Library

The final physical flow begins from a dedicated MOS primitive library:

```text
layout/primitives/neurolif_mos_primitives_nf1.gds
```

The library contains seven device types:

| Primitive | W (µm) | L (µm) |
|---|---:|---:|
| N_LOGIC | 1.00 | 0.15 |
| P_LOGIC | 2.00 | 0.15 |
| N_FB | 0.42 | 0.30 |
| P_FB | 0.42 | 0.30 |
| P_SYN | 0.84 | 0.50 |
| N_LEAK | 0.42 | 1.00 |
| N_RESET | 1.20 | 0.15 |

All final primitives use:

```text
nf = 1
interdig = 0
```

An earlier primitive library was rejected because the PMOS generator produced a multi-finger implementation inconsistent with the intended device topology.

## Body and Well Connections

The final body-tie strategy uses standalone substrate and well taps.

```text
n_tap → PMOS / NWELL body connection → VDD
p_tap → NMOS substrate connection    → VSS
```

This approach passed the official SKY130 DRC and was retained throughout the final layout.

## Weighted Synapse Layout

The canonical weighted-synapse layout is:

```text
layout/synapse/neurolif_synapse_vss_v1.gds
```

The final synapse contains three identical PMOS unit-current devices together with the corresponding switching devices.

The physical synapse was completed and verified before integration into the full neuron.

Final synapse status:

```text
Fully routed                         PASS
Official SKY130 DRC                  0 violations
Geometry connectivity/topology      PASS
Cross-net shorts                     None detected
PMOS common NWELL                    Verified
Body ties                            Verified
KLayout LVS                          Netlists match
```

## Full-Neuron Placement

The full neuron integrates the closed weighted synapse together with the leak device, Schmitt detector, output buffer and reset transistor.

The physical design was routed in multiple stages rather than generated as one monolithic layout.

The principal routing sequence was:

```text
Placement
   ↓
VDD
   ↓
VSS
   ↓
VMEM
   ↓
VLEAK
   ↓
P_MID
   ↓
N_MID
   ↓
VRAW
   ↓
SPIKE output
   ↓
SPIKE → reset-gate connection
```

This staged flow makes each major conductor network independently inspectable.

## Routing Layers

The final design uses multiple physical and routing layers including:

```text
POLY
MET1
VIA1
MET2
```

The public KLayout screenshots show the routed metal network together with transistor and process geometry.

The final presentation convention uses:

```text
MET1  → cyan
MET2  → blue
VIA1  → yellow
POLY  → red
```

These colors are presentation settings only and do not alter the GDS content.

## Routing Debugging and Engineering Checks

Several routing iterations were required before final closure.

### VDD

An earlier VDD-routed version was DRC-clean but electrically incomplete because the `MN_FB` VDD connection was missing.

A later routing revision corrected this omission.

This demonstrated that DRC alone is insufficient to establish electrical correctness.

### P_MID

An earlier `P_MID` routing version produced two MET1 notch violations.

The final `P_MID` routing revision corrected those geometries and returned to zero DRC violations.

### VRAW

An earlier `VRAW` route produced a real MET1 short between `VRAW` and `VSS`.

The final revision moved the crossing through MET2 and VIA1, eliminating the short and restoring both DRC and connectivity correctness.

These rejected routing versions are not part of the public final design flow.

## Canonical Final Physical Artifact

The frozen final physical GDS is:

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

This GDS is the canonical physical artifact and should be treated as immutable.

## LVS Derivative

LVS uses a separate verification-only derivative:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

Top cell:

```text
NEUROLIF_FULL_NEURON_LVS_V1
```

This derivative adds the required top-level extraction labels:

```text
VDD
VSS
VBIAS
GATE_W0
GATE_W1
VLEAK
VMEM
SPIKE
```

The LVS derivative does not replace the canonical physical GDS.

The physical geometry was checked to remain unchanged apart from the verification labels.

## Final Physical Inventory

The closed neuron contains:

```text
MOS devices             17
PFET                     8
NFET                     9
External pins            8
Logical conductor nets  14
```

The physical membrane capacitor is external by design.

## Final Physical Verification

The final physical core passed:

```text
Official SKY130 DRC
PASS
0 violations

Independent geometry-based connectivity/topology audit
PASS

Cross-net shorts
None detected

Floating conductor nets
None detected

Body/well connectivity
PASS

Official KLayout LVS
PASS
Netlists match
```

## Public Physical-Design Scripts

The repository preserves the principal construction sequence under:

```text
scripts/physical/
```

This includes:

- primitive generation
- synapse placement and routing
- full-neuron placement
- staged routing of power, membrane and internal nodes
- final reset-path routing

The public scripts use curated repository paths for shared public references and final verification inputs. The final standalone DRC and LVS reproduction runners and the full-neuron connectivity audit use repository-relative project paths rather than personal machine-specific paths.

Some historical construction stages still depend on intermediate GDS files or manifests that are intentionally not included in the curated public release. This is an artifact-retention boundary rather than a path-normalization defect.
## Scope and Limitations

This is a pre-silicon educational physical-design implementation using the open SKY130 PDK.

The project does not claim:

- fabricated silicon
- tapeout
- measured post-silicon results
- signoff for commercial manufacturing

Parasitic extraction and post-layout transient simulation remain possible future extensions.
