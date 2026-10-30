# ================================================================
# NeuroLIF-SKY130
# STEP 35A — Full-neuron N_MID routing V1
#
# Routing Stage 6/9
#
# Input:
#   neurolif_full_neuron_pmid_v2.gds
#
# Frozen topology:
#
#   MN_ST1 VRAW  VMEM N_MID VSS
#   MN_ST2 N_MID VMEM VSS   VSS
#   MN_FB  VDD   VRAW N_MID VSS
#
# Therefore N_MID connects:
#
#   MN_ST1 LEFT_SD  = source = N_MID
#   MN_ST2 RIGHT_SD = drain  = N_MID
#   MN_FB  LEFT_SD  = source = N_MID
#
# Routing strategy:
#
#   - M1 left section joins MN_ST1 + MN_ST2
#   - M1 right section joins MN_FB
#   - short M2 bridge crosses the existing MP_FB->VSS M1 drop
#   - 2 x M1/VIA1/M2 landing sites
#
# Existing VMEM M2 columns at x=17 and x=21 are NOT crossed.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 35A: FULL-NEURON N_MID ROUTING V1")
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
    / "neurolif_full_neuron_pmid_v2.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_pmid_v2.json"
)

REFERENCE_SPICE = (
    NEURON_DIR
    / "neurolif_full_neuron_reference_v1.spice"
)

PMID_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_pmid_v2_drc.lyrdb"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_nmid_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_nmid_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_nmid_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_PMID_V2"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_NMID_V1"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    PMID_DRC_REPORT,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. HASH
# ================================================================

def sha256_file(path):

    h = hashlib.sha256()

    with path.open("rb") as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            h.update(block)

    return h.hexdigest()


INPUT_HASH_BEFORE = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. REFERENCE TOPOLOGY
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


REFERENCE_LINES = {

    "MN_ST1":
        "MN_ST1 VRAW VMEM N_MID VSS",

    "MN_ST2":
        "MN_ST2 N_MID VMEM VSS VSS",

    "MN_FB":
        "MN_FB VDD VRAW N_MID VSS",

}


reference_checks = {

    name:
        line in reference_text

    for name, line
    in REFERENCE_LINES.items()

}


REFERENCE_OK = all(
    reference_checks.values()
)


print()
print("=" * 80)
print("REFERENCE N_MID TOPOLOGY")
print("=" * 80)


for name, status in reference_checks.items():

    print(
        f"{name:10s}:",
        status
    )


print(
    "Reference valid:",
    REFERENCE_OK
)


if not REFERENCE_OK:

    raise RuntimeError(
        "Frozen N_MID topology mismatch."
    )


# ================================================================
# 4. LOAD STAGE-5 CANONICAL GDS
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
# 5. LAYERS
# ================================================================

M1_LAYER = layout.find_layer(
    68,
    20
)

VIA1_LAYER = layout.find_layer(
    68,
    44
)

M2_LAYER = layout.find_layer(
    69,
    20
)


for name, layer_index in [

    ("MET1 68/20", M1_LAYER),

    ("VIA1 68/44", VIA1_LAYER),

    ("MET2 69/20", M2_LAYER),

]:

    if layer_index is None:

        raise RuntimeError(
            f"Missing layer: {name}"
        )


# ================================================================
# 6. PRIMITIVES
# ================================================================

N_LOGIC_NAME = (
    "N_LOGIC_W1000_L0150"
)

N_FB_NAME = (
    "N_FB_W0420_L0300"
)


n_logic = layout.cell(
    N_LOGIC_NAME
)

n_fb = layout.cell(
    N_FB_NAME
)


if n_logic is None:
    raise RuntimeError(N_LOGIC_NAME)

if n_fb is None:
    raise RuntimeError(N_FB_NAME)


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
            min(x1, x2)
        ),

        to_dbu(
            y - width / 2
        ),

        to_dbu(
            max(x1, x2)
        ),

        to_dbu(
            y + width / 2
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
            x - width / 2
        ),

        to_dbu(
            min(y1, y2)
        ),

        to_dbu(
            x + width / 2
        ),

        to_dbu(
            max(y1, y2)
        ),

    )


def centered_box(
    x,
    y,
    width,
    height=None,
):

    if height is None:
        height = width


    return kdb.Box(

        to_dbu(
            x - width / 2
        ),

        to_dbu(
            y - height / 2
        ),

        to_dbu(
            x + width / 2
        ),

        to_dbu(
            y + height / 2
        ),

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
        return (box.left + box.right) / 2.0

    def cy(box):
        return (box.bottom + box.top) / 2.0


    left_sd = min(
        boxes,
        key=cx,
    )

    right_sd = max(
        boxes,
        key=cx,
    )


    gate_boxes = [

        box

        for box in boxes

        if (
            box != left_sd
            and
            box != right_sd
        )

    ]


    bottom_gate = min(
        gate_boxes,
        key=cy,
    )

    top_gate = max(
        gate_boxes,
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


N_LOGIC_TERMS = primitive_terminal_boxes(
    n_logic
)

N_FB_TERMS = primitive_terminal_boxes(
    n_fb
)


# ================================================================
# 9. FROZEN INSTANCE ORIGINS
# ================================================================

ORIGINS = {

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

}


def abs_box(
    terms,
    terminal,
    instance,
):

    return translate_box(

        terms[
            terminal
        ],

        ORIGINS[
            instance
        ],

    )


# ================================================================
# 10. N_MID TARGETS
# ================================================================

TARGET_BOXES = {

    "MN_ST1_SOURCE":

        abs_box(
            N_LOGIC_TERMS,
            "LEFT_SD",
            "MN_ST1",
        ),

    "MN_ST2_DRAIN":

        abs_box(
            N_LOGIC_TERMS,
            "RIGHT_SD",
            "MN_ST2",
        ),

    "MN_FB_SOURCE":

        abs_box(
            N_FB_TERMS,
            "LEFT_SD",
            "MN_FB",
        ),

}


TARGET_POINTS = {

    name:
        center_um(box)

    for name, box
    in TARGET_BOXES.items()

}


print()
print("=" * 80)
print("N_MID TARGET TERMINALS")
print("=" * 80)


for name, point in TARGET_POINTS.items():

    box = TARGET_BOXES[
        name
    ]

    print(
        f"{name:18s}: "
        f"center={tuple(round(v, 3) for v in point)} "
        f"bbox=("
        f"{to_um(box.left):.3f}, "
        f"{to_um(box.bottom):.3f}, "
        f"{to_um(box.right):.3f}, "
        f"{to_um(box.top):.3f})"
    )


# ================================================================
# 11. PROTECTED TERMINALS
# ================================================================

PROTECTED_BOXES = {

    # MN_ST1 drain = VRAW
    "MN_ST1_DRAIN_VRAW":

        abs_box(
            N_LOGIC_TERMS,
            "RIGHT_SD",
            "MN_ST1",
        ),

    # MN_ST2 source = VSS
    "MN_ST2_SOURCE_VSS":

        abs_box(
            N_LOGIC_TERMS,
            "LEFT_SD",
            "MN_ST2",
        ),

    # MN_FB drain = VDD
    "MN_FB_DRAIN_VDD":

        abs_box(
            N_FB_TERMS,
            "RIGHT_SD",
            "MN_FB",
        ),


    # MN_ST1 gates = VMEM
    "MN_ST1_GATE_B":

        abs_box(
            N_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MN_ST1",
        ),

    "MN_ST1_GATE_T":

        abs_box(
            N_LOGIC_TERMS,
            "TOP_GATE",
            "MN_ST1",
        ),


    # MN_ST2 gates = VMEM
    "MN_ST2_GATE_B":

        abs_box(
            N_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MN_ST2",
        ),

    "MN_ST2_GATE_T":

        abs_box(
            N_LOGIC_TERMS,
            "TOP_GATE",
            "MN_ST2",
        ),


    # MN_FB gates = VRAW
    "MN_FB_GATE_B":

        abs_box(
            N_FB_TERMS,
            "BOTTOM_GATE",
            "MN_FB",
        ),

    "MN_FB_GATE_T":

        abs_box(
            N_FB_TERMS,
            "TOP_GATE",
            "MN_FB",
        ),

}


# ================================================================
# 12. ROUTING DIMENSIONS
# ================================================================

M1_WIDTH = (
    0.230
)

M1_PATCH_SIZE = (
    0.500
)

VIA1_SIZE = (
    0.150
)

M2_PATCH_SIZE = (
    0.500
)

M2_WIDTH = (
    0.400
)


NMID_BUS_Y = (
    9.000
)


# ================================================================
# 13. LOCAL ESCAPE X POSITIONS
#
# ST1:
#   left of device
#
# ST2:
#   right of device, avoiding VMEM gate geometry
#
# FB:
#   left of source but to the RIGHT of existing VSS drop.
#
# The MN_FB escape is x=23.700 specifically to maintain
# >=0.14um notch clearance both to the source terminal and
# to the existing VSS drop.
# ================================================================

ST1_ESCAPE_X = (
    15.400
)

ST2_ESCAPE_X = (
    21.400
)

FB_ESCAPE_X = (
    23.700
)


# ================================================================
# 14. M1/M2 BRIDGE
#
# Existing MP_FB->VSS M1 drop:
#
#   x = 23.185 ... 23.415
#
# So place bridge landing patches on either side.
# ================================================================

BRIDGE_LEFT_X = (
    22.750
)

BRIDGE_RIGHT_X = (
    23.850
)


# ================================================================
# 15. EXPLICIT CLEARANCE CALCULATIONS
# ================================================================

M1_MIN_SPACING = (
    0.140
)


MN_FB_SOURCE_LEFT = to_um(
    TARGET_BOXES[
        "MN_FB_SOURCE"
    ].left
)


FB_ESCAPE_RIGHT_EDGE = (
    FB_ESCAPE_X
    +
    M1_WIDTH / 2.0
)


FB_SOURCE_NOTCH_CLEARANCE = (

    MN_FB_SOURCE_LEFT
    -
    FB_ESCAPE_RIGHT_EDGE

)


# Frozen Step31 MP_FB VSS drop:
VSS_DROP_LEFT = (
    23.185
)

VSS_DROP_RIGHT = (
    23.415
)


FB_ESCAPE_LEFT_EDGE = (
    FB_ESCAPE_X
    -
    M1_WIDTH / 2.0
)


FB_TO_VSS_CLEARANCE = (

    FB_ESCAPE_LEFT_EDGE
    -
    VSS_DROP_RIGHT

)


BRIDGE_LEFT_PATCH_RIGHT = (

    BRIDGE_LEFT_X
    +
    M1_PATCH_SIZE / 2.0

)


BRIDGE_LEFT_TO_VSS = (

    VSS_DROP_LEFT
    -
    BRIDGE_LEFT_PATCH_RIGHT

)


BRIDGE_RIGHT_PATCH_LEFT = (

    BRIDGE_RIGHT_X
    -
    M1_PATCH_SIZE / 2.0

)


BRIDGE_RIGHT_TO_VSS = (

    BRIDGE_RIGHT_PATCH_LEFT
    -
    VSS_DROP_RIGHT

)


CLEARANCE_CHECKS = {

    "MN_FB_SOURCE_NOTCH":
        FB_SOURCE_NOTCH_CLEARANCE,

    "MN_FB_ESCAPE_TO_VSS":
        FB_TO_VSS_CLEARANCE,

    "LEFT_BRIDGE_PATCH_TO_VSS":
        BRIDGE_LEFT_TO_VSS,

    "RIGHT_BRIDGE_PATCH_TO_VSS":
        BRIDGE_RIGHT_TO_VSS,

}


CLEARANCES_OK = all(

    value >= M1_MIN_SPACING

    for value
    in CLEARANCE_CHECKS.values()

)


print()
print("=" * 80)
print("EXPLICIT M1 CLEARANCE AUDIT")
print("=" * 80)


for name, value in CLEARANCE_CHECKS.items():

    print(
        f"{name:28s}: "
        f"{value:.3f} um "
        f"required >= {M1_MIN_SPACING:.3f} um "
        f"valid={value >= M1_MIN_SPACING}"
    )


print(
    "All explicit clearances valid:",
    CLEARANCES_OK
)


# ================================================================
# 16. PRE-EXISTING CONDUCTORS
# ================================================================

PRE_M1 = kdb.Region(

    input_top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


PRE_M2 = kdb.Region(

    input_top.begin_shapes_rec(
        M2_LAYER
    )

).merged()


# ================================================================
# 17. CREATE OUTPUT TOP
# ================================================================

if layout.cell(
    OUTPUT_TOP_NAME
) is not None:

    raise RuntimeError(
        f"Output top already exists: {OUTPUT_TOP_NAME}"
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
# 18. NEW M1 ROUTING
# ================================================================

m1_shapes = {


    # MN_ST1 source -> left escape.
    "MN_ST1_SOURCE_STUB":

        horizontal_box(

            ST1_ESCAPE_X,

            TARGET_POINTS[
                "MN_ST1_SOURCE"
            ][0],

            TARGET_POINTS[
                "MN_ST1_SOURCE"
            ][1],

            M1_WIDTH,

        ),


    "MN_ST1_VERTICAL":

        vertical_box(

            ST1_ESCAPE_X,

            TARGET_POINTS[
                "MN_ST1_SOURCE"
            ][1],

            NMID_BUS_Y,

            M1_WIDTH,

        ),


    # MN_ST2 drain -> right escape.
    "MN_ST2_DRAIN_STUB":

        horizontal_box(

            TARGET_POINTS[
                "MN_ST2_DRAIN"
            ][0],

            ST2_ESCAPE_X,

            TARGET_POINTS[
                "MN_ST2_DRAIN"
            ][1],

            M1_WIDTH,

        ),


    "MN_ST2_VERTICAL":

        vertical_box(

            ST2_ESCAPE_X,

            TARGET_POINTS[
                "MN_ST2_DRAIN"
            ][1],

            NMID_BUS_Y,

            M1_WIDTH,

        ),


    # MN_FB source -> left escape.
    "MN_FB_SOURCE_STUB":

        horizontal_box(

            FB_ESCAPE_X,

            TARGET_POINTS[
                "MN_FB_SOURCE"
            ][0],

            TARGET_POINTS[
                "MN_FB_SOURCE"
            ][1],

            M1_WIDTH,

        ),


    "MN_FB_VERTICAL":

        vertical_box(

            FB_ESCAPE_X,

            TARGET_POINTS[
                "MN_FB_SOURCE"
            ][1],

            NMID_BUS_Y,

            M1_WIDTH,

        ),


    # Left M1 N_MID section.
    "NMID_LEFT_BUS":

        horizontal_box(

            ST1_ESCAPE_X,

            BRIDGE_LEFT_X,

            NMID_BUS_Y,

            M1_WIDTH,

        ),


    # Right M1 N_MID section.
    "NMID_RIGHT_BUS":

        horizontal_box(

            FB_ESCAPE_X,

            BRIDGE_RIGHT_X,

            NMID_BUS_Y,

            M1_WIDTH,

        ),


    # M1 bridge landing patches.
    "BRIDGE_LEFT_M1_PATCH":

        centered_box(

            BRIDGE_LEFT_X,

            NMID_BUS_Y,

            M1_PATCH_SIZE,

        ),


    "BRIDGE_RIGHT_M1_PATCH":

        centered_box(

            BRIDGE_RIGHT_X,

            NMID_BUS_Y,

            M1_PATCH_SIZE,

        ),

}


for box in m1_shapes.values():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


# ================================================================
# 19. VIA1
# ================================================================

via1_shapes = {

    "BRIDGE_LEFT_VIA":

        centered_box(

            BRIDGE_LEFT_X,

            NMID_BUS_Y,

            VIA1_SIZE,

        ),

    "BRIDGE_RIGHT_VIA":

        centered_box(

            BRIDGE_RIGHT_X,

            NMID_BUS_Y,

            VIA1_SIZE,

        ),

}


for box in via1_shapes.values():

    top.shapes(
        VIA1_LAYER
    ).insert(
        box
    )


# ================================================================
# 20. M2 BRIDGE
# ================================================================

m2_shapes = {

    "BRIDGE_LEFT_M2_PATCH":

        centered_box(

            BRIDGE_LEFT_X,

            NMID_BUS_Y,

            M2_PATCH_SIZE,

        ),

    "BRIDGE_RIGHT_M2_PATCH":

        centered_box(

            BRIDGE_RIGHT_X,

            NMID_BUS_Y,

            M2_PATCH_SIZE,

        ),

    "NMID_M2_BRIDGE":

        horizontal_box(

            BRIDGE_LEFT_X,

            BRIDGE_RIGHT_X,

            NMID_BUS_Y,

            M2_WIDTH,

        ),

}


for box in m2_shapes.values():

    top.shapes(
        M2_LAYER
    ).insert(
        box
    )


# ================================================================
# 21. NEW REGIONS
# ================================================================

NEW_M1 = kdb.Region()


for box in m1_shapes.values():

    NEW_M1.insert(
        box
    )


NEW_M1.merge()


NEW_M2 = kdb.Region()


for box in m2_shapes.values():

    NEW_M2.insert(
        box
    )


NEW_M2.merge()


# ================================================================
# 22. NEW NETWORK COMPONENT STRUCTURE
#
# Expected:
#
#   NEW_M1 = 2 components
#       left  : ST1 + ST2 + left bridge landing
#       right : FB + right bridge landing
#
#   NEW_M2 = 1 component
#       bridge
# ================================================================

NEW_M1_COMPONENTS = list(
    NEW_M1.each_merged()
)

NEW_M2_COMPONENTS = list(
    NEW_M2.each_merged()
)


M1_COMPONENT_COUNT_OK = (
    len(
        NEW_M1_COMPONENTS
    ) == 2
)


M2_COMPONENT_COUNT_OK = (
    len(
        NEW_M2_COMPONENTS
    ) == 1
)


print()
print("=" * 80)
print("NEW N_MID COMPONENT STRUCTURE")
print("=" * 80)

print(
    "New M1 components:",
    len(
        NEW_M1_COMPONENTS
    ),
    "(expected 2)"
)

print(
    "New M2 components:",
    len(
        NEW_M2_COMPONENTS
    ),
    "(expected 1)"
)

print(
    "M1 structure correct:",
    M1_COMPONENT_COUNT_OK
)

print(
    "M2 structure correct:",
    M2_COMPONENT_COUNT_OK
)


# ================================================================
# 23. TARGET LANDINGS
# ================================================================

TARGET_LANDINGS_OK = True


TARGET_ROUTE_MAP = {

    "MN_ST1_SOURCE":
        "MN_ST1_SOURCE_STUB",

    "MN_ST2_DRAIN":
        "MN_ST2_DRAIN_STUB",

    "MN_FB_SOURCE":
        "MN_FB_SOURCE_STUB",

}


print()
print("=" * 80)
print("N_MID TARGET LANDING AUDIT")
print("=" * 80)


for target_name, route_name in TARGET_ROUTE_MAP.items():

    landed = not (

        kdb.Region(
            m1_shapes[
                route_name
            ]
        )

        &

        kdb.Region(
            TARGET_BOXES[
                target_name
            ]
        )

    ).is_empty()


    TARGET_LANDINGS_OK &= landed


    print(
        f"{target_name:18s}:",
        landed
    )


# ================================================================
# 24. NEW M1 MAY TOUCH PRE-EXISTING M1 ONLY AT N_MID TARGETS
# ================================================================

ALLOWED_M1_OVERLAP = kdb.Region()


for box in TARGET_BOXES.values():

    ALLOWED_M1_OVERLAP.insert(
        box
    )


ALLOWED_M1_OVERLAP.merge()


ACTUAL_M1_OVERLAP = (

    NEW_M1
    &
    PRE_M1

)


UNEXPECTED_M1_OVERLAP = (

    ACTUAL_M1_OVERLAP
    -
    ALLOWED_M1_OVERLAP

)


NO_UNEXPECTED_M1_OVERLAP = (
    UNEXPECTED_M1_OVERLAP.is_empty()
)


print()
print("=" * 80)
print("PRE-EXISTING M1 SHORT AUDIT")
print("=" * 80)

print(
    "Unexpected M1 overlap:",
    not NO_UNEXPECTED_M1_OVERLAP
)

print(
    "Only intended N_MID terminals touched:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 25. NEW M2 MUST TOUCH NO PRE-EXISTING M2
# ================================================================

UNEXPECTED_M2_OVERLAP = (

    NEW_M2
    &
    PRE_M2

)


NO_UNEXPECTED_M2_OVERLAP = (
    UNEXPECTED_M2_OVERLAP.is_empty()
)


print()
print("=" * 80)
print("PRE-EXISTING M2 SHORT AUDIT")
print("=" * 80)

print(
    "Unexpected existing-M2 contact:",
    not NO_UNEXPECTED_M2_OVERLAP
)

print(
    "N_MID bridge isolated from existing M2:",
    NO_UNEXPECTED_M2_OVERLAP
)


# ================================================================
# 26. PROTECTED TERMINALS
# ================================================================

PROTECTED_CLEAR = True


print()
print("=" * 80)
print("PROTECTED TERMINAL AUDIT")
print("=" * 80)


for name, box in PROTECTED_BOXES.items():

    overlap = not (

        NEW_M1

        &

        kdb.Region(
            box
        )

    ).is_empty()


    clear = (
        not overlap
    )


    PROTECTED_CLEAR &= clear


    print(
        f"{name:20s}: "
        f"overlap={overlap} "
        f"clear={clear}"
    )


# ================================================================
# 27. VIA LANDING AUDIT
# ================================================================

VIA_LANDING_OK = True


VIA_DATA = {

    "LEFT":

        {
            "via":
                via1_shapes[
                    "BRIDGE_LEFT_VIA"
                ],

            "m1":
                m1_shapes[
                    "BRIDGE_LEFT_M1_PATCH"
                ],

            "m2":
                m2_shapes[
                    "BRIDGE_LEFT_M2_PATCH"
                ],
        },

    "RIGHT":

        {
            "via":
                via1_shapes[
                    "BRIDGE_RIGHT_VIA"
                ],

            "m1":
                m1_shapes[
                    "BRIDGE_RIGHT_M1_PATCH"
                ],

            "m2":
                m2_shapes[
                    "BRIDGE_RIGHT_M2_PATCH"
                ],
        },

}


print()
print("=" * 80)
print("VIA LANDING AUDIT")
print("=" * 80)


for side, data in VIA_DATA.items():

    via_region = kdb.Region(
        data[
            "via"
        ]
    )

    m1_region = kdb.Region(
        data[
            "m1"
        ]
    )

    m2_region = kdb.Region(
        data[
            "m2"
        ]
    )


    via_inside_m1 = (

        (
            via_region
            -
            m1_region
        ).is_empty()

    )


    via_inside_m2 = (

        (
            via_region
            -
            m2_region
        ).is_empty()

    )


    m1_connected = not (

        m1_region
        &
        NEW_M1

    ).is_empty()


    m2_connected = not (

        m2_region
        &
        NEW_M2

    ).is_empty()


    valid = bool(

        via_inside_m1

        and

        via_inside_m2

        and

        m1_connected

        and

        m2_connected

    )


    VIA_LANDING_OK &= valid


    print(
        f"{side:8s}: "
        f"M1={via_inside_m1} "
        f"M2={via_inside_m2} "
        f"M1net={m1_connected} "
        f"M2net={m2_connected} "
        f"valid={valid}"
    )


# ================================================================
# 28. CROSS-LAYER CONNECTIVITY LOGIC
#
# Each side of the M1 network must touch its respective via,
# and the M2 bridge must connect both via sites.
# ================================================================

LEFT_VIA_TOUCHES_M1 = not (

    kdb.Region(
        via1_shapes[
            "BRIDGE_LEFT_VIA"
        ]
    )

    &

    NEW_M1

).is_empty()


RIGHT_VIA_TOUCHES_M1 = not (

    kdb.Region(
        via1_shapes[
            "BRIDGE_RIGHT_VIA"
        ]
    )

    &

    NEW_M1

).is_empty()


LEFT_VIA_TOUCHES_M2 = not (

    kdb.Region(
        via1_shapes[
            "BRIDGE_LEFT_VIA"
        ]
    )

    &

    NEW_M2

).is_empty()


RIGHT_VIA_TOUCHES_M2 = not (

    kdb.Region(
        via1_shapes[
            "BRIDGE_RIGHT_VIA"
        ]
    )

    &

    NEW_M2

).is_empty()


CROSS_LAYER_CONNECTED = bool(

    M1_COMPONENT_COUNT_OK

    and

    M2_COMPONENT_COUNT_OK

    and

    LEFT_VIA_TOUCHES_M1

    and

    RIGHT_VIA_TOUCHES_M1

    and

    LEFT_VIA_TOUCHES_M2

    and

    RIGHT_VIA_TOUCHES_M2

)


print()
print("=" * 80)
print("CROSS-LAYER N_MID CONNECTIVITY")
print("=" * 80)

print(
    "Left via touches M1 :",
    LEFT_VIA_TOUCHES_M1
)

print(
    "Right via touches M1:",
    RIGHT_VIA_TOUCHES_M1
)

print(
    "Left via touches M2 :",
    LEFT_VIA_TOUCHES_M2
)

print(
    "Right via touches M2:",
    RIGHT_VIA_TOUCHES_M2
)

print(
    "Complete N_MID path :",
    CROSS_LAYER_CONNECTED
)


# ================================================================
# 29. TOP-LEVEL SHAPE COUNTS
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        M1_LAYER
    ).each()

)


TOP_VIA1_COUNT = sum(

    1

    for _
    in top.shapes(
        VIA1_LAYER
    ).each()

)


TOP_M2_COUNT = sum(

    1

    for _
    in top.shapes(
        M2_LAYER
    ).each()

)


EXPECTED_M1_COUNT = (
    10
)

EXPECTED_VIA1_COUNT = (
    2
)

EXPECTED_M2_COUNT = (
    3
)


COUNTS_OK = bool(

    TOP_M1_COUNT
    ==
    EXPECTED_M1_COUNT

    and

    TOP_VIA1_COUNT
    ==
    EXPECTED_VIA1_COUNT

    and

    TOP_M2_COUNT
    ==
    EXPECTED_M2_COUNT

)


print()
print("=" * 80)
print("NEW TOP-LEVEL SHAPE COUNTS")
print("=" * 80)

print(
    "M1   :",
    TOP_M1_COUNT,
    "/",
    EXPECTED_M1_COUNT
)

print(
    "VIA1 :",
    TOP_VIA1_COUNT,
    "/",
    EXPECTED_VIA1_COUNT
)

print(
    "M2   :",
    TOP_M2_COUNT,
    "/",
    EXPECTED_M2_COUNT
)

print(
    "Counts correct:",
    COUNTS_OK
)


# ================================================================
# 30. SERIALIZATION
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
            int(layer_index),
            int(info.layer),
            int(info.datatype),
        )

    )


def save_options(fmt):

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
# 31. WRITE
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

    save_options(
        "GDS2"
    ),

)


layout.write(

    str(
        OUTPUT_OAS
    ),

    save_options(
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
# 32. READBACK
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

verify_via1 = verify.find_layer(
    68,
    44
)

verify_m2 = verify.find_layer(
    69,
    20
)


READBACK_M1 = sum(

    1

    for _
    in verify_top.shapes(
        verify_m1
    ).each()

)


READBACK_VIA1 = sum(

    1

    for _
    in verify_top.shapes(
        verify_via1
    ).each()

)


READBACK_M2 = sum(

    1

    for _
    in verify_top.shapes(
        verify_m2
    ).each()

)


READBACK_COUNTS_OK = bool(

    READBACK_M1
    ==
    EXPECTED_M1_COUNT

    and

    READBACK_VIA1
    ==
    EXPECTED_VIA1_COUNT

    and

    READBACK_M2
    ==
    EXPECTED_M2_COUNT

)


# ================================================================
# 33. INPUT INTEGRITY
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
# 34. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "35A",

    "routing_stage":
        "6_of_9_N_MID",

    "version":
        "v1",

    "status":
        "CONSTRUCTION_PASS_PENDING_DRC",

    "input": {

        "gds":
            str(INPUT_GDS),

        "top":
            INPUT_TOP_NAME,

        "sha256":
            INPUT_HASH_BEFORE,

    },

    "output": {

        "gds":
            str(OUTPUT_GDS),

        "oas":
            str(OUTPUT_OAS),

        "top":
            OUTPUT_TOP_NAME,

    },

    "net":
        "N_MID",

    "targets": {

        name:
            list(point)

        for name, point
        in TARGET_POINTS.items()

    },

    "routing": {

        "m1_bus_y_um":
            NMID_BUS_Y,

        "st1_escape_x_um":
            ST1_ESCAPE_X,

        "st2_escape_x_um":
            ST2_ESCAPE_X,

        "fb_escape_x_um":
            FB_ESCAPE_X,

        "bridge_left_x_um":
            BRIDGE_LEFT_X,

        "bridge_right_x_um":
            BRIDGE_RIGHT_X,

        "m1_width_um":
            M1_WIDTH,

        "m1_patch_um":
            M1_PATCH_SIZE,

        "via1_um":
            VIA1_SIZE,

        "m2_width_um":
            M2_WIDTH,

    },

    "explicit_clearances_um":
        CLEARANCE_CHECKS,

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "explicit_clearances":
            CLEARANCES_OK,

        "m1_component_structure":
            M1_COMPONENT_COUNT_OK,

        "m2_component_structure":
            M2_COMPONENT_COUNT_OK,

        "target_landings":
            TARGET_LANDINGS_OK,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "no_unexpected_m2_overlap":
            NO_UNEXPECTED_M2_OVERLAP,

        "protected_terminals":
            PROTECTED_CLEAR,

        "via_landings":
            VIA_LANDING_OK,

        "cross_layer_connected":
            CROSS_LAYER_CONNECTED,

        "shape_counts":
            COUNTS_OK,

        "gds_write":
            GDS_OK,

        "oas_write":
            OAS_OK,

        "readback":
            READBACK_OK,

        "readback_counts":
            READBACK_COUNTS_OK,

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
# 35. FINAL GATE
# ================================================================

STEP35A_PASS = bool(

    REFERENCE_OK

    and

    CLEARANCES_OK

    and

    M1_COMPONENT_COUNT_OK

    and

    M2_COMPONENT_COUNT_OK

    and

    TARGET_LANDINGS_OK

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    NO_UNEXPECTED_M2_OVERLAP

    and

    PROTECTED_CLEAR

    and

    VIA_LANDING_OK

    and

    CROSS_LAYER_CONNECTED

    and

    COUNTS_OK

    and

    GDS_OK

    and

    OAS_OK

    and

    READBACK_OK

    and

    READBACK_COUNTS_OK

    and

    INPUT_UNCHANGED

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 35A RESULT")
print("=" * 80)

print(
    "Reference N_MID topology    :",
    REFERENCE_OK
)

print(
    "Explicit M1 clearances      :",
    CLEARANCES_OK
)

print(
    "M1 component structure      :",
    M1_COMPONENT_COUNT_OK
)

print(
    "M2 bridge structure         :",
    M2_COMPONENT_COUNT_OK
)

print(
    "All target landings valid   :",
    TARGET_LANDINGS_OK
)

print(
    "No unexpected M1 overlap    :",
    NO_UNEXPECTED_M1_OVERLAP
)

print(
    "No unexpected M2 overlap    :",
    NO_UNEXPECTED_M2_OVERLAP
)

print(
    "Protected terminals clear   :",
    PROTECTED_CLEAR
)

print(
    "All VIA1 landings valid     :",
    VIA_LANDING_OK
)

print(
    "Cross-layer N_MID connected :",
    CROSS_LAYER_CONNECTED
)

print(
    "Shape counts correct        :",
    COUNTS_OK
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
    "Read-back counts            :",
    READBACK_COUNTS_OK
)

print(
    "Canonical Stage-5 unchanged :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP35A_PASS =",
    STEP35A_PASS
)


if not STEP35A_PASS:

    raise RuntimeError(
        "STEP 35A N_MID construction failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 6/9 — N_MID CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "N_MID connects:"
)

print(
    "  MN_ST1 source"
)

print(
    "  MN_ST2 drain"
)

print(
    "  MN_FB source"
)

print()
print(
    "Routing:"
)

print(
    "  M1 left section"
)

print(
    "  M2 bridge over existing VSS M1 drop"
)

print(
    "  M1 right section"
)

print()
print(
    "Protected:"
)

print(
    "  MN_ST1 drain / VRAW"
)

print(
    "  MN_ST2 source / VSS"
)

print(
    "  MN_FB drain / VDD"
)

print(
    "  all three gate networks"
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
    "  Official SKY130 DRC on N_MID V1."
)