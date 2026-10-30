# ================================================================
# NeuroLIF-SKY130
# STEP 30C — Corrected full-neuron VDD routing V2
#
# REPLACES FAILED V1.
#
# Root cause of V1:
#   Vertical VDD branches launched directly from P_LOGIC source
#   center and clipped the upper gate-contact M1 of:
#
#       MP_ST1
#       MP_BUF
#
# Correction:
#   Source -> 0.600 um LEFT M1 escape -> vertical VDD branch.
#
# Built FROM:
#   neurolif_full_neuron_placement_v1.gds
#
# NOT from:
#   neurolif_full_neuron_vdd_v1.gds
#
# No other routing is introduced.
# ================================================================

from pathlib import Path
import json
import hashlib

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 30C: CORRECTED VDD ROUTING V2")
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

SYNAPSE_DIR = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
)


INPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_placement_v1.gds"
)

OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v2.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v2.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v2.json"
)

PLACEMENT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_placement_v1.json"
)

SYNAPSE_FINAL_RECORD = (
    SYNAPSE_DIR
    / "neurolif_synapse_final_verification_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_PLACEMENT_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VDD_V2"
)


for path in [
    INPUT_GDS,
    PLACEMENT_MANIFEST,
    SYNAPSE_FINAL_RECORD,
]:

    if not path.exists():
        raise FileNotFoundError(path)


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

            digest.update(chunk)

    return digest.hexdigest()


INPUT_HASH_BEFORE = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. DEPENDENCY AUDIT
# ================================================================

placement_manifest = json.loads(

    PLACEMENT_MANIFEST.read_text(
        encoding="utf-8"
    )

)

synapse_record = json.loads(

    SYNAPSE_FINAL_RECORD.read_text(
        encoding="utf-8"
    )

)


PLACEMENT_VALID = bool(

    placement_manifest[
        "checks"
    ][
        "instance_collision_free"
    ]

    and

    placement_manifest[
        "checks"
    ][
        "closed_synapse_source_unchanged"
    ]

)


SYNAPSE_CLOSED = bool(

    synapse_record.get(
        "STEP28C_PASS",
        False
    )

    and

    synapse_record.get(
        "final_status"
    ) == "CLOSED"

)


print()
print("=" * 80)
print("DEPENDENCY STATUS")
print("=" * 80)

print(
    "Placement valid       :",
    PLACEMENT_VALID
)

print(
    "Weighted synapse closed:",
    SYNAPSE_CLOSED
)


if not PLACEMENT_VALID:
    raise RuntimeError(
        "Placement dependency invalid."
    )

if not SYNAPSE_CLOSED:
    raise RuntimeError(
        "Synapse dependency invalid."
    )


# ================================================================
# 4. LOAD PLACEMENT
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)


DBU = layout.dbu


placement_top = layout.cell(
    INPUT_TOP_NAME
)


if placement_top is None:

    raise RuntimeError(
        f"Missing top: {INPUT_TOP_NAME}"
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
# 5. CELLS / LAYERS
# ================================================================

P_LOGIC_NAME = (
    "P_LOGIC_W2000_L0150"
)

P_FB_NAME = (
    "P_FB_W0420_L0300"
)

N_TAP_NAME = (
    "N_TAP_VDD_W1000_H1000"
)


p_logic = layout.cell(
    P_LOGIC_NAME
)

p_fb = layout.cell(
    P_FB_NAME
)

n_tap = layout.cell(
    N_TAP_NAME
)


for name, cell in [
    (P_LOGIC_NAME, p_logic),
    (P_FB_NAME, p_fb),
    (N_TAP_NAME, n_tap),
]:

    if cell is None:
        raise RuntimeError(
            f"Missing cell: {name}"
        )


M1_LAYER = layout.find_layer(
    68,
    20
)


if M1_LAYER is None:
    raise RuntimeError(
        "MET1 68/20 missing."
    )


# ================================================================
# 6. HELPERS
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


def translated_center(
    box,
    origin,
):

    x, y = center_um(box)

    return (
        x + origin[0],
        y + origin[1],
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


def probe_region(
    x,
    y,
    half=0.010,
):

    return kdb.Region(

        kdb.Box(

            to_dbu(x - half),
            to_dbu(y - half),

            to_dbu(x + half),
            to_dbu(y + half),

        )

    )


# ================================================================
# 7. EXTRACT MOS TERMINAL M1 BOXES
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

            f"{cell.name}: "
            f"expected at least 4 terminal M1 shapes, "
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
        key=cx
    )

    right_sd = max(
        boxes,
        key=cx
    )


    remaining = [

        box

        for box in boxes

        if (
            box != left_sd
            and
            box != right_sd
        )

    ]


    bottom_gate = min(
        remaining,
        key=cy
    )

    top_gate = max(
        remaining,
        key=cy
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


print()
print("=" * 80)
print("P_LOGIC TERMINAL GEOMETRY")
print("=" * 80)


for name, box in P_LOGIC_TERMS.items():

    print(
        name,
        "bbox_um=(",
        round(to_um(box.left), 3),
        round(to_um(box.bottom), 3),
        round(to_um(box.right), 3),
        round(to_um(box.top), 3),
        ")",
        "center=",
        tuple(
            round(v, 3)
            for v in center_um(box)
        )
    )


# ================================================================
# 8. FROZEN PLACEMENT ORIGINS
# ================================================================

ORIGINS = {

    "N_TAP_LOGIC":
        (12.5, 14.0),

    "MP_ST1":
        (16.0, 14.0),

    "MP_ST2":
        (20.0, 14.0),

    "MP_FB":
        (24.0, 14.0),

    "MP_BUF":
        (28.0, 14.0),

}


# ================================================================
# 9. TARGET TERMINALS
# ================================================================

MP_ST1_SOURCE_BOX = translate_box(

    P_LOGIC_TERMS[
        "LEFT_SD"
    ],

    ORIGINS[
        "MP_ST1"
    ],

)


MP_BUF_SOURCE_BOX = translate_box(

    P_LOGIC_TERMS[
        "LEFT_SD"
    ],

    ORIGINS[
        "MP_BUF"
    ],

)


MP_ST1_SOURCE = center_um(
    MP_ST1_SOURCE_BOX
)

MP_BUF_SOURCE = center_um(
    MP_BUF_SOURCE_BOX
)


# N-tap M1.
n_tap_m1 = kdb.Region(

    n_tap.shapes(
        M1_LAYER
    )

).merged()


if n_tap_m1.is_empty():

    raise RuntimeError(
        "N-tap M1 missing."
    )


N_TAP_BOX = translate_box(

    n_tap_m1.bbox(),

    ORIGINS[
        "N_TAP_LOGIC"
    ],

)


N_TAP_CENTER = center_um(
    N_TAP_BOX
)


SYNAPSE_VDD_ANCHOR = (
    8.50,
    10.00,
)


# ================================================================
# 10. V2 ESCAPE GEOMETRY
# ================================================================

SOURCE_ESCAPE = (
    0.600
)


MP_ST1_ESCAPE = (

    MP_ST1_SOURCE[0]
    -
    SOURCE_ESCAPE,

    MP_ST1_SOURCE[1],

)


MP_BUF_ESCAPE = (

    MP_BUF_SOURCE[0]
    -
    SOURCE_ESCAPE,

    MP_BUF_SOURCE[1],

)


print()
print("=" * 80)
print("CORRECTED SOURCE ESCAPES")
print("=" * 80)

print(
    "MP_ST1 source:",
    MP_ST1_SOURCE
)

print(
    "MP_ST1 escape:",
    MP_ST1_ESCAPE
)

print()

print(
    "MP_BUF source:",
    MP_BUF_SOURCE
)

print(
    "MP_BUF escape:",
    MP_BUF_ESCAPE
)


# ================================================================
# 11. RAIL Y
# ================================================================

pmos_entries = [

    (
        p_logic,
        ORIGINS[
            "MP_ST1"
        ]
    ),

    (
        p_logic,
        ORIGINS[
            "MP_ST2"
        ]
    ),

    (
        p_fb,
        ORIGINS[
            "MP_FB"
        ]
    ),

    (
        p_logic,
        ORIGINS[
            "MP_BUF"
        ]
    ),

]


pmos_tops = []


for cell, origin in pmos_entries:

    abs_bbox = translate_box(

        cell.bbox(),

        origin,

    )

    pmos_tops.append(
        to_um(
            abs_bbox.top
        )
    )


PMOS_MAX_TOP = max(
    pmos_tops
)


VDD_RAIL_Y = round(

    PMOS_MAX_TOP
    + 1.500,

    3,

)


RAIL_LEFT_X = (
    SYNAPSE_VDD_ANCHOR[0]
)

RAIL_RIGHT_X = round(

    MP_BUF_SOURCE[0]
    + 0.800,

    3,

)


# ================================================================
# 12. WIDTHS
# ================================================================

SOURCE_WIDTH = (
    0.230
)

RAIL_WIDTH = (
    0.400
)

TAP_WIDTH = (
    0.400
)

BRIDGE_WIDTH = (
    0.400
)


# ================================================================
# 13. CREATE V2 TOP
# ================================================================

if layout.cell(
    OUTPUT_TOP_NAME
) is not None:

    raise RuntimeError(
        f"Existing cell: {OUTPUT_TOP_NAME}"
    )


top = layout.create_cell(
    OUTPUT_TOP_NAME
)


top.insert(

    kdb.CellInstArray(

        placement_top.cell_index(),

        kdb.Trans(
            0,
            0
        ),

    )

)


# ================================================================
# 14. CREATE VDD V2 ROUTES
# ================================================================

route_boxes = {}


route_boxes[
    "VDD_RAIL"
] = horizontal_box(

    RAIL_LEFT_X,
    RAIL_RIGHT_X,

    VDD_RAIL_Y,

    RAIL_WIDTH,

)


route_boxes[
    "SYNAPSE_VDD_BRIDGE"
] = vertical_box(

    SYNAPSE_VDD_ANCHOR[0],

    SYNAPSE_VDD_ANCHOR[1],

    VDD_RAIL_Y,

    BRIDGE_WIDTH,

)


route_boxes[
    "N_TAP_VDD_BRANCH"
] = vertical_box(

    N_TAP_CENTER[0],

    N_TAP_CENTER[1],

    VDD_RAIL_Y,

    TAP_WIDTH,

)


# ------------------------------------------------
# Corrected ST1 source:
# source -> LEFT escape -> vertical.
# ------------------------------------------------

route_boxes[
    "MP_ST1_SOURCE_STUB"
] = horizontal_box(

    MP_ST1_ESCAPE[0],

    MP_ST1_SOURCE[0],

    MP_ST1_SOURCE[1],

    SOURCE_WIDTH,

)


route_boxes[
    "MP_ST1_VDD_VERTICAL"
] = vertical_box(

    MP_ST1_ESCAPE[0],

    MP_ST1_ESCAPE[1],

    VDD_RAIL_Y,

    SOURCE_WIDTH,

)


# ------------------------------------------------
# Corrected BUF source:
# source -> LEFT escape -> vertical.
# ------------------------------------------------

route_boxes[
    "MP_BUF_SOURCE_STUB"
] = horizontal_box(

    MP_BUF_ESCAPE[0],

    MP_BUF_SOURCE[0],

    MP_BUF_SOURCE[1],

    SOURCE_WIDTH,

)


route_boxes[
    "MP_BUF_VDD_VERTICAL"
] = vertical_box(

    MP_BUF_ESCAPE[0],

    MP_BUF_ESCAPE[1],

    VDD_RAIL_Y,

    SOURCE_WIDTH,

)


for name, box in route_boxes.items():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


print()
print("=" * 80)
print("VDD V2 ROUTE SHAPES")
print("=" * 80)


for name, box in route_boxes.items():

    print(
        f"{name:26s}",
        "(",
        round(to_um(box.left), 3),
        round(to_um(box.bottom), 3),
        round(to_um(box.right), 3),
        round(to_um(box.top), 3),
        ")"
    )


# ================================================================
# 15. NEW ROUTE REGION
# ================================================================

NEW_VDD = kdb.Region()


for box in route_boxes.values():

    NEW_VDD.insert(
        box
    )


NEW_VDD.merge()


NEW_COMPONENT_COUNT = len(

    list(
        NEW_VDD.each_merged()
    )

)


NEW_ROUTE_CONNECTED = (
    NEW_COMPONENT_COUNT == 1
)


print()
print("=" * 80)
print("NEW VDD CONNECTIVITY")
print("=" * 80)

print(
    "Merged components:",
    NEW_COMPONENT_COUNT
)

print(
    "Single component:",
    NEW_ROUTE_CONNECTED
)


# ================================================================
# 16. PRE-EXISTING M1 + VDD
# ================================================================

PRE_M1 = kdb.Region(

    placement_top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


FULL_M1 = (

    PRE_M1
    +
    NEW_VDD

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
        y
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

            hits.append(index)


    if len(hits) != 1:
        return None

    return hits[0]


# ================================================================
# 17. VDD TARGET ROOT AUDIT
# ================================================================

VDD_TARGETS = {

    "SYNAPSE_VDD":
        SYNAPSE_VDD_ANCHOR,

    "N_TAP_LOGIC":
        N_TAP_CENTER,

    "MP_ST1_SOURCE":
        MP_ST1_SOURCE,

    "MP_BUF_SOURCE":
        MP_BUF_SOURCE,

}


roots = {

    name:
        root_at_point(
            point[0],
            point[1]
        )

    for name, point
    in VDD_TARGETS.items()

}


print()
print("=" * 80)
print("VDD ROOT AUDIT")
print("=" * 80)


for name, root in roots.items():

    print(
        f"{name:18s}:",
        root
    )


root_set = set(
    roots.values()
)


VDD_CONNECTED = bool(

    None not in root_set

    and

    len(root_set) == 1

)


VDD_ROOT = (

    next(iter(root_set))

    if VDD_CONNECTED

    else None

)


print(
    "All intended VDD terminals same root:",
    VDD_CONNECTED
)


# ================================================================
# 18. BUILD FULL PROTECTED TERMINAL BOX LIST
#
# Unlike V1, audit ENTIRE terminal boxes, not just their centers.
# ================================================================

def abs_terminal_box(
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


protected_boxes = {

    # ST1
    "MP_ST1_DRAIN":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "RIGHT_SD",
            "MP_ST1"
        ),

    "MP_ST1_GATE_B":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MP_ST1"
        ),

    "MP_ST1_GATE_T":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "TOP_GATE",
            "MP_ST1"
        ),


    # ST2: nothing routed to VDD.
    "MP_ST2_LEFT_SD":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "LEFT_SD",
            "MP_ST2"
        ),

    "MP_ST2_RIGHT_SD":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "RIGHT_SD",
            "MP_ST2"
        ),

    "MP_ST2_GATE_B":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MP_ST2"
        ),

    "MP_ST2_GATE_T":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "TOP_GATE",
            "MP_ST2"
        ),


    # Feedback PFET: nothing routed to VDD at diffusion/gate.
    "MP_FB_LEFT_SD":
        abs_terminal_box(
            P_FB_TERMS,
            "LEFT_SD",
            "MP_FB"
        ),

    "MP_FB_RIGHT_SD":
        abs_terminal_box(
            P_FB_TERMS,
            "RIGHT_SD",
            "MP_FB"
        ),

    "MP_FB_GATE_B":
        abs_terminal_box(
            P_FB_TERMS,
            "BOTTOM_GATE",
            "MP_FB"
        ),

    "MP_FB_GATE_T":
        abs_terminal_box(
            P_FB_TERMS,
            "TOP_GATE",
            "MP_FB"
        ),


    # BUF
    "MP_BUF_DRAIN":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "RIGHT_SD",
            "MP_BUF"
        ),

    "MP_BUF_GATE_B":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "BOTTOM_GATE",
            "MP_BUF"
        ),

    "MP_BUF_GATE_T":
        abs_terminal_box(
            P_LOGIC_TERMS,
            "TOP_GATE",
            "MP_BUF"
        ),

}


# ================================================================
# 19. FULL-BOX DIRECT INTERSECTION AUDIT
# ================================================================

DIRECT_PROTECTED_CLEAR = True


print()
print("=" * 80)
print("FULL TERMINAL-BOX / VDD OVERLAP AUDIT")
print("=" * 80)


for name, box in protected_boxes.items():

    overlap = not (

        NEW_VDD
        &
        kdb.Region(
            box
        )

    ).is_empty()


    clear = (
        not overlap
    )


    DIRECT_PROTECTED_CLEAR &= clear


    print(
        f"{name:18s}: "
        f"overlap={overlap} "
        f"clear={clear}"
    )


# ================================================================
# 20. ELECTRICAL ROOT AUDIT OF PROTECTED TERMINALS
# ================================================================

PROTECTED_ROOTS_CLEAR = True


print()
print("=" * 80)
print("PROTECTED TERMINAL ROOT AUDIT")
print("=" * 80)


for name, box in protected_boxes.items():

    point = center_um(
        box
    )


    root = root_at_point(
        point[0],
        point[1]
    )


    shorted = bool(

        VDD_CONNECTED

        and

        root == VDD_ROOT

    )


    clear = (
        not shorted
    )


    PROTECTED_ROOTS_CLEAR &= clear


    print(
        f"{name:18s} "
        f"root={root} "
        f"clear_of_VDD={clear}"
    )


# ================================================================
# 21. SOURCE ESCAPE CLEARANCE TO UPPER GATES
#
# Direct numeric diagnostic.
# ================================================================

ST1_TOP_GATE_BOX = protected_boxes[
    "MP_ST1_GATE_T"
]

BUF_TOP_GATE_BOX = protected_boxes[
    "MP_BUF_GATE_T"
]


ST1_VERTICAL = route_boxes[
    "MP_ST1_VDD_VERTICAL"
]

BUF_VERTICAL = route_boxes[
    "MP_BUF_VDD_VERTICAL"
]


def horizontal_gap_um(
    box_a,
    box_b,
):

    if box_a.right < box_b.left:

        return to_um(
            box_b.left
            -
            box_a.right
        )

    if box_b.right < box_a.left:

        return to_um(
            box_a.left
            -
            box_b.right
        )

    return 0.0


ST1_GATE_GAP = horizontal_gap_um(

    ST1_VERTICAL,

    ST1_TOP_GATE_BOX,

)


BUF_GATE_GAP = horizontal_gap_um(

    BUF_VERTICAL,

    BUF_TOP_GATE_BOX,

)


MIN_REQUIRED_DIAGNOSTIC_GAP = (
    0.140
)


ESCAPE_CLEARANCE_OK = bool(

    ST1_GATE_GAP
    >= MIN_REQUIRED_DIAGNOSTIC_GAP

    and

    BUF_GATE_GAP
    >= MIN_REQUIRED_DIAGNOSTIC_GAP

)


print()
print("=" * 80)
print("SOURCE-ESCAPE / UPPER-GATE CLEARANCE")
print("=" * 80)

print(
    "MP_ST1 vertical-to-gate gap:",
    round(
        ST1_GATE_GAP,
        3
    ),
    "um"
)

print(
    "MP_BUF vertical-to-gate gap:",
    round(
        BUF_GATE_GAP,
        3
    ),
    "um"
)

print(
    "Diagnostic minimum:",
    MIN_REQUIRED_DIAGNOSTIC_GAP,
    "um"
)

print(
    "Escape clearance OK:",
    ESCAPE_CLEARANCE_OK
)


# ================================================================
# 22. TOP-LEVEL ROUTE COUNT
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        M1_LAYER
    ).each()

)


EXPECTED_TOP_M1 = (
    7
)


TOP_M1_COUNT_OK = (
    TOP_M1_COUNT
    ==
    EXPECTED_TOP_M1
)


print()
print("=" * 80)
print("ROUTE COUNT")
print("=" * 80)

print(
    "Top-level M1 shapes:",
    TOP_M1_COUNT
)

print(
    "Expected:",
    EXPECTED_TOP_M1
)

print(
    "Count correct:",
    TOP_M1_COUNT_OK
)


# ================================================================
# 23. POPULATED LAYERS
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


# ================================================================
# 24. SAVE OPTIONS
# ================================================================

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
# 25. WRITE
# ================================================================

OUTPUT_GDS.unlink(
    missing_ok=True
)

OUTPUT_OAS.unlink(
    missing_ok=True
)


layout.write(

    str(OUTPUT_GDS),

    save_options(
        "GDS2"
    ),

)


layout.write(

    str(OUTPUT_OAS),

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
# 26. READBACK
# ================================================================

verify = kdb.Layout()

verify.read(
    str(OUTPUT_GDS)
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


READBACK_ROUTE_COUNT = 0


if (
    verify_top is not None
    and
    verify_m1 is not None
):

    READBACK_ROUTE_COUNT = sum(

        1

        for _
        in verify_top.shapes(
            verify_m1
        ).each()

    )


READBACK_COUNT_OK = (
    READBACK_ROUTE_COUNT
    ==
    EXPECTED_TOP_M1
)


# ================================================================
# 27. INPUT INTEGRITY
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
# 28. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "30C",

    "routing_stage":
        "1_of_9_VDD_corrected_v2",

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

    "rejected_predecessor":

        str(
            NEURON_DIR
            / "neurolif_full_neuron_vdd_v1.gds"
        ),

    "v1_failure":

        "MP_ST1 and MP_BUF vertical source branches "
        "clipped upper gate-contact M1.",

    "correction": {

        "source_escape_um":
            SOURCE_ESCAPE,

        "direction":
            "LEFT",

        "mp_st1_escape":
            list(MP_ST1_ESCAPE),

        "mp_buf_escape":
            list(MP_BUF_ESCAPE),

        "st1_gate_gap_um":
            ST1_GATE_GAP,

        "buf_gate_gap_um":
            BUF_GATE_GAP,

    },

    "checks": {

        "placement_valid":
            PLACEMENT_VALID,

        "synapse_closed":
            SYNAPSE_CLOSED,

        "new_route_connected":
            NEW_ROUTE_CONNECTED,

        "vdd_targets_connected":
            VDD_CONNECTED,

        "full_terminal_box_clearance":
            DIRECT_PROTECTED_CLEAR,

        "protected_roots_clear":
            PROTECTED_ROOTS_CLEAR,

        "escape_clearance":
            ESCAPE_CLEARANCE_OK,

        "top_m1_count":
            TOP_M1_COUNT_OK,

        "gds":
            GDS_OK,

        "oas":
            OAS_OK,

        "readback":
            READBACK_OK,

        "readback_route_count":
            READBACK_COUNT_OK,

        "input_unchanged":
            INPUT_UNCHANGED,

    },

}


OUTPUT_MANIFEST.write_text(

    json.dumps(
        manifest,
        indent=2
    ),

    encoding="utf-8",

)


MANIFEST_OK = bool(

    OUTPUT_MANIFEST.exists()

    and

    OUTPUT_MANIFEST.stat().st_size > 0

)


# ================================================================
# 29. FINAL GATE
# ================================================================

STEP30C_PASS = bool(

    PLACEMENT_VALID

    and

    SYNAPSE_CLOSED

    and

    NEW_ROUTE_CONNECTED

    and

    VDD_CONNECTED

    and

    DIRECT_PROTECTED_CLEAR

    and

    PROTECTED_ROOTS_CLEAR

    and

    ESCAPE_CLEARANCE_OK

    and

    TOP_M1_COUNT_OK

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
print("STEP 30C RESULT")
print("=" * 80)

print(
    "Placement dependency        :",
    PLACEMENT_VALID
)

print(
    "Closed synapse dependency   :",
    SYNAPSE_CLOSED
)

print(
    "New VDD route connected     :",
    NEW_ROUTE_CONNECTED
)

print(
    "All VDD targets same root   :",
    VDD_CONNECTED
)

print(
    "Full protected boxes clear  :",
    DIRECT_PROTECTED_CLEAR
)

print(
    "Protected roots clear       :",
    PROTECTED_ROOTS_CLEAR
)

print(
    "Escape clearance valid      :",
    ESCAPE_CLEARANCE_OK
)

print(
    "Top-level route count       :",
    TOP_M1_COUNT_OK
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
    "Placement source unchanged  :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP30C_PASS =",
    STEP30C_PASS
)


if not STEP30C_PASS:

    raise RuntimeError(
        "STEP 30C corrected VDD routing failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 1/9 — CORRECTED VDD V2 CONSTRUCTION PASS")
print("=" * 80)

print()
print(
    "VDD V1       : REJECTED"
)

print(
    "VDD V2       : CONSTRUCTION PASS"
)

print(
    "Source escape:",
    SOURCE_ESCAPE,
    "um LEFT"
)

print(
    "MP_ST1 gate gap:",
    round(ST1_GATE_GAP, 3),
    "um"
)

print(
    "MP_BUF gate gap:",
    round(BUF_GATE_GAP, 3),
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
    "Official SKY130 DRC on VDD V2."
)