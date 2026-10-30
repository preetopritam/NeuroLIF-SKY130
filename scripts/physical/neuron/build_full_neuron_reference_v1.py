# ================================================================
# NeuroLIF-SKY130
# STEP 29A — Freeze complete-neuron physical reference V1
#
# Purpose:
#   Lock the exact transistor-level topology BEFORE placement.
#
# Existing closed sub-block:
#   Corrected weighted synapse = 7 MOS
#
# Added neuron circuitry:
#   Leak NMOS       = 1
#   6T Schmitt      = 6
#   Output inverter = 2
#   Reset NMOS      = 1
#
# Total = 17 MOS
#
# Cmem policy:
#   The validated 5 pF membrane capacitor remains external/ideal.
#   VMEM is therefore retained as a top-level pin.
#
# No GDS is modified.
# ================================================================

from pathlib import Path
import json
import re


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 29A: FULL-NEURON REFERENCE FREEZE V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

NEURON_DIR = (
    PROJECT_ROOT
    / "layout"
    / "neuron"
)

NEURON_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

ARCH_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_architecture_v1.json"
)


SYNAPSE_FINAL_RECORD = (
    PROJECT_ROOT
    / "verification"
    / "synapse"
    / "neurolif_synapse_final_verification_v1.json"
)


if not SYNAPSE_FINAL_RECORD.exists():

    raise FileNotFoundError(
        SYNAPSE_FINAL_RECORD
    )


# ================================================================
# 2. CONFIRM CLOSED SYNAPSE
# ================================================================

synapse_record = json.loads(

    SYNAPSE_FINAL_RECORD.read_text(
        encoding="utf-8"
    )

)


SYNAPSE_CLOSED = bool(

    synapse_record.get(
        "STEP28C_PASS",
        False,
    )

    and

    synapse_record.get(
        "final_status",
        ""
    ) == "CLOSED"

)


print()
print("=" * 80)
print("CLOSED SYNAPSE DEPENDENCY")
print("=" * 80)

print(
    "Synapse final record:",
    SYNAPSE_FINAL_RECORD
)

print(
    "Synapse closed:",
    SYNAPSE_CLOSED
)


if not SYNAPSE_CLOSED:

    raise RuntimeError(
        "Weighted synapse is not formally closed."
    )


# ================================================================
# 3. FROZEN DIMENSIONS
# ================================================================

DIMENSIONS = {

    "N_LOGIC": {
        "W_um": 1.00,
        "L_um": 0.15,
    },

    "P_LOGIC": {
        "W_um": 2.00,
        "L_um": 0.15,
    },

    "N_FB": {
        "W_um": 0.42,
        "L_um": 0.30,
    },

    "P_FB": {
        "W_um": 0.42,
        "L_um": 0.30,
    },

    "P_SYN": {
        "W_um": 0.84,
        "L_um": 0.50,
    },

    "N_SWITCH": {
        "W_um": 1.00,
        "L_um": 0.15,
    },

    "N_LEAK": {
        "W_um": 0.42,
        "L_um": 1.00,
    },

    "N_RESET": {
        "W_um": 1.20,
        "L_um": 0.15,
    },

}


# ================================================================
# 4. REFERENCE SPICE
#
# MOS syntax:
#
#   Mname D G S B model W=... L=...
#
# IMPORTANT:
#
# Final corrected Schmitt feedback:
#
#   MN_FB:
#       D = VDD
#       G = VRAW
#       S = N_MID
#       B = VSS
#
#   MP_FB:
#       D = VSS
#       G = VRAW
#       S = P_MID
#       B = VDD
#
# This is the corrected non-crossed feedback topology.
# ================================================================

spice_text = """* ================================================================
* NeuroLIF-SKY130
* Complete LIF neuron physical reference V1
*
* Pre-silicon educational SKY130 design.
*
* Core:
*   7-MOS weighted synapse
*   1-MOS leak
*   6-MOS corrected Schmitt trigger
*   2-MOS output inverter
*   1-MOS reset
*
* Total MOS = 17
*
* External membrane capacitance:
*   CMEM = 5 pF from VMEM to VSS in the simulation/testbench.
*   It is NOT physically instantiated in this core revision.
*
* MOS syntax:
*   Mname D G S B model W=... L=...
* ================================================================


* ================================================================
* CLOSED WEIGHTED SYNAPSE
* ================================================================

.SUBCKT NEUROLIF_WEIGHTED_SYNAPSE \
VDD VSS VBIAS GATE_W0 GATE_W1 VMEM

* PMOS reference
MP_REF VBIAS VBIAS VDD VDD \
sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u

* Three identical PMOS unit sources
MP_U1A N_U1A VBIAS VDD VDD \
sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u

MP_U0 N_U0 VBIAS VDD VDD \
sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u

MP_U1B N_U1B VBIAS VDD VDD \
sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u

* Three identical NMOS selection switches
MN_SW1A N_U1A GATE_W1 VMEM VSS \
sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u

MN_SW0 N_U0 GATE_W0 VMEM VSS \
sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u

MN_SW1B N_U1B GATE_W1 VMEM VSS \
sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u

.ENDS NEUROLIF_WEIGHTED_SYNAPSE


* ================================================================
* COMPLETE NEURON CORE
* ================================================================

.SUBCKT NEUROLIF_FULL_NEURON_V1 \
VDD VSS VBIAS GATE_W0 GATE_W1 VLEAK VMEM SPIKE


* ------------------------------------------------
* Closed weighted-synapse block
* ------------------------------------------------

XWS \
VDD VSS VBIAS GATE_W0 GATE_W1 VMEM \
NEUROLIF_WEIGHTED_SYNAPSE


* ------------------------------------------------
* Membrane leak
*
* D = VMEM
* G = VLEAK
* S = VSS
* B = VSS
* ------------------------------------------------

MN_LEAK VMEM VLEAK VSS VSS \
sky130_fd_pr__nfet_01v8 W=0.42u L=1.00u


* ================================================================
* CORRECTED 6T SCHMITT THRESHOLD DETECTOR
*
* Input  = VMEM
* Output = VRAW
*
* Internal nodes:
*   P_MID
*   N_MID
* ================================================================


* ------------------------------------------------
* PMOS input stack
* ------------------------------------------------

MP_ST1 P_MID VMEM VDD VDD \
sky130_fd_pr__pfet_01v8 W=2.00u L=0.15u

MP_ST2 VRAW VMEM P_MID VDD \
sky130_fd_pr__pfet_01v8 W=2.00u L=0.15u


* ------------------------------------------------
* NMOS input stack
* ------------------------------------------------

MN_ST1 VRAW VMEM N_MID VSS \
sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u

MN_ST2 N_MID VMEM VSS VSS \
sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u


* ------------------------------------------------
* CORRECTED feedback devices
*
* DO NOT substitute the older crossed-feedback form.
* ------------------------------------------------

MN_FB VDD VRAW N_MID VSS \
sky130_fd_pr__nfet_01v8 W=0.42u L=0.30u

MP_FB VSS VRAW P_MID VDD \
sky130_fd_pr__pfet_01v8 W=0.42u L=0.30u


* ================================================================
* OUTPUT INVERTER
*
* Converts Schmitt raw output VRAW into positive SPIKE.
* ================================================================

MP_BUF SPIKE VRAW VDD VDD \
sky130_fd_pr__pfet_01v8 W=2.00u L=0.15u

MN_BUF SPIKE VRAW VSS VSS \
sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u


* ================================================================
* DIRECT SPIKE-CONTROLLED RESET
*
* D = VMEM
* G = SPIKE
* S = VSS
* B = VSS
* ================================================================

MN_RST VMEM SPIKE VSS VSS \
sky130_fd_pr__nfet_01v8 W=1.20u L=0.15u


.ENDS NEUROLIF_FULL_NEURON_V1
"""


REFERENCE_SPICE.write_text(

    spice_text,

    encoding="utf-8",

)


SPICE_WRITE_OK = bool(

    REFERENCE_SPICE.exists()

    and

    REFERENCE_SPICE.stat().st_size > 0

)


# ================================================================
# 5. PARSE ACTUAL MOS STATEMENTS
# ================================================================

mos_lines = []


for line in spice_text.splitlines():

    stripped = line.strip()

    if not stripped:

        continue

    if stripped.startswith("*"):

        continue

    if stripped[0].upper() == "M":

        mos_lines.append(
            stripped
        )


TOTAL_MOS = len(
    mos_lines
)


PFET_COUNT = sum(

    1

    for line
    in mos_lines

    if "sky130_fd_pr__pfet_01v8" in line

)


NFET_COUNT = sum(

    1

    for line
    in mos_lines

    if "sky130_fd_pr__nfet_01v8" in line

)


DEVICE_COUNT_OK = bool(

    TOTAL_MOS == 17

    and

    PFET_COUNT == 8

    and

    NFET_COUNT == 9

)


print()
print("=" * 80)
print("DEVICE COUNT AUDIT")
print("=" * 80)

print(
    "Total MOS:",
    TOTAL_MOS,
    "(expected 17)"
)

print(
    "PFET:",
    PFET_COUNT,
    "(expected 8)"
)

print(
    "NFET:",
    NFET_COUNT,
    "(expected 9)"
)

print(
    "Device count correct:",
    DEVICE_COUNT_OK
)


# ================================================================
# 6. ADDED-CIRCUIT COUNT
# ================================================================

SYNAPSE_MOS = 7

ADDED_MOS = (
    TOTAL_MOS
    - SYNAPSE_MOS
)


ADDED_COUNT_OK = (
    ADDED_MOS == 10
)


print()
print("=" * 80)
print("NEURON EXTENSION COUNT")
print("=" * 80)

print(
    "Closed synapse MOS:",
    SYNAPSE_MOS
)

print(
    "Added neuron MOS:",
    ADDED_MOS,
    "(expected 10)"
)

print(
    "Extension count correct:",
    ADDED_COUNT_OK
)


# ================================================================
# 7. EXTERNAL PIN AUDIT
# ================================================================

EXPECTED_EXTERNAL_PINS = [

    "VDD",

    "VSS",

    "VBIAS",

    "GATE_W0",

    "GATE_W1",

    "VLEAK",

    "VMEM",

    "SPIKE",

]


top_subckt_match = re.search(

    r"\.SUBCKT\s+NEUROLIF_FULL_NEURON_V1\s+"
    r"(.*?)"
    r"(?=\n\n)",

    spice_text,

    flags=(
        re.IGNORECASE
        |
        re.DOTALL
    ),

)


# Because the declaration uses SPICE continuation syntax,
# perform a direct normalized check instead.

normalized = (

    spice_text

    .replace("\\\n", " ")

    .replace("\n", " ")

)


pin_pattern = re.compile(

    r"\.SUBCKT\s+NEUROLIF_FULL_NEURON_V1\s+"
    r"VDD\s+VSS\s+VBIAS\s+GATE_W0\s+GATE_W1\s+"
    r"VLEAK\s+VMEM\s+SPIKE",

    re.IGNORECASE,

)


PIN_INTERFACE_OK = bool(

    pin_pattern.search(
        normalized
    )

)


print()
print("=" * 80)
print("TOP-LEVEL INTERFACE")
print("=" * 80)

print(
    "External pins:"
)

for pin in EXPECTED_EXTERNAL_PINS:

    print(
        " ",
        pin
    )


print(
    "Pin declaration correct:",
    PIN_INTERFACE_OK
)


# ================================================================
# 8. CRITICAL TOPOLOGY AUDITS
# ================================================================

critical_strings = {

    "leak":
        "MN_LEAK VMEM VLEAK VSS VSS",

    "schmitt_nf":
        "MN_FB VDD VRAW N_MID VSS",

    "schmitt_pf":
        "MP_FB VSS VRAW P_MID VDD",

    "buffer_p":
        "MP_BUF SPIKE VRAW VDD VDD",

    "buffer_n":
        "MN_BUF SPIKE VRAW VSS VSS",

    "reset":
        "MN_RST VMEM SPIKE VSS VSS",

}


topology_checks = {}


for name, text in critical_strings.items():

    topology_checks[
        name
    ] = bool(
        text
        in spice_text
    )


TOPOLOGY_OK = all(
    topology_checks.values()
)


print()
print("=" * 80)
print("CRITICAL TOPOLOGY AUDIT")
print("=" * 80)


for name, status in topology_checks.items():

    print(
        f"{name:16s}:",
        status
    )


print(
    "Critical topology correct:",
    TOPOLOGY_OK
)


# ================================================================
# 9. CMEM POLICY
# ================================================================

CMEM_PHYSICAL = False

CMEM_EXTERNAL_FF = 5.0


print()
print("=" * 80)
print("MEMBRANE CAPACITOR POLICY")
print("=" * 80)

print(
    "Validated capacitance:",
    f"{CMEM_EXTERNAL_FF:.1f} pF"
)

print(
    "Physical capacitor in core:",
    CMEM_PHYSICAL
)

print(
    "VMEM retained as external pin:",
    True
)


# ================================================================
# 10. ARCHITECTURE MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "29A",

    "artifact":
        "full_neuron_physical_reference_v1",

    "status":
        "REFERENCE_FROZEN"
        if (
            SYNAPSE_CLOSED
            and DEVICE_COUNT_OK
            and ADDED_COUNT_OK
            and PIN_INTERFACE_OK
            and TOPOLOGY_OK
            and SPICE_WRITE_OK
        )
        else "INVALID",

    "closed_dependency": {

        "block":
            "weighted_synapse",

        "verification_record":
            str(
                SYNAPSE_FINAL_RECORD
            ),

        "closed":
            SYNAPSE_CLOSED,

        "mos_count":
            7,

    },

    "top_cell":
        "NEUROLIF_FULL_NEURON_V1",

    "external_pins":
        EXPECTED_EXTERNAL_PINS,

    "internal_nets": [

        "VRAW",

        "P_MID",

        "N_MID",

        "N_U1A",

        "N_U0",

        "N_U1B",

    ],

    "devices": {

        "weighted_synapse": {

            "mos":
                7,

            "status":
                "CLOSED",

        },

        "leak": {

            "primitive":
                "N_LEAK",

            "count":
                1,

            "W_um":
                0.42,

            "L_um":
                1.00,

        },

        "schmitt": {

            "count":
                6,

            "input_pmos": {

                "count":
                    2,

                "W_um":
                    2.00,

                "L_um":
                    0.15,

            },

            "input_nmos": {

                "count":
                    2,

                "W_um":
                    1.00,

                "L_um":
                    0.15,

            },

            "feedback_nmos": {

                "count":
                    1,

                "W_um":
                    0.42,

                "L_um":
                    0.30,

            },

            "feedback_pmos": {

                "count":
                    1,

                "W_um":
                    0.42,

                "L_um":
                    0.30,

            },

            "feedback_connectivity": {

                "MN_FB": [
                    "VDD",
                    "VRAW",
                    "N_MID",
                    "VSS",
                ],

                "MP_FB": [
                    "VSS",
                    "VRAW",
                    "P_MID",
                    "VDD",
                ],

            },

        },

        "output_inverter": {

            "count":
                2,

            "pmos_W_um":
                2.00,

            "nmos_W_um":
                1.00,

            "L_um":
                0.15,

        },

        "reset": {

            "count":
                1,

            "W_um":
                1.20,

            "L_um":
                0.15,

            "gate":
                "SPIKE",

        },

    },

    "mos_totals": {

        "total":
            TOTAL_MOS,

        "pfet":
            PFET_COUNT,

        "nfet":
            NFET_COUNT,

        "synapse":
            SYNAPSE_MOS,

        "added_neuron":
            ADDED_MOS,

    },

    "membrane_capacitor": {

        "validated_value_pF":
            5.0,

        "physical_in_core":
            False,

        "implementation":
            "external_or_testbench",

        "connection":
            "VMEM-to-VSS",

        "reason":
            "No physical SKY130 capacitor implementation "
            "has yet been independently selected and verified.",

    },

    "physical_plan": {

        "next_phase":
            "placement",

        "reuse_closed_synapse":
            True,

        "modify_closed_synapse_geometry":
            False,

        "placement_blocks": [

            "closed_weighted_synapse",

            "N_LEAK",

            "6T_SCHMITT",

            "OUTPUT_INVERTER",

            "N_RESET",

            "body_taps",

        ],

    },

    "checks": {

        "closed_synapse":
            SYNAPSE_CLOSED,

        "spice_write":
            SPICE_WRITE_OK,

        "device_count":
            DEVICE_COUNT_OK,

        "added_device_count":
            ADDED_COUNT_OK,

        "pin_interface":
            PIN_INTERFACE_OK,

        "critical_topology":
            TOPOLOGY_OK,

    },

}


ARCH_MANIFEST.write_text(

    json.dumps(
        manifest,
        indent=2,
    ),

    encoding="utf-8",

)


MANIFEST_OK = bool(

    ARCH_MANIFEST.exists()

    and

    ARCH_MANIFEST.stat().st_size > 0

)


# ================================================================
# 11. FINAL GATE
# ================================================================

STEP29A_PASS = bool(

    SYNAPSE_CLOSED

    and

    SPICE_WRITE_OK

    and

    DEVICE_COUNT_OK

    and

    ADDED_COUNT_OK

    and

    PIN_INTERFACE_OK

    and

    TOPOLOGY_OK

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 29A RESULT")
print("=" * 80)

print(
    "Closed synapse dependency :",
    SYNAPSE_CLOSED
)

print(
    "Reference SPICE written   :",
    SPICE_WRITE_OK
)

print(
    "17-MOS total              :",
    DEVICE_COUNT_OK
)

print(
    "10-MOS neuron extension   :",
    ADDED_COUNT_OK
)

print(
    "Top-level interface       :",
    PIN_INTERFACE_OK
)

print(
    "Corrected topology        :",
    TOPOLOGY_OK
)

print(
    "Architecture manifest     :",
    MANIFEST_OK
)

print()

print(
    "STEP29A_PASS =",
    STEP29A_PASS
)


if not STEP29A_PASS:

    raise RuntimeError(
        "STEP 29A full-neuron reference freeze failed."
    )


print()
print("=" * 80)
print("FULL-NEURON REFERENCE STATUS")
print("=" * 80)

print()
print(
    "Weighted synapse : CLOSED / REUSED UNCHANGED"
)

print(
    "Neuron topology  : FROZEN"
)

print(
    "Total MOS        : 17"
)

print(
    "Added MOS        : 10"
)

print(
    "CMEM             : EXTERNAL 5 pF"
)

print(
    "Next phase       : PHYSICAL PLACEMENT"
)

print()
print(
    "Reference SPICE:"
)

print(
    REFERENCE_SPICE
)

print()
print(
    "Architecture manifest:"
)

print(
    ARCH_MANIFEST
)