\# NeuroLIF-SKY130 Reproducibility



\## Purpose



This document describes the environment and public workflow required to inspect and reproduce the main NeuroLIF-SKY130 physical-design and verification artifacts.



The repository is intended to be reproducible without bundling the SKY130 PDK, KLayout installation or local virtual environment.



\## Frozen Tool Versions



The physical-design flow was developed with:



```text

KLayout 0.30.12

Python 3.11.9

gdsfactory 8.4.0

kfactory 0.17.8

```



The project should be reproduced with these versions where practical.



Upgrading packages may alter generated geometry, APIs or serialization behavior.



\## SKY130 Environment



Technology:



```text

Efabless SKY130

```



The KLayout technology tree used during development followed the standard structure:



```text

KLayout/

└── salt/

&#x20;   └── Efabless\_sky130/

&#x20;       └── tech/

&#x20;           └── sky130/

&#x20;               ├── python/

&#x20;               ├── drc/

&#x20;               └── lvs/

```



The public repository does not include the PDK.



Users must install the SKY130 KLayout technology separately.



\## Simulation PDK Version



The transistor-level simulation environment used a pinned SKY130 PDK revision:



```text

44a43c23c81b45b8e774ae7a84899a5a778b6b0b

```



This commit is provided for reproducibility of transistor-level simulation behavior.



The repository does not redistribute the PDK itself.



\## Repository Layout



Important reproducibility directories are:



```text

circuit/

layout/

scripts/

verification/

results/

notebooks/

figures/

```



The physical construction scripts are under:



```text

scripts/physical/

```



Verification scripts are under:



```text

scripts/verification/

scripts/klayout/

```



\## Canonical Physical Artifact



The frozen final physical layout is:



```text

layout/neuron/

neurolif\_full\_neuron\_final\_routed\_v1.gds

```



Top cell:



```text

NEUROLIF\_FULL\_NEURON\_FINAL\_ROUTED\_V1

```



Canonical SHA-256:



```text

74fcc1478c50e2fd590d333e576c99fd1fec03d72c43f3679c15fd50e8d9a6de

```



This file should not be replaced by the LVS derivative.



\## LVS Derivative



The verification-only labelled LVS layout is:



```text

layout/neuron/

neurolif\_full\_neuron\_lvs\_v1.gds

```



Top cell:



```text

NEUROLIF\_FULL\_NEURON\_LVS\_V1

```



This file exists specifically for extraction and LVS.



The canonical physical GDS remains the authoritative layout artifact.



\## Python Path Handling



The public Python scripts use repository-relative paths for project files.



Typical pattern:



```python

from pathlib import Path



ROOT = Path(\_\_file\_\_).resolve().parents\[3]

```



Local tool installations use the current user's home directory rather than a hard-coded username.



For example:



```python

Path.home() / "KLayout" / "salt" / "Efabless\_sky130"

```



This avoids publishing machine-specific paths.



\## Primitive Generation



The public primitive-generation flow begins with:



```text

scripts/physical/primitives/

build\_neurolif\_primitives\_nf1.py

```



The final primitive library contains:



```text

N\_LOGIC

P\_LOGIC

N\_FB

P\_FB

P\_SYN

N\_LEAK

N\_RESET

```



All final MOS primitives use:



```text

nf = 1

interdig = 0

```



The generated canonical library is:



```text

layout/primitives/

neurolif\_mos\_primitives\_nf1.gds

```



\## Weighted-Synapse Construction



The public weighted-synapse construction sequence is:



```text

build\_synapse\_placement\_v1.py

route\_synapse\_vdd\_v1.py

route\_synapse\_vbias\_v1.py

route\_synapse\_branches\_v2.py

route\_synapse\_vmem\_v1.py

route\_synapse\_weight\_gates\_v2.py

route\_synapse\_vss\_v1.py

```



The canonical completed synapse is:



```text

layout/synapse/

neurolif\_synapse\_vss\_v1.gds

```



\## Full-Neuron Construction



The public full-neuron construction sequence includes:



```text

build\_full\_neuron\_reference\_v1.py

build\_full\_neuron\_placement\_v1.py



route\_full\_neuron\_vdd\_v2.py

route\_full\_neuron\_vdd\_v3.py

route\_full\_neuron\_vss\_v1.py

route\_full\_neuron\_vmem\_v1.py

route\_full\_neuron\_vleak\_v1.py

route\_full\_neuron\_pmid\_v2.py

route\_full\_neuron\_nmid\_v1.py

route\_full\_neuron\_vraw\_v2.py

route\_full\_neuron\_spike\_v1.py

route\_full\_neuron\_reset\_gate\_v1.py

```



`route\_full\_neuron\_vdd\_v2.py` is intentionally retained because the final VDD routing script depends on its output.



Rejected debug routing versions are not included in the main public construction sequence.



\## GDS Serialization



During development, explicit layer mapping was required when writing final GDS/OASIS files.



The established pattern is:



```python

save\_options = kdb.SaveLayoutOptions()

save\_options.format = "GDS2"

save\_options.deselect\_all\_layers()



for layer\_index, gds\_layer, datatype, name in populated\_layers:

&#x20;   save\_options.add\_layer(

&#x20;       layer\_index,

&#x20;       kdb.LayerInfo(

&#x20;           int(gds\_layer),

&#x20;           int(datatype),

&#x20;       ),

&#x20;   )



layout.write(

&#x20;   str(OUTPUT\_GDS),

&#x20;   save\_options,

)

```



Equivalent explicit layer mapping is used for OASIS serialization.



\## DRC Reproduction



Public runner:



```text

scripts/klayout/run\_final\_drc.py

```



The script checks:



```text

layout/neuron/

neurolif\_full\_neuron\_final\_routed\_v1.gds

```



using the official SKY130 KLayout DRC deck.



The expected result is:



```text

KLayout return code: 0

Violation count: 0



DRC\_CLEAN = True

FINAL\_DRC\_REPRODUCTION\_PASS = True

```



Fresh reproduction results are written to:



```text

verification/neuron/drc/reproduced/

```



The preserved original verification evidence under:



```text

verification/neuron/drc/

```



is not overwritten.



\## LVS Reproduction



Public runner:



```text

scripts/klayout/run\_final\_lvs.py

```



The layout input is:



```text

layout/neuron/

neurolif\_full\_neuron\_lvs\_v1.gds

```



Reference schematic:



```text

circuit/lvs/

neurolif\_full\_neuron\_lvs\_reference\_v1.spice

```



Expected result:



```text

KLayout return code: 0



Success message found  : True

Mismatch message found : False



Extracted MOS count    : 17 / 17



LVS\_PASS = True



OFFICIAL RESULT: NETLISTS MATCH

FINAL\_LVS\_REPRODUCTION\_PASS = True

```



Fresh LVS reproduction outputs are written to:



```text

verification/neuron/lvs/reproduced/

```



\## Connectivity Audit



The independent geometry-based connectivity check is:



```text

scripts/verification/neuron/

audit\_full\_neuron\_connectivity\_v1.py

```



The final audit record is:



```text

verification/neuron/connectivity/

neurolif\_full\_neuron\_final\_connectivity\_audit\_v1.json

```



Expected final properties include:



```text

17 MOS devices

14 logical conductor nets

No cross-net shorts

No floating conductor nets

Correct weighted-synapse topology

Correct Schmitt/buffer/reset topology

Correct body/well connectivity

```



\## Public Results



The concise public result files are:



```text

results/nominal/

nominal\_summary.json



results/synapse/

weight\_current\_summary.csv



results/pvt/

pvt\_27point\_summary.csv



results/variation/

variation\_13case\_summary.csv

```



These files contain the final validated results only.



The stale development result archive is intentionally excluded.



\## Public Notebooks



The public notebooks are:



```text

notebooks/

01\_neurolif\_nominal\_validation.ipynb



02\_weighted\_synapse\_characterization.ipynb



03\_pvt\_and\_variation\_analysis.ipynb

```



These notebooks read the frozen public result files and reproduce the main tables and plots.



They are intentionally cleaner than the original development notebook and do not contain obsolete debugging experiments.



\## Nominal Validation



Expected final nominal values include:



```text

VTH\_UP   = 1.023948 V

VTH\_DOWN = 0.824096 V

Hysteresis = 199.852 mV

```



Final synaptic currents:



```text

00 =   0.002 nA

01 = 103.734 nA

10 = 207.470 nA

11 = 311.206 nA

```



Expected scaling:



```text

10 / 01 ≈ 2

11 / 01 ≈ 3

```



\## Robustness Validation



The frozen transistor-level validation status is:



```text

Post-patch nominal validation      PASS

Functional numerical convergence  PASS

PVT sweep                          27 / 27 PASS

Deterministic variation            13 / 13 PASS

```



The deterministic variation sweep is not a Monte Carlo mismatch study.



\## Verification Evidence



The repository preserves:



```text

DRC report databases

DRC logs

Connectivity audit JSON

LVS databases

Extracted netlists

LVS logs

Final verification JSON records

```



Visual supporting evidence is under:



```text

figures/layout/

figures/verification/

```



\## Reproducibility Boundary



Reproducing this repository requires third-party software and PDK components that are not included here.



Users are responsible for installing and complying with the licenses of:



\- KLayout

\- SKY130 / Efabless SKY130 technology files

\- Python

\- gdsfactory

\- kfactory

\- ngspice and related simulation dependencies



\## Project Scope



NeuroLIF-SKY130 is a pre-silicon educational neuromorphic circuit-design project.



The current reproducible claim covers:



\- transistor-level simulation validation

\- weighted-synapse characterization

\- staged physical implementation

\- official SKY130 DRC

\- independent geometry connectivity auditing

\- KLayout LVS



The repository does not claim:



\- fabricated silicon

\- tapeout

\- measured silicon results

\- production manufacturing signoff

\- parasitic-extracted post-layout transient simulation



PEX and post-layout simulation are reserved as future extensions.

