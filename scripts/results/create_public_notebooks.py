from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "notebooks"

NOTEBOOK_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def markdown_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            line + "\n"
            for line in text.strip().splitlines()
        ],
    }


def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            line + "\n"
            for line in code.strip().splitlines()
        ],
    }


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.x",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(filename, cells):
    path = NOTEBOOK_DIR / filename

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            make_notebook(cells),
            f,
            indent=2,
        )

    print(
        "[CREATED]",
        path.relative_to(ROOT),
    )


# ============================================================
# COMMON ROOT-FINDING CODE FOR NOTEBOOKS
# ============================================================

root_code = r'''
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def find_repo_root():
    start = Path.cwd().resolve()

    candidates = [
        start,
        *start.parents,
    ]

    for candidate in candidates:

        if (
            (candidate / "results").exists()
            and
            (candidate / "layout").exists()
        ):
            return candidate

    raise RuntimeError(
        "Could not locate NeuroLIF-SKY130 repository root."
    )


ROOT = find_repo_root()

print("Repository root:", ROOT)
'''


# ============================================================
# NOTEBOOK 01
# Nominal neuron validation
# ============================================================

nb1_cells = [

    markdown_cell(
r'''
# NeuroLIF-SKY130 — Nominal Neuron Validation

This notebook presents the **final validated nominal TT behavior**
of the NeuroLIF-SKY130 transistor-level leaky integrate-and-fire
neuron.

Final nominal conditions:

- SKY130 1.8 V devices
- process corner: TT
- supply: 1.80 V
- temperature: 27 °C
- external membrane capacitance: 5 pF
- corrected unit-cell weighted synapse
- corrected CMOS Schmitt threshold detector
- direct spike-controlled reset
- transient command: `tran 10n 0.0004 0 1n`

This notebook reads the frozen public result artifact rather than
the earlier development/debug notebook.
'''
    ),

    code_cell(root_code),

    code_cell(
r'''
import json


RESULT_FILE = (
    ROOT
    / "results"
    / "nominal"
    / "nominal_summary.json"
)


with RESULT_FILE.open(
    "r",
    encoding="utf-8",
) as f:

    nominal = json.load(f)


print(
    "POST_PATCH_NOMINAL_PASS =",
    nominal["POST_PATCH_NOMINAL_PASS"],
)


assert (
    nominal["POST_PATCH_NOMINAL_PASS"]
    is True
)
'''
    ),

    markdown_cell(
r'''
## Schmitt threshold behavior

The corrected six-transistor Schmitt detector provides a positive
hysteresis window around the membrane switching point.
'''
    ),

    code_cell(
r'''
schmitt = nominal["schmitt"]

print(
    f"VTH_UP   = {schmitt['vth_up_V']:.6f} V"
)

print(
    f"VTH_DOWN = {schmitt['vth_down_V']:.6f} V"
)

print(
    f"Hysteresis = "
    f"{schmitt['hysteresis_mV']:.3f} mV"
)
'''
    ),

    markdown_cell(
r'''
## 2-bit weight response

The final weighted synapse uses the encoding:

| Code | Active unit current cells |
|---|---:|
| 00 | 0 |
| 01 | 1 |
| 10 | 2 |
| 11 | 3 |

The expected neuron behavior is a monotonic increase in firing
activity as the number of active unit cells increases.
'''
    ),

    code_cell(
r'''
rows = []

for weight, data in nominal["weights"].items():

    rows.append({
        "weight":
            weight,

        "spike_count":
            data["spike_count"],

        "firing_rate_Hz":
            data["firing_rate_Hz"],

        "energy_total_J":
            data["energy_total_J"],

        "energy_per_spike_J":
            data["energy_per_spike_J"],

        "vmem_min_V":
            data["vmem_min_V"],

        "vmem_max_V":
            data["vmem_max_V"],

        "spike_max_V":
            data["spike_max_V"],
    })


nominal_df = pd.DataFrame(rows)

nominal_df
'''
    ),

    code_cell(
r'''
fig, ax = plt.subplots(
    figsize=(7, 4.5)
)

ax.bar(
    nominal_df["weight"],
    nominal_df["spike_count"],
)

ax.set_xlabel(
    "2-bit synaptic weight"
)

ax.set_ylabel(
    "Spike count"
)

ax.set_title(
    "Final nominal TT firing response"
)

ax.grid(
    axis="y",
    alpha=0.25,
)

plt.tight_layout()
plt.show()
'''
    ),

    code_cell(
r'''
checks = nominal["checks"]

for name, value in checks.items():

    print(
        f"{name:35s} : {value}"
    )


assert all(
    checks.values()
)

print()
print(
    "NOMINAL_NOTEBOOK_PASS = True"
)
'''
    ),

    markdown_cell(
r'''
## Interpretation

At the final post-patch transient resolution:

- weight `00` remains silent
- weight `01` fires
- weight `10` fires faster
- weight `11` gives the strongest response
- the firing response is monotonic
- the output spike reaches a valid high level

These are **pre-silicon simulation results**. They are not
fabricated-silicon measurements.
'''
    ),
]


write_notebook(
    "01_neurolif_nominal_validation.ipynb",
    nb1_cells,
)


# ============================================================
# NOTEBOOK 02
# Weighted synapse characterization
# ============================================================

nb2_cells = [

    markdown_cell(
r'''
# NeuroLIF-SKY130 — Weighted Synapse Characterization

This notebook documents the corrected 2-bit electronic synapse.

The final implementation deliberately uses **identical PMOS unit
current cells** rather than a geometrically doubled PMOS device.

Final encoding:

- `00` → 0 active unit cells
- `01` → 1 active unit cell
- `10` → 2 identical unit cells in parallel
- `11` → 3 active unit cells
'''
    ),

    code_cell(root_code),

    code_cell(
r'''
RESULT_FILE = (
    ROOT
    / "results"
    / "synapse"
    / "weight_current_summary.csv"
)


synapse_df = pd.read_csv(
    RESULT_FILE,
    dtype={
        "weight": str,
    },
)


synapse_df["weight"] = (
    synapse_df["weight"]
    .str.zfill(2)
)


synapse_df
'''
    ),

    markdown_cell(
r'''
## Unit-cell weighting result

During development, a nominally 2×-wide PMOS did **not** deliver
2× the unit-cell current in the selected SKY130 configuration.

The observed characterization was approximately:

- one unit PMOS: **103.738 nA**
- one nominally 2×-wide PMOS: **98.196 nA**
- two identical unit PMOS devices in parallel: **207.476 nA**

Therefore the final synapse uses replicated identical unit cells.
No stronger claim is made about the exact physical cause of the
wide-device behavior.
'''
    ),

    code_cell(
r'''
table = (
    synapse_df
    .set_index("weight")
)


i01 = float(
    table.loc[
        "01",
        "median_delivered_current_nA",
    ]
)

i10 = float(
    table.loc[
        "10",
        "median_delivered_current_nA",
    ]
)

i11 = float(
    table.loc[
        "11",
        "median_delivered_current_nA",
    ]
)


ratio_2x = i10 / i01
ratio_3x = i11 / i01


print(
    f"I01 = {i01:.4f} nA"
)

print(
    f"I10 = {i10:.4f} nA"
)

print(
    f"I11 = {i11:.4f} nA"
)

print()

print(
    f"I10 / I01 = {ratio_2x:.6f}"
)

print(
    f"I11 / I01 = {ratio_3x:.6f}"
)
'''
    ),

    code_cell(
r'''
fig, ax = plt.subplots(
    figsize=(7, 4.5)
)

ax.bar(
    synapse_df["weight"],
    synapse_df[
        "median_delivered_current_nA"
    ],
)

ax.set_xlabel(
    "2-bit weight"
)

ax.set_ylabel(
    "Median delivered current (nA)"
)

ax.set_title(
    "Final unit-cell weighted synapse"
)

ax.grid(
    axis="y",
    alpha=0.25,
)

plt.tight_layout()
plt.show()
'''
    ),

    code_cell(
r'''
WEIGHT_SCALING_PASS = bool(

    1.95 <= ratio_2x <= 2.05

    and

    2.95 <= ratio_3x <= 3.05
)


print(
    "WEIGHT_SCALING_PASS =",
    WEIGHT_SCALING_PASS,
)


assert WEIGHT_SCALING_PASS
'''
    ),

    markdown_cell(
r'''
## Final implementation decision

The final layout therefore contains three identical PMOS current
cells:

- one cell assigned to the 1× bit
- two identical cells assigned to the 2× bit

When both bits are active, all three unit cells contribute.

This is an implementation and characterization result rather than
a claim of a novel current-mirror principle.
'''
    ),
]


write_notebook(
    "02_weighted_synapse_characterization.ipynb",
    nb2_cells,
)


# ============================================================
# NOTEBOOK 03
# PVT and deterministic variation
# ============================================================

nb3_cells = [

    markdown_cell(
r'''
# NeuroLIF-SKY130 — PVT and Deterministic Variation Analysis

This notebook summarizes the final robustness validation used to
freeze the transistor-level NeuroLIF-SKY130 design before physical
implementation.

Two validation sets are included:

1. **27-point PVT sweep**
   - FF, TT and SS process corners
   - 1.62 V, 1.80 V and 1.98 V
   - −40 °C, 27 °C and 125 °C

2. **13 deterministic parameter-variation conditions**
   - membrane capacitance
   - synaptic reference current
   - leak bias

The deterministic parameter sweep is **not Monte Carlo mismatch
analysis**.
'''
    ),

    code_cell(root_code),

    code_cell(
r'''
PVT_FILE = (
    ROOT
    / "results"
    / "pvt"
    / "pvt_27point_summary.csv"
)

VAR_FILE = (
    ROOT
    / "results"
    / "variation"
    / "variation_13case_summary.csv"
)


pvt_df = pd.read_csv(
    PVT_FILE
)

variation_df = pd.read_csv(
    VAR_FILE
)


print(
    "PVT rows:",
    len(pvt_df)
)

print(
    "Variation rows:",
    len(variation_df)
)
'''
    ),

    markdown_cell(
r'''
## PVT validation
'''
    ),

    code_cell(
r'''
pvt_pass = (
    pvt_df["point_pass"]
    .astype(str)
    .str.lower()
    .eq("true")
)


print(
    "PVT points passed:",
    int(pvt_pass.sum()),
    "/",
    len(pvt_df),
)


assert len(pvt_df) == 27
assert pvt_pass.all()


pvt_df
'''
    ),

    code_cell(
r'''
fig, ax = plt.subplots(
    figsize=(8, 4.8)
)


for weight in [
    "01",
    "10",
    "11",
]:

    ax.plot(
        range(len(pvt_df)),
        pvt_df[
            f"spikes_{weight}"
        ],
        marker="o",
        label=f"Weight {weight}",
    )


ax.set_xlabel(
    "PVT point index"
)

ax.set_ylabel(
    "Spike count"
)

ax.set_title(
    "Firing response across 27 PVT points"
)

ax.legend()

ax.grid(
    alpha=0.25,
)

plt.tight_layout()
plt.show()
'''
    ),

    markdown_cell(
r'''
Some PVT points may suppress lower-weight firing while the final
functional criteria still pass. The robustness gate checks the
required circuit behavior rather than demanding an identical
spike count at every operating point.
'''
    ),

    markdown_cell(
r'''
## Deterministic parameter variation
'''
    ),

    code_cell(
r'''
variation_pass = (
    variation_df[
        "condition_pass"
    ]
    .astype(str)
    .str.lower()
    .eq("true")
)


print(
    "Variation conditions passed:",
    int(
        variation_pass.sum()
    ),
    "/",
    len(
        variation_df
    ),
)


assert (
    len(
        variation_df
    )
    == 13
)

assert variation_pass.all()


variation_df
'''
    ),

    code_cell(
r'''
fig, ax = plt.subplots(
    figsize=(9, 4.8)
)


ax.plot(
    variation_df["condition"],
    variation_df["spikes_11"],
    marker="o",
)


ax.set_xlabel(
    "Deterministic variation condition"
)

ax.set_ylabel(
    "Weight-11 spike count"
)

ax.set_title(
    "Weight-11 response under deterministic variation"
)

ax.tick_params(
    axis="x",
    rotation=60,
)

ax.grid(
    alpha=0.25,
)

plt.tight_layout()
plt.show()
'''
    ),

    code_cell(
r'''
FULL_PVT_PASS = bool(
    len(pvt_df) == 27
    and
    pvt_pass.all()
)


DETERMINISTIC_VARIATION_PASS = bool(
    len(variation_df) == 13
    and
    variation_pass.all()
)


FINAL_ROBUSTNESS_SUMMARY_PASS = bool(

    FULL_PVT_PASS

    and

    DETERMINISTIC_VARIATION_PASS
)


print(
    "FULL_PVT_PASS =",
    FULL_PVT_PASS,
)

print(
    "DETERMINISTIC_VARIATION_PASS =",
    DETERMINISTIC_VARIATION_PASS,
)

print(
    "FINAL_ROBUSTNESS_SUMMARY_PASS =",
    FINAL_ROBUSTNESS_SUMMARY_PASS,
)


assert FINAL_ROBUSTNESS_SUMMARY_PASS
'''
    ),

    markdown_cell(
r'''
## Final robustness status

The frozen public data records:

- **27 / 27 PVT points passed**
- **13 / 13 deterministic variation conditions passed**

These results supported the pre-layout circuit freeze.

The deterministic sweep should not be described as process Monte
Carlo or transistor mismatch analysis.
'''
    ),
]


write_notebook(
    "03_pvt_and_variation_analysis.ipynb",
    nb3_cells,
)


print()
print("=" * 72)
print("PUBLIC NOTEBOOK GENERATION COMPLETE")
print("=" * 72)
print("Notebook count: 3")
print("PUBLIC_NOTEBOOK_GENERATION_PASS = True")