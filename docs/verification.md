# NeuroLIF-SKY130 Verification

## Overview

The final NeuroLIF-SKY130 physical core was verified using three complementary methods:

1. official SKY130 design-rule checking
2. independent geometry-based connectivity and topology auditing
3. official KLayout layout-versus-schematic comparison

These checks address different failure modes and are intentionally used together.

## Final Verified Core

Canonical physical GDS:

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

Final physical inventory:

```text
MOS devices             17
PFET                     8
NFET                     9
External pins            8
Logical conductor nets  14
```

The physical membrane capacitor is external by design.

## 1. Official SKY130 DRC

The final routed neuron was checked using the official SKY130 KLayout DRC deck.

Final result:

```text
Official SKY130 DRC
PASS

Violation count
0
```

The public repository preserves the corresponding report database and log under:

```text
verification/neuron/drc/
```

including:

```text
neurolif_full_neuron_final_routed_v1_drc.lyrdb
neurolif_full_neuron_final_routed_v1_drc.log
```

A standalone public reproduction runner is also provided:

```text
scripts/klayout/run_final_drc.py
```

The reproduced run returned:

```text
KLayout return code: 0
Violation count: 0

DRC_CLEAN = True
FINAL_DRC_REPRODUCTION_PASS = True
```

Fresh reproduction outputs are written separately under:

```text
verification/neuron/drc/reproduced/
```

so the original frozen verification evidence is not overwritten.

## Why DRC Alone Is Not Sufficient

DRC establishes geometric compliance with the technology rules, but it does not guarantee that every intended electrical connection is correct.

During development, an earlier VDD-routed version was DRC-clean while one intended `MN_FB` VDD connection was still missing.

This is why the project also includes an independent connectivity/topology audit and LVS.

## 2. Geometry-Based Connectivity and Topology Audit

The final routed GDS was independently analyzed at the conductor-geometry level.

Preserved audit record:

```text
verification/neuron/connectivity/
neurolif_full_neuron_final_connectivity_audit_v1.json
```

Final audit result:

```text
17 MOS devices           VERIFIED
14 logical nets          VERIFIED

Cross-net shorts         NONE DETECTED
Floating conductor nets  NONE DETECTED

Weighted synapse         VERIFIED
Schmitt + buffer         VERIFIED
Leak path                VERIFIED
SPIKE reset feedback     VERIFIED

PMOS body / NWELL        VERIFIED
NMOS substrate / VSS     VERIFIED

Physical Cmem            EXTERNAL BY DESIGN
```

Final audit status:

```text
STEP39A_PASS = True
```

The corresponding public audit script is:

```text
scripts/verification/neuron/
audit_full_neuron_connectivity_v1.py
```

The public full-neuron connectivity audit now uses the curated repository paths for the reference schematic, final DRC evidence and connectivity output.

The preserved JSON audit record remains authoritative for the frozen final design.

## 3. KLayout LVS

LVS uses the verification-only labelled derivative:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

Top cell:

```text
NEUROLIF_FULL_NEURON_LVS_V1
```

Reference schematic:

```text
circuit/lvs/
neurolif_full_neuron_lvs_reference_v1.spice
```

The derivative adds the eight required extraction labels:

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

The labelled LVS derivative does not replace the canonical physical GDS.

## LVS Result

The official KLayout/SKY130 comparison returned:

```text
Return code: 0

Success message found  : True
Mismatch message found : False

OFFICIAL RESULT:
NETLISTS MATCH
```

Authoritative KLayout message:

```text
INFO : Congratulations! Netlists match.
```

Extracted inventory:

```text
MOS total = 17 / 17
PFET      = 8 / 8
NFET      = 9 / 9
```

All expected top-level pins were present:

```text
VDD      True
VSS      True
VBIAS    True
GATE_W0  True
GATE_W1  True
VLEAK    True
VMEM     True
SPIKE    True
```

Final status:

```text
STEP40B_PASS = True
```

The preserved LVS evidence is stored under:

```text
verification/neuron/lvs/
```

including:

```text
neurolif_full_neuron_lvs_v1.log
neurolif_full_neuron_lvs_v1.lvsdb
neurolif_full_neuron_extracted_v1.cir
```

## LVS Reproduction Runner

The standalone public reproduction script is:

```text
scripts/klayout/run_final_lvs.py
```

A fresh reproduction run returned:

```text
Success message found  : True
Mismatch message found : False
Extracted MOS count    : 17 / 17

VDD      True
VSS      True
VBIAS    True
GATE_W0  True
GATE_W1  True
VLEAK    True
VMEM     True
SPIKE    True

LVS_PASS = True

OFFICIAL RESULT: NETLISTS MATCH
FINAL_LVS_REPRODUCTION_PASS = True
```

The reproduced results are written separately under:

```text
verification/neuron/lvs/reproduced/
```

so the preserved original LVS evidence remains unchanged.

## Verification Reproducibility Boundary

The final DRC and LVS reproduction runners use repository-relative project paths, while the full-neuron connectivity audit has also been normalized to the curated repository structure.

Historical step-by-step construction scripts are preserved as part of the design lineage. Some of those scripts depend on intermediate GDS files or manifests that are intentionally not included in the curated public repository.

For example, the final-routing manifest preserves a historical input reference to:

```text
layout/neuron/neurolif_full_neuron_spike_v1.gds
```

This intermediate artifact is not part of the curated release.

Therefore, the repository should not be interpreted as a complete replay of every intermediate physical-design stage from a fresh clone.

The frozen final verification artifacts and machine-readable verification records remain the authoritative evidence for the released design.

## Weighted-Synapse Verification

The weighted synapse was independently closed before full-neuron integration.

Canonical synapse layout:

```text
layout/synapse/neurolif_synapse_vss_v1.gds
```

Final synapse verification status:

```text
Fully routed                         PASS
Official SKY130 DRC                 0 violations
Geometry connectivity/topology     PASS
Cross-net shorts                    None detected
Body ties                           Verified
PMOS common NWELL                   Verified
KLayout LVS                         Netlists match
```

The corresponding verification evidence is preserved under:

```text
verification/synapse/
```

## Final Machine-Readable Verification Record

The final physical-verification record is:

```text
verification/neuron/
neurolif_full_neuron_final_verification_v1.json
```

It records:

```text
Transistor topology          VERIFIED

MOS count                    17 / 17
PFET / NFET                  8 / 9

All routing stages           COMPLETE

Official SKY130 DRC          PASS - 0 violations

Connectivity/topology audit  PASS

Logical conductor nets       14 / 14

Cross-net shorts             NONE DETECTED
Floating conductor nets      NONE DETECTED

Body/well connectivity       PASS

Official KLayout LVS         PASS - NETLISTS MATCH

Top-level pins               PASS

Physical Cmem                EXTERNAL BY DESIGN

FINAL_VERIFICATION_PASS      True
```

Final project status:

```text
NEUROLIF-SKY130 - PHYSICAL CORE CLOSED
```

## Verification Summary

| Verification item | Result |
|---|---|
| Official SKY130 DRC | PASS |
| DRC violations | 0 |
| Geometry connectivity audit | PASS |
| Logical conductor nets | 14 / 14 |
| Cross-net shorts | None detected |
| Floating conductor nets | None detected |
| Body/well connectivity | PASS |
| Official KLayout LVS | PASS |
| LVS comparison | Netlists match |
| Extracted MOS | 17 / 17 |
| External pins | 8 / 8 |

## Evidence Figures

Visual verification evidence is stored under:

```text
figures/verification/
```

including:

```text
klayout_final_drc_zero.png
klayout_final_lvs_match.png
```

These screenshots are supporting presentation evidence.

The machine-readable logs, report databases, extracted netlists and audit records remain the primary verification artifacts.

Machine-specific absolute filesystem paths in public logs and report databases have been replaced with neutral placeholders such as:

```text
<REPO_ROOT>
<DEV_ROOT>
<USER_HOME>
```

where applicable.

This sanitization changes only path metadata and does not alter the underlying verification results.

## Scope of the Verification Claim

The supported claim is:

> The NeuroLIF-SKY130 transistor-level neuron core is fully routed, passes the official SKY130 DRC with zero violations, passes an independent geometry-based connectivity/topology audit and passes KLayout LVS against the intended 17-MOS reference schematic.

This remains a pre-silicon educational SKY130 design.

The repository does not claim:

- fabricated silicon
- tapeout
- measured post-silicon performance
- production signoff
- post-layout parasitic simulation

Parasitic extraction and post-layout transient simulation remain possible future extensions.
