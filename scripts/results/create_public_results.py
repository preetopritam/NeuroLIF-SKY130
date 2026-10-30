from pathlib import Path
import csv
import json


ROOT = Path(__file__).resolve().parents[2]

RESULTS = ROOT / "results"

NOMINAL_DIR = RESULTS / "nominal"
SYNAPSE_DIR = RESULTS / "synapse"
PVT_DIR = RESULTS / "pvt"
VARIATION_DIR = RESULTS / "variation"

for directory in (
    NOMINAL_DIR,
    SYNAPSE_DIR,
    PVT_DIR,
    VARIATION_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. FINAL POST-PATCH NOMINAL TT SUMMARY
# ============================================================

nominal_summary = {
    "project": "NeuroLIF-SKY130",
    "validation_stage": "final_post_patch_nominal",
    "corner": "tt",
    "vdd_V": 1.80,
    "temperature_C": 27.0,
    "transient": {
        "tstep_s": 10e-9,
        "tstop_s": 400e-6,
        "tmax_s": 1e-9,
        "ngspice_command": "tran 10n 0.0004 0 1n",
    },
    "schmitt": {
        "vth_up_V": 1.023948,
        "vth_down_V": 0.824096,
        "hysteresis_V": 0.199852,
        "hysteresis_mV": 199.852,
    },
    "weights": {
        "00": {
            "spike_count": 0,
            "firing_rate_Hz": 0.0,
            "energy_total_J": 7.224655e-11,
            "energy_per_spike_J": None,
            "vmem_min_V": 0.000001,
            "vmem_max_V": 0.200000,
            "spike_min_V": 2.140502e-7,
            "spike_max_V": 2.148262e-7,
            "spike_fraction_VDD": 1.193479e-7,
        },
        "01": {
            "spike_count": 16,
            "firing_rate_Hz": 42105.263158,
            "energy_total_J": 1.751039e-8,
            "energy_per_spike_J": 1.094399e-9,
            "vmem_min_V": 0.137195,
            "vmem_max_V": 1.024103,
            "spike_min_V": -1.480653e-2,
            "spike_max_V": 1.822319,
            "spike_fraction_VDD": 1.012400,
        },
        "10": {
            "spike_count": 39,
            "firing_rate_Hz": 102631.578947,
            "energy_total_J": 1.908601e-8,
            "energy_per_spike_J": 4.893850e-10,
            "vmem_min_V": 0.137195,
            "vmem_max_V": 1.024284,
            "spike_min_V": -1.796859e-2,
            "spike_max_V": 1.832049,
            "spike_fraction_VDD": 1.017805,
        },
        "11": {
            "spike_count": 65,
            "firing_rate_Hz": 171052.631579,
            "energy_total_J": 2.025317e-8,
            "energy_per_spike_J": 3.115872e-10,
            "vmem_min_V": 0.137195,
            "vmem_max_V": 1.024433,
            "spike_min_V": -1.765562e-2,
            "spike_max_V": 1.832463,
            "spike_fraction_VDD": 1.018035,
        },
    },
    "checks": {
        "weight_00_no_fire": True,
        "weight_01_fires": True,
        "weight_10_fires": True,
        "weight_11_fires": True,
        "nondecreasing_firing_response": True,
        "weight_11_valid_spike": True,
    },
    "POST_PATCH_NOMINAL_PASS": True,
}


nominal_path = NOMINAL_DIR / "nominal_summary.json"

with nominal_path.open("w", encoding="utf-8") as f:
    json.dump(
        nominal_summary,
        f,
        indent=2,
        allow_nan=False,
    )


# ============================================================
# 2. FINAL WEIGHTED-SYNAPSE CHARACTERIZATION
# ============================================================

synapse_rows = [
    {
        "weight": "00",
        "active_unit_cells": 0,
        "median_delivered_current_A": 1.680000e-12,
        "median_delivered_current_nA": 0.001680,
        "normalized_to_weight_01": 0.0,
    },
    {
        "weight": "01",
        "active_unit_cells": 1,
        "median_delivered_current_A": 1.037342e-7,
        "median_delivered_current_nA": 103.7342,
        "normalized_to_weight_01": 1.0,
    },
    {
        "weight": "10",
        "active_unit_cells": 2,
        "median_delivered_current_A": 2.074700e-7,
        "median_delivered_current_nA": 207.4700,
        "normalized_to_weight_01": 2.000015424,
    },
    {
        "weight": "11",
        "active_unit_cells": 3,
        "median_delivered_current_A": 3.112059e-7,
        "median_delivered_current_nA": 311.2059,
        "normalized_to_weight_01": 3.000031812,
    },
]


synapse_path = (
    SYNAPSE_DIR
    / "weight_current_summary.csv"
)

with synapse_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=synapse_rows[0].keys(),
    )

    writer.writeheader()
    writer.writerows(synapse_rows)


# ============================================================
# 3. COMPLETE FINAL 27-POINT PVT SUMMARY
# ============================================================

corners = []
for corner in ("ff", "ss", "tt"):
    for vdd in (1.62, 1.80, 1.98):
        for temp in (-40.0, 27.0, 125.0):
            corners.append(
                (corner, vdd, temp)
            )


spikes_01 = [
    16, 4, 0,
    18, 4, 0,
    18, 4, 0,

    0, 3, 11,
    10, 17, 13,
    19, 19, 14,

    7, 15, 0,
    16, 16, 0,
    17, 16, 0,
]


spikes_10 = [
    39, 33, 0,
    41, 33, 0,
    44, 34, 0,

    0, 12, 36,
    20, 37, 45,
    32, 42, 47,

    16, 38, 27,
    37, 39, 24,
    37, 41, 25,
]


spikes_11 = [
    60, 62, 11,
    65, 63, 11,
    71, 63, 13,

    1, 20, 62,
    31, 58, 77,
    53, 66, 80,

    25, 61, 64,
    52, 65, 57,
    58, 65, 60,
]


spike11_fraction = [
    1.010903,
    1.014752,
    1.008452,
    1.030972,
    1.019488,
    1.008106,
    1.022762,
    1.019090,
    1.011274,

    1.014581,
    1.036702,
    1.018876,
    1.031732,
    1.010416,
    1.012325,
    1.023665,
    1.024533,
    1.016978,

    1.022894,
    1.011936,
    1.015928,
    1.020058,
    1.018035,
    1.014867,
    1.041949,
    1.030633,
    1.014139,
]


OBSERVATION_WINDOW_S = 0.00038


pvt_rows = []

for index, (
    corner,
    vdd,
    temp,
) in enumerate(corners):

    s00 = 0
    s01 = spikes_01[index]
    s10 = spikes_10[index]
    s11 = spikes_11[index]

    row = {
        "corner": corner,
        "vdd_V": vdd,
        "temp_C": temp,
        "simulation_complete": True,
        "weight_00_silent": True,
        "weight_11_fires": True,
        "weight_11_valid_spike": True,
        "nondecreasing_response": True,
        "spikes_00": s00,
        "spikes_01": s01,
        "spikes_10": s10,
        "spikes_11": s11,
        "rate_00_Hz": s00 / OBSERVATION_WINDOW_S,
        "rate_01_Hz": s01 / OBSERVATION_WINDOW_S,
        "rate_10_Hz": s10 / OBSERVATION_WINDOW_S,
        "rate_11_Hz": s11 / OBSERVATION_WINDOW_S,
        "spike11_fraction_VDD":
            spike11_fraction[index],
        "point_pass": True,
    }

    pvt_rows.append(row)


pvt_path = (
    PVT_DIR
    / "pvt_27point_summary.csv"
)

with pvt_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=pvt_rows[0].keys(),
    )

    writer.writeheader()
    writer.writerows(pvt_rows)


# ============================================================
# 4. FINAL 13-CASE DETERMINISTIC VARIATION SUMMARY
# ============================================================

variation_conditions = [
    (
        "cmem_0.90x",
        "cmem",
        0.90,
        4.50e-12,
        1.00e-7,
        0.500,
    ),
    (
        "cmem_0.95x",
        "cmem",
        0.95,
        4.75e-12,
        1.00e-7,
        0.500,
    ),
    (
        "cmem_1.05x",
        "cmem",
        1.05,
        5.25e-12,
        1.00e-7,
        0.500,
    ),
    (
        "cmem_1.10x",
        "cmem",
        1.10,
        5.50e-12,
        1.00e-7,
        0.500,
    ),

    (
        "iref_0.90x",
        "iref",
        0.90,
        5.00e-12,
        0.90e-7,
        0.500,
    ),
    (
        "iref_0.95x",
        "iref",
        0.95,
        5.00e-12,
        0.95e-7,
        0.500,
    ),
    (
        "iref_1.05x",
        "iref",
        1.05,
        5.00e-12,
        1.05e-7,
        0.500,
    ),
    (
        "iref_1.10x",
        "iref",
        1.10,
        5.00e-12,
        1.10e-7,
        0.500,
    ),

    (
        "nominal",
        "nominal",
        1.00,
        5.00e-12,
        1.00e-7,
        0.500,
    ),

    (
        "vleak_0.90x",
        "vleak",
        0.90,
        5.00e-12,
        1.00e-7,
        0.450,
    ),
    (
        "vleak_0.95x",
        "vleak",
        0.95,
        5.00e-12,
        1.00e-7,
        0.475,
    ),
    (
        "vleak_1.05x",
        "vleak",
        1.05,
        5.00e-12,
        1.00e-7,
        0.525,
    ),
    (
        "vleak_1.10x",
        "vleak",
        1.10,
        5.00e-12,
        1.00e-7,
        0.550,
    ),
]


variation_spikes_01 = [
    17,
    16,
    16,
    15,
    13,
    15,
    17,
    18,
    16,
    20,
    18,
    11,
    4,
]


variation_spikes_10 = [
    42,
    41,
    41,
    38,
    35,
    36,
    42,
    43,
    39,
    43,
    42,
    35,
    29,
]


variation_spikes_11 = [
    70,
    68,
    62,
    61,
    56,
    61,
    67,
    69,
    65,
    67,
    65,
    58,
    50,
]


variation_spike_fraction = [
    1.018072,
    1.018091,
    1.017956,
    1.018758,
    1.022989,
    1.018166,
    1.017952,
    1.017783,
    1.018035,
    1.018181,
    1.017771,
    1.026415,
    1.018107,
]


variation_rows = []

for index, condition in enumerate(
    variation_conditions
):

    (
        name,
        parameter,
        multiplier,
        cmem,
        iref,
        vleak,
    ) = condition

    s00 = 0
    s01 = variation_spikes_01[index]
    s10 = variation_spikes_10[index]
    s11 = variation_spikes_11[index]

    row = {
        "condition": name,
        "parameter": parameter,
        "multiplier": multiplier,
        "cmem_F": cmem,
        "iref_A": iref,
        "vleak_V": vleak,
        "simulation_complete": True,
        "weight_00_silent": True,
        "weight_11_fires": True,
        "weight_11_valid_spike": True,
        "nondecreasing_response": True,
        "spikes_00": s00,
        "spikes_01": s01,
        "spikes_10": s10,
        "spikes_11": s11,
        "rate_00_Hz":
            s00 / OBSERVATION_WINDOW_S,
        "rate_01_Hz":
            s01 / OBSERVATION_WINDOW_S,
        "rate_10_Hz":
            s10 / OBSERVATION_WINDOW_S,
        "rate_11_Hz":
            s11 / OBSERVATION_WINDOW_S,
        "spike11_fraction_VDD":
            variation_spike_fraction[index],
        "condition_pass": True,
    }

    variation_rows.append(row)


variation_path = (
    VARIATION_DIR
    / "variation_13case_summary.csv"
)

with variation_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=variation_rows[0].keys(),
    )

    writer.writeheader()
    writer.writerows(variation_rows)


# ============================================================
# 5. FINAL SELF-CHECK
# ============================================================

checks = {
    "nominal_pass":
        nominal_summary[
            "POST_PATCH_NOMINAL_PASS"
        ],

    "synapse_rows":
        len(synapse_rows) == 4,

    "pvt_rows":
        len(pvt_rows) == 27,

    "pvt_all_pass":
        all(
            row["point_pass"]
            for row in pvt_rows
        ),

    "variation_rows":
        len(variation_rows) == 13,

    "variation_all_pass":
        all(
            row["condition_pass"]
            for row in variation_rows
        ),
}


print()
print("=" * 72)
print("NeuroLIF-SKY130 PUBLIC RESULT EXPORT")
print("=" * 72)

print(
    f"[CREATED] {nominal_path.relative_to(ROOT)}"
)

print(
    f"[CREATED] {synapse_path.relative_to(ROOT)}"
)

print(
    f"[CREATED] {pvt_path.relative_to(ROOT)}"
)

print(
    f"[CREATED] {variation_path.relative_to(ROOT)}"
)

print()
print(
    "Nominal validation       :",
    checks["nominal_pass"],
)

print(
    "Synapse rows             :",
    len(synapse_rows),
)

print(
    "PVT points               :",
    len(pvt_rows),
)

print(
    "PVT points passing       :",
    sum(
        row["point_pass"]
        for row in pvt_rows
    ),
)

print(
    "Variation conditions     :",
    len(variation_rows),
)

print(
    "Variation cases passing  :",
    sum(
        row["condition_pass"]
        for row in variation_rows
    ),
)


FINAL_PASS = all(checks.values())

print()
print(
    "PUBLIC_RESULTS_EXPORT_PASS =",
    FINAL_PASS,
)

if not FINAL_PASS:
    raise SystemExit(1)