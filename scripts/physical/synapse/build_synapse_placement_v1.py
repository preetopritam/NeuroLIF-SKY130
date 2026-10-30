# ================================================================
# NeuroLIF-SKY130
# STEP 19A — Weighted-synapse placement V1
#
# PLACEMENT ONLY.
#
# No circuit routing is created.
# No S/D terminal is electrically assigned yet.
#
# Topology represented:
#
#   PMOS:
#       P_REF
#       P_U0
#       P_U1A
#       P_U1B
#
#   NMOS switches:
#       SW0
#       SW1A
#       SW1B
#
#   Body ties:
#       N_TAP_VDD -> future VDD
#       P_TAP_VSS -> future VSS
#
# PMOS devices are placed in one continuous NWELL.
# ================================================================

from pathlib import Path
import json
import sys

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 19A: SYNAPSE PLACEMENT V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PRIMITIVE_GDS = (
    PROJECT_ROOT
    / "layout"
    / "primitives"
    / "neurolif_mos_primitives_nf1.gds"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_GDS = (
    OUTPUT_DIR
    / "neurolif_synapse_placement_v1.gds"
)

OUTPUT_OAS = (
    OUTPUT_DIR
    / "neurolif_synapse_placement_v1.oas"
)

MANIFEST_FILE = (
    OUTPUT_DIR
    / "neurolif_synapse_placement_v1.json"
)


SKY130_PYTHON_ROOT = (
    Path.home()
    / "KLayout"
    / "salt"
    / "Efabless_sky130"
    / "tech"
    / "sky130"
    / "python"
)


print()
print("Primitive GDS :", PRIMITIVE_GDS)
print("Output GDS    :", OUTPUT_GDS)
print("Output OASIS  :", OUTPUT_OAS)
print("Manifest      :", MANIFEST_FILE)


if not PRIMITIVE_GDS.exists():
    raise FileNotFoundError(
        PRIMITIVE_GDS
    )


if not SKY130_PYTHON_ROOT.exists():
    raise FileNotFoundError(
        SKY130_PYTHON_ROOT
    )


if str(SKY130_PYTHON_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(SKY130_PYTHON_ROOT)
    )


# ================================================================
# 2. IMPORT PACKAGE TAP GENERATOR
# ================================================================

from cells.via_generator import (
    vias_gen_draw,
)


# ================================================================
# 3. LOAD CANONICAL MOS LIBRARY
# ================================================================

layout = kdb.Layout()

layout.read(
    str(
        PRIMITIVE_GDS
    )
)


DBU = layout.dbu


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
    "Cells after primitive load:",
    layout.cells()
)


# ================================================================
# 4. REQUIRED CANONICAL CELLS
# ================================================================

P_SYN_NAME = (
    "P_SYN_W0840_L0500"
)

N_SWITCH_NAME = (
    "N_LOGIC_W1000_L0150"
)


p_syn = layout.cell(
    P_SYN_NAME
)

n_switch = layout.cell(
    N_SWITCH_NAME
)


if p_syn is None:

    raise RuntimeError(
        f"Missing canonical primitive: {P_SYN_NAME}"
    )


if n_switch is None:

    raise RuntimeError(
        f"Missing canonical primitive: {N_SWITCH_NAME}"
    )


print()
print(
    "P_SYN bbox:",
    p_syn.bbox()
)

print(
    "N_SWITCH bbox:",
    n_switch.bbox()
)


# ================================================================
# 5. CREATE CANONICAL TAP CELLS
#
# Exact generator settings already validated in Step 18E/F.
# ================================================================

N_TAP_NAME = (
    "N_TAP_VDD_W1000_H1000"
)

P_TAP_NAME = (
    "P_TAP_VSS_W1000_H1000"
)


n_tap = layout.cell(
    N_TAP_NAME
)

if n_tap is None:

    n_tap = layout.create_cell(
        N_TAP_NAME
    )


    vias_gen_draw(

        cell=n_tap,

        l=1.0,

        w=1.0,

        start_layer="n_tap",

        end_layer="metal1",

    )


p_tap = layout.cell(
    P_TAP_NAME
)

if p_tap is None:

    p_tap = layout.create_cell(
        P_TAP_NAME
    )


    vias_gen_draw(

        cell=p_tap,

        l=1.0,

        w=1.0,

        start_layer="p_tap",

        end_layer="metal1",

    )


print()
print("=" * 80)
print("BODY-TAP CELLS")
print("=" * 80)

print(
    N_TAP_NAME,
    "bbox:",
    n_tap.bbox()
)

print(
    P_TAP_NAME,
    "bbox:",
    p_tap.bbox()
)


# ================================================================
# 6. TOP CELL
# ================================================================

TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_PLACEMENT_V1"
)


existing_top = layout.cell(
    TOP_NAME
)

if existing_top is not None:

    raise RuntimeError(
        f"Top cell already exists: {TOP_NAME}"
    )


top = layout.create_cell(
    TOP_NAME
)


# ================================================================
# 7. PLACEMENT PLAN
#
# All coordinates are instance ORIGINS in micrometers.
#
# PMOS row pitch = 3 um
#
# Arrangement:
#
#     P_U1A | P_REF | P_U0 | P_U1B
#
# The two W1 units therefore flank the complete row.
#
# NMOS switch channel centers are aligned approximately under
# their associated PMOS channel centers.
# ================================================================

PLACEMENTS_UM = {

    # Shared PMOS body tie
    "N_TAP_VDD": (
        -2.500,
        8.000,
    ),

    # Four identical PMOS devices
    "P_U1A": (
        0.000,
        8.000,
    ),

    "P_REF": (
        3.000,
        8.000,
    ),

    "P_U0": (
        6.000,
        8.000,
    ),

    "P_U1B": (
        9.000,
        8.000,
    ),

    # Shared NMOS substrate tie
    "P_TAP_VSS": (
        -2.500,
        2.500,
    ),

    # Switches
    #
    # +0.175 um approximately aligns the nfet channel center
    # with the corresponding PMOS channel center.
    "SW1A": (
        0.175,
        2.500,
    ),

    "SW0": (
        6.175,
        2.500,
    ),

    "SW1B": (
        9.175,
        2.500,
    ),

}


ROLE_TO_CELL = {

    "N_TAP_VDD":
        n_tap,

    "P_U1A":
        p_syn,

    "P_REF":
        p_syn,

    "P_U0":
        p_syn,

    "P_U1B":
        p_syn,

    "P_TAP_VSS":
        p_tap,

    "SW1A":
        n_switch,

    "SW0":
        n_switch,

    "SW1B":
        n_switch,

}


# ================================================================
# 8. COORDINATE HELPERS
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


def translated_box(
    box,
    dx,
    dy,
):

    return kdb.Box(

        box.left + dx,

        box.bottom + dy,

        box.right + dx,

        box.top + dy,

    )


def box_um(
    box,
):

    return (

        box.left * DBU,

        box.bottom * DBU,

        box.right * DBU,

        box.top * DBU,

    )


# ================================================================
# 9. PLACE INSTANCES
# ================================================================

print()
print("=" * 80)
print("INSTANCE PLACEMENT")
print("=" * 80)


placement_manifest = {}


for role, (
    x_um,
    y_um,
) in PLACEMENTS_UM.items():

    cell = ROLE_TO_CELL[
        role
    ]


    dx = to_dbu(
        x_um
    )

    dy = to_dbu(
        y_um
    )


    top.insert(

        kdb.CellInstArray(

            cell.cell_index(),

            kdb.Trans(
                dx,
                dy,
            ),

        )

    )


    placed_bbox = translated_box(

        cell.bbox(),

        dx,

        dy,

    )


    placement_manifest[
        role
    ] = {

        "cell":
            cell.name,

        "origin_um": [
            x_um,
            y_um,
        ],

        "bbox_um": [
            round(
                value,
                3,
            )
            for value in box_um(
                placed_bbox
            )
        ],

    }


    print(
        f"{role:12s} "
        f"-> {cell.name:24s} "
        f"@ ({x_um:.3f}, "
        f"{y_um:.3f}) um"
    )


# ================================================================
# 10. BUILD ONE CONTINUOUS PMOS NWELL
#
# IMPORTANT:
#
# Each canonical P_SYN already has a valid NWELL around itself.
# The N_TAP also has an NWELL.
#
# A single NWELL rectangle spanning their outer NWELL bounds is
# added so that:
#
#   N_TAP + P_U1A + P_REF + P_U0 + P_U1B
#
# reside in one electrically continuous n-well.
#
# This is NOT electrical Metal1 routing.
# ================================================================

NWELL_LAYER = layout.find_layer(
    64,
    20,
)


if NWELL_LAYER is None:

    NWELL_LAYER = layout.layer(
        kdb.LayerInfo(
            64,
            20,
        )
    )


PMOS_WELL_ROLES = [

    "N_TAP_VDD",

    "P_U1A",

    "P_REF",

    "P_U0",

    "P_U1B",

]


nwell_boxes = []


for role in PMOS_WELL_ROLES:

    cell = ROLE_TO_CELL[
        role
    ]


    x_um, y_um = (
        PLACEMENTS_UM[
            role
        ]
    )


    dx = to_dbu(
        x_um
    )

    dy = to_dbu(
        y_um
    )


    for shape in cell.shapes(
        NWELL_LAYER
    ).each():

        nwell_boxes.append(

            translated_box(

                shape.bbox(),

                dx,

                dy,

            )

        )


if not nwell_boxes:

    raise RuntimeError(
        "No PMOS/N-tap NWELL geometry found."
    )


COMMON_NWELL = kdb.Box(

    min(
        box.left
        for box in nwell_boxes
    ),

    min(
        box.bottom
        for box in nwell_boxes
    ),

    max(
        box.right
        for box in nwell_boxes
    ),

    max(
        box.top
        for box in nwell_boxes
    ),

)


top.shapes(
    NWELL_LAYER
).insert(
    COMMON_NWELL
)


print()
print("=" * 80)
print("COMMON PMOS NWELL")
print("=" * 80)

print(
    "NWELL bbox um:",
    tuple(
        round(
            value,
            3,
        )
        for value
        in box_um(
            COMMON_NWELL
        )
    )
)


# ================================================================
# 11. COMMON-NWELL CONNECTIVITY AUDIT
#
# Every original PMOS/n-tap nwell rectangle must overlap the new
# common well rectangle.
# ================================================================

def overlaps(
    a,
    b,
):

    return not (

        a.right <= b.left
        or

        a.left >= b.right
        or

        a.top <= b.bottom
        or

        a.bottom >= b.top

    )


WELL_CONNECTIVITY_OK = all(

    overlaps(
        COMMON_NWELL,
        box,
    )

    for box in nwell_boxes

)


print(
    "All PMOS/tap wells overlap common NWELL:",
    WELL_CONNECTIVITY_OK
)


if not WELL_CONNECTIVITY_OK:

    raise RuntimeError(
        "Common NWELL does not overlap every required well."
    )


# ================================================================
# 12. VERTICAL ISOLATION AUDIT
#
# Ensure the common PMOS NWELL does not reach the NMOS row or
# p-substrate tap.
# ================================================================

NMOS_ROLES = [

    "P_TAP_VSS",

    "SW1A",

    "SW0",

    "SW1B",

]


nmos_bboxes = []


for role in NMOS_ROLES:

    cell = ROLE_TO_CELL[
        role
    ]


    x_um, y_um = (
        PLACEMENTS_UM[
            role
        ]
    )


    nmos_bboxes.append(

        translated_box(

            cell.bbox(),

            to_dbu(
                x_um
            ),

            to_dbu(
                y_um
            ),

        )

    )


NWELL_CLEAR_OF_NMOS = all(

    not overlaps(
        COMMON_NWELL,
        box,
    )

    for box in nmos_bboxes

)


print()
print(
    "Common NWELL clear of NMOS/p-tap:",
    NWELL_CLEAR_OF_NMOS
)


if not NWELL_CLEAR_OF_NMOS:

    raise RuntimeError(
        "PMOS NWELL overlaps NMOS-row geometry."
    )


# ================================================================
# 13. TOPOLOGY / ROLE AUDIT
# ================================================================

print()
print("=" * 80)
print("SYNAPSE ROLE AUDIT")
print("=" * 80)


EXPECTED_PMOS = {

    "P_REF",
    "P_U0",
    "P_U1A",
    "P_U1B",

}

EXPECTED_SWITCHES = {

    "SW0",
    "SW1A",
    "SW1B",

}


actual_pmos = {

    role

    for role, cell
    in ROLE_TO_CELL.items()

    if cell.name == P_SYN_NAME

}

actual_switches = {

    role

    for role, cell
    in ROLE_TO_CELL.items()

    if (
        cell.name
        == N_SWITCH_NAME
    )

}


PMOS_COUNT_OK = (
    actual_pmos
    == EXPECTED_PMOS
)

SWITCH_COUNT_OK = (
    actual_switches
    == EXPECTED_SWITCHES
)


print(
    "PMOS roles:",
    sorted(
        actual_pmos
    )
)

print(
    "PMOS topology correct:",
    PMOS_COUNT_OK
)

print()

print(
    "Switch roles:",
    sorted(
        actual_switches
    )
)

print(
    "Switch topology correct:",
    SWITCH_COUNT_OK
)


# ================================================================
# 14. NO ROUTING CLAIM
#
# We intentionally add no new Metal1 geometry to the top cell.
# The only top-level geometry created is the common NWELL patch.
# ================================================================

MET1_LAYER = layout.find_layer(
    68,
    20,
)


TOP_LEVEL_MET1_COUNT = 0


if MET1_LAYER is not None:

    TOP_LEVEL_MET1_COUNT = sum(

        1

        for _
        in top.shapes(
            MET1_LAYER
        ).each()

    )


NO_ROUTING = (
    TOP_LEVEL_MET1_COUNT == 0
)


print()
print("=" * 80)
print("ROUTING AUDIT")
print("=" * 80)

print(
    "Top-level MET1 shapes:",
    TOP_LEVEL_MET1_COUNT
)

print(
    "NO_ROUTING =",
    NO_ROUTING
)


if not NO_ROUTING:

    raise RuntimeError(
        "Unexpected top-level Metal1 routing exists."
    )


# ================================================================
# 15. TOP BOUNDING BOX
# ================================================================

print()
print("=" * 80)
print("TOP GEOMETRY")
print("=" * 80)

print(
    "Top bbox:",
    top.bbox()
)

print(
    "Top bbox um:",
    tuple(
        round(
            value,
            3,
        )
        for value
        in box_um(
            top.bbox()
        )
    )
)


# ================================================================
# 16. USED-LAYER INVENTORY
# ================================================================

used_layers = []


for layer_index in layout.layer_indexes():

    used = False


    # Check top + all child cells reachable conceptually
    # through this output library.
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


    used_layers.append(

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


print()
print("=" * 80)
print("USED LAYERS")
print("=" * 80)


for internal, layer, datatype in used_layers:

    print(
        f"Internal {internal} "
        f"-> GDS "
        f"{layer}/{datatype}"
    )


# ================================================================
# 17. EXPLICIT SAVE OPTIONS
# ================================================================

def make_save_options(
    fmt,
):

    options = (
        kdb.SaveLayoutOptions()
    )

    options.format = fmt

    options.deselect_all_layers()


    for internal, layer, datatype in used_layers:

        options.add_layer(

            internal,

            kdb.LayerInfo(
                layer,
                datatype,
            ),

        )


    return options


# ================================================================
# 18. WRITE GDS
# ================================================================

OUTPUT_GDS.unlink(
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


GDS_OK = bool(

    OUTPUT_GDS.exists()

    and

    OUTPUT_GDS.stat().st_size > 0

)


# ================================================================
# 19. WRITE OASIS
# ================================================================

OUTPUT_OAS.unlink(
    missing_ok=True
)


layout.write(

    str(
        OUTPUT_OAS
    ),

    make_save_options(
        "OASIS"
    ),

)


OAS_OK = bool(

    OUTPUT_OAS.exists()

    and

    OUTPUT_OAS.stat().st_size > 0

)


# ================================================================
# 20. READ-BACK
# ================================================================

verify = kdb.Layout()

verify.read(
    str(
        OUTPUT_GDS
    )
)


verify_top = verify.cell(
    TOP_NAME
)


READBACK_OK = bool(

    verify_top is not None

    and

    not verify_top.bbox().empty()

)


# ================================================================
# 21. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "revision":
        "placement_v1",

    "top_cell":
        TOP_NAME,

    "routing_present":
        False,

    "device_topology": {

        "P_REF":
            "P_SYN_W0840_L0500",

        "P_U0":
            "P_SYN_W0840_L0500",

        "P_U1A":
            "P_SYN_W0840_L0500",

        "P_U1B":
            "P_SYN_W0840_L0500",

        "SW0":
            "N_LOGIC_W1000_L0150",

        "SW1A":
            "N_LOGIC_W1000_L0150",

        "SW1B":
            "N_LOGIC_W1000_L0150",

    },

    "logical_weight_mapping": {

        "00":
            [],

        "01":
            ["P_U0"],

        "10":
            [
                "P_U1A",
                "P_U1B",
            ],

        "11":
            [
                "P_U0",
                "P_U1A",
                "P_U1B",
            ],

    },

    "body_strategy": {

        "pmos":
            "shared continuous NWELL "
            "with N_TAP_VDD",

        "pmos_body_future_net":
            "VDD",

        "nmos":
            "P_TAP_VSS substrate tap",

        "nmos_body_future_net":
            "VSS",

    },

    "pmos_row_order": [

        "P_U1A",
        "P_REF",
        "P_U0",
        "P_U1B",

    ],

    "placement_um":
        placement_manifest,

    "common_nwell_bbox_um": [

        round(
            value,
            3,
        )

        for value in box_um(
            COMMON_NWELL
        )

    ],

    "checks": {

        "pmos_count_topology":
            PMOS_COUNT_OK,

        "switch_count_topology":
            SWITCH_COUNT_OK,

        "well_connectivity":
            WELL_CONNECTIVITY_OK,

        "nwell_clear_of_nmos":
            NWELL_CLEAR_OF_NMOS,

        "no_routing":
            NO_ROUTING,

        "gds_write":
            GDS_OK,

        "oas_write":
            OAS_OK,

        "readback":
            READBACK_OK,

    },

}


MANIFEST_FILE.write_text(

    json.dumps(
        manifest,
        indent=2,
    ),

    encoding="utf-8",

)


MANIFEST_OK = bool(

    MANIFEST_FILE.exists()

    and

    MANIFEST_FILE.stat().st_size > 0

)


# ================================================================
# 22. FINAL GATE
# ================================================================

STEP19A_PASS = bool(

    PMOS_COUNT_OK

    and

    SWITCH_COUNT_OK

    and

    WELL_CONNECTIVITY_OK

    and

    NWELL_CLEAR_OF_NMOS

    and

    NO_ROUTING

    and

    GDS_OK

    and

    OAS_OK

    and

    READBACK_OK

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 19A RESULT")
print("=" * 80)


print(
    "4 PMOS topology        :",
    PMOS_COUNT_OK
)

print(
    "3 switch topology      :",
    SWITCH_COUNT_OK
)

print(
    "Common NWELL connected :",
    WELL_CONNECTIVITY_OK
)

print(
    "NWELL clear of NMOS    :",
    NWELL_CLEAR_OF_NMOS
)

print(
    "Routing absent         :",
    NO_ROUTING
)

print(
    "GDS write              :",
    GDS_OK
)

print(
    "OASIS write            :",
    OAS_OK
)

print(
    "GDS read-back          :",
    READBACK_OK
)

print(
    "Manifest write         :",
    MANIFEST_OK
)

print()
print(
    "STEP19A_PASS =",
    STEP19A_PASS
)


if not STEP19A_PASS:

    raise RuntimeError(
        "STEP 19A failed."
    )


print()
print(
    "WEIGHTED SYNAPSE PLACEMENT V1 GENERATED"
)

print()
print(
    "NO ELECTRICAL ROUTING HAS BEEN CREATED."
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)