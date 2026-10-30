# NeuroLIF-SKY130 Verification

## Overview

The final NeuroLIF-SKY130 physical core was verified using three complementary methods:

1. official SKY130 design-rule checking
2. independent geometry-based connectivity and topology auditing
3. official KLayout layout-versus-schematic comparison

These checks address different failure modes and are intentionally used together.

## Final Verified Core

Canonical physical GDS:

```text id="2htmtt"
layout/neuron/neurolif_full_neuron_final_routed_v1.gds
```

Top cell:

```text id="5quu0e"
NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1
```

Canonical SHA-256:

```text id="kpyx2q"
74fcc1478c50e2fd590d333e576c99fd1fec03d72c43f3679c15fd50e8d9a6de
```

Final physical inventory:

```text id="26r6ht"
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

```text id="pqmmsi"
Official SKY130 DRC
PASS

Violation count
0
```

The public repository preserves the corresponding report database and log under:

```text id="96apht"
verification/neuron/drc/
```

including:

```text id="wej4hw"
neurolif_full_neuron_final_routed_v1_drc.lyrdb
neurolif_full_neuron_final_routed_v1_drc.log
```

A standalone public reproduction runner is also provided:

```text id="pjnfja"
scripts/klayout/run_final_drc.py
```

The reproduced run returned:

```text id="c0g71e"
KLayout return code: 0
Violation count: 0

DRC_CLEAN = True
FINAL_DRC_REPRODUCTION_PASS = True
```

Fresh reproduction outputs are written separately under:

```text id="t8pk3v"
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

```text id="qoqnj4"
verification/neuron/connectivity/
neurolif_full_neuron_final_connectivity_audit_v1.json
```

Final audit result:

```text id="rg1h9b"
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

```text id="qi0nfc"
STEP39A_PASS = True
```

The corresponding public audit script is:

```text id="w2vo1k"
scripts/verification/neuron/
audit_full_neuron_connectivity_v1.py
```

The preserved JSON record is authoritative for the frozen final design.

The audit script was originally developed against the development-directory layout. Until its remaining path assumptions are normalized to the curated public repository structure, it should not be described as a guaranteed one-command fresh-clone reproduction step.

## 3. KLayout LVS

LVS uses the verification-only labelled derivative:

```text id="1zkrjt"
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

Top cell:

```text id="797xb8"
NEUROLIF_FULL_NEURON_LVS_V1
```

Reference schematic:

```text id="4d31vo"
circuit/lvs/
neurolif_full_neuron_lvs_reference_v1.spice
```

The derivative adds the eight required extraction labels:

```text id="w72oo6"
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

```text id="smajut"
Return code: 0

Success message found  : True
Mismatch message found : False

OFFICIAL RESULT:
NETLISTS MATCH
```

Authoritative KLayout message:

```text id="zx1wx7"
INFO : Congratulations! Netlists match.
```

Extracted inventory:

```text id="8x1ggi"
MOS total = 17 / 17
PFET      = 8 / 8
NFET      = 9 / 9
```

All expected top-level pins were present:

```text id="ndbc7g"
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

```text id="gqrcpj"
STEP40B_PASS = True
```

The preserved LVS evidence is stored under:

```text id="o1be2z"
verification/neuron/lvs/
```

including:

```text id="niz2d6"
neurolif_full_neuron_lvs_v1.log
neurolif_full_neuron_lvs_v1.lvsdb
neurolif_full_neuron_extracted_v1.cir
```

## LVS Reproduction Runner

The standalone public reproduction script is:

```text id="2797hl"
scripts/klayout/run_final_lvs.py
```

A fresh reproduction run returned:

```text id="hurbdf"
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

```text id="n09m2y"
verification/neuron/lvs/reproduced/
```

so the preserved original LVS evidence remains unchanged.

## Weighted-Synapse Verification

The weighted synapse was independently closed before full-neuron integration.

Canonical synapse layout:

```text id="82md47"
layout/synapse/neurolif_synapse_vss_v1.gds
```

Final synapse verification status:

```text id="ejrxuc"
Fully routed                         PASS
Official SKY130 DRC                  0 violations
Geometry connectivity/topology      PASS
Cross-net shorts                     None detected
Body ties                            Verified
PMOS common NWELL                    Verified
KLayout LVS                          Netlists match
```

The corresponding verification evidence is preserved under:

```text id="so0crb"
verification/synapse/
```

## Final Machine-Readable Verification Record

The final physical-verification record is:

```text id="eajq9r"
verification/neuron/
neurolif_full_neuron_final_verification_v1.json
```

It records:

```text id="95q9iw"
Transistor topology          VERIFIED

MOS count                    17 / 17
PFET / NFET                  8 / 9

All routing stages           COMPLETE

Official SKY130 DRC          PASS — 0 violations

Connectivity/topology audit  PASS

Logical conductor nets       14 / 14

Cross-net shorts             NONE DETECTED
Floating conductor nets      NONE DETECTED

Body/well connectivity       PASS

Official KLayout LVS         PASS — NETLISTS MATCH

Top-level pins               PASS

Physical Cmem                EXTERNAL BY DESIGN

FINAL_VERIFICATION_PASS      True
```

Final project status:

```text id="1gom8d"
NEUROLIF-SKY130 — PHYSICAL CORE CLOSED
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

```text id="ivdcnk"
figures/verification/
```

including:

```text id="nw8ss0"
klayout_final_drc_zero.png
klayout_final_lvs_match.png
```

These screenshots are supporting presentation evidence.

The machine-readable logs, report databases, extracted netlists and audit records remain the primary verification artifacts.

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