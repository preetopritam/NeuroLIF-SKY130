# ================================================================
# NeuroLIF-SKY130
# STEP 36C — Full-neuron VRAW routing V2
#
# Routing Stage 7/9
#
# V1 rejection:
#   MP_FB_GATE_VERTICAL shorted to existing VSS M1 detour.
#
# Exact V1 overlap:
#   bbox = (24.335, 12.985, 24.565, 13.215) um
#
# V2 repair:
#   MP_FB gate escapes LEFT on M1 to x=22.600
#   -> M1/VIA1/M2
#   -> M2 vertical to VRAW Bridge-1
#
# This crosses the VSS M1 routing on M2, not M1.
#
# Input is canonical Stage-6:
#   neurolif_full_neuron_nmid_v1.gds
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 36C: FULL-NEURON VRAW ROUTING V2")
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
    / "neurolif_full_neuron_nmid_v1.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_nmid_v1.json"
)

REFERENCE_SPICE = (
    NEURON_DIR
    / "neurolif_full_neuron_reference_v1.spice"
)

NMID_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_nmid_v1_drc.lyrdb"
)

OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vraw_v2.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_vraw_v2.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vraw_v2.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_NMID_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VRAW_V2"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    NMID_DRC_REPORT,
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

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


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

    "MP_ST2":
        "MP_ST2 VRAW VMEM P_MID VDD",

    "MN_ST1":
        "MN_ST1 VRAW VMEM N_MID VSS",

    "MN_FB":
        "MN_FB VDD VRAW N_MID VSS",

    "MP_FB":
        "MP_FB VSS VRAW P_MID VDD",

    "MP_BUF":
        "MP_BUF SPIKE VRAW VDD VDD",

    "MN_BUF":
        "MN_BUF SPIKE VRAW VSS VSS",

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
print("REFERENCE VRAW TOPOLOGY")
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
        "Frozen VRAW topology mismatch."
    )


# ================================================================
# 4. LOAD CANONICAL STAGE-6
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
# 6. DEVICE CELLS
# ================================================================

CELL_NAMES = {

    "P_LOGIC":
        "P_LOGIC_W2000_L0150",

    "N_LOGIC":
        "N_LOGIC_W1000_L0150",

    "P_FB":
        "P_FB_W0420_L0300",

    "N_FB":
        "N_FB_W0420_L0300",

}


cells = {}


for role, name in CELL_NAMES.items():

    cell = layout.cell(
        name
    )

    if cell is None:

        raise RuntimeError(
            f"Missing primitive: {name}"
        )

    cells[
        role
    ] = cell


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
            f"{cell.name}: expected >=4 M1 terminals."
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


    gates = [

        box

        for box in boxes

        if (
            box != left_sd
            and
            box != right_sd
        )

    ]


    bottom_gate = min(
        gates,
        key=cy,
    )

    top_gate = max(
        gates,
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

    role:
        primitive_terminal_boxes(
            cell
        )

    for role, cell
    in cells.items()

}


# ================================================================
# 9. FROZEN PLACEMENT
# ================================================================

ORIGINS = {

    "MP_ST2":
        (
            20.0,
            14.0,
        ),

    "MN_ST1":
        (
            16.0,
            7.0,
        ),

    "MN_FB":
        (
            24.0,
            7.0,
        ),

    "MP_FB":
        (
            24.0,
            14.0,
        ),

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

}


def abs_box(
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
# 10. VRAW TARGETS
# ================================================================

TARGET_BOXES = {

    "MP_ST2_DRAIN":

        abs_box(
            "P_LOGIC",
            "RIGHT_SD",
            "MP_ST2",
        ),

    "MN_ST1_DRAIN":

        abs_box(
            "N_LOGIC",
            "RIGHT_SD",
            "MN_ST1",
        ),

    "MN_FB_GATE":

        abs_box(
            "N_FB",
            "BOTTOM_GATE",
            "MN_FB",
        ),

    "MP_FB_GATE":

        abs_box(
            "P_FB",
            "BOTTOM_GATE",
            "MP_FB",
        ),

    "MP_BUF_GATE":

        abs_box(
            "P_LOGIC",
            "BOTTOM_GATE",
            "MP_BUF",
        ),

    "MN_BUF_GATE":

        abs_box(
            "N_LOGIC",
            "BOTTOM_GATE",
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
print("VRAW TARGET TERMINALS")
print("=" * 80)


for name, point in TARGET_POINTS.items():

    print(
        f"{name:18s}:",
        tuple(
            round(
                v,
                3
            )

            for v in point
        )
    )


# ================================================================
# 11. PROTECTED TERMINALS
# ================================================================

PROTECTED_BOXES = {

    "MP_ST2_SOURCE_PMID":

        abs_box(
            "P_LOGIC",
            "LEFT_SD",
            "MP_ST2",
        ),

    "MP_ST2_GATE_B_VMEM":

        abs_box(
            "P_LOGIC",
            "BOTTOM_GATE",
            "MP_ST2",
        ),

    "MP_ST2_GATE_T_VMEM":

        abs_box(
            "P_LOGIC",
            "TOP_GATE",
            "MP_ST2",
        ),

    "MN_ST1_SOURCE_NMID":

        abs_box(
            "N_LOGIC",
            "LEFT_SD",
            "MN_ST1",
        ),

    "MN_ST1_GATE_B_VMEM":

        abs_box(
            "N_LOGIC",
            "BOTTOM_GATE",
            "MN_ST1",
        ),

    "MN_ST1_GATE_T_VMEM":

        abs_box(
            "N_LOGIC",
            "TOP_GATE",
            "MN_ST1",
        ),

    "MN_FB_SOURCE_NMID":

        abs_box(
            "N_FB",
            "LEFT_SD",
            "MN_FB",
        ),

    "MN_FB_DRAIN_VDD":

        abs_box(
            "N_FB",
            "RIGHT_SD",
            "MN_FB",
        ),

    "MP_FB_SOURCE_PMID":

        abs_box(
            "P_FB",
            "LEFT_SD",
            "MP_FB",
        ),

    "MP_FB_DRAIN_VSS":

        abs_box(
            "P_FB",
            "RIGHT_SD",
            "MP_FB",
        ),

    "MP_BUF_SOURCE_VDD":

        abs_box(
            "P_LOGIC",
            "LEFT_SD",
            "MP_BUF",
        ),

    "MP_BUF_DRAIN_SPIKE":

        abs_box(
            "P_LOGIC",
            "RIGHT_SD",
            "MP_BUF",
        ),

    "MN_BUF_SOURCE_VSS":

        abs_box(
            "N_LOGIC",
            "LEFT_SD",
            "MN_BUF",
        ),

    "MN_BUF_DRAIN_SPIKE":

        abs_box(
            "N_LOGIC",
            "RIGHT_SD",
            "MN_BUF",
        ),

}


# ================================================================
# 12. ROUTING CONSTANTS
# ================================================================

M1_WIDTH = (
    0.230
)

M1_PATCH = (
    0.500
)

VIA1_SIZE = (
    0.150
)

M2_PATCH = (
    0.500
)

M2_WIDTH = (
    0.400
)


VRAW_BUS_Y = (
    11.500
)


# Existing VSS and VDD M1 obstacles.

VSS_LEFT = (
    23.185
)

VSS_RIGHT = (
    23.415
)

VSS_HORIZONTAL_TOP = (
    13.215
)


VDD_LEFT = (
    25.235
)

VDD_RIGHT = (
    25.465
)


# ================================================================
# 13. VRAW BRIDGE LOCATIONS
# ================================================================

BRIDGE1_LEFT_X = (
    22.750
)

BRIDGE1_RIGHT_X = (
    23.850
)

BRIDGE2_LEFT_X = (
    24.800
)

BRIDGE2_RIGHT_X = (
    25.900
)


# Other existing V1 route positions.

MN_ST1_M2_X = (
    18.000
)

MP_ST2_ESCAPE_X = (
    21.600
)

MN_FB_M2_X = (
    25.100
)

MN_BUF_ESCAPE_X = (
    29.200
)


# ================================================================
# 14. V2 MP_FB REPAIR LOCATION
# ================================================================

MP_FB_M2_X = (
    22.600
)


print()
print("=" * 80)
print("VRAW V2 MP_FB REPAIR")
print("=" * 80)

print(
    "Rejected V1 route:",
    "vertical M1 through VSS"
)

print(
    "V2 M1/M2 transfer X:",
    MP_FB_M2_X,
    "um"
)


# ================================================================
# 15. EXPLICIT CLEARANCES
# ================================================================

M1_MIN = (
    0.140
)


BRIDGE1_LEFT_PATCH_RIGHT = (
    BRIDGE1_LEFT_X
    +
    M1_PATCH / 2
)

BRIDGE1_RIGHT_PATCH_LEFT = (
    BRIDGE1_RIGHT_X
    -
    M1_PATCH / 2
)


BRIDGE2_LEFT_PATCH_RIGHT = (
    BRIDGE2_LEFT_X
    +
    M1_PATCH / 2
)

BRIDGE2_RIGHT_PATCH_LEFT = (
    BRIDGE2_RIGHT_X
    -
    M1_PATCH / 2
)


MN_FB_GATE_RIGHT = to_um(
    TARGET_BOXES[
        "MN_FB_GATE"
    ].right
)

MN_FB_PATCH_LEFT = (
    MN_FB_M2_X
    -
    M1_PATCH / 2
)


MP_FB_STUB_BOTTOM = (
    TARGET_POINTS[
        "MP_FB_GATE"
    ][1]
    -
    M1_WIDTH / 2
)


MP_FB_PATCH_RIGHT = (
    MP_FB_M2_X
    +
    M1_PATCH / 2
)


# P_MID MP_FB source via patch from frozen Stage 5:
PMID_FB_PATCH_LEFT = (
    23.400
    -
    0.250
)

PMID_FB_PATCH_BOTTOM = (
    14.210
    -
    0.250
)


MP_FB_PATCH_TO_VSS_VERTICAL = (
    VSS_LEFT
    -
    MP_FB_PATCH_RIGHT
)


MP_FB_STUB_TO_VSS_HORIZONTAL = (
    MP_FB_STUB_BOTTOM
    -
    VSS_HORIZONTAL_TOP
)


MP_FB_PATCH_TO_PMID_X = (
    PMID_FB_PATCH_LEFT
    -
    MP_FB_PATCH_RIGHT
)


MP_FB_PATCH_TOP = (
    TARGET_POINTS[
        "MP_FB_GATE"
    ][1]
    +
    M1_PATCH / 2
)


MP_FB_PATCH_TO_PMID_Y = (
    PMID_FB_PATCH_BOTTOM
    -
    MP_FB_PATCH_TOP
)


CLEARANCE_CHECKS = {

    "BRIDGE1_LEFT_TO_VSS":

        VSS_LEFT
        -
        BRIDGE1_LEFT_PATCH_RIGHT,

    "BRIDGE1_RIGHT_TO_VSS":

        BRIDGE1_RIGHT_PATCH_LEFT
        -
        VSS_RIGHT,

    "BRIDGE2_LEFT_TO_VDD":

        VDD_LEFT
        -
        BRIDGE2_LEFT_PATCH_RIGHT,

    "BRIDGE2_RIGHT_TO_VDD":

        BRIDGE2_RIGHT_PATCH_LEFT
        -
        VDD_RIGHT,

    "MN_FB_GATE_TO_VIA_PATCH":

        MN_FB_PATCH_LEFT
        -
        MN_FB_GATE_RIGHT,

    "MP_FB_STUB_ABOVE_VSS":

        MP_FB_STUB_TO_VSS_HORIZONTAL,

    "MP_FB_PATCH_LEFT_OF_VSS":

        MP_FB_PATCH_TO_VSS_VERTICAL,

}


CLEARANCES_OK = all(

    value >= M1_MIN

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
        f"required >= {M1_MIN:.3f} um "
        f"valid={value >= M1_MIN}"
    )


print()
print(
    "MP_FB patch -> frozen P_MID patch X gap:",
    round(
        MP_FB_PATCH_TO_PMID_X,
        3
    ),
    "um"
)

print(
    "MP_FB patch -> frozen P_MID patch Y gap:",
    round(
        MP_FB_PATCH_TO_PMID_Y,
        3
    ),
    "um"
)

print(
    "All explicit M1 clearances valid:",
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
        f"Output top exists: {OUTPUT_TOP_NAME}"
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
# 18. M1 GEOMETRY
# ================================================================

m1_shapes = {


    # MN_ST1 drain transfer.
    "MN_ST1_DRAIN_STUB":

        horizontal_box(

            TARGET_POINTS[
                "MN_ST1_DRAIN"
            ][0],

            MN_ST1_M2_X,

            TARGET_POINTS[
                "MN_ST1_DRAIN"
            ][1],

            M1_WIDTH,

        ),

    "MN_ST1_BOTTOM_PATCH":

        centered_box(

            MN_ST1_M2_X,

            TARGET_POINTS[
                "MN_ST1_DRAIN"
            ][1],

            M1_PATCH,

        ),

    "MN_ST1_TOP_PATCH":

        centered_box(

            MN_ST1_M2_X,

            VRAW_BUS_Y,

            M1_PATCH,

        ),


    # MP_ST2 drain.
    "MP_ST2_DRAIN_STUB":

        horizontal_box(

            TARGET_POINTS[
                "MP_ST2_DRAIN"
            ][0],

            MP_ST2_ESCAPE_X,

            TARGET_POINTS[
                "MP_ST2_DRAIN"
            ][1],

            M1_WIDTH,

        ),

    "MP_ST2_VERTICAL":

        vertical_box(

            MP_ST2_ESCAPE_X,

            TARGET_POINTS[
                "MP_ST2_DRAIN"
            ][1],

            VRAW_BUS_Y,

            M1_WIDTH,

        ),


    # MN_FB gate.
    "MN_FB_GATE_STUB":

        horizontal_box(

            TARGET_POINTS[
                "MN_FB_GATE"
            ][0],

            MN_FB_M2_X,

            TARGET_POINTS[
                "MN_FB_GATE"
            ][1],

            M1_WIDTH,

        ),

    "MN_FB_BOTTOM_PATCH":

        centered_box(

            MN_FB_M2_X,

            TARGET_POINTS[
                "MN_FB_GATE"
            ][1],

            M1_PATCH,

        ),


    # ------------------------------------------------------------
    # MP_FB GATE — V2 REPAIR
    #
    # No vertical M1 through VSS.
    # Escape LEFT on M1 to x=22.600.
    # ------------------------------------------------------------

    "MP_FB_GATE_STUB":

        horizontal_box(

            MP_FB_M2_X,

            TARGET_POINTS[
                "MP_FB_GATE"
            ][0],

            TARGET_POINTS[
                "MP_FB_GATE"
            ][1],

            M1_WIDTH,

        ),

    "MP_FB_TRANSFER_M1_PATCH":

        centered_box(

            MP_FB_M2_X,

            TARGET_POINTS[
                "MP_FB_GATE"
            ][1],

            M1_PATCH,

        ),


    # MP_BUF gate.
    "MP_BUF_GATE_VERTICAL":

        vertical_box(

            TARGET_POINTS[
                "MP_BUF_GATE"
            ][0],

            VRAW_BUS_Y,

            TARGET_POINTS[
                "MP_BUF_GATE"
            ][1],

            M1_WIDTH,

        ),


    # MN_BUF gate.
    "MN_BUF_GATE_STUB":

        horizontal_box(

            TARGET_POINTS[
                "MN_BUF_GATE"
            ][0],

            MN_BUF_ESCAPE_X,

            TARGET_POINTS[
                "MN_BUF_GATE"
            ][1],

            M1_WIDTH,

        ),

    "MN_BUF_VERTICAL":

        vertical_box(

            MN_BUF_ESCAPE_X,

            TARGET_POINTS[
                "MN_BUF_GATE"
            ][1],

            VRAW_BUS_Y,

            M1_WIDTH,

        ),


    # VRAW M1 corridor.
    "VRAW_LEFT_BUS":

        horizontal_box(

            MN_ST1_M2_X,

            BRIDGE1_LEFT_X,

            VRAW_BUS_Y,

            M1_WIDTH,

        ),

    "VRAW_MIDDLE_BUS":

        horizontal_box(

            BRIDGE1_RIGHT_X,

            BRIDGE2_LEFT_X,

            VRAW_BUS_Y,

            M1_WIDTH,

        ),

    "VRAW_RIGHT_BUS":

        horizontal_box(

            BRIDGE2_RIGHT_X,

            MN_BUF_ESCAPE_X,

            VRAW_BUS_Y,

            M1_WIDTH,

        ),


    # VSS crossing bridge landings.
    "B1_LEFT_M1_PATCH":

        centered_box(

            BRIDGE1_LEFT_X,

            VRAW_BUS_Y,

            M1_PATCH,

        ),

    "B1_RIGHT_M1_PATCH":

        centered_box(

            BRIDGE1_RIGHT_X,

            VRAW_BUS_Y,

            M1_PATCH,

        ),


    # VDD crossing bridge landings.
    "B2_LEFT_M1_PATCH":

        centered_box(

            BRIDGE2_LEFT_X,

            VRAW_BUS_Y,

            M1_PATCH,

        ),

    "B2_RIGHT_M1_PATCH":

        centered_box(

            BRIDGE2_RIGHT_X,

            VRAW_BUS_Y,

            M1_PATCH,

        ),

}


for box in m1_shapes.values():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


# ================================================================
# 19. VIA1 GEOMETRY
# ================================================================

via1_shapes = {


    "MN_ST1_BOTTOM_VIA":

        centered_box(

            MN_ST1_M2_X,

            TARGET_POINTS[
                "MN_ST1_DRAIN"
            ][1],

            VIA1_SIZE,

        ),

    "MN_ST1_TOP_VIA":

        centered_box(

            MN_ST1_M2_X,

            VRAW_BUS_Y,

            VIA1_SIZE,

        ),


    "MN_FB_BOTTOM_VIA":

        centered_box(

            MN_FB_M2_X,

            TARGET_POINTS[
                "MN_FB_GATE"
            ][1],

            VIA1_SIZE,

        ),


    # New V2 MP_FB transfer via.
    "MP_FB_TRANSFER_VIA":

        centered_box(

            MP_FB_M2_X,

            TARGET_POINTS[
                "MP_FB_GATE"
            ][1],

            VIA1_SIZE,

        ),


    "B1_LEFT_VIA":

        centered_box(

            BRIDGE1_LEFT_X,

            VRAW_BUS_Y,

            VIA1_SIZE,

        ),

    "B1_RIGHT_VIA":

        centered_box(

            BRIDGE1_RIGHT_X,

            VRAW_BUS_Y,

            VIA1_SIZE,

        ),

    "B2_LEFT_VIA":

        centered_box(

            BRIDGE2_LEFT_X,

            VRAW_BUS_Y,

            VIA1_SIZE,

        ),

    "B2_RIGHT_VIA":

        centered_box(

            BRIDGE2_RIGHT_X,

            VRAW_BUS_Y,

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
# 20. M2 GEOMETRY
# ================================================================

m2_shapes = {


    # MN_ST1 transfer.
    "MN_ST1_BOTTOM_M2_PATCH":

        centered_box(

            MN_ST1_M2_X,

            TARGET_POINTS[
                "MN_ST1_DRAIN"
            ][1],

            M2_PATCH,

        ),

    "MN_ST1_TOP_M2_PATCH":

        centered_box(

            MN_ST1_M2_X,

            VRAW_BUS_Y,

            M2_PATCH,

        ),

    "MN_ST1_M2_VERTICAL":

        vertical_box(

            MN_ST1_M2_X,

            TARGET_POINTS[
                "MN_ST1_DRAIN"
            ][1],

            VRAW_BUS_Y,

            M2_WIDTH,

        ),


    # Bridge 1 over VSS.
    "B1_LEFT_M2_PATCH":

        centered_box(

            BRIDGE1_LEFT_X,

            VRAW_BUS_Y,

            M2_PATCH,

        ),

    "B1_RIGHT_M2_PATCH":

        centered_box(

            BRIDGE1_RIGHT_X,

            VRAW_BUS_Y,

            M2_PATCH,

        ),

    "VRAW_M2_BRIDGE1":

        horizontal_box(

            BRIDGE1_LEFT_X,

            BRIDGE1_RIGHT_X,

            VRAW_BUS_Y,

            M2_WIDTH,

        ),


    # Bridge 2 over VDD.
    "B2_LEFT_M2_PATCH":

        centered_box(

            BRIDGE2_LEFT_X,

            VRAW_BUS_Y,

            M2_PATCH,

        ),

    "B2_RIGHT_M2_PATCH":

        centered_box(

            BRIDGE2_RIGHT_X,

            VRAW_BUS_Y,

            M2_PATCH,

        ),

    "VRAW_M2_BRIDGE2":

        horizontal_box(

            BRIDGE2_LEFT_X,

            BRIDGE2_RIGHT_X,

            VRAW_BUS_Y,

            M2_WIDTH,

        ),


    # MN_FB gate transfer.
    "MN_FB_BOTTOM_M2_PATCH":

        centered_box(

            MN_FB_M2_X,

            TARGET_POINTS[
                "MN_FB_GATE"
            ][1],

            M2_PATCH,

        ),

    "MN_FB_M2_VERTICAL":

        vertical_box(

            MN_FB_M2_X,

            TARGET_POINTS[
                "MN_FB_GATE"
            ][1],

            VRAW_BUS_Y,

            M2_WIDTH,

        ),


    # ------------------------------------------------------------
    # MP_FB V2 transfer.
    #
    # M2 vertical terminates directly into Bridge-1.
    # ------------------------------------------------------------

    "MP_FB_TRANSFER_M2_PATCH":

        centered_box(

            MP_FB_M2_X,

            TARGET_POINTS[
                "MP_FB_GATE"
            ][1],

            M2_PATCH,

        ),

    "MP_FB_M2_VERTICAL":

        vertical_box(

            MP_FB_M2_X,

            VRAW_BUS_Y,

            TARGET_POINTS[
                "MP_FB_GATE"
            ][1],

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
# 22. COMPONENT STRUCTURE
# ================================================================

M1_COMPONENTS = list(
    NEW_M1.each_merged()
)

M2_COMPONENTS = list(
    NEW_M2.each_merged()
)


# V2 adds a separate MP_FB M1 landing component.
M1_STRUCTURE_OK = (
    len(
        M1_COMPONENTS
    ) == 6
)


# M2 remains:
#   MN_ST1 transfer
#   Bridge1 + MP_FB transfer
#   Bridge2 + MN_FB transfer
M2_STRUCTURE_OK = (
    len(
        M2_COMPONENTS
    ) == 3
)


print()
print("=" * 80)
print("NEW VRAW V2 COMPONENT STRUCTURE")
print("=" * 80)

print(
    "M1 components:",
    len(
        M1_COMPONENTS
    ),
    "(expected 6)"
)

print(
    "M2 components:",
    len(
        M2_COMPONENTS
    ),
    "(expected 3)"
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
# 23. TARGET LANDINGS
# ================================================================

TARGET_ROUTE_MAP = {

    "MP_ST2_DRAIN":
        "MP_ST2_DRAIN_STUB",

    "MN_ST1_DRAIN":
        "MN_ST1_DRAIN_STUB",

    "MN_FB_GATE":
        "MN_FB_GATE_STUB",

    "MP_FB_GATE":
        "MP_FB_GATE_STUB",

    "MP_BUF_GATE":
        "MP_BUF_GATE_VERTICAL",

    "MN_BUF_GATE":
        "MN_BUF_GATE_STUB",

}


TARGET_LANDINGS_OK = True


print()
print("=" * 80)
print("VRAW V2 TARGET LANDING AUDIT")
print("=" * 80)


for target, route in TARGET_ROUTE_MAP.items():

    landed = not (

        kdb.Region(
            TARGET_BOXES[
                target
            ]
        )

        &

        kdb.Region(
            m1_shapes[
                route
            ]
        )

    ).is_empty()


    TARGET_LANDINGS_OK &= landed


    print(
        f"{target:18s}:",
        landed
    )


# ================================================================
# 24. PRE-EXISTING M1 OVERLAP AUDIT
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
    "Only intended VRAW terminals touched:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 25. PRE-EXISTING M2 OVERLAP AUDIT
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
    "VRAW isolated from pre-existing M2:",
    NO_UNEXPECTED_M2_OVERLAP
)


# ================================================================
# 26. PROTECTED TERMINAL AUDIT
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
        f"{name:22s}: "
        f"overlap={overlap} "
        f"clear={clear}"
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


    in_m1 = (

        (
            via_region
            -
            NEW_M1
        ).is_empty()

    )


    in_m2 = (

        (
            via_region
            -
            NEW_M2
        ).is_empty()

    )


    valid = bool(
        in_m1
        and
        in_m2
    )


    VIA_LANDING_OK &= valid


    print(
        f"{name:22s}: "
        f"M1={in_m1} "
        f"M2={in_m2} "
        f"valid={valid}"
    )


# ================================================================
# 28. CROSS-LAYER GRAPH CONNECTIVITY
# ================================================================

graph = {}


for index in range(
    len(
        M1_COMPONENTS
    )
):

    graph[
        ("M1", index)
    ] = set()


for index in range(
    len(
        M2_COMPONENTS
    )
):

    graph[
        ("M2", index)
    ] = set()


VIA_GRAPH_OK = True


for via_name, via_box in via1_shapes.items():

    via_region = kdb.Region(
        via_box
    )


    m1_hits = []

    m2_hits = []


    for index, polygon in enumerate(
        M1_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            &

            via_region

        ).is_empty():

            m1_hits.append(
                index
            )


    for index, polygon in enumerate(
        M2_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            &

            via_region

        ).is_empty():

            m2_hits.append(
                index
            )


    if (
        len(
            m1_hits
        ) != 1

        or

        len(
            m2_hits
        ) != 1
    ):

        VIA_GRAPH_OK = False

        print(
            "Graph ambiguity:",
            via_name,
            "M1=",
            m1_hits,
            "M2=",
            m2_hits
        )

        continue


    m1_node = (
        "M1",
        m1_hits[0],
    )

    m2_node = (
        "M2",
        m2_hits[0],
    )


    graph[
        m1_node
    ].add(
        m2_node
    )

    graph[
        m2_node
    ].add(
        m1_node
    )


ALL_NODES = set(
    graph.keys()
)


if ALL_NODES:

    start = next(
        iter(
            ALL_NODES
        )
    )

    visited = set()

    stack = [
        start
    ]


    while stack:

        node = stack.pop()

        if node in visited:
            continue

        visited.add(
            node
        )

        stack.extend(

            graph[
                node
            ]
            -
            visited

        )


else:

    visited = set()


GRAPH_CONNECTED = bool(

    VIA_GRAPH_OK

    and

    visited
    ==
    ALL_NODES

)


print()
print("=" * 80)
print("CROSS-LAYER VRAW V2 CONNECTIVITY")
print("=" * 80)

print(
    "VIA graph valid:",
    VIA_GRAPH_OK
)

print(
    "Graph nodes:",
    len(
        ALL_NODES
    )
)

print(
    "Visited nodes:",
    len(
        visited
    )
)

print(
    "Entire VRAW V2 connected:",
    GRAPH_CONNECTED
)


# ================================================================
# 29. SHAPE COUNTS
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
    19
)

EXPECTED_VIA1_COUNT = (
    8
)

EXPECTED_M2_COUNT = (
    13
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
        "36C",

    "routing_stage":
        "7_of_9_VRAW",

    "version":
        "v2",

    "status":
        "CONSTRUCTION_PASS_PENDING_DRC",

    "v1_status":
        "REJECTED_VRAW_TO_VSS_M1_SHORT",

    "v1_failure": {

        "shape":
            "MP_FB_GATE_VERTICAL",

        "existing_net":
            "VSS",

        "overlap_bbox_um":
            [
                24.335,
                12.985,
                24.565,
                13.215,
            ],

    },

    "repair": {

        "mp_fb_m1_vertical_removed":
            True,

        "mp_fb_transfer_x_um":
            MP_FB_M2_X,

        "strategy":
            "M1_left_escape_then_M2_vertical_to_bridge1",

    },

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

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "explicit_clearances":
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

        "via_landings":
            VIA_LANDING_OK,

        "cross_layer_graph":
            GRAPH_CONNECTED,

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

STEP36C_PASS = bool(

    REFERENCE_OK

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

    VIA_LANDING_OK

    and

    GRAPH_CONNECTED

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
print("STEP 36C RESULT")
print("=" * 80)

print(
    "Reference VRAW topology     :",
    REFERENCE_OK
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
    "All VRAW target landings    :",
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
    "Cross-layer VRAW connected  :",
    GRAPH_CONNECTED
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
    "Canonical Stage-6 unchanged :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP36C_PASS =",
    STEP36C_PASS
)


if not STEP36C_PASS:

    raise RuntimeError(
        "STEP 36C VRAW V2 construction failed."
    )


print()
print("=" * 80)
print("VRAW V2 CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "VRAW V1:"
)

print(
    "  REJECTED"
)

print(
    "  MP_FB gate M1 route shorted to VSS"
)

print()
print(
    "VRAW V2:"
)

print(
    "  MP_FB gate transferred to M2 at x=22.600 um"
)

print(
    "  VSS crossed only on different metal layer"
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
    "  Official SKY130 DRC on VRAW V2."
)