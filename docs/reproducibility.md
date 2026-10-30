# NeuroLIF-SKY130 Reproducibility

## Purpose

This document describes the environment, repository structure and public workflow for inspecting and reproducing the main NeuroLIF-SKY130 simulation, physical-design and verification artifacts.

The repository does not bundle the SKY130 PDK, KLayout installation, Python virtual environment or other third-party dependencies. These must be installed separately.

The curated public repository provides direct reproduction runners for the final DRC and LVS checks and repository-normalized paths for the final full-neuron connectivity audit.

The historical physical-construction chain is also preserved. However, some intermediate construction artifacts are intentionally not included in the curated release, so the repository should not be interpreted as a complete fresh-clone replay of every historical routing stage.

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

This revision is recorded to improve reproducibility of transistor-level simulation behavior.

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

This file is the canonical physical artifact.

It should not be replaced by the LVS-labelled derivative.

## LVS Derivative

The verification-only labelled layout is:

```text
layout/neuron/neurolif_full_neuron_lvs_v1.gds
```

Top cell:

```text
NEUROLIF_FULL_NEURON_LVS_V1
```

This derivative adds the top-level labels required for extraction and LVS.

It does not replace the canonical final routed GDS.

## Path Handling

Public project files are resolved using repository-relative paths rather than machine-specific absolute paths.

A typical pattern is:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

LAYOUT_DIR = (
    PROJECT_ROOT
    / "layout"
    / "neuron"
)

VERIFY_DIR = (
    PROJECT_ROOT
    / "verification"
    / "neuron"
)
```

External tool installations may be located using the current user's home directory where appropriate:

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

## Public Path Sanitization

Machine-specific absolute filesystem paths appearing in preserved logs and report databases have been replaced with neutral placeholders where applicable.

Examples include:

```text
<REPO_ROOT>
<DEV_ROOT>
<USER_HOME>
```

This sanitization affects only path metadata.

It does not change:

- physical geometry
- device extraction
- DRC results
- LVS results
- connectivity results
- simulation results

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

The public primitive-generation scripts are stored under:

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

Its preserved verification evidence is stored under:

```text
verification/synapse/
```

The public synapse verification scripts use the curated locations for the reference schematic, connectivity record and LVS evidence.

Some early synapse construction manifests are historical intermediate artifacts and are not included in the curated public release.

Therefore, the weighted-synapse section should be interpreted as a preserved construction lineage plus frozen final evidence rather than a guaranteed replay of every historical intermediate stage from a clean clone.

## Full-Neuron Construction

The public full-neuron construction sequence preserves the successful physical-design path:

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

The public scripts use the curated repository location for the full-neuron reference schematic:

```text
circuit/reference/neurolif_full_neuron_reference_v1.spice
```

and the final synapse verification record:

```text
verification/synapse/neurolif_synapse_final_verification_v1.json
```

`route_full_neuron_vdd_v2.py` is retained because the successful VDD V3 stage depends on its generated intermediate artifact.

Rejected debugging routes are not part of the canonical final implementation.

## Historical Intermediate Artifacts

The repository intentionally focuses on final physical artifacts, verification evidence and the successful design lineage rather than every temporary development file.

For example, the final-routing manifest records the historical input:

```text
layout/neuron/neurolif_full_neuron_spike_v1.gds
```

That intermediate GDS is not included in the curated public release.

This is intentional historical metadata and should not be replaced with a different existing path merely to make every manifest reference resolve.

Similarly, some early construction manifests required by individual historical routing stages are not distributed.

These omissions affect complete historical workflow replay, not the validity of the final frozen design or its preserved verification evidence.

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

Expected validated result:

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

Expected validated result:

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

The independent geometry-based full-neuron connectivity audit is implemented in:

```text
scripts/verification/neuron/audit_full_neuron_connectivity_v1.py
```

The public script uses curated repository paths for:

```text
layout/neuron/
circuit/reference/
verification/neuron/drc/
verification/neuron/connectivity/
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

The preserved JSON record remains authoritative for the frozen final design.

## Reproduction Scope

The repository distinguishes between final verification reproduction and complete historical construction replay.

### Final verification workflows

The following public workflows use the curated repository structure:

```text
public analysis notebooks
final standalone DRC runner
final standalone LVS runner
full-neuron connectivity audit
```

The DRC and LVS standalone runners have preserved successful reproduction evidence in the repository.

The connectivity audit script has been normalized to the curated repository paths and operates on the preserved final design and verification inputs.

### Historical construction workflows

The construction scripts preserve the successful development sequence and now use curated paths for shared public references where applicable.

However, some historical intermediate GDS files and manifests are intentionally absent from the curated release.

Therefore, the complete physical-construction chain should not be advertised as a guaranteed one-command fresh-clone reconstruction of every historical stage.

This is an artifact-retention boundary rather than a path-normalization defect.

## Public Simulation Results

The concise frozen result files are:

```text
results/nominal/nominal_summary.json

results/synapse/weight_current_summary.csv

results/pvt/pvt_27point_summary.csv

results/variation/variation_13case_summary.csv
```

These contain the final validated public results rather than the complete development and debugging history.

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
VTH_UP     = 1.023948 V
VTH_DOWN   = 0.824096 V
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

Representative nominal firing behavior is:

```text
00   0 spikes    0 Hz
01  16 spikes   42.1 kHz
10  39 spikes  102.6 kHz
11  65 spikes  171.1 kHz
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
- weight `11` produces at least one valid spike
- the response remains nondecreasing with increasing synaptic weight

Therefore, `27 / 27 PASS` does not mean that intermediate weights `01` and `10` necessarily produce spikes at every process, voltage and temperature corner.

For example, some valid corners may produce responses such as:

```text
00 = 0
01 = 0
10 = 0
11 > 0
```

provided the defined acceptance criteria remain satisfied.

The deterministic 13-case variation sweep is not a Monte Carlo mismatch analysis.

## Verification Evidence

The repository preserves machine-readable verification artifacts including:

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

Screenshots are supporting presentation material.

The machine-readable reports, logs and records remain the primary verification evidence.

## Final Verification Record

The main machine-readable full-neuron verification record is:

```text
verification/neuron/
neurolif_full_neuron_final_verification_v1.json
```

Its curated artifact references point to the public locations for:

```text
verification/neuron/drc/
verification/neuron/connectivity/
verification/neuron/lvs/
circuit/lvs/
layout/neuron/
```

The record preserves the final status:

```text
MOS total                 17
PFET                       8
NFET                       9
Logical conductor nets    14
External pins              8

Official SKY130 DRC       PASS
DRC violations             0

Connectivity audit        PASS

KLayout LVS               PASS
Netlists match            True

FINAL_VERIFICATION_PASS   True
```

## Reproducibility Boundary

Reproducing the repository requires third-party tools and technology files that are not distributed here.

Users are responsible for installing and complying with the licenses of:

- KLayout
- SKY130 / Efabless SKY130 technology files
- Python
- gdsfactory
- kfactory
- ngspice and related simulation dependencies

The repository's reproducibility claim covers the preserved final design, public simulation summaries and final verification workflows.

It does not imply that every historical intermediate development artifact is included.

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
