# ================================================================
# NeuroLIF-SKY130
# STEP 20A — Weighted-synapse VDD routing V1
#
# Adds ONLY:
#   - PMOS sources -> VDD
#   - N_TAP_VDD -> VDD
#   - one common VDD Metal1 rail
#
# Does NOT route:
#   VBIAS
#   PMOS drains
#   switch gates
#   VMEM
#   VSS
#
# The Step 19 placement cell is preserved as a child cell.
# ================================================================

from pathlib import Path
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 20A: VDD ROUTING V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_placement_v1.gds"
)

PLACEMENT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_placement_v1.json"
)

OUTPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vdd_v1.gds"
)

OUTPUT_OAS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vdd_v1.oas"
)

OUTPUT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vdd_v1.json"
)


PLACEMENT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_PLACEMENT_V1"
)

NEW_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VDD_V1"
)

P_SYN_NAME = (
    "P_SYN_W0840_L0500"
)

N_TAP_NAME = (
    "N_TAP_VDD_W1000_H1000"
)


print()
print("Input GDS :", INPUT_GDS)
print("Manifest  :", PLACEMENT_MANIFEST)
print("Output GDS:", OUTPUT_GDS)


if not INPUT_GDS.exists():
    raise FileNotFoundError(INPUT_GDS)

if not PLACEMENT_MANIFEST.exists():
    raise FileNotFoundError(
        PLACEMENT_MANIFEST
    )


# ================================================================
# 2. LOAD PLACEMENT LIBRARY
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)

DBU = layout.dbu


placement_top = layout.cell(
    PLACEMENT_TOP_NAME
)

p_syn = layout.cell(
    P_SYN_NAME
)

n_tap = layout.cell(
    N_TAP_NAME
)


if placement_top is None:
    raise RuntimeError(
        f"Missing cell: {PLACEMENT_TOP_NAME}"
    )

if p_syn is None:
    raise RuntimeError(
        f"Missing cell: {P_SYN_NAME}"
    )

if n_tap is None:
    raise RuntimeError(
        f"Missing cell: {N_TAP_NAME}"
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
    "Placement top found:",
    True
)


# ================================================================
# 3. LOAD PLACEMENT MANIFEST
# ================================================================

manifest = json.loads(
    PLACEMENT_MANIFEST.read_text(
        encoding="utf-8"
    )
)


placements = manifest[
    "placement_um"
]


PMOS_ROLES = [
    "P_U1A",
    "P_REF",
    "P_U0",
    "P_U1B",
]


# ================================================================
# 4. LAYERS
# ================================================================

DIFF_LAYER = layout.find_layer(
    65,
    20
)

MET1_LAYER = layout.find_layer(
    68,
    20
)


if DIFF_LAYER is None:
    raise RuntimeError(
        "DIFF layer 65/20 missing."
    )

if MET1_LAYER is None:
    raise RuntimeError(
        "MET1 layer 68/20 missing."
    )


# ================================================================
# 5. HELPERS
# ================================================================

def to_dbu(value_um):

    return int(
        round(
            value_um
            / DBU
        )
    )


def box_um(box):

    return (

        box.left * DBU,
        box.bottom * DBU,
        box.right * DBU,
        box.top * DBU,

    )


def center(box):

    return (

        (
            box.left
            + box.right
        ) / 2.0,

        (
            box.bottom
            + box.top
        ) / 2.0,

    )


def overlaps(a, b):

    return not (

        a.right <= b.left
        or
        a.left >= b.right
        or
        a.top <= b.bottom
        or
        a.bottom >= b.top

    )


def translate_box(
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


def make_box_um(
    x1,
    y1,
    x2,
    y2,
):

    return kdb.Box(

        to_dbu(
            min(x1, x2)
        ),

        to_dbu(
            min(y1, y2)
        ),

        to_dbu(
            max(x1, x2)
        ),

        to_dbu(
            max(y1, y2)
        ),

    )


# ================================================================
# 6. DETERMINE P_SYN TERMINALS PROGRAMMATICALLY
#
# M1 overlapping DIFF = source/drain.
# Left diffusion = source/VDD by layout convention for this block.
# Right diffusion remains drain.
#
# Non-diffusion M1 = gate contacts.
# ================================================================

diff_shapes = [
    shape.bbox()
    for shape
    in p_syn.shapes(
        DIFF_LAYER
    ).each()
]

m1_shapes = [
    shape.bbox()
    for shape
    in p_syn.shapes(
        MET1_LAYER
    ).each()
]


if len(diff_shapes) != 1:

    raise RuntimeError(
        "P_SYN expected one DIFF shape."
    )


diff_box = diff_shapes[0]


sd_boxes = [
    box
    for box in m1_shapes
    if overlaps(
        box,
        diff_box
    )
]


gate_boxes = [
    box
    for box in m1_shapes
    if not overlaps(
        box,
        diff_box
    )
]


sd_boxes.sort(
    key=lambda box:
        center(box)[0]
)


if len(sd_boxes) != 2:

    raise RuntimeError(
        "P_SYN expected exactly two "
        "diffusion M1 landings."
    )


if len(gate_boxes) != 2:

    raise RuntimeError(
        "P_SYN expected exactly two "
        "gate M1 landings."
    )


SOURCE_LOCAL = sd_boxes[0]
DRAIN_LOCAL = sd_boxes[1]


print()
print("=" * 80)
print("P_SYN TERMINAL CONVENTION")
print("=" * 80)

print(
    "SOURCE/VDD = left diffusion M1"
)

print(
    "Local source bbox um:",
    tuple(
        round(v, 3)
        for v in box_um(
            SOURCE_LOCAL
        )
    )
)

print(
    "Local drain bbox um:",
    tuple(
        round(v, 3)
        for v in box_um(
            DRAIN_LOCAL
        )
    )
)


# ================================================================
# 7. CREATE NEW ROUTED PARENT CELL
# ================================================================

if layout.cell(
    NEW_TOP_NAME
) is not None:

    raise RuntimeError(
        f"Cell already exists: {NEW_TOP_NAME}"
    )


top = layout.create_cell(
    NEW_TOP_NAME
)


# Preserve placement cell as immutable child.
top.insert(

    kdb.CellInstArray(

        placement_top.cell_index(),

        kdb.Trans(
            0,
            0,
        ),

    )

)


# ================================================================
# 8. VDD ROUTING PLAN
#
# Rail:
#   y = 10.0 um
#   width = 0.40 um
#
# Each source:
#   source landing
#       ↓
#   short LEFT horizontal escape
#       ↓
#   vertical Metal1 branch
#       ↓
#   VDD rail
#
# This keeps vertical branches away from PMOS gate contacts.
# ================================================================

RAIL_CENTER_Y = 10.000
RAIL_WIDTH = 0.400

SOURCE_ROUTE_WIDTH = 0.230

ESCAPE_OFFSET_X = 0.500

TAP_BRANCH_WIDTH = 0.400


# ================================================================
# 9. CALCULATE ABSOLUTE SOURCE / RESERVED TERMINALS
# ================================================================

source_abs = {}
reserved_abs = {}


for role in PMOS_ROLES:

    origin = placements[
        role
    ][
        "origin_um"
    ]

    x_um = float(
        origin[0]
    )

    y_um = float(
        origin[1]
    )


    dx = to_dbu(
        x_um
    )

    dy = to_dbu(
        y_um
    )


    source_box = translate_box(

        SOURCE_LOCAL,

        dx,
        dy,

    )


    drain_box = translate_box(

        DRAIN_LOCAL,

        dx,
        dy,

    )


    gate_abs = [

        translate_box(
            gate,
            dx,
            dy,
        )

        for gate
        in gate_boxes

    ]


    source_abs[
        role
    ] = source_box


    reserved_abs[
        role
    ] = [

        drain_box,
        *gate_abs,

    ]


# ================================================================
# 10. FIND N-TAP MET1
# ================================================================

tap_m1_boxes = [

    shape.bbox()

    for shape
    in n_tap.shapes(
        MET1_LAYER
    ).each()

]


if len(
    tap_m1_boxes
) != 1:

    raise RuntimeError(
        "Expected exactly one N_TAP Metal1 shape."
    )


tap_origin = placements[
    "N_TAP_VDD"
][
    "origin_um"
]


tap_dx = to_dbu(
    float(
        tap_origin[0]
    )
)

tap_dy = to_dbu(
    float(
        tap_origin[1]
    )
)


TAP_M1_ABS = translate_box(

    tap_m1_boxes[0],

    tap_dx,
    tap_dy,

)


# ================================================================
# 11. BUILD SOURCE ESCAPES + VERTICALS
# ================================================================

routing_boxes = []


print()
print("=" * 80)
print("PMOS VDD SOURCE ROUTES")
print("=" * 80)


escape_x_values = []


for role in PMOS_ROLES:

    source_box = source_abs[
        role
    ]


    source_cx_dbu, source_cy_dbu = center(
        source_box
    )


    source_cx = (
        source_cx_dbu
        * DBU
    )

    source_cy = (
        source_cy_dbu
        * DBU
    )


    escape_x = (
        source_cx
        - ESCAPE_OFFSET_X
    )


    escape_x_values.append(
        escape_x
    )


    # ------------------------------------------------------------
    # Horizontal escape
    #
    # Width in Y = 0.23 um.
    # Right edge overlaps source Metal1 landing.
    # ------------------------------------------------------------

    h_box = make_box_um(

        escape_x
        - SOURCE_ROUTE_WIDTH / 2.0,

        source_cy
        - SOURCE_ROUTE_WIDTH / 2.0,

        source_cx
        + SOURCE_ROUTE_WIDTH / 2.0,

        source_cy
        + SOURCE_ROUTE_WIDTH / 2.0,

    )


    # ------------------------------------------------------------
    # Vertical branch
    # ------------------------------------------------------------

    v_box = make_box_um(

        escape_x
        - SOURCE_ROUTE_WIDTH / 2.0,

        source_cy
        - SOURCE_ROUTE_WIDTH / 2.0,

        escape_x
        + SOURCE_ROUTE_WIDTH / 2.0,

        RAIL_CENTER_Y
        + RAIL_WIDTH / 2.0,

    )


    top.shapes(
        MET1_LAYER
    ).insert(
        h_box
    )


    top.shapes(
        MET1_LAYER
    ).insert(
        v_box
    )


    routing_boxes.extend(
        [
            h_box,
            v_box,
        ]
    )


    print(
        f"{role:6s} | "
        f"source center = "
        f"({source_cx:.3f}, "
        f"{source_cy:.3f}) um | "
        f"escape x = "
        f"{escape_x:.3f} um"
    )


# ================================================================
# 12. N-TAP VERTICAL CONNECTION
# ================================================================

tap_cx_dbu, tap_cy_dbu = center(
    TAP_M1_ABS
)


tap_cx = (
    tap_cx_dbu
    * DBU
)

tap_cy = (
    tap_cy_dbu
    * DBU
)


tap_branch = make_box_um(

    tap_cx
    - TAP_BRANCH_WIDTH / 2.0,

    tap_cy
    - TAP_BRANCH_WIDTH / 2.0,

    tap_cx
    + TAP_BRANCH_WIDTH / 2.0,

    RAIL_CENTER_Y
    + RAIL_WIDTH / 2.0,

)


top.shapes(
    MET1_LAYER
).insert(
    tap_branch
)


routing_boxes.append(
    tap_branch
)


print()
print(
    "N_TAP branch center x:",
    round(
        tap_cx,
        3
    ),
    "um"
)


# ================================================================
# 13. COMMON VDD RAIL
# ================================================================

rail_left = min(
    tap_cx,
    *escape_x_values
) - 0.200

rail_right = max(
    escape_x_values
) + 0.200


VDD_RAIL = make_box_um(

    rail_left,

    RAIL_CENTER_Y
    - RAIL_WIDTH / 2.0,

    rail_right,

    RAIL_CENTER_Y
    + RAIL_WIDTH / 2.0,

)


top.shapes(
    MET1_LAYER
).insert(
    VDD_RAIL
)


routing_boxes.append(
    VDD_RAIL
)


print()
print("=" * 80)
print("VDD RAIL")
print("=" * 80)

print(
    "Rail bbox um:",
    tuple(
        round(
            value,
            3
        )
        for value
        in box_um(
            VDD_RAIL
        )
    )
)


# ================================================================
# 14. CONNECTIVITY GEOMETRY AUDIT
# ================================================================

print()
print("=" * 80)
print("VDD CONNECTIVITY GEOMETRY AUDIT")
print("=" * 80)


SOURCE_CONNECTIONS_OK = True


for role in PMOS_ROLES:

    source_box = source_abs[
        role
    ]


    connected = any(

        overlaps(
            source_box,
            route
        )

        for route
        in routing_boxes

    )


    print(
        f"{role:6s} source touched:",
        connected
    )


    SOURCE_CONNECTIONS_OK &= connected


TAP_CONNECTION_OK = any(

    overlaps(
        TAP_M1_ABS,
        route
    )

    for route
    in routing_boxes

)


print(
    "N_TAP touched:",
    TAP_CONNECTION_OK
)


# ================================================================
# 15. RESERVED-TERMINAL COLLISION AUDIT
#
# VDD routing must NOT touch:
#   - any PMOS drain
#   - either gate landing
# ================================================================

print()
print("=" * 80)
print("RESERVED TERMINAL COLLISION AUDIT")
print("=" * 80)


RESERVED_CLEAR = True


for role in PMOS_ROLES:

    collisions = 0


    for reserved in reserved_abs[
        role
    ]:

        for route in routing_boxes:

            if overlaps(
                reserved,
                route
            ):

                collisions += 1


    clear = (
        collisions == 0
    )


    print(
        f"{role:6s} reserved terminals clear:",
        clear
    )


    RESERVED_CLEAR &= clear


# ================================================================
# 16. TOP-LEVEL M1 COUNT
# ================================================================

TOP_LEVEL_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        MET1_LAYER
    ).each()

)


EXPECTED_M1_COUNT = (

    4 * 2   # four horizontal + four vertical source routes
    + 1     # n-tap branch
    + 1     # rail

)


M1_COUNT_OK = (
    TOP_LEVEL_M1_COUNT
    == EXPECTED_M1_COUNT
)


print()
print("=" * 80)
print("TOP-LEVEL ROUTING AUDIT")
print("=" * 80)

print(
    "Top-level M1 shapes:",
    TOP_LEVEL_M1_COUNT
)

print(
    "Expected M1 shapes :",
    EXPECTED_M1_COUNT
)

print(
    "M1 count correct   :",
    M1_COUNT_OK
)


# ================================================================
# 17. USED LAYERS
# ================================================================

used_layers = []


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


# ================================================================
# 18. SAVE OPTIONS
# ================================================================

def make_save_options(fmt):

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
# 19. WRITE GDS + OASIS
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
# 20. READ-BACK
# ================================================================

verify = kdb.Layout()

verify.read(
    str(
        OUTPUT_GDS
    )
)


verify_top = verify.cell(
    NEW_TOP_NAME
)


READBACK_OK = bool(

    verify_top is not None

    and

    not verify_top.bbox().empty()

)


# ================================================================
# 21. MANIFEST
# ================================================================

output_manifest = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "revision":
        "vdd_v1",

    "top_cell":
        NEW_TOP_NAME,

    "parent_placement_cell":
        PLACEMENT_TOP_NAME,

    "routed_nets": [
        "VDD",
    ],

    "unrouted_nets": [

        "VBIAS",
        "PMOS_TO_SWITCH",
        "GATE_W0",
        "GATE_W1",
        "VMEM",
        "VSS",

    ],

    "pmos_source_assignment":
        "left diffusion terminal",

    "vdd_rail_bbox_um": [

        round(
            value,
            3
        )

        for value in box_um(
            VDD_RAIL
        )

    ],

    "checks": {

        "all_pmos_sources_connected":
            SOURCE_CONNECTIONS_OK,

        "n_tap_connected":
            TAP_CONNECTION_OK,

        "reserved_terminals_clear":
            RESERVED_CLEAR,

        "top_level_m1_count":
            M1_COUNT_OK,

        "gds_write":
            GDS_OK,

        "oas_write":
            OAS_OK,

        "readback":
            READBACK_OK,

    },

}


OUTPUT_MANIFEST.write_text(

    json.dumps(
        output_manifest,
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

STEP20A_PASS = bool(

    SOURCE_CONNECTIONS_OK

    and

    TAP_CONNECTION_OK

    and

    RESERVED_CLEAR

    and

    M1_COUNT_OK

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
print("STEP 20A RESULT")
print("=" * 80)


print(
    "All PMOS sources connected :",
    SOURCE_CONNECTIONS_OK
)

print(
    "N_TAP connected            :",
    TAP_CONNECTION_OK
)

print(
    "Reserved terminals clear   :",
    RESERVED_CLEAR
)

print(
    "M1 shape audit             :",
    M1_COUNT_OK
)

print(
    "GDS write                  :",
    GDS_OK
)

print(
    "OASIS write                :",
    OAS_OK
)

print(
    "GDS read-back              :",
    READBACK_OK
)

print(
    "Manifest write             :",
    MANIFEST_OK
)

print()
print(
    "STEP20A_PASS =",
    STEP20A_PASS
)


if not STEP20A_PASS:

    raise RuntimeError(
        "STEP 20A failed."
    )


print()
print(
    "VDD ROUTING V1 GENERATED"
)

print(
    "Only the VDD net has been routed."
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)