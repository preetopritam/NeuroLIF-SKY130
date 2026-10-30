# ================================================================
# NeuroLIF-SKY130
# STEP 32A — Full-neuron VMEM distribution V1
#
# Routing Stage 3/9
#
# Input:
#   neurolif_full_neuron_vss_v1.gds
#
# VMEM connectivity:
#
#   existing closed-synapse VMEM
#       -> MP_ST1 gate
#       -> MP_ST2 gate
#       -> MN_ST1 gate
#       -> MN_ST2 gate
#       -> MN_LEAK drain
#       -> MN_RST drain
#       -> external VMEM access
#
# Main distribution layer:
#   MET2 69/20
#
# Local terminal escapes:
#   MET1 68/20
#
# Layer transition:
#   VIA1 68/44
#
# Validated M1<->M2 via geometry:
#   M1 patch : 0.500 x 0.500 um
#   VIA1     : 0.150 x 0.150 um
#   M2 patch : 0.500 x 0.500 um
#
# CMEM:
#   remains EXTERNAL / IDEAL 5 pF.
#   No physical capacitor is introduced.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 32A: FULL-NEURON VMEM DISTRIBUTION V1")
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
    / "neurolif_full_neuron_vss_v1.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vss_v1.json"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

VSS_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_vss_v1_drc.lyrdb"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vmem_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_vmem_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vmem_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VSS_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VMEM_V1"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    VSS_DRC_REPORT,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. HASH HELPER
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

            digest.update(
                chunk
            )

    return digest.hexdigest()


INPUT_HASH_BEFORE = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. FROZEN REFERENCE TOPOLOGY CHECK
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


REFERENCE_REQUIREMENTS = {

    "MP_ST1":
        "MP_ST1 P_MID VMEM VDD VDD",

    "MP_ST2":
        "MP_ST2 VRAW VMEM P_MID VDD",

    "MN_ST1":
        "MN_ST1 VRAW VMEM N_MID VSS",

    "MN_ST2":
        "MN_ST2 N_MID VMEM VSS VSS",

    "MN_LEAK":
        "MN_LEAK VMEM VLEAK VSS VSS",

    "MN_RST":
        "MN_RST VMEM SPIKE VSS VSS",

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
print("REFERENCE VMEM TOPOLOGY AUDIT")
print("=" * 80)


for name, status in reference_checks.items():

    print(
        f"{name:10s}:",
        status
    )


print(
    "Reference VMEM topology valid:",
    REFERENCE_OK
)


if not REFERENCE_OK:

    raise RuntimeError(
        "Frozen VMEM reference topology mismatch."
    )


# ================================================================
# 4. LOAD STAGE-2 CANONICAL GDS
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

    (
        "MET1 68/20",
        M1_LAYER,
    ),

    (
        "VIA1 68/44",
        VIA1_LAYER,
    ),

    (
        "MET2 69/20",
        M2_LAYER,
    ),

]:

    if layer_index is None:

        raise RuntimeError(
            f"Missing layer: {name}"
        )


# ================================================================
# 6. REQUIRED DEVICE CELLS
# ================================================================

CELL_NAMES = {

    "P_LOGIC":
        "P_LOGIC_W2000_L0150",

    "N_LOGIC":
        "N_LOGIC_W1000_L0150",

    "N_LEAK":
        "N_LEAK_W0420_L1000",

    "N_RESET":
        "N_RESET_W1200_L0150",

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
# 7. GEOMETRY HELPERS
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

        box.left
        + dx,

        box.bottom
        + dy,

        box.right
        + dx,

        box.top
        + dy,

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


def probe_region(
    x,
    y,
    half=0.010,
):

    return kdb.Region(

        centered_box(
            x,
            y,
            2 * half,
        )

    )


# ================================================================
# 8. DEVICE TERMINAL EXTRACTION
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


    if len(
        boxes
    ) < 4:

        raise RuntimeError(

            f"{cell.name}: expected >=4 M1 terminal shapes, "
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


    remaining = [

        box

        for box
        in boxes

        if (
            box != left_sd
            and
            box != right_sd
        )

    ]


    bottom_gate = min(
        remaining,
        key=cy,
    )

    top_gate = max(
        remaining,
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
            cells[
                role
            ]
        )

    for role in CELL_NAMES

}


# ================================================================
# 9. FROZEN PLACEMENT ORIGINS
# ================================================================

ORIGINS = {

    "MP_ST1":
        (
            16.0,
            14.0,
        ),

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

    "MN_ST2":
        (
            20.0,
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
# 10. VMEM TARGET TERMINALS
#
# We use the LOWER gate contact for the four Schmitt input gates.
# Both M1 gate contacts belong to the same transistor gate.
# ================================================================

TARGET_BOXES = {

    "MP_ST1_GATE":

        abs_terminal_box(
            "P_LOGIC",
            "BOTTOM_GATE",
            "MP_ST1",
        ),

    "MP_ST2_GATE":

        abs_terminal_box(
            "P_LOGIC",
            "BOTTOM_GATE",
            "MP_ST2",
        ),

    "MN_ST1_GATE":

        abs_terminal_box(
            "N_LOGIC",
            "BOTTOM_GATE",
            "MN_ST1",
        ),

    "MN_ST2_GATE":

        abs_terminal_box(
            "N_LOGIC",
            "BOTTOM_GATE",
            "MN_ST2",
        ),

    "MN_LEAK_DRAIN":

        abs_terminal_box(
            "N_LEAK",
            "RIGHT_SD",
            "MN_LEAK",
        ),

    "MN_RST_DRAIN":

        abs_terminal_box(
            "N_RESET",
            "RIGHT_SD",
            "MN_RST",
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
print("VMEM TARGET TERMINALS")
print("=" * 80)


for name, point in TARGET_POINTS.items():

    print(
        f"{name:18s}:",
        tuple(
            round(
                value,
                3
            )

            for value
            in point
        )
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


# ================================================================
# 12. IDENTIFY EXISTING SYNAPSE VMEM M2 COMPONENT
#
# Frozen synapse VMEM bus lies at y = 1.000 um.
#
# Find the M2 component that intersects a thin horizontal
# observation strip around y=1.0 and has substantial width.
# ================================================================

VMEM_Y = (
    1.000
)


VMEM_SEARCH_STRIP = kdb.Region(

    kdb.Box(

        to_dbu(
            -1.0
        ),

        to_dbu(
            VMEM_Y
            -
            0.020
        ),

        to_dbu(
            12.0
        ),

        to_dbu(
            VMEM_Y
            +
            0.020
        ),

    )

)


m2_components = list(
    PRE_M2.each_merged()
)


vmem_candidates = []


for index, polygon in enumerate(
    m2_components
):

    region = kdb.Region(
        polygon
    )


    hit = (
        region
        &
        VMEM_SEARCH_STRIP
    )


    if hit.is_empty():
        continue


    bbox = hit.bbox()


    width_um = to_um(
        bbox.width()
    )


    if width_um < 2.0:
        continue


    vmem_candidates.append({

        "index":
            index,

        "polygon":
            polygon,

        "region":
            region,

        "intersection":
            hit,

        "intersection_bbox":
            bbox,

        "width_um":
            width_um,

    })


print()
print("=" * 80)
print("EXISTING VMEM M2 SEARCH")
print("=" * 80)

print(
    "Candidate count:",
    len(
        vmem_candidates
    )
)


for candidate in vmem_candidates:

    bbox = candidate[
        "intersection_bbox"
    ]

    print(
        "  candidate",
        candidate[
            "index"
        ],
        "x=(",
        round(
            to_um(
                bbox.left
            ),
            3
        ),
        ",",
        round(
            to_um(
                bbox.right
            ),
            3
        ),
        ") width=",
        round(
            candidate[
                "width_um"
            ],
            3
        ),
        "um"
    )


if len(
    vmem_candidates
) != 1:

    raise RuntimeError(

        "Could not uniquely identify the existing synapse "
        "VMEM M2 bus."

    )


VMEM_COMPONENT = (
    vmem_candidates[
        0
    ][
        "region"
    ]
)


VMEM_INTERSECTION_BBOX = (
    vmem_candidates[
        0
    ][
        "intersection_bbox"
    ]
)


# Choose an interior point near the RIGHT end of the existing bus.
VMEM_ANCHOR = (

    to_um(
        VMEM_INTERSECTION_BBOX.right
    )
    -
    0.100,

    VMEM_Y,

)


VMEM_ANCHOR_EXISTS = not (

    VMEM_COMPONENT

    &

    probe_region(
        VMEM_ANCHOR[0],
        VMEM_ANCHOR[1],
    )

).is_empty()


print(
    "VMEM anchor:",
    tuple(
        round(
            value,
            3
        )

        for value
        in VMEM_ANCHOR
    )
)

print(
    "VMEM anchor valid:",
    VMEM_ANCHOR_EXISTS
)


if not VMEM_ANCHOR_EXISTS:

    raise RuntimeError(
        "Selected VMEM anchor does not lie on existing VMEM."
    )


# ================================================================
# 13. NEW VIA LANDING POINTS
#
# Gate/drain terminals escape horizontally RIGHT to remote
# M1<->M2 via sites.
# ================================================================

VIA_POINTS = {

    # Shared X column for ST1 PMOS/NMOS input gates.
    "MP_ST1_GATE":
        (
            17.000,
            TARGET_POINTS[
                "MP_ST1_GATE"
            ][1],
        ),

    "MN_ST1_GATE":
        (
            17.000,
            TARGET_POINTS[
                "MN_ST1_GATE"
            ][1],
        ),


    # Shared X column for ST2 PMOS/NMOS input gates.
    "MP_ST2_GATE":
        (
            21.000,
            TARGET_POINTS[
                "MP_ST2_GATE"
            ][1],
        ),

    "MN_ST2_GATE":
        (
            21.000,
            TARGET_POINTS[
                "MN_ST2_GATE"
            ][1],
        ),


    # Leak and reset drain escapes.
    "MN_LEAK_DRAIN":
        (
            34.200,
            TARGET_POINTS[
                "MN_LEAK_DRAIN"
            ][1],
        ),

    "MN_RST_DRAIN":
        (
            37.300,
            TARGET_POINTS[
                "MN_RST_DRAIN"
            ][1],
        ),

}


print()
print("=" * 80)
print("VMEM VIA LANDING POINTS")
print("=" * 80)


for name, point in VIA_POINTS.items():

    print(
        f"{name:18s}:",
        tuple(
            round(
                value,
                3
            )

            for value
            in point
        )
    )


# ================================================================
# 14. ROUTE DIMENSIONS
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


VMEM_EXTERNAL_X = (
    38.000
)

VMEM_EXTERNAL_POINT = (
    VMEM_EXTERNAL_X,
    VMEM_Y,
)


# ================================================================
# 15. CREATE OUTPUT WRAPPER
# ================================================================

if layout.cell(
    OUTPUT_TOP_NAME
) is not None:

    raise RuntimeError(
        f"Output cell exists: {OUTPUT_TOP_NAME}"
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
# 16. LOCAL M1 ESCAPES
# ================================================================

m1_shapes = {}


for name, target in TARGET_POINTS.items():

    via_point = VIA_POINTS[
        name
    ]


    m1_shapes[
        f"{name}_STUB"
    ] = horizontal_box(

        target[0],

        via_point[0],

        target[1],

        M1_STUB_WIDTH,

    )


    m1_shapes[
        f"{name}_PATCH"
    ] = centered_box(

        via_point[0],

        via_point[1],

        M1_PATCH_SIZE,

    )


for name, box in m1_shapes.items():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


# ================================================================
# 17. VIA1 + M2 LANDING PATCHES
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
# 18. M2 VMEM DISTRIBUTION
#
# Main trunk remains at y=1.0 and extends to an external-access
# endpoint at x=38.0.
#
# Four vertical VMEM branches:
#
#   x=17.0 -> ST1 PMOS + NMOS gates
#   x=21.0 -> ST2 PMOS + NMOS gates
#   x=34.2 -> leak drain
#   x=37.3 -> reset drain
# ================================================================

m2_route_shapes = {


    "VMEM_MAIN_TRUNK":

        horizontal_box(

            VMEM_ANCHOR[0],

            VMEM_EXTERNAL_X,

            VMEM_Y,

            M2_ROUTE_WIDTH,

        ),


    "VMEM_ST1_VERTICAL":

        vertical_box(

            17.000,

            VMEM_Y,

            VIA_POINTS[
                "MP_ST1_GATE"
            ][1],

            M2_ROUTE_WIDTH,

        ),


    "VMEM_ST2_VERTICAL":

        vertical_box(

            21.000,

            VMEM_Y,

            VIA_POINTS[
                "MP_ST2_GATE"
            ][1],

            M2_ROUTE_WIDTH,

        ),


    "VMEM_LEAK_VERTICAL":

        vertical_box(

            VIA_POINTS[
                "MN_LEAK_DRAIN"
            ][0],

            VMEM_Y,

            VIA_POINTS[
                "MN_LEAK_DRAIN"
            ][1],

            M2_ROUTE_WIDTH,

        ),


    "VMEM_RESET_VERTICAL":

        vertical_box(

            VIA_POINTS[
                "MN_RST_DRAIN"
            ][0],

            VMEM_Y,

            VIA_POINTS[
                "MN_RST_DRAIN"
            ][1],

            M2_ROUTE_WIDTH,

        ),

}


for name, box in m2_route_shapes.items():

    top.shapes(
        M2_LAYER
    ).insert(
        box
    )


# ================================================================
# 19. NEW REGIONS
# ================================================================

NEW_M1 = kdb.Region()


for box in m1_shapes.values():

    NEW_M1.insert(
        box
    )


NEW_M1.merge()


NEW_VIA1 = kdb.Region()


for box in via1_shapes.values():

    NEW_VIA1.insert(
        box
    )


NEW_VIA1.merge()


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
# 20. M2 CONNECTIVITY
# ================================================================

NEW_M2_COMPONENT_COUNT = len(

    list(
        NEW_M2.each_merged()
    )

)


NEW_M2_SINGLE_COMPONENT = (
    NEW_M2_COMPONENT_COUNT == 1
)


NEW_M2_TOUCHES_EXISTING_VMEM = not (

    NEW_M2

    &

    VMEM_COMPONENT

).is_empty()


FULL_VMEM_M2 = (

    VMEM_COMPONENT
    +
    NEW_M2

).merged()


FULL_VMEM_M2_COMPONENT_COUNT = len(

    list(
        FULL_VMEM_M2.each_merged()
    )

)


VMEM_M2_CONNECTED = (

    FULL_VMEM_M2_COMPONENT_COUNT == 1

)


print()
print("=" * 80)
print("VMEM M2 CONNECTIVITY")
print("=" * 80)

print(
    "New M2 components:",
    NEW_M2_COMPONENT_COUNT
)

print(
    "New M2 single component:",
    NEW_M2_SINGLE_COMPONENT
)

print(
    "Touches existing VMEM:",
    NEW_M2_TOUCHES_EXISTING_VMEM
)

print(
    "Combined VMEM M2 components:",
    FULL_VMEM_M2_COMPONENT_COUNT
)

print(
    "VMEM M2 connected:",
    VMEM_M2_CONNECTED
)


# ================================================================
# 21. CHECK AGAINST OTHER PRE-EXISTING M2 NETS
# ================================================================

OTHER_PRE_M2 = (

    PRE_M2
    -
    VMEM_COMPONENT

)


UNEXPECTED_M2_OVERLAP = (

    NEW_M2
    &
    OTHER_PRE_M2

)


NO_UNEXPECTED_M2_OVERLAP = (
    UNEXPECTED_M2_OVERLAP.is_empty()
)


print()
print("=" * 80)
print("PRE-EXISTING M2 SHORT AUDIT")
print("=" * 80)

print(
    "Unexpected overlap with non-VMEM M2:",
    not NO_UNEXPECTED_M2_OVERLAP
)

print(
    "Only existing VMEM contacted:",
    NO_UNEXPECTED_M2_OVERLAP
)


# ================================================================
# 22. INTENDED M1 LANDING AUDIT
#
# New M1 may overlap pre-existing M1 only at the six intended
# target terminal boxes.
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
    "Only VMEM target terminals contacted:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 23. EVERY TARGET MUST TOUCH ITS NEW M1 STUB
# ================================================================

TARGET_M1_LANDING_OK = True


print()
print("=" * 80)
print("TARGET M1 LANDING AUDIT")
print("=" * 80)


for name, target_box in TARGET_BOXES.items():

    stub = kdb.Region(

        m1_shapes[
            f"{name}_STUB"
        ]

    )


    target_region = kdb.Region(
        target_box
    )


    hit = not (

        stub
        &
        target_region

    ).is_empty()


    TARGET_M1_LANDING_OK &= hit


    print(
        f"{name:18s}:",
        hit
    )


# ================================================================
# 24. VIA ENCLOSURE / CONNECTIVITY AUDIT
#
# Each via must lie inside both its M1 patch and M2 patch.
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


    m1_patch_region = kdb.Region(

        m1_shapes[
            f"{name}_PATCH"
        ]

    )


    m2_patch_region = kdb.Region(

        m2_patch_shapes[
            name
        ]

    )


    via_inside_m1 = (

        (
            via_region
            -
            m1_patch_region
        ).is_empty()

    )


    via_inside_m2 = (

        (
            via_region
            -
            m2_patch_region
        ).is_empty()

    )


    m1_stub_touch = not (

        m1_patch_region

        &

        kdb.Region(
            m1_shapes[
                f"{name}_STUB"
            ]
        )

    ).is_empty()


    m2_route_touch = not (

        m2_patch_region
        &
        NEW_M2

    ).is_empty()


    valid = bool(

        via_inside_m1

        and

        via_inside_m2

        and

        m1_stub_touch

        and

        m2_route_touch

    )


    VIA_LANDING_OK &= valid


    print(
        f"{name:18s}: "
        f"M1={via_inside_m1} "
        f"M2={via_inside_m2} "
        f"stub={m1_stub_touch} "
        f"route={m2_route_touch} "
        f"valid={valid}"
    )


# ================================================================
# 25. EXTERNAL VMEM ACCESS
# ================================================================

EXTERNAL_VMEM_ACCESS_OK = not (

    NEW_M2

    &

    probe_region(
        VMEM_EXTERNAL_POINT[0],
        VMEM_EXTERNAL_POINT[1],
    )

).is_empty()


print()
print("=" * 80)
print("EXTERNAL VMEM ACCESS")
print("=" * 80)

print(
    "VMEM external point:",
    VMEM_EXTERNAL_POINT
)

print(
    "Accessible on M2:",
    EXTERNAL_VMEM_ACCESS_OK
)

print(
    "Physical Cmem added:",
    False
)

print(
    "Cmem policy:",
    "EXTERNAL / IDEAL 5 pF"
)


# ================================================================
# 26. NEW SHAPE COUNTS
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
    12
)

EXPECTED_VIA1_COUNT = (
    6
)

EXPECTED_M2_COUNT = (
    11
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
# 27. POPULATED LAYERS FOR SERIALIZATION
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
# 28. WRITE
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
# 29. READBACK
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


READBACK_M1_COUNT = sum(

    1

    for _
    in verify_top.shapes(
        verify_m1
    ).each()

)


READBACK_VIA1_COUNT = sum(

    1

    for _
    in verify_top.shapes(
        verify_via1
    ).each()

)


READBACK_M2_COUNT = sum(

    1

    for _
    in verify_top.shapes(
        verify_m2
    ).each()

)


READBACK_COUNTS_OK = bool(

    READBACK_M1_COUNT
    ==
    EXPECTED_M1_COUNT

    and

    READBACK_VIA1_COUNT
    ==
    EXPECTED_VIA1_COUNT

    and

    READBACK_M2_COUNT
    ==
    EXPECTED_M2_COUNT

)


# ================================================================
# 30. INPUT INTEGRITY
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
# 31. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "32A",

    "routing_stage":
        "3_of_9_VMEM",

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
        "VMEM",

    "targets": {

        name:
            list(
                point
            )

        for name, point
        in TARGET_POINTS.items()

    },

    "existing_vmem_anchor_um":
        list(
            VMEM_ANCHOR
        ),

    "external_vmem_access_um":
        list(
            VMEM_EXTERNAL_POINT
        ),

    "cmem": {

        "implemented_physically":
            False,

        "value_pf":
            5.0,

        "policy":
            "external_ideal",

    },

    "routing": {

        "m1_layer":
            "68/20",

        "via1_layer":
            "68/44",

        "m2_layer":
            "69/20",

        "m1_stub_width_um":
            M1_STUB_WIDTH,

        "m1_patch_um":
            M1_PATCH_SIZE,

        "via1_um":
            VIA1_SIZE,

        "m2_patch_um":
            M2_PATCH_SIZE,

        "m2_width_um":
            M2_ROUTE_WIDTH,

    },

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "existing_vmem_identified":
            VMEM_ANCHOR_EXISTS,

        "new_m2_single_component":
            NEW_M2_SINGLE_COMPONENT,

        "new_m2_touches_existing_vmem":
            NEW_M2_TOUCHES_EXISTING_VMEM,

        "combined_vmem_m2_connected":
            VMEM_M2_CONNECTED,

        "no_other_m2_overlap":
            NO_UNEXPECTED_M2_OVERLAP,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "target_m1_landings":
            TARGET_M1_LANDING_OK,

        "via_landings":
            VIA_LANDING_OK,

        "external_vmem_access":
            EXTERNAL_VMEM_ACCESS_OK,

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
# 32. FINAL GATE
# ================================================================

STEP32A_PASS = bool(

    REFERENCE_OK

    and

    VMEM_ANCHOR_EXISTS

    and

    NEW_M2_SINGLE_COMPONENT

    and

    NEW_M2_TOUCHES_EXISTING_VMEM

    and

    VMEM_M2_CONNECTED

    and

    NO_UNEXPECTED_M2_OVERLAP

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    TARGET_M1_LANDING_OK

    and

    VIA_LANDING_OK

    and

    EXTERNAL_VMEM_ACCESS_OK

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
print("STEP 32A RESULT")
print("=" * 80)

print(
    "Reference VMEM topology     :",
    REFERENCE_OK
)

print(
    "Existing VMEM identified    :",
    VMEM_ANCHOR_EXISTS
)

print(
    "New VMEM M2 connected       :",
    NEW_M2_SINGLE_COMPONENT
)

print(
    "Touches existing VMEM       :",
    NEW_M2_TOUCHES_EXISTING_VMEM
)

print(
    "Combined VMEM connected     :",
    VMEM_M2_CONNECTED
)

print(
    "No unexpected M2 overlap    :",
    NO_UNEXPECTED_M2_OVERLAP
)

print(
    "No unexpected M1 overlap    :",
    NO_UNEXPECTED_M1_OVERLAP
)

print(
    "Target M1 landings valid    :",
    TARGET_M1_LANDING_OK
)

print(
    "All VIA1 landings valid     :",
    VIA_LANDING_OK
)

print(
    "External VMEM accessible    :",
    EXTERNAL_VMEM_ACCESS_OK
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
    "Stage-2 source unchanged    :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP32A_PASS =",
    STEP32A_PASS
)


if not STEP32A_PASS:

    raise RuntimeError(
        "STEP 32A VMEM construction failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 3/9 — VMEM CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "VMEM connected to:"
)

print(
    "  existing weighted-synapse VMEM"
)

print(
    "  MP_ST1 gate"
)

print(
    "  MP_ST2 gate"
)

print(
    "  MN_ST1 gate"
)

print(
    "  MN_ST2 gate"
)

print(
    "  MN_LEAK drain"
)

print(
    "  MN_RST drain"
)

print(
    "  external VMEM M2 endpoint"
)

print()
print(
    "Cmem:"
)

print(
    "  external / ideal 5 pF"
)

print(
    "  no physical capacitor introduced"
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
    "  Official SKY130 DRC on VMEM V1."
)