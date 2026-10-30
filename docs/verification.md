\# NeuroLIF-SKY130 Verification



\## Overview



The final NeuroLIF-SKY130 physical core was verified using three complementary methods:



1\. official SKY130 design-rule checking

2\. independent geometry-based connectivity and topology auditing

3\. official KLayout layout-versus-schematic comparison



These checks address different failure modes and are intentionally used together.



\## Final Verified Core



Canonical physical GDS:



```text

layout/neuron/neurolif\_full\_neuron\_final\_routed\_v1.gds

```



Top cell:



```text

NEUROLIF\_FULL\_NEURON\_FINAL\_ROUTED\_V1

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



\## 1. Official SKY130 DRC



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

neurolif\_full\_neuron\_final\_routed\_v1\_drc.lyrdb

neurolif\_full\_neuron\_final\_routed\_v1\_drc.log

```



A public reproduction runner is also provided:



```text

scripts/klayout/run\_final\_drc.py

```



The reproduced run independently returned:



```text

KLayout return code: 0

Violation count: 0

DRC\_CLEAN = True

FINAL\_DRC\_REPRODUCTION\_PASS = True

```



Reproduced outputs are written separately under:



```text

verification/neuron/drc/reproduced/

```



so the original frozen verification evidence is not overwritten.



\## Why DRC Alone Is Not Sufficient



DRC establishes geometric compliance with the technology rules, but it does not guarantee that every intended electrical connection is correct.



During development, an earlier VDD-routed version was DRC-clean while one intended `MN\_FB` VDD connection was still missing.



This is why the project also includes an independent connectivity audit and LVS.



\## 2. Geometry-Based Connectivity and Topology Audit



The final routed GDS was independently analyzed at the conductor-geometry level.



Audit record:



```text

verification/neuron/connectivity/

neurolif\_full\_neuron\_final\_connectivity\_audit\_v1.json

```



Final audit result:



```text

17 MOS devices          VERIFIED

14 logical nets         VERIFIED



Cross-net shorts        NONE DETECTED

Floating conductor nets NONE DETECTED



Weighted synapse        VERIFIED

Schmitt + buffer        VERIFIED

Leak path               VERIFIED

SPIKE reset feedback    VERIFIED



PMOS body / NWELL       VERIFIED

NMOS substrate / VSS    VERIFIED



Physical Cmem           EXTERNAL BY DESIGN

```



Final status:



```text

STEP39A\_PASS = True

```



The corresponding public audit script is:



```text

scripts/verification/neuron/

audit\_full\_neuron\_connectivity\_v1.py

```



\## 3. KLayout LVS



LVS uses the verification-only labelled derivative:



```text

layout/neuron/neurolif\_full\_neuron\_lvs\_v1.gds

```



Top cell:



```text

NEUROLIF\_FULL\_NEURON\_LVS\_V1

```



Reference schematic:



```text

circuit/lvs/

neurolif\_full\_neuron\_lvs\_reference\_v1.spice

```



The derivative adds the eight required extraction labels:



```text

VDD

VSS

VBIAS

GATE\_W0

GATE\_W1

VLEAK

VMEM

SPIKE

```



The labelled LVS derivative does not replace the canonical physical GDS.



\## LVS Result



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

GATE\_W0  True

GATE\_W1  True

VLEAK    True

VMEM     True

SPIKE    True

```



Final status:



```text

STEP40B\_PASS = True

```



The preserved LVS evidence is stored under:



```text

verification/neuron/lvs/

```



including:



```text

neurolif\_full\_neuron\_lvs\_v1.log

neurolif\_full\_neuron\_lvs\_v1.lvsdb

neurolif\_full\_neuron\_extracted\_v1.cir

```



\## LVS Reproduction Runner



The public reproduction script is:



```text

scripts/klayout/run\_final\_lvs.py

```



A fresh reproduction run returned:



```text

Success message found  : True

Mismatch message found : False

Extracted MOS count    : 17 / 17



VDD      True

VSS      True

VBIAS    True

GATE\_W0  True

GATE\_W1  True

VLEAK    True

VMEM     True

SPIKE    True



LVS\_PASS = True



OFFICIAL RESULT: NETLISTS MATCH

FINAL\_LVS\_REPRODUCTION\_PASS = True

```



The reproduced results are written separately under:



```text

verification/neuron/lvs/reproduced/

```



\## Weighted-Synapse Verification



The weighted synapse was independently closed before full-neuron integration.



Canonical synapse layout:



```text

layout/synapse/neurolif\_synapse\_vss\_v1.gds

```



Final synapse verification status:



```text

Fully routed                         PASS

Official SKY130 DRC                  0 violations

Geometry connectivity/topology      PASS

Cross-net shorts                     None detected

Body ties                            Verified

PMOS common NWELL                    Verified

KLayout LVS                          Netlists match

```



The corresponding evidence is preserved under:



```text

verification/synapse/

```



\## Final Machine-Readable Verification Record



The final physical-verification record is:



```text

verification/neuron/

neurolif\_full\_neuron\_final\_verification\_v1.json

```



It records:



```text

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



FINAL\_VERIFICATION\_PASS      True

```



Final project status:



```text

NEUROLIF-SKY130 — PHYSICAL CORE CLOSED

```



\## Verification Summary



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



\## Evidence Figures



The repository includes visual verification evidence under:



```text

figures/verification/

```



including:



```text

klayout\_final\_drc\_zero.png

klayout\_final\_lvs\_match.png

```



These screenshots are supporting presentation evidence.



The machine-readable logs, report databases, extracted netlists and audit records remain the primary verification artifacts.



\## Scope of the Verification Claim



The supported claim is:



> The NeuroLIF-SKY130 transistor-level neuron core is fully routed, passes the official SKY130 DRC with zero violations, passes an independent geometry-based connectivity/topology audit and passes KLayout LVS against the intended 17-MOS reference schematic.



This remains a pre-silicon educational SKY130 design.



The repository does not claim:



\- fabricated silicon

\- tapeout

\- measured post-silicon performance

\- production signoff

\- post-layout parasitic simulation

