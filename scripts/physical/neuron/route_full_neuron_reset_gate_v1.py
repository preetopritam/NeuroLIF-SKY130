# ================================================================
# NeuroLIF-SKY130
# STEP 38A — Final routing Stage 9/9
# SPIKE -> MN_RST gate
#
# Input:
#   neurolif_full_neuron_spike_v1.gds
#
# Frozen topology:
#
#   MN_RST VMEM SPIKE VSS VSS
#
# Existing:
#   MN_RST drain  -> VMEM
#   MN_RST source -> VSS
#   SPIKE          -> MP_BUF drain + MN_BUF drain + external M2
#
# Missing:
#   SPIKE -> MN_RST gate
#
# Strategy:
#   existing SPIKE M2 spine at x=28.600
#        |
#        +---- M2 horizontal @ y=MN_RST top-gate contact
#                                      |
#                                     VIA1
#                                      |
#                                MN_RST gate M1
#
# This is the FINAL routing stage.
# ================================================================

from pathlib import Path
import hashlib
import json
import math

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 38A: SPIKE -> MN_RST GATE")
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
    / "neurolif_full_neuron_spike_v1.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_spike_v1.json"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

STAGE8_DRC = (
    NEURON_DIR
    / "neurolif_full_neuron_spike_v1_drc.lyrdb"
)

OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_final_routed_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_final_routed_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_final_routed_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_SPIKE_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    STAGE8_DRC,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. INPUT HASH
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
# 3. FROZEN REFERENCE
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


REFERENCE_LINES = {

    "MN_RST":
        "MN_RST VMEM SPIKE VSS VSS",

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
print("REFERENCE FINAL-SPIKE TOPOLOGY")
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
        "Frozen reset/SPIKE topology mismatch."
    )


# ================================================================
# 4. LOAD CANONICAL STAGE-8
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
# 6. RESET DEVICE
# ================================================================

N_RESET_NAME = (
    "N_RESET_W1200_L0150"
)


n_reset = layout.cell(
    N_RESET_NAME
)


if n_reset is None:

    raise RuntimeError(
        f"Missing primitive: {N_RESET_NAME}"
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


def box_um(
    box,
):

    return (

        round(
            to_um(
                box.left
            ),
            3
        ),

        round(
            to_um(
                box.bottom
            ),
            3
        ),

        round(
            to_um(
                box.right
            ),
            3
        ),

        round(
            to_um(
                box.top
            ),
            3
        ),

    )


# ================================================================
# 8. RESET TERMINAL EXTRACTION
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
            f"{cell.name}: expected >=4 M1 terminal shapes."
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


RESET_TERMS = primitive_terminal_boxes(
    n_reset
)


# ================================================================
# 9. RESET INSTANCE
# ================================================================

MN_RST_ORIGIN = (
    36.0,
    7.0
)


def reset_abs_box(
    terminal,
):

    return translate_box(

        RESET_TERMS[
            terminal
        ],

        MN_RST_ORIGIN,

    )


RESET_SOURCE = reset_abs_box(
    "LEFT_SD"
)

RESET_DRAIN = reset_abs_box(
    "RIGHT_SD"
)

RESET_GATE_BOTTOM = reset_abs_box(
    "BOTTOM_GATE"
)

RESET_GATE_TOP = reset_abs_box(
    "TOP_GATE"
)


RESET_SOURCE_POINT = center_um(
    RESET_SOURCE
)

RESET_DRAIN_POINT = center_um(
    RESET_DRAIN
)

RESET_GATE_BOTTOM_POINT = center_um(
    RESET_GATE_BOTTOM
)

RESET_GATE_TOP_POINT = center_um(
    RESET_GATE_TOP
)


print()
print("=" * 80)
print("MN_RST PHYSICAL TERMINALS")
print("=" * 80)

print(
    "Source / VSS      :",
    RESET_SOURCE_POINT,
    "bbox=",
    box_um(
        RESET_SOURCE
    )
)

print(
    "Drain / VMEM      :",
    RESET_DRAIN_POINT,
    "bbox=",
    box_um(
        RESET_DRAIN
    )
)

print(
    "Bottom gate/SPIKE :",
    RESET_GATE_BOTTOM_POINT,
    "bbox=",
    box_um(
        RESET_GATE_BOTTOM
    )
)

print(
    "Top gate/SPIKE    :",
    RESET_GATE_TOP_POINT,
    "bbox=",
    box_um(
        RESET_GATE_TOP
    )
)


# ================================================================
# 10. ROUTING PARAMETERS
# ================================================================

SPIKE_X = (
    28.600
)


RESET_GATE_X = (
    RESET_GATE_TOP_POINT[
        0
    ]
)

RESET_GATE_Y = (
    RESET_GATE_TOP_POINT[
        1
    ]
)


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


print()
print("=" * 80)
print("FINAL SPIKE BRANCH GEOMETRY")
print("=" * 80)

print(
    "Existing SPIKE spine X:",
    SPIKE_X,
    "um"
)

print(
    "MN_RST gate target:",
    (
        RESET_GATE_X,
        RESET_GATE_Y,
    )
)

print(
    "New branch layer:",
    "MET2"
)


# ================================================================
# 11. PRE-EXISTING CONDUCTORS
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


PRE_M2_COMPONENTS = list(
    PRE_M2.each_merged()
)


# ================================================================
# 12. IDENTIFY EXISTING SPIKE M2 COMPONENT
# ================================================================

def component_at_point(
    components,
    x,
    y,
):

    probe = kdb.Region(

        centered_box(
            x,
            y,
            0.020,
        )

    )


    hits = []


    for index, polygon in enumerate(
        components
    ):

        if not (

            kdb.Region(
                polygon
            )

            &

            probe

        ).is_empty():

            hits.append(
                index
            )


    if len(
        hits
    ) == 1:

        return hits[0]


    return None


SPIKE_COMPONENT = component_at_point(

    PRE_M2_COMPONENTS,

    SPIKE_X,

    RESET_GATE_Y,

)


print()
print("=" * 80)
print("EXISTING SPIKE M2 IDENTIFICATION")
print("=" * 80)

print(
    "SPIKE component index:",
    SPIKE_COMPONENT
)


SPIKE_COMPONENT_FOUND = (
    SPIKE_COMPONENT is not None
)


# ================================================================
# 13. RESET LANDING CLEARANCE
# ================================================================

M1_MIN_SPACING = (
    0.140
)


LANDING = centered_box(

    RESET_GATE_X,

    RESET_GATE_Y,

    M1_LANDING_SIZE,

)


# Minimum axis-aligned box distance helper.
def rectangle_distance_um(
    a,
    b,
):

    ax1 = to_um(
        a.left
    )

    ay1 = to_um(
        a.bottom
    )

    ax2 = to_um(
        a.right
    )

    ay2 = to_um(
        a.top
    )

    bx1 = to_um(
        b.left
    )

    by1 = to_um(
        b.bottom
    )

    bx2 = to_um(
        b.right
    )

    by2 = to_um(
        b.top
    )


    dx = max(

        bx1 - ax2,

        ax1 - bx2,

        0.0,

    )


    dy = max(

        by1 - ay2,

        ay1 - by2,

        0.0,

    )


    return math.hypot(
        dx,
        dy
    )


SOURCE_CLEARANCE = rectangle_distance_um(

    LANDING,
    RESET_SOURCE,

)


DRAIN_CLEARANCE = rectangle_distance_um(

    LANDING,
    RESET_DRAIN,

)


LANDING_CLEARANCE_OK = bool(

    SOURCE_CLEARANCE
    >=
    M1_MIN_SPACING

    and

    DRAIN_CLEARANCE
    >=
    M1_MIN_SPACING

)


print()
print("=" * 80)
print("RESET-GATE M1 CLEARANCE AUDIT")
print("=" * 80)

print(
    "Landing -> reset source/VSS:",
    round(
        SOURCE_CLEARANCE,
        3
    ),
    "um"
)

print(
    "Landing -> reset drain/VMEM:",
    round(
        DRAIN_CLEARANCE,
        3
    ),
    "um"
)

print(
    "Required minimum:",
    M1_MIN_SPACING,
    "um"
)

print(
    "Landing clear:",
    LANDING_CLEARANCE_OK
)


# ================================================================
# 14. CREATE OUTPUT TOP
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
# 15. NEW M1 LANDING
# ================================================================

m1_shapes = {

    "MN_RST_SPIKE_GATE_LANDING":

        centered_box(

            RESET_GATE_X,

            RESET_GATE_Y,

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
# 16. VIA1
# ================================================================

via1_shapes = {

    "MN_RST_SPIKE_GATE_VIA":

        centered_box(

            RESET_GATE_X,

            RESET_GATE_Y,

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
# 17. M2 FINAL SPIKE BRANCH
# ================================================================

m2_shapes = {

    "MN_RST_SPIKE_M2_PATCH":

        centered_box(

            RESET_GATE_X,

            RESET_GATE_Y,

            M2_LANDING_SIZE,

        ),

    "SPIKE_TO_RESET_M2_BRANCH":

        horizontal_box(

            SPIKE_X,

            RESET_GATE_X,

            RESET_GATE_Y,

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
# 18. NEW REGIONS
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
# 19. RESET GATE LANDING
# ================================================================

TOP_GATE_LANDING = not (

    NEW_M1

    &

    kdb.Region(
        RESET_GATE_TOP
    )

).is_empty()


BOTTOM_GATE_PHYSICALLY_UNTOUCHED = (

    NEW_M1

    &

    kdb.Region(
        RESET_GATE_BOTTOM
    )

).is_empty()


print()
print("=" * 80)
print("RESET-GATE LANDING AUDIT")
print("=" * 80)

print(
    "Top gate contacted:",
    TOP_GATE_LANDING
)

print(
    "Bottom gate M1 untouched:",
    BOTTOM_GATE_PHYSICALLY_UNTOUCHED
)

print(
    "Both are same MOS gate through poly."
)


# ================================================================
# 20. SOURCE / DRAIN MUST STAY CLEAR
# ================================================================

SOURCE_OVERLAP = not (

    NEW_M1

    &

    kdb.Region(
        RESET_SOURCE
    )

).is_empty()


DRAIN_OVERLAP = not (

    NEW_M1

    &

    kdb.Region(
        RESET_DRAIN
    )

).is_empty()


RESET_SD_CLEAR = bool(

    not SOURCE_OVERLAP

    and

    not DRAIN_OVERLAP
)


print()
print("=" * 80)
print("RESET SOURCE/DRAIN PROTECTION")
print("=" * 80)

print(
    "Source/VSS overlap:",
    SOURCE_OVERLAP
)

print(
    "Drain/VMEM overlap:",
    DRAIN_OVERLAP
)

print(
    "Reset source/drain clear:",
    RESET_SD_CLEAR
)


# ================================================================
# 21. NEW M1 MAY TOUCH ONLY RESET TOP GATE
# ================================================================

ACTUAL_M1_OVERLAP = (

    NEW_M1

    &

    PRE_M1

)


ALLOWED_M1_OVERLAP = kdb.Region(
    RESET_GATE_TOP
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
    "Only MN_RST top gate contacted:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 22. NEW M2 MAY TOUCH ONLY EXISTING SPIKE COMPONENT
# ================================================================

TOUCHED_M2_COMPONENTS = []


for index, polygon in enumerate(
    PRE_M2_COMPONENTS
):

    hit = not (

        NEW_M2

        &

        kdb.Region(
            polygon
        )

    ).is_empty()


    if hit:

        TOUCHED_M2_COMPONENTS.append(
            index
        )


M2_TOUCHES_ONLY_SPIKE = bool(

    SPIKE_COMPONENT_FOUND

    and

    TOUCHED_M2_COMPONENTS
    ==
    [
        SPIKE_COMPONENT
    ]

)


print()
print("=" * 80)
print("PRE-EXISTING M2 CONNECTIVITY AUDIT")
print("=" * 80)

print(
    "Existing SPIKE component:",
    SPIKE_COMPONENT
)

print(
    "Touched M2 components:",
    TOUCHED_M2_COMPONENTS
)

print(
    "Touches only existing SPIKE:",
    M2_TOUCHES_ONLY_SPIKE
)


# ================================================================
# 23. VIA LANDING
# ================================================================

via_region = kdb.Region(

    via1_shapes[
        "MN_RST_SPIKE_GATE_VIA"
    ]

)


VIA_IN_M1 = (

    (
        via_region
        -
        NEW_M1
    ).is_empty()

)


VIA_IN_M2 = (

    (
        via_region
        -
        NEW_M2
    ).is_empty()

)


VIA_LANDING_OK = bool(

    VIA_IN_M1

    and

    VIA_IN_M2
)


print()
print("=" * 80)
print("VIA LANDING AUDIT")
print("=" * 80)

print(
    "VIA enclosed by M1:",
    VIA_IN_M1
)

print(
    "VIA enclosed by M2:",
    VIA_IN_M2
)

print(
    "VIA landing valid:",
    VIA_LANDING_OK
)


# ================================================================
# 24. NEW M2 INTERNAL CONNECTIVITY
# ================================================================

NEW_M2_COMPONENTS = list(
    NEW_M2.each_merged()
)


NEW_M2_CONNECTED = (
    len(
        NEW_M2_COMPONENTS
    ) == 1
)


SPIKE_BRANCH_START = kdb.Region(

    centered_box(

        SPIKE_X,

        RESET_GATE_Y,

        0.020,

    )

)


BRANCH_TOUCHES_EXISTING_SPIKE = not (

    SPIKE_BRANCH_START

    &

    PRE_M2

).is_empty()


print()
print("=" * 80)
print("FINAL SPIKE CONNECTIVITY")
print("=" * 80)

print(
    "New M2 components:",
    len(
        NEW_M2_COMPONENTS
    ),
    "(expected 1)"
)

print(
    "New branch internally connected:",
    NEW_M2_CONNECTED
)

print(
    "Branch touches existing SPIKE:",
    BRANCH_TOUCHES_EXISTING_SPIKE
)

print(
    "Reset gate contacted:",
    TOP_GATE_LANDING
)


FINAL_SPIKE_CONNECTED = bool(

    NEW_M2_CONNECTED

    and

    BRANCH_TOUCHES_EXISTING_SPIKE

    and

    M2_TOUCHES_ONLY_SPIKE

    and

    VIA_LANDING_OK

    and

    TOP_GATE_LANDING
)


print(
    "SPIKE -> MN_RST gate complete:",
    FINAL_SPIKE_CONNECTED
)


# ================================================================
# 25. NEW SHAPE COUNTS
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
    1
)

EXPECTED_VIA1_COUNT = (
    1
)

EXPECTED_M2_COUNT = (
    2
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
# 26. SERIALIZATION MAP
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
        "38A",

    "routing_stage":
        "9_of_9_SPIKE_TO_RESET",

    "version":
        "v1",

    "status":
        "FINAL_ROUTING_CONSTRUCTION_PASS_PENDING_DRC",

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

    "connection": {

        "existing_net":
            "SPIKE",

        "target_device":
            "MN_RST",

        "target_terminal":
            "gate",

        "physical_gate_contact":
            "TOP_GATE",

        "target_coordinate_um":
            list(
                RESET_GATE_TOP_POINT
            ),

    },

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "spike_component_found":
            SPIKE_COMPONENT_FOUND,

        "landing_clearance":
            LANDING_CLEARANCE_OK,

        "top_gate_landing":
            TOP_GATE_LANDING,

        "bottom_gate_physically_untouched":
            BOTTOM_GATE_PHYSICALLY_UNTOUCHED,

        "reset_source_drain_clear":
            RESET_SD_CLEAR,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "m2_touches_only_spike":
            M2_TOUCHES_ONLY_SPIKE,

        "via_landing":
            VIA_LANDING_OK,

        "new_m2_connected":
            NEW_M2_CONNECTED,

        "branch_touches_existing_spike":
            BRANCH_TOUCHES_EXISTING_SPIKE,

        "final_spike_connected":
            FINAL_SPIKE_CONNECTED,

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
# 31. FINAL GATE
# ================================================================

STEP38A_PASS = bool(

    REFERENCE_OK

    and

    SPIKE_COMPONENT_FOUND

    and

    LANDING_CLEARANCE_OK

    and

    TOP_GATE_LANDING

    and

    BOTTOM_GATE_PHYSICALLY_UNTOUCHED

    and

    RESET_SD_CLEAR

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    M2_TOUCHES_ONLY_SPIKE

    and

    VIA_LANDING_OK

    and

    NEW_M2_CONNECTED

    and

    BRANCH_TOUCHES_EXISTING_SPIKE

    and

    FINAL_SPIKE_CONNECTED

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
print("STEP 38A RESULT")
print("=" * 80)

print(
    "Reference topology          :",
    REFERENCE_OK
)

print(
    "Existing SPIKE identified   :",
    SPIKE_COMPONENT_FOUND
)

print(
    "Reset-gate landing clearance:",
    LANDING_CLEARANCE_OK
)

print(
    "MN_RST top gate contacted   :",
    TOP_GATE_LANDING
)

print(
    "MN_RST source/drain clear   :",
    RESET_SD_CLEAR
)

print(
    "No unexpected M1 overlap    :",
    NO_UNEXPECTED_M1_OVERLAP
)

print(
    "M2 touches only SPIKE       :",
    M2_TOUCHES_ONLY_SPIKE
)

print(
    "VIA landing valid           :",
    VIA_LANDING_OK
)

print(
    "New M2 internally connected :",
    NEW_M2_CONNECTED
)

print(
    "Branch touches SPIKE        :",
    BRANCH_TOUCHES_EXISTING_SPIKE
)

print(
    "SPIKE -> reset gate complete:",
    FINAL_SPIKE_CONNECTED
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
    "Canonical Stage-8 unchanged :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP38A_PASS =",
    STEP38A_PASS
)


if not STEP38A_PASS:

    raise RuntimeError(
        "STEP 38A final reset-gate routing failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 9/9 — CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "SPIKE now connects:"
)

print(
    "  MP_BUF drain"
)

print(
    "  MN_BUF drain"
)

print(
    "  external SPIKE output"
)

print(
    "  MN_RST gate"
)

print()
print(
    "All 9 routing stages are now physically constructed."
)

print()
print(
    "Candidate final routed GDS:"
)

print(
    OUTPUT_GDS
)

print()
print(
    "NEXT:"
)

print(
    "  Official full SKY130 DRC on final routed core."
)