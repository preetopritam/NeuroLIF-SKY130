# ================================================================
# NeuroLIF-SKY130
# STEP 37A — Full-neuron SPIKE output routing V1
#
# Routing Stage 8/9
#
# Input:
#   neurolif_full_neuron_vraw_v2.gds
#
# Frozen topology:
#
#   MP_BUF SPIKE VRAW VDD VDD
#   MN_BUF SPIKE VRAW VSS VSS
#
# Stage-8 scope:
#
#   MP_BUF drain
#        |
#        +------ SPIKE ------ external access
#        |
#   MN_BUF drain
#
# IMPORTANT:
#   MN_RST gate is NOT connected in this stage.
#   SPIKE -> reset gate is Stage 9/9.
#
# Routing strategy:
#
#   MP_BUF drain -> local M1 landing -> VIA1
#                                      |
#                                      M2 vertical SPIKE spine
#                                      |
#   MN_BUF drain -> local M1 landing -> VIA1
#
# M2 crosses the frozen VRAW M1 corridor safely.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 37A: SPIKE OUTPUT ROUTING V1")
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
    / "neurolif_full_neuron_vraw_v2.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vraw_v2.json"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

VRAW_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_vraw_v2_drc.lyrdb"
)

OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_spike_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_spike_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_spike_v1.json"
)

INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VRAW_V2"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_SPIKE_V1"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    VRAW_DRC_REPORT,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. INPUT HASH
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
# 3. FROZEN REFERENCE TOPOLOGY
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


REFERENCE_LINES = {

    "MP_BUF":
        "MP_BUF SPIKE VRAW VDD VDD",

    "MN_BUF":
        "MN_BUF SPIKE VRAW VSS VSS",

    "MN_RST":
        "MN_RST VMEM SPIKE VSS VSS",

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
print("REFERENCE SPIKE TOPOLOGY")
print("=" * 80)


for name, result in reference_checks.items():

    print(
        f"{name:10s}:",
        result
    )


print(
    "Reference valid:",
    REFERENCE_OK
)


if not REFERENCE_OK:

    raise RuntimeError(
        "Frozen SPIKE topology mismatch."
    )


print()
print(
    "Stage-8 scope:"
)

print(
    "  MP_BUF drain + MN_BUF drain + external SPIKE"
)

print(
    "Stage-9 deferred:"
)

print(
    "  SPIKE -> MN_RST gate"
)


# ================================================================
# 4. LOAD CANONICAL STAGE-7
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


for name, index in [

    ("MET1 68/20", M1_LAYER),

    ("VIA1 68/44", VIA1_LAYER),

    ("MET2 69/20", M2_LAYER),

]:

    if index is None:

        raise RuntimeError(
            f"Missing layer: {name}"
        )


# ================================================================
# 6. DEVICE CELLS
# ================================================================

P_LOGIC_NAME = (
    "P_LOGIC_W2000_L0150"
)

N_LOGIC_NAME = (
    "N_LOGIC_W1000_L0150"
)

N_RESET_NAME = (
    "N_RESET_W1200_L0150"
)


p_logic = layout.cell(
    P_LOGIC_NAME
)

n_logic = layout.cell(
    N_LOGIC_NAME
)

n_reset = layout.cell(
    N_RESET_NAME
)


for name, cell in [

    (P_LOGIC_NAME, p_logic),

    (N_LOGIC_NAME, n_logic),

    (N_RESET_NAME, n_reset),

]:

    if cell is None:

        raise RuntimeError(
            f"Missing primitive: {name}"
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

    return kdb.Box(

        box.left
        +
        to_dbu(
            origin[0]
        ),

        box.bottom
        +
        to_dbu(
            origin[1]
        ),

        box.right
        +
        to_dbu(
            origin[0]
        ),

        box.top
        +
        to_dbu(
            origin[1]
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
            x
            -
            width / 2
        ),

        to_dbu(
            y
            -
            height / 2
        ),

        to_dbu(
            x
            +
            width / 2
        ),

        to_dbu(
            y
            +
            height / 2
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
            f"{cell.name}: insufficient M1 terminal shapes."
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


P_LOGIC_TERMS = primitive_terminal_boxes(
    p_logic
)

N_LOGIC_TERMS = primitive_terminal_boxes(
    n_logic
)

N_RESET_TERMS = primitive_terminal_boxes(
    n_reset
)


# ================================================================
# 9. FROZEN INSTANCE ORIGINS
# ================================================================

ORIGINS = {

    "MP_BUF":
        (
            28.0,
            14.0,
        ),

    "MN_BUF":
        (
            28.0,
            7.0,
        ),

    "MN_RST":
        (
            36.0,
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
# 10. SPIKE TARGETS
# ================================================================

TARGET_BOXES = {

    "MP_BUF_DRAIN":

        abs_box(
            P_LOGIC_TERMS,
            "RIGHT_SD",
            "MP_BUF",
        ),

    "MN_BUF_DRAIN":

        abs_box(
            N_LOGIC_TERMS,
            "RIGHT_SD",
            "MN_BUF",
        ),

}


TARGET_POINTS = {

    name:
        center_um(
            box
        )

    for name, box
    in TARGET_BOXES.items()

}


print()
print("=" * 80)
print("SPIKE TARGET TERMINALS")
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

    "MP_BUF_SOURCE_VDD":

        abs_box(
            P_LOGIC_TERMS,
            "LEFT_SD",
            "MP_BUF",
        ),

    "MP_BUF_GATE_B_VRAW":

        abs_box(
            P_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MP_BUF",
        ),

    "MP_BUF_GATE_T_VRAW":

        abs_box(
            P_LOGIC_TERMS,
            "TOP_GATE",
            "MP_BUF",
        ),


    "MN_BUF_SOURCE_VSS":

        abs_box(
            N_LOGIC_TERMS,
            "LEFT_SD",
            "MN_BUF",
        ),

    "MN_BUF_GATE_B_VRAW":

        abs_box(
            N_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MN_BUF",
        ),

    "MN_BUF_GATE_T_VRAW":

        abs_box(
            N_LOGIC_TERMS,
            "TOP_GATE",
            "MN_BUF",
        ),


    # Reset gate must remain untouched until Stage 9.
    "MN_RST_GATE_B_STAGE9":

        abs_box(
            N_RESET_TERMS,
            "BOTTOM_GATE",
            "MN_RST",
        ),

    "MN_RST_GATE_T_STAGE9":

        abs_box(
            N_RESET_TERMS,
            "TOP_GATE",
            "MN_RST",
        ),

}


# ================================================================
# 12. ROUTING CONSTANTS
# ================================================================

VIA1_SIZE = (
    0.150
)

M1_LANDING_SIZE = (
    0.300
)

M2_LANDING_SIZE = (
    0.500
)

M2_WIDTH = (
    0.400
)


# Both drains are at x = 28.600.
SPIKE_X = (
    TARGET_POINTS[
        "MP_BUF_DRAIN"
    ][0]
)


SPIKE_BOTTOM_Y = (
    TARGET_POINTS[
        "MN_BUF_DRAIN"
    ][1]
)

SPIKE_TOP_DRAIN_Y = (
    TARGET_POINTS[
        "MP_BUF_DRAIN"
    ][1]
)


# Extend beyond upper drain for external output access.
SPIKE_EXTERNAL_Y = (
    16.500
)


# ================================================================
# 13. BASIC ALIGNMENT AUDIT
# ================================================================

DRAINS_ALIGNED = bool(

    abs(
        TARGET_POINTS[
            "MP_BUF_DRAIN"
        ][0]
        -
        TARGET_POINTS[
            "MN_BUF_DRAIN"
        ][0]
    )
    <
    1e-9

)


print()
print("=" * 80)
print("SPIKE ROUTING GEOMETRY")
print("=" * 80)

print(
    "Drain X aligned:",
    DRAINS_ALIGNED
)

print(
    "SPIKE M2 spine X:",
    SPIKE_X,
    "um"
)

print(
    "Bottom drain Y:",
    SPIKE_BOTTOM_Y,
    "um"
)

print(
    "Top drain Y:",
    SPIKE_TOP_DRAIN_Y,
    "um"
)

print(
    "External SPIKE point:",
    (
        SPIKE_X,
        SPIKE_EXTERNAL_Y,
    )
)


# ================================================================
# 14. EXPLICIT M1 CLEARANCE AUDIT
#
# New 0.300um M1 landing patches sit directly on the drain
# terminals.
#
# Source-right edge -> new patch-left edge must be >= m1.2.
# ================================================================

M1_MIN_SPACING = (
    0.140
)


MP_SOURCE_BOX = PROTECTED_BOXES[
    "MP_BUF_SOURCE_VDD"
]

MN_SOURCE_BOX = PROTECTED_BOXES[
    "MN_BUF_SOURCE_VSS"
]


SPIKE_PATCH_LEFT = (
    SPIKE_X
    -
    M1_LANDING_SIZE / 2.0
)

SPIKE_PATCH_RIGHT = (
    SPIKE_X
    +
    M1_LANDING_SIZE / 2.0
)


MP_SOURCE_RIGHT = to_um(
    MP_SOURCE_BOX.right
)

MN_SOURCE_RIGHT = to_um(
    MN_SOURCE_BOX.right
)


MP_SOURCE_CLEARANCE = (
    SPIKE_PATCH_LEFT
    -
    MP_SOURCE_RIGHT
)

MN_SOURCE_CLEARANCE = (
    SPIKE_PATCH_LEFT
    -
    MN_SOURCE_RIGHT
)


# Frozen MN_BUF VRAW vertical:
#
# x = 29.200 +/- 0.115
#
VRAW_MN_BUF_VERTICAL_LEFT = (
    29.200
    -
    0.230 / 2.0
)


SPIKE_PATCH_TO_VRAW = (
    VRAW_MN_BUF_VERTICAL_LEFT
    -
    SPIKE_PATCH_RIGHT
)


CLEARANCE_CHECKS = {

    "MP_BUF_SOURCE_TO_SPIKE":

        MP_SOURCE_CLEARANCE,

    "MN_BUF_SOURCE_TO_SPIKE":

        MN_SOURCE_CLEARANCE,

    "SPIKE_PATCH_TO_VRAW_RIGHT":

        SPIKE_PATCH_TO_VRAW,

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
        f"{name:30s}: "
        f"{value:.3f} um "
        f"required >= {M1_MIN_SPACING:.3f} um "
        f"valid={value >= M1_MIN_SPACING}"
    )


print(
    "All explicit M1 clearances valid:",
    CLEARANCES_OK
)


# ================================================================
# 15. PRE-EXISTING CONDUCTORS
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
# 16. CREATE OUTPUT TOP
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
# 17. NEW M1 LANDINGS
# ================================================================

m1_shapes = {

    "MP_BUF_SPIKE_LANDING":

        centered_box(

            TARGET_POINTS[
                "MP_BUF_DRAIN"
            ][0],

            TARGET_POINTS[
                "MP_BUF_DRAIN"
            ][1],

            M1_LANDING_SIZE,

        ),


    "MN_BUF_SPIKE_LANDING":

        centered_box(

            TARGET_POINTS[
                "MN_BUF_DRAIN"
            ][0],

            TARGET_POINTS[
                "MN_BUF_DRAIN"
            ][1],

            M1_LANDING_SIZE,

        ),

}


for box in m1_shapes.values():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


# ================================================================
# 18. VIA1
# ================================================================

via1_shapes = {

    "MP_BUF_SPIKE_VIA":

        centered_box(

            TARGET_POINTS[
                "MP_BUF_DRAIN"
            ][0],

            TARGET_POINTS[
                "MP_BUF_DRAIN"
            ][1],

            VIA1_SIZE,

        ),


    "MN_BUF_SPIKE_VIA":

        centered_box(

            TARGET_POINTS[
                "MN_BUF_DRAIN"
            ][0],

            TARGET_POINTS[
                "MN_BUF_DRAIN"
            ][1],

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
# 19. M2 SPIKE NETWORK
# ================================================================

m2_shapes = {

    "MP_BUF_SPIKE_M2_PATCH":

        centered_box(

            TARGET_POINTS[
                "MP_BUF_DRAIN"
            ][0],

            TARGET_POINTS[
                "MP_BUF_DRAIN"
            ][1],

            M2_LANDING_SIZE,

        ),


    "MN_BUF_SPIKE_M2_PATCH":

        centered_box(

            TARGET_POINTS[
                "MN_BUF_DRAIN"
            ][0],

            TARGET_POINTS[
                "MN_BUF_DRAIN"
            ][1],

            M2_LANDING_SIZE,

        ),


    "SPIKE_M2_SPINE":

        vertical_box(

            SPIKE_X,

            SPIKE_BOTTOM_Y,

            SPIKE_EXTERNAL_Y,

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
# 20. NEW REGIONS
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
# 21. COMPONENT STRUCTURE
# ================================================================

M1_COMPONENTS = list(
    NEW_M1.each_merged()
)

M2_COMPONENTS = list(
    NEW_M2.each_merged()
)


M1_STRUCTURE_OK = (
    len(
        M1_COMPONENTS
    ) == 2
)


M2_STRUCTURE_OK = (
    len(
        M2_COMPONENTS
    ) == 1
)


print()
print("=" * 80)
print("NEW SPIKE COMPONENT STRUCTURE")
print("=" * 80)

print(
    "M1 components:",
    len(
        M1_COMPONENTS
    ),
    "(expected 2)"
)

print(
    "M2 components:",
    len(
        M2_COMPONENTS
    ),
    "(expected 1)"
)

print(
    "M1 structure valid:",
    M1_STRUCTURE_OK
)

print(
    "M2 structure valid:",
    M2_STRUCTURE_OK
)


# ================================================================
# 22. TARGET LANDING AUDIT
# ================================================================

TARGET_LANDINGS_OK = True


print()
print("=" * 80)
print("SPIKE TARGET LANDING AUDIT")
print("=" * 80)


TARGET_TO_SHAPE = {

    "MP_BUF_DRAIN":
        "MP_BUF_SPIKE_LANDING",

    "MN_BUF_DRAIN":
        "MN_BUF_SPIKE_LANDING",

}


for target_name, shape_name in TARGET_TO_SHAPE.items():

    landed = not (

        kdb.Region(
            TARGET_BOXES[
                target_name
            ]
        )

        &

        kdb.Region(
            m1_shapes[
                shape_name
            ]
        )

    ).is_empty()


    TARGET_LANDINGS_OK &= landed


    print(
        f"{target_name:18s}:",
        landed
    )


# ================================================================
# 23. PRE-EXISTING M1 OVERLAP
#
# Only the two intended buffer drains may be touched.
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
    "Only buffer drains touched:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 24. PRE-EXISTING M2 OVERLAP
#
# SPIKE is a new net at this stage, therefore its new M2 network
# must not contact any pre-existing M2 network.
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
    "SPIKE isolated from existing M2:",
    NO_UNEXPECTED_M2_OVERLAP
)


# ================================================================
# 25. PROTECTED TERMINAL AUDIT
# ================================================================

PROTECTED_CLEAR = True


print()
print("=" * 80)
print("PROTECTED TERMINAL AUDIT")
print("=" * 80)


for name, box in PROTECTED_BOXES.items():

    m1_overlap = not (

        NEW_M1

        &

        kdb.Region(
            box
        )

    ).is_empty()


    clear = (
        not m1_overlap
    )


    PROTECTED_CLEAR &= clear


    print(
        f"{name:24s}: "
        f"overlap={m1_overlap} "
        f"clear={clear}"
    )


# ================================================================
# 26. RESET GATE MUST REMAIN DEFERRED
# ================================================================

RESET_GATE_DEFERRED = bool(

    (

        NEW_M1

        &

        kdb.Region(
            PROTECTED_BOXES[
                "MN_RST_GATE_B_STAGE9"
            ]
        )

    ).is_empty()

    and

    (

        NEW_M1

        &

        kdb.Region(
            PROTECTED_BOXES[
                "MN_RST_GATE_T_STAGE9"
            ]
        )

    ).is_empty()

)


print()
print("=" * 80)
print("STAGE-9 RESET-GATE DEFERMENT")
print("=" * 80)

print(
    "MN_RST gate untouched:",
    RESET_GATE_DEFERRED
)


# ================================================================
# 27. VIA LANDING AUDIT
# ================================================================

VIA_LANDING_OK = True


print()
print("=" * 80)
print("VIA LANDING AUDIT")
print("=" * 80)


for name, via_box in via1_shapes.items():

    via_region = kdb.Region(
        via_box
    )


    inside_m1 = (

        (
            via_region
            -
            NEW_M1
        ).is_empty()

    )


    inside_m2 = (

        (
            via_region
            -
            NEW_M2
        ).is_empty()

    )


    valid = bool(

        inside_m1

        and

        inside_m2

    )


    VIA_LANDING_OK &= valid


    print(
        f"{name:22s}: "
        f"M1={inside_m1} "
        f"M2={inside_m2} "
        f"valid={valid}"
    )


# ================================================================
# 28. CROSS-LAYER SPIKE CONNECTIVITY
# ================================================================

BOTTOM_VIA_REGION = kdb.Region(
    via1_shapes[
        "MN_BUF_SPIKE_VIA"
    ]
)

TOP_VIA_REGION = kdb.Region(
    via1_shapes[
        "MP_BUF_SPIKE_VIA"
    ]
)


BOTTOM_TO_M1 = not (

    BOTTOM_VIA_REGION
    &
    NEW_M1

).is_empty()


BOTTOM_TO_M2 = not (

    BOTTOM_VIA_REGION
    &
    NEW_M2

).is_empty()


TOP_TO_M1 = not (

    TOP_VIA_REGION
    &
    NEW_M1

).is_empty()


TOP_TO_M2 = not (

    TOP_VIA_REGION
    &
    NEW_M2

).is_empty()


SPIKE_CONNECTED = bool(

    M1_STRUCTURE_OK

    and

    M2_STRUCTURE_OK

    and

    BOTTOM_TO_M1

    and

    BOTTOM_TO_M2

    and

    TOP_TO_M1

    and

    TOP_TO_M2

)


print()
print("=" * 80)
print("CROSS-LAYER SPIKE CONNECTIVITY")
print("=" * 80)

print(
    "MN_BUF drain -> M2:",
    BOTTOM_TO_M1
    and
    BOTTOM_TO_M2
)

print(
    "MP_BUF drain -> M2:",
    TOP_TO_M1
    and
    TOP_TO_M2
)

print(
    "Single M2 SPIKE network:",
    M2_STRUCTURE_OK
)

print(
    "Complete SPIKE path:",
    SPIKE_CONNECTED
)


# ================================================================
# 29. EXTERNAL SPIKE ACCESS
# ================================================================

EXTERNAL_PROBE = kdb.Region(

    centered_box(

        SPIKE_X,

        SPIKE_EXTERNAL_Y,

        0.020,

    )

)


EXTERNAL_SPIKE_ACCESSIBLE = not (

    EXTERNAL_PROBE
    &
    NEW_M2

).is_empty()


print()
print("=" * 80)
print("EXTERNAL SPIKE ACCESS")
print("=" * 80)

print(
    "External SPIKE coordinate:",
    (
        SPIKE_X,
        SPIKE_EXTERNAL_Y,
    )
)

print(
    "M2 accessible:",
    EXTERNAL_SPIKE_ACCESSIBLE
)


# ================================================================
# 30. SHAPE COUNTS
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
    2
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
# 31. SERIALIZATION LAYER MAP
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
# 32. WRITE
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
# 33. READBACK
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
# 34. INPUT INTEGRITY
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
# 35. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "37A",

    "routing_stage":
        "8_of_9_SPIKE_OUTPUT",

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
        "SPIKE",

    "stage_8_scope": [

        "MP_BUF drain",

        "MN_BUF drain",

        "external SPIKE access",

    ],

    "stage_9_deferred": [

        "MN_RST gate",

    ],

    "routing": {

        "spike_x_um":
            SPIKE_X,

        "external_spike_y_um":
            SPIKE_EXTERNAL_Y,

        "via1_size_um":
            VIA1_SIZE,

        "m1_landing_size_um":
            M1_LANDING_SIZE,

        "m2_landing_size_um":
            M2_LANDING_SIZE,

        "m2_width_um":
            M2_WIDTH,

    },

    "clearances_um":
        CLEARANCE_CHECKS,

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "drains_aligned":
            DRAINS_ALIGNED,

        "explicit_m1_clearances":
            CLEARANCES_OK,

        "m1_structure":
            M1_STRUCTURE_OK,

        "m2_structure":
            M2_STRUCTURE_OK,

        "target_landings":
            TARGET_LANDINGS_OK,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "no_unexpected_m2_overlap":
            NO_UNEXPECTED_M2_OVERLAP,

        "protected_terminals":
            PROTECTED_CLEAR,

        "reset_gate_deferred":
            RESET_GATE_DEFERRED,

        "via_landings":
            VIA_LANDING_OK,

        "spike_connected":
            SPIKE_CONNECTED,

        "external_spike_access":
            EXTERNAL_SPIKE_ACCESSIBLE,

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
# 36. FINAL GATE
# ================================================================

STEP37A_PASS = bool(

    REFERENCE_OK

    and

    DRAINS_ALIGNED

    and

    CLEARANCES_OK

    and

    M1_STRUCTURE_OK

    and

    M2_STRUCTURE_OK

    and

    TARGET_LANDINGS_OK

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    NO_UNEXPECTED_M2_OVERLAP

    and

    PROTECTED_CLEAR

    and

    RESET_GATE_DEFERRED

    and

    VIA_LANDING_OK

    and

    SPIKE_CONNECTED

    and

    EXTERNAL_SPIKE_ACCESSIBLE

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
print("STEP 37A RESULT")
print("=" * 80)

print(
    "Reference SPIKE topology    :",
    REFERENCE_OK
)

print(
    "Buffer drains aligned       :",
    DRAINS_ALIGNED
)

print(
    "Explicit M1 clearances      :",
    CLEARANCES_OK
)

print(
    "M1 component structure      :",
    M1_STRUCTURE_OK
)

print(
    "M2 component structure      :",
    M2_STRUCTURE_OK
)

print(
    "All SPIKE target landings   :",
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
    "Reset gate deferred         :",
    RESET_GATE_DEFERRED
)

print(
    "All VIA1 landings valid     :",
    VIA_LANDING_OK
)

print(
    "SPIKE cross-layer connected :",
    SPIKE_CONNECTED
)

print(
    "External SPIKE accessible   :",
    EXTERNAL_SPIKE_ACCESSIBLE
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
    "Canonical Stage-7 unchanged :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP37A_PASS =",
    STEP37A_PASS
)


if not STEP37A_PASS:

    raise RuntimeError(
        "STEP 37A SPIKE construction failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 8/9 — SPIKE OUTPUT CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "SPIKE connects:"
)

print(
    "  MP_BUF drain"
)

print(
    "  MN_BUF drain"
)

print(
    "  external M2 SPIKE access"
)

print()
print(
    "MN_RST gate:"
)

print(
    "  intentionally NOT connected yet"
)

print(
    "  deferred to Routing Stage 9/9"
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
    "  Official SKY130 DRC on SPIKE V1."
)