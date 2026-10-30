# ================================================================
# NeuroLIF-SKY130
# STEP 34D — Full-neuron P_MID routing V2
#
# Purpose:
#   Repair the two m1.2 violations in rejected P_MID V1.
#
# Confirmed official DRC root cause:
#
#   MP_FB_SOURCE terminal left edge : x = 24.005 um
#   V1 via-patch right edge         : x = 23.900 um
#
#   resulting notch spacing:
#       24.005 - 23.900 = 0.105 um
#
#   SKY130 m1.2 minimum:
#       0.140 um
#
# V2 repair:
#
#   MP_FB_SOURCE via center:
#       V1: x = 23.650 um
#       V2: x = 23.400 um
#
#   V2 patch right edge:
#       23.400 + 0.250 = 23.650 um
#
#   expected notch clearance:
#       24.005 - 23.650 = 0.355 um
#
# IMPORTANT:
#   Rebuild directly from canonical Stage-4 GDS.
#   Do NOT modify rejected P_MID V1.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 34D: P_MID V2 SPACING REPAIR")
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
    / "neurolif_full_neuron_vleak_v1.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vleak_v1.json"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

STAGE4_DRC = (
    NEURON_DIR
    / "neurolif_full_neuron_vleak_v1_drc.lyrdb"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_pmid_v2.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_pmid_v2.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_pmid_v2.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VLEAK_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_PMID_V2"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    STAGE4_DRC,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. INPUT HASH
# ================================================================

def sha256_file(path):

    h = hashlib.sha256()

    with path.open("rb") as f:

        while True:

            block = f.read(
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

    "MP_ST1":
        "MP_ST1 P_MID VMEM VDD VDD",

    "MP_ST2":
        "MP_ST2 VRAW VMEM P_MID VDD",

    "MP_FB":
        "MP_FB VSS VRAW P_MID VDD",

}


reference_checks = {

    key:
        value in reference_text

    for key, value
    in REFERENCE_LINES.items()

}


REFERENCE_OK = all(
    reference_checks.values()
)


print()
print("=" * 80)
print("REFERENCE P_MID TOPOLOGY")
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
        "Frozen P_MID topology mismatch."
    )


# ================================================================
# 4. LOAD CANONICAL STAGE-4 GDS
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

P_LOGIC_NAME = (
    "P_LOGIC_W2000_L0150"
)

P_FB_NAME = (
    "P_FB_W0420_L0300"
)


p_logic = layout.cell(
    P_LOGIC_NAME
)

p_fb = layout.cell(
    P_FB_NAME
)


if p_logic is None:
    raise RuntimeError(P_LOGIC_NAME)

if p_fb is None:
    raise RuntimeError(P_FB_NAME)


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

            f"{cell.name}: expected >=4 M1 terminal shapes, "
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


P_LOGIC_TERMS = primitive_terminal_boxes(
    p_logic
)

P_FB_TERMS = primitive_terminal_boxes(
    p_fb
)


# ================================================================
# 9. PLACEMENT
# ================================================================

ORIGINS = {

    "MP_ST1":
        (16.0, 14.0),

    "MP_ST2":
        (20.0, 14.0),

    "MP_FB":
        (24.0, 14.0),

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
# 10. P_MID TARGETS
# ================================================================

TARGET_BOXES = {

    "MP_ST1_DRAIN":

        abs_box(
            P_LOGIC_TERMS,
            "RIGHT_SD",
            "MP_ST1",
        ),

    "MP_ST2_SOURCE":

        abs_box(
            P_LOGIC_TERMS,
            "LEFT_SD",
            "MP_ST2",
        ),

    "MP_FB_SOURCE":

        abs_box(
            P_FB_TERMS,
            "LEFT_SD",
            "MP_FB",
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
print("P_MID TARGET TERMINALS")
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

    "MP_ST1_SOURCE_VDD":

        abs_box(
            P_LOGIC_TERMS,
            "LEFT_SD",
            "MP_ST1",
        ),

    "MP_ST2_DRAIN_VRAW":

        abs_box(
            P_LOGIC_TERMS,
            "RIGHT_SD",
            "MP_ST2",
        ),

    "MP_FB_DRAIN_VSS":

        abs_box(
            P_FB_TERMS,
            "RIGHT_SD",
            "MP_FB",
        ),

    "MP_ST1_GATE_B":

        abs_box(
            P_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MP_ST1",
        ),

    "MP_ST1_GATE_T":

        abs_box(
            P_LOGIC_TERMS,
            "TOP_GATE",
            "MP_ST1",
        ),

    "MP_ST2_GATE_B":

        abs_box(
            P_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MP_ST2",
        ),

    "MP_ST2_GATE_T":

        abs_box(
            P_LOGIC_TERMS,
            "TOP_GATE",
            "MP_ST2",
        ),

    "MP_FB_GATE_B":

        abs_box(
            P_FB_TERMS,
            "BOTTOM_GATE",
            "MP_FB",
        ),

    "MP_FB_GATE_T":

        abs_box(
            P_FB_TERMS,
            "TOP_GATE",
            "MP_FB",
        ),

}


# ================================================================
# 12. ROUTING PARAMETERS
# ================================================================

M1_STUB_WIDTH = (
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

M2_ROUTE_WIDTH = (
    0.400
)

PMID_BUS_Y = (
    17.000
)


# ================================================================
# 13. V2 VIA LOCATIONS
#
# Only MP_FB source differs from rejected V1.
# ================================================================

VIA_POINTS = {

    "MP_ST1_DRAIN":
        (
            17.400,
            TARGET_POINTS[
                "MP_ST1_DRAIN"
            ][1],
        ),

    "MP_ST2_SOURCE":
        (
            19.400,
            TARGET_POINTS[
                "MP_ST2_SOURCE"
            ][1],
        ),

    # V1 = 23.650 -> caused 0.105um m1.2 notches.
    # V2 = 23.400 -> expected 0.355um notch clearance.
    "MP_FB_SOURCE":
        (
            23.400,
            TARGET_POINTS[
                "MP_FB_SOURCE"
            ][1],
        ),

}


print()
print("=" * 80)
print("P_MID V2 VIA LOCATIONS")
print("=" * 80)


for name, point in VIA_POINTS.items():

    print(
        f"{name:18s}:",
        tuple(
            round(v, 3)
            for v in point
        )
    )


# ================================================================
# 14. EXPLICIT M1 NECK / NOTCH CLEARANCE AUDIT
#
# For a target and its wider 0.500um via patch connected by
# a narrower 0.230um stub, the side-notch spacing is the
# horizontal gap between target terminal and patch.
#
# Must be >= SKY130 m1.2 = 0.140um.
# ================================================================

M1_MIN_SPACING = (
    0.140
)


NECK_CLEARANCES = {}


for name, target_box in TARGET_BOXES.items():

    target_center = TARGET_POINTS[
        name
    ]

    via_point = VIA_POINTS[
        name
    ]


    patch_left = (
        via_point[0]
        -
        M1_PATCH_SIZE / 2.0
    )

    patch_right = (
        via_point[0]
        +
        M1_PATCH_SIZE / 2.0
    )


    target_left = to_um(
        target_box.left
    )

    target_right = to_um(
        target_box.right
    )


    # Patch is to RIGHT of terminal.
    if via_point[0] > target_center[0]:

        clearance = (
            patch_left
            -
            target_right
        )

        direction = (
            "PATCH_RIGHT_OF_TARGET"
        )

    # Patch is to LEFT of terminal.
    else:

        clearance = (
            target_left
            -
            patch_right
        )

        direction = (
            "PATCH_LEFT_OF_TARGET"
        )


    NECK_CLEARANCES[
        name
    ] = {

        "clearance_um":
            clearance,

        "direction":
            direction,

        "valid":
            clearance
            >=
            M1_MIN_SPACING,

    }


print()
print("=" * 80)
print("EXPLICIT m1.2 NECK-CLEARANCE AUDIT")
print("=" * 80)


for name, result in NECK_CLEARANCES.items():

    print(
        f"{name:18s}: "
        f"{result['clearance_um']:.3f} um "
        f"required >= {M1_MIN_SPACING:.3f} um "
        f"valid={result['valid']}"
    )


NECK_CLEARANCE_OK = all(

    result[
        "valid"
    ]

    for result
    in NECK_CLEARANCES.values()

)


MP_FB_CLEARANCE = (
    NECK_CLEARANCES[
        "MP_FB_SOURCE"
    ][
        "clearance_um"
    ]
)


print()
print(
    "MP_FB V1 confirmed clearance : 0.105 um"
)

print(
    "MP_FB V2 calculated clearance:",
    round(
        MP_FB_CLEARANCE,
        3
    ),
    "um"
)

print(
    "All neck clearances valid    :",
    NECK_CLEARANCE_OK
)


# ================================================================
# 15. PRE-EXISTING ROUTING
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
# 16. CREATE OUTPUT WRAPPER
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
# 17. M1 STUBS + PATCHES
# ================================================================

m1_shapes = {}


for name, target_point in TARGET_POINTS.items():

    via_point = VIA_POINTS[
        name
    ]


    m1_shapes[
        f"{name}_STUB"
    ] = horizontal_box(

        target_point[0],

        via_point[0],

        target_point[1],

        M1_STUB_WIDTH,

    )


    m1_shapes[
        f"{name}_PATCH"
    ] = centered_box(

        via_point[0],

        via_point[1],

        M1_PATCH_SIZE,

    )


for box in m1_shapes.values():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


# ================================================================
# 18. VIA1 + M2 PATCHES
# ================================================================

via1_shapes = {}
m2_patch_shapes = {}


for name, point in VIA_POINTS.items():

    via1_shapes[
        name
    ] = centered_box(

        point[0],

        point[1],

        VIA1_SIZE,

    )


    m2_patch_shapes[
        name
    ] = centered_box(

        point[0],

        point[1],

        M2_PATCH_SIZE,

    )


for box in via1_shapes.values():

    top.shapes(
        VIA1_LAYER
    ).insert(
        box
    )


for box in m2_patch_shapes.values():

    top.shapes(
        M2_LAYER
    ).insert(
        box
    )


# ================================================================
# 19. M2 P_MID NETWORK
# ================================================================

m2_route_shapes = {

    "PMID_BUS":

        horizontal_box(

            VIA_POINTS[
                "MP_ST1_DRAIN"
            ][0],

            VIA_POINTS[
                "MP_FB_SOURCE"
            ][0],

            PMID_BUS_Y,

            M2_ROUTE_WIDTH,

        ),

    "PMID_ST1_VERTICAL":

        vertical_box(

            VIA_POINTS[
                "MP_ST1_DRAIN"
            ][0],

            VIA_POINTS[
                "MP_ST1_DRAIN"
            ][1],

            PMID_BUS_Y,

            M2_ROUTE_WIDTH,

        ),

    "PMID_ST2_VERTICAL":

        vertical_box(

            VIA_POINTS[
                "MP_ST2_SOURCE"
            ][0],

            VIA_POINTS[
                "MP_ST2_SOURCE"
            ][1],

            PMID_BUS_Y,

            M2_ROUTE_WIDTH,

        ),

    "PMID_FB_VERTICAL":

        vertical_box(

            VIA_POINTS[
                "MP_FB_SOURCE"
            ][0],

            VIA_POINTS[
                "MP_FB_SOURCE"
            ][1],

            PMID_BUS_Y,

            M2_ROUTE_WIDTH,

        ),

}


for box in m2_route_shapes.values():

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


for box in m2_patch_shapes.values():

    NEW_M2.insert(
        box
    )


for box in m2_route_shapes.values():

    NEW_M2.insert(
        box
    )


NEW_M2.merge()


# ================================================================
# 21. NEW P_MID M2 CONNECTIVITY
# ================================================================

M2_COMPONENT_COUNT = len(

    list(
        NEW_M2.each_merged()
    )

)


NEW_M2_CONNECTED = (
    M2_COMPONENT_COUNT == 1
)


print()
print("=" * 80)
print("P_MID V2 M2 CONNECTIVITY")
print("=" * 80)

print(
    "Merged components:",
    M2_COMPONENT_COUNT
)

print(
    "Single P_MID network:",
    NEW_M2_CONNECTED
)


# ================================================================
# 22. NO CONTACT WITH PRE-EXISTING M2
# ================================================================

PRE_M2_OVERLAP = (

    NEW_M2
    &
    PRE_M2

)


NO_PREEXISTING_M2_SHORT = (
    PRE_M2_OVERLAP.is_empty()
)


print()
print("=" * 80)
print("PRE-EXISTING M2 AUDIT")
print("=" * 80)

print(
    "Unexpected M2 overlap:",
    not NO_PREEXISTING_M2_SHORT
)

print(
    "P_MID isolated from existing M2:",
    NO_PREEXISTING_M2_SHORT
)


# ================================================================
# 23. M1 CONTACT AUDIT
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
print("PRE-EXISTING M1 AUDIT")
print("=" * 80)

print(
    "Unexpected M1 overlap:",
    not NO_UNEXPECTED_M1_OVERLAP
)

print(
    "Only intended P_MID terminals touched:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 24. TARGET LANDINGS
# ================================================================

TARGET_LANDINGS_OK = True


print()
print("=" * 80)
print("TARGET LANDING AUDIT")
print("=" * 80)


for name, target_box in TARGET_BOXES.items():

    stub_region = kdb.Region(

        m1_shapes[
            f"{name}_STUB"
        ]

    )


    landed = not (

        stub_region

        &

        kdb.Region(
            target_box
        )

    ).is_empty()


    TARGET_LANDINGS_OK &= landed


    print(
        f"{name:18s}:",
        landed
    )


# ================================================================
# 25. PROTECTED TERMINALS
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
# 26. VIA LANDINGS
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


    m1_patch = kdb.Region(

        m1_shapes[
            f"{name}_PATCH"
        ]

    )


    m2_patch = kdb.Region(

        m2_patch_shapes[
            name
        ]

    )


    via_inside_m1 = (

        (
            via_region
            -
            m1_patch
        ).is_empty()

    )


    via_inside_m2 = (

        (
            via_region
            -
            m2_patch
        ).is_empty()

    )


    m1_stub_connected = not (

        m1_patch

        &

        kdb.Region(
            m1_shapes[
                f"{name}_STUB"
            ]
        )

    ).is_empty()


    m2_connected = not (

        m2_patch
        &
        NEW_M2

    ).is_empty()


    valid = bool(

        via_inside_m1

        and

        via_inside_m2

        and

        m1_stub_connected

        and

        m2_connected

    )


    VIA_LANDING_OK &= valid


    print(
        f"{name:18s}: "
        f"M1={via_inside_m1} "
        f"M2={via_inside_m2} "
        f"stub={m1_stub_connected} "
        f"route={m2_connected} "
        f"valid={valid}"
    )


# ================================================================
# 27. SHAPE COUNTS
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
    6
)

EXPECTED_VIA1_COUNT = (
    3
)

EXPECTED_M2_COUNT = (
    7
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
# 28. SERIALIZATION
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
# 29. WRITE
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
# 30. READBACK
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
# 31. INPUT INTEGRITY
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
# 32. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "34D",

    "routing_stage":
        "5_of_9_P_MID",

    "version":
        "v2",

    "status":
        "CONSTRUCTION_PASS_PENDING_DRC",

    "v1_status":
        "REJECTED_m1.2_2_violations",

    "repair": {

        "confirmed_rule":
            "m1.2",

        "required_spacing_um":
            0.140,

        "confirmed_v1_spacing_um":
            0.105,

        "confirmed_marker_x_edges_um":
            [
                23.900,
                24.005,
            ],

        "mp_fb_v1_via_x_um":
            23.650,

        "mp_fb_v2_via_x_um":
            23.400,

        "calculated_v2_clearance_um":
            MP_FB_CLEARANCE,

    },

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

    "via_points": {

        name:
            list(point)

        for name, point
        in VIA_POINTS.items()

    },

    "neck_clearances": {

        name: {

            "clearance_um":
                result[
                    "clearance_um"
                ],

            "valid":
                result[
                    "valid"
                ],

        }

        for name, result
        in NECK_CLEARANCES.items()

    },

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "neck_clearance":
            NECK_CLEARANCE_OK,

        "new_m2_connected":
            NEW_M2_CONNECTED,

        "no_existing_m2_short":
            NO_PREEXISTING_M2_SHORT,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "target_landings":
            TARGET_LANDINGS_OK,

        "protected_terminals":
            PROTECTED_CLEAR,

        "via_landings":
            VIA_LANDING_OK,

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
# 33. FINAL GATE
# ================================================================

STEP34D_PASS = bool(

    REFERENCE_OK

    and

    NECK_CLEARANCE_OK

    and

    NEW_M2_CONNECTED

    and

    NO_PREEXISTING_M2_SHORT

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    TARGET_LANDINGS_OK

    and

    PROTECTED_CLEAR

    and

    VIA_LANDING_OK

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
print("STEP 34D RESULT")
print("=" * 80)

print(
    "Reference P_MID topology    :",
    REFERENCE_OK
)

print(
    "All m1.2 neck clearances    :",
    NECK_CLEARANCE_OK
)

print(
    "MP_FB V2 clearance          :",
    round(
        MP_FB_CLEARANCE,
        3
    ),
    "um"
)

print(
    "New P_MID M2 connected      :",
    NEW_M2_CONNECTED
)

print(
    "No existing-M2 short        :",
    NO_PREEXISTING_M2_SHORT
)

print(
    "No unexpected M1 overlap    :",
    NO_UNEXPECTED_M1_OVERLAP
)

print(
    "All target landings valid   :",
    TARGET_LANDINGS_OK
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
    "Canonical Stage-4 unchanged :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP34D_PASS =",
    STEP34D_PASS
)


if not STEP34D_PASS:

    raise RuntimeError(
        "STEP 34D P_MID V2 construction failed."
    )


print()
print("=" * 80)
print("P_MID V2 CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "P_MID V1:"
)

print(
    "  REJECTED"
)

print(
    "  2 x m1.2 violations"
)

print(
    "  confirmed spacing = 0.105 um"
)

print()
print(
    "P_MID V2:"
)

print(
    "  MP_FB via moved left"
)

print(
    "  calculated MP_FB notch clearance =",
    round(
        MP_FB_CLEARANCE,
        3
    ),
    "um"
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
    "  Official SKY130 DRC on P_MID V2."
)