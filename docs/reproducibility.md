# NeuroLIF-SKY130 Reproducibility

## Purpose

This document describes the environment, repository structure and public workflow for inspecting and reproducing the main NeuroLIF-SKY130 simulation, physical-design and verification artifacts.

The repository does not bundle the SKY130 PDK, KLayout installation, Python virtual environment or other third-party dependencies. These must be installed separately.

The current public repository supports direct reproduction of the final DRC and LVS checks. The complete historical physical-construction chain is also preserved, but some older verification/construction scripts may require path normalization before they can be executed end-to-end from a fresh clone.

## Frozen Tool Versions

The physical-design flow was developed using:

```text
KLayout 0.30.12
Python 3.11.9
gdsfactory 8.4.0
kfactory 0.17.8
```

These versions are recommended where practical because changes in package versions may affect APIs, generated geometry or layout serialization.

## SKY130 Environment

Physical design and verification use the Efabless SKY130 technology environment.

A typical KLayout technology installation has a structure similar to:

```text
KLayout/
└── salt/
    └── Efabless_sky130/
        └── tech/
            └── sky130/
                ├── python/
                ├── drc/
                └── lvs/
```

The SKY130 technology files are not included in this repository.

Users must install the required SKY130 KLayout technology separately.

## Simulation PDK Version

The transistor-level simulation workflow used the pinned SKY130 PDK revision:

```text
44a43c23c81b45b8e774ae7a84899a5a778b6b0b
```

This revision is recorded to improve reproducibility of the transistor-level simulation behavior.

The repository does not redistribute the PDK.

## Repository Layout

The main public directories are:

```text
circuit/
docs/
figures/
layout/
notebooks/
results/
scripts/
verification/
```

Their roles are:

```text
circuit/       reference and LVS schematics
layout/        canonical GDS/OASIS artifacts
notebooks/     clean analysis notebooks
results/       frozen simulation-result summaries
scripts/       construction and verification scripts
verification/  DRC, connectivity and LVS evidence
figures/       presentation and verification figures
docs/          technical documentation
```

## Canonical Physical Artifact

The authoritative final routed layout is:

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

This file is the canonical physical artifact and should not be replaced by the LVS-labelled derivative.

## LVS Derivative

The verification-only labelled layout is:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

Top cell:

```text
NEUROLIF_FULL_NEURON_LVS_V1
```

This file adds the top-level labels required for extraction and LVS.

It does not replace the canonical final routed GDS.

## Path Handling

Public scripts should use repository-relative paths for project artifacts rather than machine-specific absolute paths.

A typical pattern is:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT_DIR = ROOT / "layout" / "neuron"
VERIFY_DIR = ROOT / "verification" / "neuron"
```

Tool installations may be located using the current user's home directory where appropriate:

```python
from pathlib import Path

SKY130_ROOT = (
    Path.home()
    / "KLayout"
    / "salt"
    / "Efabless_sky130"
    / "tech"
    / "sky130"
)
```

No public script should require a hard-coded personal username.

## Canonical MOS Primitive Library

The final primitive library is:

```text
layout/primitives/neurolif_mos_primitives_nf1.gds
```

The seven device types are:

```text
N_LOGIC
P_LOGIC
N_FB
P_FB
P_SYN
N_LEAK
N_RESET
```

All final MOS primitives use:

```text
nf = 1
interdig = 0
```

The public primitive-generation script is located under:

```text
scripts/physical/primitives/
```

## Weighted-Synapse Construction

The weighted-synapse physical flow consists of:

```text
build_synapse_placement_v1.py
route_synapse_vdd_v1.py
route_synapse_vbias_v1.py
route_synapse_branches_v2.py
route_synapse_vmem_v1.py
route_synapse_weight_gates_v2.py
route_synapse_vss_v1.py
```

The completed canonical synapse layout is:

```text
layout/synapse/neurolif_synapse_vss_v1.gds
```

The final synapse was independently verified before integration into the full neuron.

## Full-Neuron Construction

The public full-neuron construction sequence preserves the successful physical-design path, including:

```text
build_full_neuron_reference_v1.py
build_full_neuron_placement_v1.py

route_full_neuron_vdd_v2.py
route_full_neuron_vdd_v3.py
route_full_neuron_vss_v1.py
route_full_neuron_vmem_v1.py
route_full_neuron_vleak_v1.py
route_full_neuron_pmid_v2.py
route_full_neuron_nmid_v1.py
route_full_neuron_vraw_v2.py
route_full_neuron_spike_v1.py
route_full_neuron_reset_gate_v1.py
```

`route_full_neuron_vdd_v2.py` is retained because the successful VDD V3 stage depends on its generated intermediate artifact.

Rejected debugging routes are not part of the canonical final implementation.

## GDS Serialization

During development, explicit layer mapping was required when writing GDS files.

The established pattern is:

```python
save_options = kdb.SaveLayoutOptions()
save_options.format = "GDS2"
save_options.deselect_all_layers()

for layer_index, gds_layer, datatype, name in populated_layers:
    save_options.add_layer(
        layer_index,
        kdb.LayerInfo(
            int(gds_layer),
            int(datatype),
        ),
    )

layout.write(
    str(OUTPUT_GDS),
    save_options,
)
```

Equivalent explicit layer mapping is used when serializing OASIS layouts.

## Final DRC Reproduction

The standalone public DRC runner is:

```text
scripts/klayout/run_final_drc.py
```

It checks:

```text
layout/neuron/neurolif_full_neuron_final_routed_v1.gds
```

using the official SKY130 KLayout DRC deck.

Expected result:

```text
KLayout return code: 0
Violation count: 0

DRC_CLEAN = True
FINAL_DRC_REPRODUCTION_PASS = True
```

Fresh reproduction outputs are written to:

```text
verification/neuron/drc/reproduced/
```

The preserved original verification evidence remains under:

```text
verification/neuron/drc/
```

and is not overwritten.

## Final LVS Reproduction

The standalone public LVS runner is:

```text
scripts/klayout/run_final_lvs.py
```

Layout input:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

Reference schematic:

```text
circuit/lvs/neurolif_full_neuron_lvs_reference_v1.spice
```

Expected result:

```text
KLayout return code: 0

Success message found  : True
Mismatch message found : False

Extracted MOS count    : 17 / 17

LVS_PASS = True

OFFICIAL RESULT: NETLISTS MATCH
FINAL_LVS_REPRODUCTION_PASS = True
```

Fresh LVS reproduction outputs are written to:

```text
verification/neuron/lvs/reproduced/
```

The preserved original LVS evidence remains unchanged.

## Connectivity Audit

The independent geometry-based connectivity audit is implemented in:

```text
scripts/verification/neuron/audit_full_neuron_connectivity_v1.py
```

The final preserved audit record is:

```text
verification/neuron/connectivity/
neurolif_full_neuron_final_connectivity_audit_v1.json
```

The validated final result includes:

```text
17 MOS devices
14 logical conductor nets

No cross-net shorts
No floating conductor nets

Weighted-synapse topology verified
Schmitt/buffer/reset topology verified
Leak path verified
Body/well connectivity verified
```

### Current Reproduction Scope

The preserved audit record is authoritative for the frozen final design.

However, the audit script was originally developed against an earlier working-directory organization. Before describing it as a one-command fresh-clone reproduction step, its input paths should be normalized to the curated public directory structure.

In particular, dependencies should reference the current public locations such as:

```text
circuit/reference/
verification/neuron/drc/
verification/neuron/connectivity/
layout/neuron/
```

rather than expecting verification artifacts to remain inside `layout/neuron/`.

The same rule applies to any older helper script that still assumes the original development directory layout.

## Public Simulation Results

The concise frozen result files are:

```text
results/nominal/nominal_summary.json

results/synapse/weight_current_summary.csv

results/pvt/pvt_27point_summary.csv

results/variation/variation_13case_summary.csv
```

These contain the final validated public results rather than the complete development/debug history.

## Public Notebooks

The clean public notebooks are:

```text
notebooks/01_neurolif_nominal_validation.ipynb

notebooks/02_weighted_synapse_characterization.ipynb

notebooks/03_pvt_and_variation_analysis.ipynb
```

They read the frozen public result files and reproduce the main tables and plots.

They intentionally exclude obsolete debugging experiments from the original development workflow.

## Nominal Validation

Representative final nominal values include:

```text
VTH_UP    = 1.023948 V
VTH_DOWN  = 0.824096 V
Hysteresis = 199.852 mV
```

Final weighted-synapse currents are approximately:

```text
00 =   0.002 nA
01 = 103.734 nA
10 = 207.470 nA
11 = 311.206 nA
```

Corresponding current scaling is approximately:

```text
10 / 01 ≈ 2
11 / 01 ≈ 3
```

## Robustness Validation

The final transistor-level validation status is:

```text
Post-patch nominal validation      PASS
Functional numerical convergence  PASS
PVT sweep                          27 / 27 passed defined acceptance criteria
Deterministic variation            13 / 13 PASS
```

For the PVT sweep, a point is considered passing when:

- the simulation completes successfully
- weight `00` remains silent
- weight `11` produces valid spiking
- the response remains nondecreasing with increasing synaptic weight

A passing PVT point therefore does not imply that every nonzero weight necessarily produces spikes at every process, voltage and temperature corner.

The deterministic variation sweep is not a Monte Carlo mismatch analysis.

## Verification Evidence

The repository preserves the following machine-readable verification artifacts:

```text
DRC report databases
DRC logs
connectivity audit JSON
LVS databases
extracted netlists
LVS logs
final verification JSON records
```

Visual supporting evidence is stored under:

```text
figures/layout/
figures/verification/
```

Screenshots are supporting presentation material; the machine-readable reports and logs remain the primary verification evidence.

## Fresh-Clone Reproducibility Status

The current curated repository should distinguish between directly reproducible final checks and preserved historical construction scripts.

### Directly reproducible

The following workflows are intended to run directly from the curated repository structure once the required external tools and PDK are installed:

```text
public analysis notebooks
final standalone DRC runner
final standalone LVS runner
```

### Preserved but requiring path normalization

Some older construction and verification-chain scripts were written against the original development directory layout.

These should not yet be described as fully fresh-clone executable until their project-file paths are normalized to the curated repository structure.

This limitation affects packaging and workflow orchestration, not the validity of the preserved final verification results.

## Reproducibility Boundary

Reproducing the repository requires third-party tools and technology files that are not distributed here.

Users are responsible for installing and complying with the licenses of:

- KLayout
- SKY130 / Efabless SKY130 technology files
- Python
- gdsfactory
- kfactory
- ngspice and related simulation dependencies

## Project Scope

NeuroLIF-SKY130 is a pre-silicon educational neuromorphic circuit-design project.

The verified project scope includes:

- transistor-level simulation validation
- weighted-synapse characterization
- staged physical implementation
- official SKY130 DRC
- independent geometry-based connectivity auditing
- KLayout LVS

The repository does not claim:

- fabricated silicon
- tapeout
- measured silicon results
- production manufacturing signoff
- parasitic-extracted post-layout transient simulation

Parasitic extraction and post-layout simulation remain possible future extensions.