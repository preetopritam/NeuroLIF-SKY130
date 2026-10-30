# ================================================================
# NeuroLIF-SKY130
# STEP 31A — Full-neuron VSS routing V1
#
# Routing Stage 2/9
#
# Input:
#   neurolif_full_neuron_vdd_v3.gds
#
# Adds VSS connections for:
#
#   existing synapse VSS
#   P_TAP_LOGIC
#   MN_ST2 source
#   MN_BUF source
#   MN_LEAK source
#   MN_RST source
#   MP_FB drain
#
# Important topology:
#
#   MP_FB VSS VRAW P_MID VDD
#
# therefore:
#
#   MP_FB RIGHT_SD = drain  = VSS
#   MP_FB LEFT_SD  = source = P_MID
#
# NMOS physical convention:
#
#   LEFT_SD = source
#   RIGHT_SD = drain
#
# except MN_FB already frozen as:
#
#   LEFT_SD  = N_MID
#   RIGHT_SD = VDD
#
# No signal routing is added.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 31A: FULL-NEURON VSS ROUTING V1")
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


INPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v3.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v3.json"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

VDD_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v3_drc.lyrdb"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vss_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_vss_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vss_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VDD_V3"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VSS_V1"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    VDD_DRC_REPORT,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. HASH
# ================================================================

def sha256_file(path):

    digest = hashlib.sha256()

    with path.open("rb") as handle:

        while True:

            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


INPUT_HASH_BEFORE = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. VERIFY REFERENCE TOPOLOGY
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


REFERENCE_REQUIREMENTS = {

    "MN_ST2":
        "MN_ST2 N_MID VMEM VSS VSS",

    "MN_BUF":
        "MN_BUF SPIKE VRAW VSS VSS",

    "MN_LEAK":
        "MN_LEAK VMEM VLEAK VSS VSS",

    "MN_RST":
        "MN_RST VMEM SPIKE VSS VSS",

    "MP_FB":
        "MP_FB VSS VRAW P_MID VDD",

}


reference_checks = {

    name:
        text in reference_text

    for name, text
    in REFERENCE_REQUIREMENTS.items()

}


REFERENCE_OK = all(
    reference_checks.values()
)


print()
print("=" * 80)
print("REFERENCE TOPOLOGY AUDIT")
print("=" * 80)


for name, status in reference_checks.items():

    print(
        f"{name:10s}:",
        status
    )


print(
    "Reference VSS topology valid:",
    REFERENCE_OK
)


if not REFERENCE_OK:

    raise RuntimeError(
        "Frozen reference topology mismatch."
    )


# ================================================================
# 4. LOAD VDD V3
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)


DBU = layout.dbu


input_top = layout.cell(
    INPUT_TOP_NAME
)


if input_top is None:

    raise RuntimeError(
        f"Missing input top: {INPUT_TOP_NAME}"
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
    "Input top:",
    INPUT_TOP_NAME
)


# ================================================================
# 5. REQUIRED CELLS
# ================================================================

CELL_NAMES = {

    "N_LOGIC":
        "N_LOGIC_W1000_L0150",

    "N_FB":
        "N_FB_W0420_L0300",

    "N_LEAK":
        "N_LEAK_W0420_L1000",

    "N_RESET":
        "N_RESET_W1200_L0150",

    "P_FB":
        "P_FB_W0420_L0300",

    "P_TAP":
        "P_TAP_VSS_W1000_H1000",

}


cells = {}


for role, name in CELL_NAMES.items():

    cell = layout.cell(
        name
    )

    if cell is None:

        raise RuntimeError(
            f"Missing required cell: {name}"
        )

    cells[
        role
    ] = cell


# ================================================================
# 6. M1 LAYER
# ================================================================

M1_LAYER = layout.find_layer(
    68,
    20
)


if M1_LAYER is None:

    raise RuntimeError(
        "MET1 68/20 missing."
    )


# ================================================================
# 7. HELPERS
# ================================================================

def to_dbu(value_um):

    return int(
        round(
            float(value_um)
            / DBU
        )
    )


def to_um(value_dbu):

    return (
        float(value_dbu)
        * DBU
    )


def center_um(box):

    return (

        to_um(
            (
                box.left
                +
                box.right
            )
            / 2.0
        ),

        to_um(
            (
                box.bottom
                +
                box.top
            )
            / 2.0
        ),

    )


def translate_box(
    box,
    origin,
):

    dx = to_dbu(
        origin[0]
    )

    dy = to_dbu(
        origin[1]
    )


    return kdb.Box(

        box.left + dx,

        box.bottom + dy,

        box.right + dx,

        box.top + dy,

    )


def horizontal_box(
    x1,
    x2,
    y,
    width,
):

    return kdb.Box(

        to_dbu(
            min(
                x1,
                x2
            )
        ),

        to_dbu(
            y
            -
            width / 2
        ),

        to_dbu(
            max(
                x1,
                x2
            )
        ),

        to_dbu(
            y
            +
            width / 2
        ),

    )


def vertical_box(
    x,
    y1,
    y2,
    width,
):

    return kdb.Box(

        to_dbu(
            x
            -
            width / 2
        ),

        to_dbu(
            min(
                y1,
                y2
            )
        ),

        to_dbu(
            x
            +
            width / 2
        ),

        to_dbu(
            max(
                y1,
                y2
            )
        ),

    )


def probe_region(
    x,
    y,
    half=0.010,
):

    return kdb.Region(

        kdb.Box(

            to_dbu(
                x - half
            ),

            to_dbu(
                y - half
            ),

            to_dbu(
                x + half
            ),

            to_dbu(
                y + half
            ),

        )

    )


# ================================================================
# 8. TERMINAL EXTRACTION
# ================================================================

def primitive_terminal_boxes(cell):

    boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            M1_LAYER
        ).each()

        if (
            shape.is_box()
            or
            shape.is_polygon()
            or
            shape.is_path()
        )

    ]


    if len(boxes) < 4:

        raise RuntimeError(

            f"{cell.name}: expected >=4 terminal M1 shapes, "
            f"found {len(boxes)}"

        )


    def cx(box):

        return (
            box.left
            +
            box.right
        ) / 2.0


    def cy(box):

        return (
            box.bottom
            +
            box.top
        ) / 2.0


    left_sd = min(
        boxes,
        key=cx,
    )

    right_sd = max(
        boxes,
        key=cx,
    )


    gate_candidates = [

        box

        for box in boxes

        if (
            box != left_sd
            and
            box != right_sd
        )

    ]


    bottom_gate = min(
        gate_candidates,
        key=cy,
    )

    top_gate = max(
        gate_candidates,
        key=cy,
    )


    return {

        "LEFT_SD":
            left_sd,

        "RIGHT_SD":
            right_sd,

        "BOTTOM_GATE":
            bottom_gate,

        "TOP_GATE":
            top_gate,

    }


TERMS = {

    "N_LOGIC":
        primitive_terminal_boxes(
            cells["N_LOGIC"]
        ),

    "N_FB":
        primitive_terminal_boxes(
            cells["N_FB"]
        ),

    "N_LEAK":
        primitive_terminal_boxes(
            cells["N_LEAK"]
        ),

    "N_RESET":
        primitive_terminal_boxes(
            cells["N_RESET"]
        ),

    "P_FB":
        primitive_terminal_boxes(
            cells["P_FB"]
        ),

}


print()
print("=" * 80)
print("PRIMITIVE TERMINAL SUMMARY")
print("=" * 80)


for primitive, terminals in TERMS.items():

    print()
    print(primitive)

    for name, box in terminals.items():

        print(
            f"  {name:12s}",
            tuple(
                round(
                    value,
                    3
                )

                for value
                in center_um(
                    box
                )
            )
        )


# ================================================================
# 9. FROZEN PLACEMENT
# ================================================================

ORIGINS = {

    "P_TAP_LOGIC":
        (
            12.5,
            7.0,
        ),

    "MN_ST1":
        (
            16.0,
            7.0,
        ),

    "MN_ST2":
        (
            20.0,
            7.0,
        ),

    "MN_FB":
        (
            24.0,
            7.0,
        ),

    "MN_BUF":
        (
            28.0,
            7.0,
        ),

    "MN_LEAK":
        (
            32.0,
            7.0,
        ),

    "MN_RST":
        (
            36.0,
            7.0,
        ),

    "MP_FB":
        (
            24.0,
            14.0,
        ),

}


def abs_terminal_box(
    primitive,
    terminal,
    instance,
):

    return translate_box(

        TERMS[
            primitive
        ][
            terminal
        ],

        ORIGINS[
            instance
        ],

    )


# ================================================================
# 10. TARGET TERMINALS
# ================================================================

MN_ST2_SOURCE_BOX = abs_terminal_box(
    "N_LOGIC",
    "LEFT_SD",
    "MN_ST2",
)

MN_BUF_SOURCE_BOX = abs_terminal_box(
    "N_LOGIC",
    "LEFT_SD",
    "MN_BUF",
)

MN_LEAK_SOURCE_BOX = abs_terminal_box(
    "N_LEAK",
    "LEFT_SD",
    "MN_LEAK",
)

MN_RST_SOURCE_BOX = abs_terminal_box(
    "N_RESET",
    "LEFT_SD",
    "MN_RST",
)

MP_FB_DRAIN_BOX = abs_terminal_box(
    "P_FB",
    "RIGHT_SD",
    "MP_FB",
)


MN_ST2_SOURCE = center_um(
    MN_ST2_SOURCE_BOX
)

MN_BUF_SOURCE = center_um(
    MN_BUF_SOURCE_BOX
)

MN_LEAK_SOURCE = center_um(
    MN_LEAK_SOURCE_BOX
)

MN_RST_SOURCE = center_um(
    MN_RST_SOURCE_BOX
)

MP_FB_DRAIN = center_um(
    MP_FB_DRAIN_BOX
)


# ================================================================
# 11. P-TAP TARGET
# ================================================================

p_tap = cells[
    "P_TAP"
]


p_tap_m1_region = kdb.Region(

    p_tap.shapes(
        M1_LAYER
    )

).merged()


if p_tap_m1_region.is_empty():

    raise RuntimeError(
        "P_TAP_LOGIC has no M1."
    )


P_TAP_BOX = translate_box(

    p_tap_m1_region.bbox(),

    ORIGINS[
        "P_TAP_LOGIC"
    ],

)


P_TAP_CENTER = center_um(
    P_TAP_BOX
)


# ================================================================
# 12. EXISTING SYNAPSE VSS
#
# Frozen Step 25A:
#
#   rail bbox (-4.0, 2.8) -> (-2.0, 3.2)
#
# Interior anchor:
# ================================================================

SYNAPSE_VSS_ANCHOR = (
    -3.0,
    3.0,
)


PRE_M1 = kdb.Region(

    input_top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


SYNAPSE_VSS_EXISTS = not (

    PRE_M1

    &

    probe_region(
        SYNAPSE_VSS_ANCHOR[0],
        SYNAPSE_VSS_ANCHOR[1],
    )

).is_empty()


print()
print("=" * 80)
print("VSS TARGETS")
print("=" * 80)

print(
    "Synapse VSS:",
    SYNAPSE_VSS_ANCHOR,
    "exists=",
    SYNAPSE_VSS_EXISTS
)

print(
    "P_TAP_LOGIC:",
    tuple(
        round(v, 3)
        for v in P_TAP_CENTER
    )
)

print(
    "MN_ST2 source:",
    tuple(
        round(v, 3)
        for v in MN_ST2_SOURCE
    )
)

print(
    "MN_BUF source:",
    tuple(
        round(v, 3)
        for v in MN_BUF_SOURCE
    )
)

print(
    "MN_LEAK source:",
    tuple(
        round(v, 3)
        for v in MN_LEAK_SOURCE
    )
)

print(
    "MN_RST source:",
    tuple(
        round(v, 3)
        for v in MN_RST_SOURCE
    )
)

print(
    "MP_FB drain:",
    tuple(
        round(v, 3)
        for v in MP_FB_DRAIN
    )
)


if not SYNAPSE_VSS_EXISTS:

    raise RuntimeError(
        "Existing closed-synapse VSS not found."
    )


# ================================================================
# 13. VSS ROUTING PARAMETERS
# ================================================================

VSS_RAIL_Y = (
    0.000
)

VSS_RAIL_WIDTH = (
    0.400
)

BRANCH_WIDTH = (
    0.230
)

TAP_WIDTH = (
    0.400
)

SOURCE_ESCAPE = (
    0.600
)


VSS_RAIL_LEFT = (
    SYNAPSE_VSS_ANCHOR[0]
)

VSS_RAIL_RIGHT = (
    36.800
)


# ================================================================
# 14. NMOS SOURCE ESCAPES
#
# All four VSS-connected NMOS source terminals escape LEFT.
# ================================================================

MN_ST2_ESCAPE = (

    MN_ST2_SOURCE[0]
    -
    SOURCE_ESCAPE,

    MN_ST2_SOURCE[1],

)


MN_BUF_ESCAPE = (

    MN_BUF_SOURCE[0]
    -
    SOURCE_ESCAPE,

    MN_BUF_SOURCE[1],

)


MN_LEAK_ESCAPE = (

    MN_LEAK_SOURCE[0]
    -
    SOURCE_ESCAPE,

    MN_LEAK_SOURCE[1],

)


MN_RST_ESCAPE = (

    MN_RST_SOURCE[0]
    -
    SOURCE_ESCAPE,

    MN_RST_SOURCE[1],

)


# ================================================================
# 15. MP_FB SPECIAL VSS DETOUR
#
# Direct RIGHT descent is blocked by the existing MN_FB->VDD
# vertical at approximately x=25.35.
#
# Therefore:
#
#   MP_FB drain
#      -> short RIGHT exit
#      -> descend below PMOS gate contact
#      -> horizontal LEFT
#      -> descend on left side of MN_FB/VDD column
#      -> VSS rail
# ================================================================

MP_FB_EXIT_X = (
    MP_FB_DRAIN[0]
    +
    0.200
)

MP_FB_DETOUR_Y = (
    13.100
)

MP_FB_DROP_X = (
    23.300
)


# ================================================================
# 16. CREATE OUTPUT WRAPPER
# ================================================================

if layout.cell(
    OUTPUT_TOP_NAME
) is not None:

    raise RuntimeError(
        f"Cell already exists: {OUTPUT_TOP_NAME}"
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
# 17. CREATE VSS GEOMETRY
# ================================================================

route_boxes = {


    # Main low VSS rail.
    "VSS_RAIL":

        horizontal_box(

            VSS_RAIL_LEFT,

            VSS_RAIL_RIGHT,

            VSS_RAIL_Y,

            VSS_RAIL_WIDTH,

        ),


    # Existing synapse VSS -> low rail.
    "SYNAPSE_VSS_BRIDGE":

        vertical_box(

            SYNAPSE_VSS_ANCHOR[0],

            SYNAPSE_VSS_ANCHOR[1],

            VSS_RAIL_Y,

            VSS_RAIL_WIDTH,

        ),


    # P-substrate tap.
    "P_TAP_VSS_BRANCH":

        vertical_box(

            P_TAP_CENTER[0],

            P_TAP_CENTER[1],

            VSS_RAIL_Y,

            TAP_WIDTH,

        ),


    # MN_ST2.
    "MN_ST2_SOURCE_STUB":

        horizontal_box(

            MN_ST2_ESCAPE[0],

            MN_ST2_SOURCE[0],

            MN_ST2_SOURCE[1],

            BRANCH_WIDTH,

        ),

    "MN_ST2_VSS_VERTICAL":

        vertical_box(

            MN_ST2_ESCAPE[0],

            MN_ST2_ESCAPE[1],

            VSS_RAIL_Y,

            BRANCH_WIDTH,

        ),


    # MN_BUF.
    "MN_BUF_SOURCE_STUB":

        horizontal_box(

            MN_BUF_ESCAPE[0],

            MN_BUF_SOURCE[0],

            MN_BUF_SOURCE[1],

            BRANCH_WIDTH,

        ),

    "MN_BUF_VSS_VERTICAL":

        vertical_box(

            MN_BUF_ESCAPE[0],

            MN_BUF_ESCAPE[1],

            VSS_RAIL_Y,

            BRANCH_WIDTH,

        ),


    # MN_LEAK.
    "MN_LEAK_SOURCE_STUB":

        horizontal_box(

            MN_LEAK_ESCAPE[0],

            MN_LEAK_SOURCE[0],

            MN_LEAK_SOURCE[1],

            BRANCH_WIDTH,

        ),

    "MN_LEAK_VSS_VERTICAL":

        vertical_box(

            MN_LEAK_ESCAPE[0],

            MN_LEAK_ESCAPE[1],

            VSS_RAIL_Y,

            BRANCH_WIDTH,

        ),


    # MN_RST.
    "MN_RST_SOURCE_STUB":

        horizontal_box(

            MN_RST_ESCAPE[0],

            MN_RST_SOURCE[0],

            MN_RST_SOURCE[1],

            BRANCH_WIDTH,

        ),

    "MN_RST_VSS_VERTICAL":

        vertical_box(

            MN_RST_ESCAPE[0],

            MN_RST_ESCAPE[1],

            VSS_RAIL_Y,

            BRANCH_WIDTH,

        ),


    # MP_FB drain special detour.
    "MP_FB_DRAIN_EXIT":

        horizontal_box(

            MP_FB_DRAIN[0],

            MP_FB_EXIT_X,

            MP_FB_DRAIN[1],

            BRANCH_WIDTH,

        ),

    "MP_FB_EXIT_VERTICAL":

        vertical_box(

            MP_FB_EXIT_X,

            MP_FB_DRAIN[1],

            MP_FB_DETOUR_Y,

            BRANCH_WIDTH,

        ),

    "MP_FB_DETOUR_LEFT":

        horizontal_box(

            MP_FB_DROP_X,

            MP_FB_EXIT_X,

            MP_FB_DETOUR_Y,

            BRANCH_WIDTH,

        ),

    "MP_FB_VSS_DROP":

        vertical_box(

            MP_FB_DROP_X,

            MP_FB_DETOUR_Y,

            VSS_RAIL_Y,

            BRANCH_WIDTH,

        ),

}


for name, box in route_boxes.items():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


print()
print("=" * 80)
print("NEW VSS M1 SHAPES")
print("=" * 80)


for name, box in route_boxes.items():

    print(
        f"{name:24s}",
        "(",
        round(
            to_um(
                box.left
            ),
            3
        ),
        ",",
        round(
            to_um(
                box.bottom
            ),
            3
        ),
        ",",
        round(
            to_um(
                box.right
            ),
            3
        ),
        ",",
        round(
            to_um(
                box.top
            ),
            3
        ),
        ")"
    )


# ================================================================
# 18. NEW VSS REGION
# ================================================================

NEW_VSS = kdb.Region()


for box in route_boxes.values():

    NEW_VSS.insert(
        box
    )


NEW_VSS.merge()


new_components = list(
    NEW_VSS.each_merged()
)


NEW_VSS_SINGLE_COMPONENT = (
    len(
        new_components
    ) == 1
)


print()
print("=" * 80)
print("NEW VSS ROUTE CONNECTIVITY")
print("=" * 80)

print(
    "Merged components:",
    len(
        new_components
    )
)

print(
    "Single VSS route component:",
    NEW_VSS_SINGLE_COMPONENT
)


# ================================================================
# 19. FULL M1 CONNECTIVITY
# ================================================================

FULL_M1 = (

    PRE_M1
    +
    NEW_VSS

).merged()


FULL_COMPONENTS = list(
    FULL_M1.each_merged()
)


def root_at_point(
    x,
    y,
):

    probe = probe_region(
        x,
        y,
    )


    hits = []


    for index, polygon in enumerate(
        FULL_COMPONENTS
    ):

        region = kdb.Region(
            polygon
        )


        if not (

            region
            &
            probe

        ).is_empty():

            hits.append(
                index
            )


    if len(
        hits
    ) != 1:

        return None


    return hits[0]


# ================================================================
# 20. ALL INTENDED VSS TARGETS
# ================================================================

VSS_TARGETS = {

    "SYNAPSE_VSS":
        SYNAPSE_VSS_ANCHOR,

    "P_TAP_LOGIC":
        P_TAP_CENTER,

    "MN_ST2_SOURCE":
        MN_ST2_SOURCE,

    "MN_BUF_SOURCE":
        MN_BUF_SOURCE,

    "MN_LEAK_SOURCE":
        MN_LEAK_SOURCE,

    "MN_RST_SOURCE":
        MN_RST_SOURCE,

    "MP_FB_DRAIN":
        MP_FB_DRAIN,

}


VSS_ROOTS = {

    name:
        root_at_point(
            point[0],
            point[1],
        )

    for name, point
    in VSS_TARGETS.items()

}


print()
print("=" * 80)
print("VSS ROOT AUDIT")
print("=" * 80)


for name, root in VSS_ROOTS.items():

    print(
        f"{name:18s}: root={root}"
    )


vss_root_set = set(
    VSS_ROOTS.values()
)


VSS_ALL_CONNECTED = bool(

    None not in vss_root_set

    and

    len(
        vss_root_set
    ) == 1

)


VSS_ROOT = (

    next(
        iter(
            vss_root_set
        )
    )

    if VSS_ALL_CONNECTED

    else None

)


print(
    "All intended VSS targets same root:",
    VSS_ALL_CONNECTED
)


# ================================================================
# 21. VDD / VSS SEPARATION
#
# Use known canonical VDD points:
#
#   existing synapse VDD
#   high VDD rail
#   MN_FB VDD drain
# ================================================================

VDD_PROBES = {

    "SYNAPSE_VDD":
        (
            8.500,
            10.000,
        ),

    "HIGH_VDD_RAIL":
        (
            25.350,
            18.220,
        ),

    "MN_FB_DRAIN_VDD":
        center_um(
            abs_terminal_box(
                "N_FB",
                "RIGHT_SD",
                "MN_FB",
            )
        ),

}


VDD_ROOTS = {

    name:
        root_at_point(
            point[0],
            point[1],
        )

    for name, point
    in VDD_PROBES.items()

}


print()
print("=" * 80)
print("VDD / VSS SEPARATION AUDIT")
print("=" * 80)


for name, root in VDD_ROOTS.items():

    print(
        f"{name:18s}: root={root}"
    )


vdd_root_set = set(
    VDD_ROOTS.values()
)


VDD_STILL_CONNECTED = bool(

    None not in vdd_root_set

    and

    len(
        vdd_root_set
    ) == 1

)


VDD_ROOT = (

    next(
        iter(
            vdd_root_set
        )
    )

    if VDD_STILL_CONNECTED

    else None

)


NO_VDD_VSS_SHORT = bool(

    VSS_ALL_CONNECTED

    and

    VDD_STILL_CONNECTED

    and

    VSS_ROOT
    !=
    VDD_ROOT

)


print(
    "VDD remains one root:",
    VDD_STILL_CONNECTED
)

print(
    "VSS root:",
    VSS_ROOT
)

print(
    "VDD root:",
    VDD_ROOT
)

print(
    "VDD and VSS distinct:",
    NO_VDD_VSS_SHORT
)


# ================================================================
# 22. PROTECTED TERMINALS
# ================================================================

protected_boxes = {


    # MN_ST1: none of its M1 terminals are VSS.
    "MN_ST1_LEFT_SD":

        abs_terminal_box(
            "N_LOGIC",
            "LEFT_SD",
            "MN_ST1",
        ),

    "MN_ST1_RIGHT_SD":

        abs_terminal_box(
            "N_LOGIC",
            "RIGHT_SD",
            "MN_ST1",
        ),

    "MN_ST1_GATE_B":

        abs_terminal_box(
            "N_LOGIC",
            "BOTTOM_GATE",
            "MN_ST1",
        ),

    "MN_ST1_GATE_T":

        abs_terminal_box(
            "N_LOGIC",
            "TOP_GATE",
            "MN_ST1",
        ),


    # MN_ST2 drain/gates.
    "MN_ST2_DRAIN":

        abs_terminal_box(
            "N_LOGIC",
            "RIGHT_SD",
            "MN_ST2",
        ),

    "MN_ST2_GATE_B":

        abs_terminal_box(
            "N_LOGIC",
            "BOTTOM_GATE",
            "MN_ST2",
        ),

    "MN_ST2_GATE_T":

        abs_terminal_box(
            "N_LOGIC",
            "TOP_GATE",
            "MN_ST2",
        ),


    # MN_FB:
    # right drain is VDD; left source/gates are signals.
    "MN_FB_SOURCE":

        abs_terminal_box(
            "N_FB",
            "LEFT_SD",
            "MN_FB",
        ),

    "MN_FB_DRAIN_VDD":

        abs_terminal_box(
            "N_FB",
            "RIGHT_SD",
            "MN_FB",
        ),

    "MN_FB_GATE_B":

        abs_terminal_box(
            "N_FB",
            "BOTTOM_GATE",
            "MN_FB",
        ),

    "MN_FB_GATE_T":

        abs_terminal_box(
            "N_FB",
            "TOP_GATE",
            "MN_FB",
        ),


    # Buffer.
    "MN_BUF_DRAIN":

        abs_terminal_box(
            "N_LOGIC",
            "RIGHT_SD",
            "MN_BUF",
        ),

    "MN_BUF_GATE_B":

        abs_terminal_box(
            "N_LOGIC",
            "BOTTOM_GATE",
            "MN_BUF",
        ),

    "MN_BUF_GATE_T":

        abs_terminal_box(
            "N_LOGIC",
            "TOP_GATE",
            "MN_BUF",
        ),


    # Leak.
    "MN_LEAK_DRAIN":

        abs_terminal_box(
            "N_LEAK",
            "RIGHT_SD",
            "MN_LEAK",
        ),

    "MN_LEAK_GATE_B":

        abs_terminal_box(
            "N_LEAK",
            "BOTTOM_GATE",
            "MN_LEAK",
        ),

    "MN_LEAK_GATE_T":

        abs_terminal_box(
            "N_LEAK",
            "TOP_GATE",
            "MN_LEAK",
        ),


    # Reset.
    "MN_RST_DRAIN":

        abs_terminal_box(
            "N_RESET",
            "RIGHT_SD",
            "MN_RST",
        ),

    "MN_RST_GATE_B":

        abs_terminal_box(
            "N_RESET",
            "BOTTOM_GATE",
            "MN_RST",
        ),

    "MN_RST_GATE_T":

        abs_terminal_box(
            "N_RESET",
            "TOP_GATE",
            "MN_RST",
        ),


    # MP_FB source/gates.
    "MP_FB_SOURCE_PMID":

        abs_terminal_box(
            "P_FB",
            "LEFT_SD",
            "MP_FB",
        ),

    "MP_FB_GATE_B":

        abs_terminal_box(
            "P_FB",
            "BOTTOM_GATE",
            "MP_FB",
        ),

    "MP_FB_GATE_T":

        abs_terminal_box(
            "P_FB",
            "TOP_GATE",
            "MP_FB",
        ),

}


PROTECTED_DIRECT_CLEAR = True
PROTECTED_ROOT_CLEAR = True


print()
print("=" * 80)
print("PROTECTED TERMINAL / VSS AUDIT")
print("=" * 80)


for name, box in protected_boxes.items():

    direct_overlap = not (

        NEW_VSS

        &

        kdb.Region(
            box
        )

    ).is_empty()


    point = center_um(
        box
    )


    root = root_at_point(
        point[0],
        point[1],
    )


    shorted_to_vss = bool(

        VSS_ROOT is not None

        and

        root == VSS_ROOT

    )


    clear = bool(

        not direct_overlap

        and

        not shorted_to_vss

    )


    PROTECTED_DIRECT_CLEAR &= (
        not direct_overlap
    )

    PROTECTED_ROOT_CLEAR &= (
        not shorted_to_vss
    )


    print(
        f"{name:20s} "
        f"overlap={direct_overlap} "
        f"root={root} "
        f"clear={clear}"
    )


# ================================================================
# 23. UNEXPECTED PRE-EXISTING M1 OVERLAP AUDIT
#
# New VSS is allowed to overlap pre-existing M1 ONLY at:
#
#   existing synapse VSS
#   P_TAP_LOGIC
#   intended source/drain terminals
#
# This catches accidental route crossings that a center probe could
# miss.
# ================================================================

ALLOWED_OVERLAP = kdb.Region()


# Existing synapse VSS rail.
ALLOWED_OVERLAP.insert(

    kdb.Box(

        to_dbu(
            -4.0
        ),

        to_dbu(
            2.8
        ),

        to_dbu(
            -2.0
        ),

        to_dbu(
            3.2
        ),

    )

)


for box in [

    P_TAP_BOX,

    MN_ST2_SOURCE_BOX,

    MN_BUF_SOURCE_BOX,

    MN_LEAK_SOURCE_BOX,

    MN_RST_SOURCE_BOX,

    MP_FB_DRAIN_BOX,

]:

    ALLOWED_OVERLAP.insert(
        box
    )


ALLOWED_OVERLAP.merge()


ACTUAL_PRE_OVERLAP = (

    NEW_VSS
    &
    PRE_M1

)


UNEXPECTED_OVERLAP = (

    ACTUAL_PRE_OVERLAP
    -
    ALLOWED_OVERLAP

)


NO_UNEXPECTED_M1_OVERLAP = (
    UNEXPECTED_OVERLAP.is_empty()
)


print()
print("=" * 80)
print("GLOBAL PRE-EXISTING M1 OVERLAP AUDIT")
print("=" * 80)

print(
    "Unexpected M1 overlap:",
    not NO_UNEXPECTED_M1_OVERLAP
)

print(
    "Only intended landing overlaps:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 24. ROUTE COUNT
# ================================================================

TOP_LEVEL_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        M1_LAYER
    ).each()

)


EXPECTED_TOP_LEVEL_M1 = (
    15
)


TOP_LEVEL_M1_COUNT_OK = (

    TOP_LEVEL_M1_COUNT
    ==
    EXPECTED_TOP_LEVEL_M1

)


print()
print("=" * 80)
print("TOP-LEVEL VSS SHAPE COUNT")
print("=" * 80)

print(
    "M1 shapes:",
    TOP_LEVEL_M1_COUNT
)

print(
    "Expected:",
    EXPECTED_TOP_LEVEL_M1
)

print(
    "Count correct:",
    TOP_LEVEL_M1_COUNT_OK
)


# ================================================================
# 25. POPULATED LAYERS
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
# 26. SAVE OPTIONS
# ================================================================

def make_save_options(fmt):

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

                gds_layer,

                datatype,

            ),

        )


    return options


# ================================================================
# 27. WRITE
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


GDS_OK = bool(

    OUTPUT_GDS.exists()

    and

    OUTPUT_GDS.stat().st_size > 0

)


OAS_OK = bool(

    OUTPUT_OAS.exists()

    and

    OUTPUT_OAS.stat().st_size > 0

)


# ================================================================
# 28. READBACK
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


READBACK_OK = bool(

    verify_top is not None

    and

    not verify_top.bbox().empty()

)


verify_m1 = verify.find_layer(
    68,
    20
)


READBACK_M1_COUNT = 0


if (
    verify_top is not None
    and
    verify_m1 is not None
):

    READBACK_M1_COUNT = sum(

        1

        for _
        in verify_top.shapes(
            verify_m1
        ).each()

    )


READBACK_COUNT_OK = (

    READBACK_M1_COUNT
    ==
    EXPECTED_TOP_LEVEL_M1

)


# ================================================================
# 29. INPUT INTEGRITY
# ================================================================

INPUT_HASH_AFTER = sha256_file(
    INPUT_GDS
)


INPUT_UNCHANGED = (

    INPUT_HASH_BEFORE
    ==
    INPUT_HASH_AFTER

)


# ================================================================
# 30. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "31A",

    "routing_stage":
        "2_of_9_VSS",

    "status":
        "CONSTRUCTION_PASS_PENDING_DRC",

    "input": {

        "gds":
            str(
                INPUT_GDS
            ),

        "top":
            INPUT_TOP_NAME,

        "sha256":
            INPUT_HASH_BEFORE,

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

    },

    "net":
        "VSS",

    "vss_targets": {

        name:
            list(
                point
            )

        for name, point
        in VSS_TARGETS.items()

    },

    "routing": {

        "layer":
            "MET1 68/20",

        "rail_y_um":
            VSS_RAIL_Y,

        "rail_width_um":
            VSS_RAIL_WIDTH,

        "branch_width_um":
            BRANCH_WIDTH,

        "nmos_source_escape_um":
            SOURCE_ESCAPE,

        "nmos_source_escape_direction":
            "LEFT",

        "mp_fb": {

            "drain":
                "RIGHT_SD",

            "net":
                "VSS",

            "exit_x_um":
                MP_FB_EXIT_X,

            "detour_y_um":
                MP_FB_DETOUR_Y,

            "drop_x_um":
                MP_FB_DROP_X,

        },

    },

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "synapse_vss_exists":
            SYNAPSE_VSS_EXISTS,

        "new_vss_single_component":
            NEW_VSS_SINGLE_COMPONENT,

        "all_vss_targets_connected":
            VSS_ALL_CONNECTED,

        "vdd_still_connected":
            VDD_STILL_CONNECTED,

        "no_vdd_vss_short":
            NO_VDD_VSS_SHORT,

        "protected_direct_clear":
            PROTECTED_DIRECT_CLEAR,

        "protected_roots_clear":
            PROTECTED_ROOT_CLEAR,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "top_level_m1_count":
            TOP_LEVEL_M1_COUNT_OK,

        "gds_write":
            GDS_OK,

        "oas_write":
            OAS_OK,

        "readback":
            READBACK_OK,

        "readback_count":
            READBACK_COUNT_OK,

        "input_unchanged":
            INPUT_UNCHANGED,

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
# 31. FINAL GATE
# ================================================================

STEP31A_PASS = bool(

    REFERENCE_OK

    and

    SYNAPSE_VSS_EXISTS

    and

    NEW_VSS_SINGLE_COMPONENT

    and

    VSS_ALL_CONNECTED

    and

    VDD_STILL_CONNECTED

    and

    NO_VDD_VSS_SHORT

    and

    PROTECTED_DIRECT_CLEAR

    and

    PROTECTED_ROOT_CLEAR

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    TOP_LEVEL_M1_COUNT_OK

    and

    GDS_OK

    and

    OAS_OK

    and

    READBACK_OK

    and

    READBACK_COUNT_OK

    and

    INPUT_UNCHANGED

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 31A RESULT")
print("=" * 80)

print(
    "Reference VSS topology      :",
    REFERENCE_OK
)

print(
    "Existing synapse VSS        :",
    SYNAPSE_VSS_EXISTS
)

print(
    "New VSS route connected     :",
    NEW_VSS_SINGLE_COMPONENT
)

print(
    "All VSS targets same root   :",
    VSS_ALL_CONNECTED
)

print(
    "VDD remains connected       :",
    VDD_STILL_CONNECTED
)

print(
    "VDD / VSS distinct          :",
    NO_VDD_VSS_SHORT
)

print(
    "Protected boxes clear       :",
    PROTECTED_DIRECT_CLEAR
)

print(
    "Protected roots clear       :",
    PROTECTED_ROOT_CLEAR
)

print(
    "No unexpected M1 overlap    :",
    NO_UNEXPECTED_M1_OVERLAP
)

print(
    "Top-level M1 count          :",
    TOP_LEVEL_M1_COUNT_OK
)

print(
    "GDS write                   :",
    GDS_OK
)

print(
    "OASIS write                 :",
    OAS_OK
)

print(
    "GDS read-back               :",
    READBACK_OK
)

print(
    "Read-back route count       :",
    READBACK_COUNT_OK
)

print(
    "VDD V3 input unchanged      :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP31A_PASS =",
    STEP31A_PASS
)


if not STEP31A_PASS:

    raise RuntimeError(
        "STEP 31A VSS construction failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 2/9 — VSS CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "Connected to VSS:"
)

print(
    "  closed-synapse VSS"
)

print(
    "  P_TAP_LOGIC"
)

print(
    "  MN_ST2 source"
)

print(
    "  MN_BUF source"
)

print(
    "  MN_LEAK source"
)

print(
    "  MN_RST source"
)

print(
    "  MP_FB drain"
)

print()
print(
    "Preserved:"
)

print(
    "  VDD V3 network"
)

print(
    "  all protected signal terminals"
)

print()
print(
    "Candidate:"
)

print(
    OUTPUT_GDS
)

print()
print(
    "NEXT:"
)

print(
    "  Official SKY130 DRC on VSS V1."
)