# ================================================================
# NeuroLIF-SKY130
# STEP 28A — Build LVS-labeled weighted-synapse derivative
#
# Frozen input:
#   neurolif_synapse_vss_v1.gds
#
# Creates:
#   neurolif_synapse_lvs_v1.gds
#   neurolif_synapse_lvs_v1.oas
#   neurolif_synapse_reference_v1.spice
#   neurolif_synapse_lvs_v1.json
#
# IMPORTANT:
#   - Frozen source GDS is NOT modified.
#   - No 68/16 or 69/16 pin polygons are added.
#   - Only LVS-recognized TEXT labels are added:
#
#         MET1 label = 68/5
#         MET2 label = 69/5
#
#   - Only external nets are labeled.
#
#   - Reference schematic uses ordinary SPICE MOS syntax:
#
#         Mname D G S B model W=... L=...
#
# ================================================================

from pathlib import Path
import json
import hashlib

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 28A: BUILD LVS-LABELED SYNAPSE V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SYNAPSE_DIR = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
)

INPUT_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_vss_v1.gds"
)

OUTPUT_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.gds"
)

OUTPUT_OAS = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.oas"
)

REFERENCE_SPICE = (
    SYNAPSE_DIR
    / "neurolif_synapse_reference_v1.spice"
)

OUTPUT_MANIFEST = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VSS_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1"
)


if not INPUT_GDS.exists():

    raise FileNotFoundError(
        INPUT_GDS
    )


# ================================================================
# 2. HASH FROZEN INPUT
#
# We record this before doing anything so the manifest proves
# which frozen GDS the LVS derivative came from.
# ================================================================

def sha256_file(
    path,
):

    digest = hashlib.sha256()


    with path.open(
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024 * 1024
            )


            if not chunk:
                break


            digest.update(
                chunk
            )


    return digest.hexdigest()


INPUT_SHA256_BEFORE = sha256_file(
    INPUT_GDS
)


print()
print("=" * 80)
print("FROZEN INPUT")
print("=" * 80)

print(
    "Input GDS:",
    INPUT_GDS
)

print(
    "SHA256:",
    INPUT_SHA256_BEFORE
)

print(
    "Step 25B:",
    "DRC CLEAN / 0 violations"
)

print(
    "Step 26A:",
    "CONNECTIVITY / TOPOLOGY PASS"
)


# ================================================================
# 3. LOAD FROZEN GDS
# ================================================================

layout = kdb.Layout()

layout.read(
    str(
        INPUT_GDS
    )
)


DBU = layout.dbu


input_top = layout.cell(
    INPUT_TOP_NAME
)


if input_top is None:

    raise RuntimeError(
        f"Missing frozen top cell: {INPUT_TOP_NAME}"
    )


print()
print("=" * 80)
print("DATABASE")
print("=" * 80)

print(
    "DBU:",
    DBU,
    "um"
)

print(
    "Frozen top:",
    INPUT_TOP_NAME
)


# ================================================================
# 4. PHYSICAL + LABEL LAYERS
# ================================================================

M1_LAYER = layout.find_layer(
    68,
    20
)

M2_LAYER = layout.find_layer(
    69,
    20
)


if M1_LAYER is None:

    raise RuntimeError(
        "MET1 drawing layer 68/20 is missing."
    )


if M2_LAYER is None:

    raise RuntimeError(
        "MET2 drawing layer 69/20 is missing."
    )


# Create/get LVS label layers.
#
# sky130.lvs:
#
#   met1_label = labels(68,5)
#   met2_label = labels(69,5)

M1_LABEL_LAYER = layout.layer(
    68,
    5
)

M2_LABEL_LAYER = layout.layer(
    69,
    5
)


print()
print("=" * 80)
print("LVS LABEL LAYERS")
print("=" * 80)

print(
    "MET1 drawing:",
    "68/20"
)

print(
    "MET1 label  :",
    "68/5"
)

print(
    "MET2 drawing:",
    "69/20"
)

print(
    "MET2 label  :",
    "69/5"
)

print()
print(
    "No 68/16 or 69/16 pin polygons will be added."
)


# ================================================================
# 5. DBU HELPERS
# ================================================================

def to_dbu(
    value_um,
):

    return int(
        round(
            value_um
            / DBU
        )
    )


def probe_box_um(
    x,
    y,
    half_um=0.010,
):

    return kdb.Box(

        to_dbu(
            x - half_um
        ),

        to_dbu(
            y - half_um
        ),

        to_dbu(
            x + half_um
        ),

        to_dbu(
            y + half_um
        ),

    )


def region_hits_probe(
    region,
    x,
    y,
):

    probe = kdb.Region(

        probe_box_um(
            x,
            y,
        )

    )


    return not (

        region
        & probe

    ).is_empty()


# ================================================================
# 6. CREATE LVS DERIVATIVE TOP
#
# The frozen top is instantiated unchanged at (0,0).
# All LVS labels are added only in the new wrapper.
# ================================================================

existing_output_top = layout.cell(
    OUTPUT_TOP_NAME
)


if existing_output_top is not None:

    raise RuntimeError(

        f"Output top already exists in input layout: "
        f"{OUTPUT_TOP_NAME}"

    )


top = layout.create_cell(
    OUTPUT_TOP_NAME
)


top.insert(

    kdb.CellInstArray(

        input_top.cell_index(),

        kdb.Trans(
            0,
            0,
        ),

    )

)


# ================================================================
# 7. BUILD ACTUAL RECURSIVE CONDUCTOR REGIONS
# ================================================================

M1_REGION = kdb.Region(

    top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


M2_REGION = kdb.Region(

    top.begin_shapes_rec(
        M2_LAYER
    )

).merged()


# ================================================================
# 8. EXTERNAL LVS LABEL PLAN
#
# These coordinates were already validated as conductor anchors
# during Steps 20-26.
#
# Five labels are on Metal1.
# VMEM is placed directly on the shared Metal2 bus.
#
# Internal branch nets are deliberately NOT labeled.
# ================================================================

labels = [

    {
        "name":
            "VDD",

        "layer_name":
            "MET1",

        "layer_index":
            M1_LABEL_LAYER,

        "conductor":
            M1_REGION,

        "x_um":
            0.000,

        "y_um":
            10.000,
    },

    {
        "name":
            "VSS",

        "layer_name":
            "MET1",

        "layer_index":
            M1_LABEL_LAYER,

        "conductor":
            M1_REGION,

        "x_um":
            -3.000,

        "y_um":
            3.000,
    },

    {
        "name":
            "VBIAS",

        "layer_name":
            "MET1",

        "layer_index":
            M1_LABEL_LAYER,

        "conductor":
            M1_REGION,

        "x_um":
            5.000,

        "y_um":
            6.800,
    },

    {
        "name":
            "GATE_W0",

        "layer_name":
            "MET1",

        "layer_index":
            M1_LABEL_LAYER,

        "conductor":
            M1_REGION,

        "x_um":
            7.000,

        "y_um":
            1.700,
    },

    {
        "name":
            "GATE_W1",

        "layer_name":
            "MET1",

        "layer_index":
            M1_LABEL_LAYER,

        "conductor":
            M1_REGION,

        "x_um":
            5.000,

        "y_um":
            4.700,
    },

    {
        "name":
            "VMEM",

        "layer_name":
            "MET2",

        "layer_index":
            M2_LABEL_LAYER,

        "conductor":
            M2_REGION,

        "x_um":
            4.000,

        "y_um":
            1.000,
    },

]


# ================================================================
# 9. PRE-INSERTION LABEL-ANCHOR AUDIT
# ================================================================

print()
print("=" * 80)
print("LABEL ANCHOR AUDIT")
print("=" * 80)


ANCHORS_OK = True


for record in labels:

    hit = region_hits_probe(

        record[
            "conductor"
        ],

        record[
            "x_um"
        ],

        record[
            "y_um"
        ],

    )


    record[
        "anchor_on_conductor"
    ] = bool(
        hit
    )


    ANCHORS_OK &= bool(
        hit
    )


    print(

        f"{record['name']:8s} "
        f"{record['layer_name']:4s} "
        f"@ "
        f"({record['x_um']:.3f}, "
        f"{record['y_um']:.3f}) um "
        f"-> conductor={hit}"

    )


if not ANCHORS_OK:

    raise RuntimeError(

        "At least one LVS label anchor is not "
        "on its intended conductor."

    )


# ================================================================
# 10. INSERT LABELS
# ================================================================

for record in labels:

    text = kdb.Text(

        record[
            "name"
        ],

        kdb.Trans(

            to_dbu(
                record[
                    "x_um"
                ]
            ),

            to_dbu(
                record[
                    "y_um"
                ]
            ),

        ),

    )


    top.shapes(

        record[
            "layer_index"
        ]

    ).insert(
        text
    )


# ================================================================
# 11. LABEL COUNT AUDIT
# ================================================================

M1_LABEL_COUNT = sum(

    1

    for shape
    in top.shapes(
        M1_LABEL_LAYER
    ).each()

    if shape.is_text()

)


M2_LABEL_COUNT = sum(

    1

    for shape
    in top.shapes(
        M2_LABEL_LAYER
    ).each()

    if shape.is_text()

)


LABEL_COUNT_OK = bool(

    M1_LABEL_COUNT == 5

    and

    M2_LABEL_COUNT == 1

)


print()
print("=" * 80)
print("LABEL COUNT AUDIT")
print("=" * 80)

print(
    "MET1 labels:",
    M1_LABEL_COUNT,
    "(expected 5)"
)

print(
    "MET2 labels:",
    M2_LABEL_COUNT,
    "(expected 1)"
)

print(
    "Counts correct:",
    LABEL_COUNT_OK
)


# ================================================================
# 12. LABEL NAME AUDIT
# ================================================================

EXPECTED_NAMES = {

    "VDD",
    "VSS",
    "VBIAS",
    "GATE_W0",
    "GATE_W1",
    "VMEM",

}


actual_names = set()


for layer_index in [

    M1_LABEL_LAYER,

    M2_LABEL_LAYER,

]:

    for shape in top.shapes(
        layer_index
    ).each():

        if not shape.is_text():

            continue


        actual_names.add(

            shape.text.string

        )


LABEL_NAMES_OK = (
    actual_names
    == EXPECTED_NAMES
)


print()
print("=" * 80)
print("LABEL NAME AUDIT")
print("=" * 80)

print(
    "Actual:",
    sorted(
        actual_names
    )
)

print(
    "Expected:",
    sorted(
        EXPECTED_NAMES
    )
)

print(
    "Names correct:",
    LABEL_NAMES_OK
)


# ================================================================
# 13. VERIFY PHYSICAL DRAWING GEOMETRY IS IDENTICAL
#
# Compare every existing input layer recursively between:
#
#   frozen top
#   LVS wrapper top
#
# except the two new label layers.
#
# No conductor/polygon geometry is allowed to change.
# ================================================================

physical_geometry_ok = True

geometry_differences = []


for layer_index in layout.layer_indexes():

    if layer_index in {

        M1_LABEL_LAYER,

        M2_LABEL_LAYER,

    }:

        continue


    input_region = kdb.Region(

        input_top.begin_shapes_rec(
            layer_index
        )

    ).merged()


    output_region = kdb.Region(

        top.begin_shapes_rec(
            layer_index
        )

    ).merged()


    difference = (

        input_region
        ^ output_region

    )


    if not difference.is_empty():

        info = layout.get_info(
            layer_index
        )


        geometry_differences.append(
            {
                "layer":
                    int(
                        info.layer
                    ),

                "datatype":
                    int(
                        info.datatype
                    ),
            }
        )


        physical_geometry_ok = False


print()
print("=" * 80)
print("FROZEN-PHYSICAL-GEOMETRY AUDIT")
print("=" * 80)

print(
    "Physical geometry unchanged:",
    physical_geometry_ok
)

print(
    "Differing physical layers:",
    geometry_differences
)


if not physical_geometry_ok:

    raise RuntimeError(
        "LVS derivative changed physical geometry."
    )


# ================================================================
# 14. CREATE REFERENCE SPICE
#
# Ordinary SPICE MOS syntax:
#
#   Mname D G S B model W=... L=...
#
#
# Corrected synapse topology:
#
# P_REF:
#   D=VBIAS
#   G=VBIAS
#   S=VDD
#   B=VDD
#
# P_U1A:
#   D=N_U1A
#   G=VBIAS
#   S=VDD
#   B=VDD
#
# P_U0:
#   D=N_U0
#   G=VBIAS
#   S=VDD
#   B=VDD
#
# P_U1B:
#   D=N_U1B
#   G=VBIAS
#   S=VDD
#   B=VDD
#
# SW1A:
#   D=N_U1A
#   G=GATE_W1
#   S=VMEM
#   B=VSS
#
# SW0:
#   D=N_U0
#   G=GATE_W0
#   S=VMEM
#   B=VSS
#
# SW1B:
#   D=N_U1B
#   G=GATE_W1
#   S=VMEM
#   B=VSS
#
# MOS S/D are electrically symmetric for this comparison.
# ================================================================

spice_text = """* ================================================================
* NeuroLIF-SKY130
* Corrected 2-bit weighted synapse
* LVS reference schematic V1
*
* Generated for:
*   NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1
*
* External pins:
*   VDD VSS VBIAS GATE_W0 GATE_W1 VMEM
*
* SPICE MOS syntax:
*   Mname D G S B model W=... L=...
* ================================================================

.SUBCKT NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1 VDD VSS VBIAS GATE_W0 GATE_W1 VMEM

* ------------------------------------------------
* PMOS reference + three identical unit branches
* W = 0.84 um
* L = 0.50 um
* ------------------------------------------------

MP_REF  VBIAS  VBIAS    VDD   VDD  sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u
MP_U1A  N_U1A  VBIAS    VDD   VDD  sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u
MP_U0   N_U0   VBIAS    VDD   VDD  sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u
MP_U1B  N_U1B  VBIAS    VDD   VDD  sky130_fd_pr__pfet_01v8 W=0.84u L=0.50u

* ------------------------------------------------
* NMOS weight-selection switches
* W = 1.00 um
* L = 0.15 um
* ------------------------------------------------

MN_SW1A N_U1A  GATE_W1  VMEM  VSS  sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u
MN_SW0  N_U0   GATE_W0  VMEM  VSS  sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u
MN_SW1B N_U1B  GATE_W1  VMEM  VSS  sky130_fd_pr__nfet_01v8 W=1.00u L=0.15u

.ENDS NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1
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
# 15. SIMPLE REFERENCE-NETLIST AUDIT
# ================================================================

spice_upper = spice_text.upper()


expected_models = {

    "SKY130_FD_PR__PFET_01V8":
        4,

    "SKY130_FD_PR__NFET_01V8":
        3,

}


model_counts = {

    model:
        spice_upper.count(
            model
        )

    for model
    in expected_models

}


# Comments contain model-independent text only, so these counts
# should correspond directly to MOS statements.

MODEL_COUNTS_OK = bool(

    model_counts[
        "SKY130_FD_PR__PFET_01V8"
    ] == 4

    and

    model_counts[
        "SKY130_FD_PR__NFET_01V8"
    ] == 3

)


SUBCKT_PRESENT = bool(

    ".SUBCKT "
    + OUTPUT_TOP_NAME

    in spice_upper

)


REFERENCE_OK = bool(

    SPICE_WRITE_OK

    and

    MODEL_COUNTS_OK

    and

    SUBCKT_PRESENT

)


print()
print("=" * 80)
print("REFERENCE SPICE AUDIT")
print("=" * 80)

print(
    "SPICE written:",
    SPICE_WRITE_OK
)

print(
    "PFET count:",
    model_counts[
        "SKY130_FD_PR__PFET_01V8"
    ],
    "(expected 4)"
)

print(
    "NFET count:",
    model_counts[
        "SKY130_FD_PR__NFET_01V8"
    ],
    "(expected 3)"
)

print(
    "Top .SUBCKT present:",
    SUBCKT_PRESENT
)

print(
    "Reference audit:",
    REFERENCE_OK
)


# ================================================================
# 16. COLLECT POPULATED LAYERS
#
# Explicit GDS/OASIS mapping is required in this environment.
# ================================================================

populated_layers = []


for layer_index in layout.layer_indexes():

    used = False


    for cell in layout.each_cell():

        if not cell.shapes(
            layer_index
        ).is_empty():

            used = True
            break


    if not used:

        continue


    info = layout.get_info(
        layer_index
    )


    populated_layers.append(

        (

            int(
                layer_index
            ),

            int(
                info.layer
            ),

            int(
                info.datatype
            ),

        )

    )


# ================================================================
# 17. EXPLICIT SAVE OPTIONS
# ================================================================

def make_save_options(
    fmt,
):

    options = kdb.SaveLayoutOptions()

    options.format = fmt

    options.deselect_all_layers()


    for (
        internal_index,
        gds_layer,
        datatype,
    ) in populated_layers:

        options.add_layer(

            internal_index,

            kdb.LayerInfo(

                int(
                    gds_layer
                ),

                int(
                    datatype
                ),

            ),

        )


    return options


# ================================================================
# 18. WRITE LVS GDS / OASIS
# ================================================================

OUTPUT_GDS.unlink(
    missing_ok=True
)

OUTPUT_OAS.unlink(
    missing_ok=True
)


layout.write(

    str(
        OUTPUT_GDS
    ),

    make_save_options(
        "GDS2"
    ),

)


layout.write(

    str(
        OUTPUT_OAS
    ),

    make_save_options(
        "OASIS"
    ),

)


GDS_WRITE_OK = bool(

    OUTPUT_GDS.exists()

    and

    OUTPUT_GDS.stat().st_size > 0

)


OAS_WRITE_OK = bool(

    OUTPUT_OAS.exists()

    and

    OUTPUT_OAS.stat().st_size > 0

)


# ================================================================
# 19. GDS READBACK
# ================================================================

verify = kdb.Layout()

verify.read(
    str(
        OUTPUT_GDS
    )
)


verify_top = verify.cell(
    OUTPUT_TOP_NAME
)


READBACK_TOP_OK = bool(

    verify_top is not None

    and

    not verify_top.bbox().empty()

)


verify_m1_label = verify.find_layer(
    68,
    5
)

verify_m2_label = verify.find_layer(
    69,
    5
)


readback_names = set()


if (
    verify_top is not None
    and
    verify_m1_label is not None
):

    for shape in verify_top.shapes(
        verify_m1_label
    ).each():

        if shape.is_text():

            readback_names.add(
                shape.text.string
            )


if (
    verify_top is not None
    and
    verify_m2_label is not None
):

    for shape in verify_top.shapes(
        verify_m2_label
    ).each():

        if shape.is_text():

            readback_names.add(
                shape.text.string
            )


READBACK_LABELS_OK = (
    readback_names
    == EXPECTED_NAMES
)


READBACK_OK = bool(

    READBACK_TOP_OK

    and

    READBACK_LABELS_OK

)


print()
print("=" * 80)
print("GDS READBACK AUDIT")
print("=" * 80)

print(
    "Top cell read back:",
    READBACK_TOP_OK
)

print(
    "Labels read back:",
    sorted(
        readback_names
    )
)

print(
    "Label readback correct:",
    READBACK_LABELS_OK
)

print(
    "Overall readback:",
    READBACK_OK
)


# ================================================================
# 20. CONFIRM FROZEN INPUT FILE WAS NOT CHANGED
# ================================================================

INPUT_SHA256_AFTER = sha256_file(
    INPUT_GDS
)


FROZEN_INPUT_UNCHANGED = (

    INPUT_SHA256_BEFORE
    == INPUT_SHA256_AFTER

)


print()
print("=" * 80)
print("FROZEN INPUT INTEGRITY")
print("=" * 80)

print(
    "Before:",
    INPUT_SHA256_BEFORE
)

print(
    "After :",
    INPUT_SHA256_AFTER
)

print(
    "Frozen source unchanged:",
    FROZEN_INPUT_UNCHANGED
)


# ================================================================
# 21. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "28A",

    "artifact":
        "weighted_synapse_lvs_derivative_v1",

    "input": {

        "gds":
            str(
                INPUT_GDS
            ),

        "top":
            INPUT_TOP_NAME,

        "sha256":
            INPUT_SHA256_BEFORE,

        "status":
            "Step 25B DRC clean; Step 26A connectivity pass",

    },

    "output": {

        "gds":
            str(
                OUTPUT_GDS
            ),

        "oas":
            str(
                OUTPUT_OAS
            ),

        "top":
            OUTPUT_TOP_NAME,

        "reference_spice":
            str(
                REFERENCE_SPICE
            ),

    },

    "lvs_labels": [

        {

            "name":
                record[
                    "name"
                ],

            "layer":
                (
                    "68/5"
                    if record[
                        "layer_name"
                    ] == "MET1"
                    else "69/5"
                ),

            "x_um":
                record[
                    "x_um"
                ],

            "y_um":
                record[
                    "y_um"
                ],

            "anchor_on_conductor":
                record[
                    "anchor_on_conductor"
                ],

        }

        for record
        in labels

    ],

    "external_pins": [

        "VDD",

        "VSS",

        "VBIAS",

        "GATE_W0",

        "GATE_W1",

        "VMEM",

    ],

    "internal_unlabeled_nets": [

        "N_U1A",

        "N_U0",

        "N_U1B",

    ],

    "reference_devices": {

        "pfet_01v8":
            4,

        "nfet_01v8":
            3,

        "total_mos":
            7,

    },

    "checks": {

        "anchors_on_conductors":
            ANCHORS_OK,

        "label_count":
            LABEL_COUNT_OK,

        "label_names":
            LABEL_NAMES_OK,

        "physical_geometry_unchanged":
            physical_geometry_ok,

        "reference_spice":
            REFERENCE_OK,

        "gds_write":
            GDS_WRITE_OK,

        "oas_write":
            OAS_WRITE_OK,

        "gds_readback":
            READBACK_OK,

        "frozen_source_unchanged":
            FROZEN_INPUT_UNCHANGED,

    },

}


OUTPUT_MANIFEST.write_text(

    json.dumps(
        manifest,
        indent=2,
    ),

    encoding="utf-8",

)


MANIFEST_OK = bool(

    OUTPUT_MANIFEST.exists()

    and

    OUTPUT_MANIFEST.stat().st_size > 0

)


# ================================================================
# 22. FINAL GATE
# ================================================================

STEP28A_PASS = bool(

    ANCHORS_OK

    and

    LABEL_COUNT_OK

    and

    LABEL_NAMES_OK

    and

    physical_geometry_ok

    and

    REFERENCE_OK

    and

    GDS_WRITE_OK

    and

    OAS_WRITE_OK

    and

    READBACK_OK

    and

    FROZEN_INPUT_UNCHANGED

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 28A RESULT")
print("=" * 80)

print(
    "Label anchors valid       :",
    ANCHORS_OK
)

print(
    "Label counts correct      :",
    LABEL_COUNT_OK
)

print(
    "Label names correct       :",
    LABEL_NAMES_OK
)

print(
    "Physical geometry frozen  :",
    physical_geometry_ok
)

print(
    "Reference SPICE valid     :",
    REFERENCE_OK
)

print(
    "GDS write                :",
    GDS_WRITE_OK
)

print(
    "OASIS write              :",
    OAS_WRITE_OK
)

print(
    "GDS read-back            :",
    READBACK_OK
)

print(
    "Frozen input unchanged    :",
    FROZEN_INPUT_UNCHANGED
)

print(
    "Manifest write           :",
    MANIFEST_OK
)

print()
print(
    "STEP28A_PASS =",
    STEP28A_PASS
)


if not STEP28A_PASS:

    raise RuntimeError(
        "STEP 28A failed."
    )


print()
print("=" * 80)
print("STEP 28A ARTIFACTS")
print("=" * 80)

print()
print(
    "Frozen physical GDS:"
)

print(
    INPUT_GDS
)

print()
print(
    "LVS derivative GDS:"
)

print(
    OUTPUT_GDS
)

print()
print(
    "LVS derivative OASIS:"
)

print(
    OUTPUT_OAS
)

print()
print(
    "Reference schematic:"
)

print(
    REFERENCE_SPICE
)

print()
print(
    "Manifest:"
)

print(
    OUTPUT_MANIFEST
)

print()
print(
    "No LVS has been executed yet."
)