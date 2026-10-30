# ================================================================
# NeuroLIF-SKY130
# STEP 20C — Weighted-synapse VBIAS routing V1
#
# Input:
#   neurolif_synapse_vdd_v1.gds
#
# Adds ONLY:
#   - common PMOS gate VBIAS bus
#   - P_REF drain -> VBIAS
#
# Existing VDD routing is preserved as an immutable child.
#
# Still NOT routed:
#   - P_U0 drain -> SW0
#   - P_U1A drain -> SW1A
#   - P_U1B drain -> SW1B
#   - GATE_W0
#   - GATE_W1
#   - VMEM
#   - VSS
# ================================================================

from pathlib import Path
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 20C: VBIAS ROUTING V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vdd_v1.gds"
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
    / "neurolif_synapse_vbias_v1.gds"
)

OUTPUT_OAS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vbias_v1.oas"
)

OUTPUT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vbias_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VDD_V1"
)

NEW_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VBIAS_V1"
)

P_SYN_NAME = (
    "P_SYN_W0840_L0500"
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
# 2. LOAD DATABASE
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)

DBU = layout.dbu


input_top = layout.cell(
    INPUT_TOP_NAME
)

p_syn = layout.cell(
    P_SYN_NAME
)


if input_top is None:

    raise RuntimeError(
        f"Missing cell: {INPUT_TOP_NAME}"
    )


if p_syn is None:

    raise RuntimeError(
        f"Missing cell: {P_SYN_NAME}"
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
    "VDD-routed parent found:",
    True
)


# ================================================================
# 3. PLACEMENT INFORMATION
# ================================================================

placement_data = json.loads(

    PLACEMENT_MANIFEST.read_text(
        encoding="utf-8"
    )

)


placements = placement_data[
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
        "DIFF layer missing."
    )


if MET1_LAYER is None:

    raise RuntimeError(
        "MET1 layer missing."
    )


# ================================================================
# 5. HELPERS
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


def center(
    box,
):

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


def box_um(
    box,
):

    return (

        box.left * DBU,

        box.bottom * DBU,

        box.right * DBU,

        box.top * DBU,

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


def make_box_um(
    x1,
    y1,
    x2,
    y2,
):

    return kdb.Box(

        to_dbu(
            min(
                x1,
                x2,
            )
        ),

        to_dbu(
            min(
                y1,
                y2,
            )
        ),

        to_dbu(
            max(
                x1,
                x2,
            )
        ),

        to_dbu(
            max(
                y1,
                y2,
            )
        ),

    )


# ================================================================
# 6. IDENTIFY LOCAL P_SYN TERMINALS
# ================================================================

diff_boxes = [

    shape.bbox()

    for shape
    in p_syn.shapes(
        DIFF_LAYER
    ).each()

]


m1_boxes = [

    shape.bbox()

    for shape
    in p_syn.shapes(
        MET1_LAYER
    ).each()

]


if len(
    diff_boxes
) != 1:

    raise RuntimeError(
        "P_SYN DIFF audit failed."
    )


diff_box = diff_boxes[
    0
]


sd_boxes = [

    box

    for box
    in m1_boxes

    if overlaps(
        box,
        diff_box,
    )

]


gate_boxes = [

    box

    for box
    in m1_boxes

    if not overlaps(
        box,
        diff_box,
    )

]


sd_boxes.sort(

    key=lambda box:
        center(
            box
        )[0]

)


gate_boxes.sort(

    key=lambda box:
        center(
            box
        )[1]

)


if len(
    sd_boxes
) != 2:

    raise RuntimeError(
        "Expected two diffusion M1 landings."
    )


if len(
    gate_boxes
) != 2:

    raise RuntimeError(
        "Expected two gate M1 landings."
    )


SOURCE_LOCAL = sd_boxes[
    0
]

DRAIN_LOCAL = sd_boxes[
    1
]

BOTTOM_GATE_LOCAL = gate_boxes[
    0
]

TOP_GATE_LOCAL = gate_boxes[
    1
]


print()
print("=" * 80)
print("P_SYN TERMINAL ASSIGNMENT")
print("=" * 80)

print(
    "Source/VDD : LEFT diffusion"
)

print(
    "Drain      : RIGHT diffusion"
)

print(
    "VBIAS gate : BOTTOM gate landing"
)

print()
print(
    "Bottom gate bbox um:",
    tuple(
        round(
            v,
            3
        )
        for v
        in box_um(
            BOTTOM_GATE_LOCAL
        )
    )
)

print(
    "Drain bbox um:",
    tuple(
        round(
            v,
            3
        )
        for v
        in box_um(
            DRAIN_LOCAL
        )
    )
)


# ================================================================
# 7. ABSOLUTE TERMINALS
# ================================================================

terminals = {}


for role in PMOS_ROLES:

    origin = placements[
        role
    ][
        "origin_um"
    ]


    dx = to_dbu(
        float(
            origin[0]
        )
    )

    dy = to_dbu(
        float(
            origin[1]
        )
    )


    terminals[
        role
    ] = {

        "source":
            translate_box(
                SOURCE_LOCAL,
                dx,
                dy,
            ),

        "drain":
            translate_box(
                DRAIN_LOCAL,
                dx,
                dy,
            ),

        "gate_bottom":
            translate_box(
                BOTTOM_GATE_LOCAL,
                dx,
                dy,
            ),

        "gate_top":
            translate_box(
                TOP_GATE_LOCAL,
                dx,
                dy,
            ),

    }


# ================================================================
# 8. CREATE NEW PARENT
#
# Entire validated VDD version becomes one child instance.
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
# 9. VBIAS ROUTING PARAMETERS
#
# Horizontal gate bus below PMOS row.
# Future drain-to-switch routes can later use Metal2.
# ================================================================

ROUTE_WIDTH = 0.230

VBIAS_BUS_Y = 6.800

BUS_LEFT = 0.300

BUS_RIGHT = 9.800

PREF_DRAIN_ESCAPE_X = 4.450


# ================================================================
# 10. COMMON VBIAS BUS
# ================================================================

VBIAS_BUS = make_box_um(

    BUS_LEFT,

    VBIAS_BUS_Y
    - ROUTE_WIDTH / 2.0,

    BUS_RIGHT,

    VBIAS_BUS_Y
    + ROUTE_WIDTH / 2.0,

)


top.shapes(
    MET1_LAYER
).insert(
    VBIAS_BUS
)


vbias_routes = [
    VBIAS_BUS,
]


print()
print("=" * 80)
print("VBIAS BUS")
print("=" * 80)

print(
    "VBIAS bus bbox um:",
    tuple(
        round(
            v,
            3
        )

        for v
        in box_um(
            VBIAS_BUS
        )
    )
)


# ================================================================
# 11. CONNECT ALL FOUR BOTTOM GATE LANDINGS
# ================================================================

print()
print("=" * 80)
print("PMOS GATE -> VBIAS ROUTES")
print("=" * 80)


for role in PMOS_ROLES:

    gate_box = terminals[
        role
    ][
        "gate_bottom"
    ]


    gate_cx_dbu, gate_cy_dbu = center(
        gate_box
    )


    gate_cx = (
        gate_cx_dbu
        * DBU
    )

    gate_cy = (
        gate_cy_dbu
        * DBU
    )


    branch = make_box_um(

        gate_cx
        - ROUTE_WIDTH / 2.0,

        VBIAS_BUS_Y
        - ROUTE_WIDTH / 2.0,

        gate_cx
        + ROUTE_WIDTH / 2.0,

        gate_cy
        + ROUTE_WIDTH / 2.0,

    )


    top.shapes(
        MET1_LAYER
    ).insert(
        branch
    )


    vbias_routes.append(
        branch
    )


    print(

        f"{role:6s} gate center = "
        f"({gate_cx:.3f}, "
        f"{gate_cy:.3f}) um"

    )


# ================================================================
# 12. DIODE-CONNECT P_REF
#
# P_REF right diffusion = VBIAS.
#
# Route:
#
#     P_REF drain
#         |
#         +---- horizontal escape right
#                        |
#                        |
#                    VBIAS BUS
#
# The vertical part is moved right of P_REF's gate contact.
# ================================================================

pref_drain = terminals[
    "P_REF"
][
    "drain"
]


pref_drain_cx_dbu, pref_drain_cy_dbu = center(
    pref_drain
)


pref_drain_cx = (
    pref_drain_cx_dbu
    * DBU
)

pref_drain_cy = (
    pref_drain_cy_dbu
    * DBU
)


pref_horizontal = make_box_um(

    pref_drain_cx
    - ROUTE_WIDTH / 2.0,

    pref_drain_cy
    - ROUTE_WIDTH / 2.0,

    PREF_DRAIN_ESCAPE_X
    + ROUTE_WIDTH / 2.0,

    pref_drain_cy
    + ROUTE_WIDTH / 2.0,

)


pref_vertical = make_box_um(

    PREF_DRAIN_ESCAPE_X
    - ROUTE_WIDTH / 2.0,

    VBIAS_BUS_Y
    - ROUTE_WIDTH / 2.0,

    PREF_DRAIN_ESCAPE_X
    + ROUTE_WIDTH / 2.0,

    pref_drain_cy
    + ROUTE_WIDTH / 2.0,

)


top.shapes(
    MET1_LAYER
).insert(
    pref_horizontal
)


top.shapes(
    MET1_LAYER
).insert(
    pref_vertical
)


vbias_routes.extend(
    [
        pref_horizontal,
        pref_vertical,
    ]
)


print()
print("=" * 80)
print("P_REF DIODE CONNECTION")
print("=" * 80)

print(
    "P_REF drain center:",
    f"({pref_drain_cx:.3f}, "
    f"{pref_drain_cy:.3f}) um"
)

print(
    "Drain escape x:",
    PREF_DRAIN_ESCAPE_X,
    "um"
)


# ================================================================
# 13. VBIAS CONNECTIVITY AUDIT
# ================================================================

print()
print("=" * 80)
print("VBIAS CONNECTIVITY AUDIT")
print("=" * 80)


ALL_GATES_CONNECTED = True


for role in PMOS_ROLES:

    gate_box = terminals[
        role
    ][
        "gate_bottom"
    ]


    touched = any(

        overlaps(
            gate_box,
            route,
        )

        for route
        in vbias_routes

    )


    print(
        f"{role:6s} gate touched:",
        touched
    )


    ALL_GATES_CONNECTED &= touched


PREF_DRAIN_CONNECTED = any(

    overlaps(
        pref_drain,
        route,
    )

    for route
    in vbias_routes

)


print(
    "P_REF drain touched:",
    PREF_DRAIN_CONNECTED
)


# ================================================================
# 14. OTHER PMOS DRAINS MUST REMAIN CLEAR
# ================================================================

print()
print("=" * 80)
print("UNROUTED PMOS DRAIN AUDIT")
print("=" * 80)


OTHER_DRAINS_CLEAR = True


for role in [

    "P_U1A",

    "P_U0",

    "P_U1B",

]:

    drain_box = terminals[
        role
    ][
        "drain"
    ]


    touched = any(

        overlaps(
            drain_box,
            route,
        )

        for route
        in vbias_routes

    )


    clear = not touched


    print(
        f"{role:6s} drain remains clear:",
        clear
    )


    OTHER_DRAINS_CLEAR &= clear


# ================================================================
# 15. ALL PMOS SOURCES MUST REMAIN CLEAR OF NEW VBIAS
# ================================================================

print()
print("=" * 80)
print("PMOS SOURCE / VDD COLLISION AUDIT")
print("=" * 80)


SOURCES_CLEAR = True


for role in PMOS_ROLES:

    source_box = terminals[
        role
    ][
        "source"
    ]


    touched = any(

        overlaps(
            source_box,
            route,
        )

        for route
        in vbias_routes

    )


    clear = not touched


    print(
        f"{role:6s} source clear of VBIAS:",
        clear
    )


    SOURCES_CLEAR &= clear


# ================================================================
# 16. RECONSTRUCT FROZEN VDD ROUTING
#
# Used only for geometric collision checking.
#
# Exact values from Step 20A.
# ================================================================

VDD_RAIL_CENTER_Y = 10.000

VDD_RAIL_WIDTH = 0.400

VDD_SOURCE_WIDTH = 0.230

VDD_ESCAPE_OFFSET_X = 0.500

VDD_TAP_WIDTH = 0.400


vdd_boxes = []


vdd_escape_x = []


for role in PMOS_ROLES:

    source_box = terminals[
        role
    ][
        "source"
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
        - VDD_ESCAPE_OFFSET_X
    )


    vdd_escape_x.append(
        escape_x
    )


    vdd_boxes.append(

        make_box_um(

            escape_x
            - VDD_SOURCE_WIDTH / 2.0,

            source_cy
            - VDD_SOURCE_WIDTH / 2.0,

            source_cx
            + VDD_SOURCE_WIDTH / 2.0,

            source_cy
            + VDD_SOURCE_WIDTH / 2.0,

        )

    )


    vdd_boxes.append(

        make_box_um(

            escape_x
            - VDD_SOURCE_WIDTH / 2.0,

            source_cy
            - VDD_SOURCE_WIDTH / 2.0,

            escape_x
            + VDD_SOURCE_WIDTH / 2.0,

            VDD_RAIL_CENTER_Y
            + VDD_RAIL_WIDTH / 2.0,

        )

    )


# N_TAP center from placement:
# origin (-2.5, 8.0)
# local M1 center (0.5, 0.5)
# => absolute (-2.0, 8.5)

VDD_TAP_CX = -2.000

VDD_TAP_CY = 8.500


vdd_boxes.append(

    make_box_um(

        VDD_TAP_CX
        - VDD_TAP_WIDTH / 2.0,

        VDD_TAP_CY
        - VDD_TAP_WIDTH / 2.0,

        VDD_TAP_CX
        + VDD_TAP_WIDTH / 2.0,

        VDD_RAIL_CENTER_Y
        + VDD_RAIL_WIDTH / 2.0,

    )

)


vdd_rail_left = min(

    VDD_TAP_CX,

    *vdd_escape_x,

) - 0.200


vdd_rail_right = max(
    vdd_escape_x
) + 0.200


vdd_boxes.append(

    make_box_um(

        vdd_rail_left,

        VDD_RAIL_CENTER_Y
        - VDD_RAIL_WIDTH / 2.0,

        vdd_rail_right,

        VDD_RAIL_CENTER_Y
        + VDD_RAIL_WIDTH / 2.0,

    )

)


# ================================================================
# 17. VDD vs VBIAS SHORT AUDIT
# ================================================================

print()
print("=" * 80)
print("VDD / VBIAS GEOMETRIC SHORT AUDIT")
print("=" * 80)


VDD_VBIAS_CLEAR = True

collision_count = 0


for vbias_box in vbias_routes:

    for vdd_box in vdd_boxes:

        if overlaps(
            vbias_box,
            vdd_box,
        ):

            collision_count += 1

            VDD_VBIAS_CLEAR = False


print(
    "VDD/VBIAS overlap count:",
    collision_count
)

print(
    "VDD/VBIAS geometrically separate:",
    VDD_VBIAS_CLEAR
)


# ================================================================
# 18. TOP-LEVEL METAL1 COUNT
#
# This new parent contains:
#
#   1 VBIAS horizontal bus
#   4 gate branches
#   1 P_REF drain horizontal
#   1 P_REF drain vertical
#
# = 7 new top-level Metal1 shapes.
#
# Existing VDD shapes remain inside child cell.
# ================================================================

TOP_LEVEL_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        MET1_LAYER
    ).each()

)


EXPECTED_TOP_LEVEL_M1 = 7


M1_COUNT_OK = (

    TOP_LEVEL_M1_COUNT
    == EXPECTED_TOP_LEVEL_M1

)


print()
print("=" * 80)
print("TOP-LEVEL METAL1 AUDIT")
print("=" * 80)

print(
    "New VBIAS M1 shapes:",
    TOP_LEVEL_M1_COUNT
)

print(
    "Expected            :",
    EXPECTED_TOP_LEVEL_M1
)

print(
    "M1 count correct    :",
    M1_COUNT_OK
)


# ================================================================
# 19. USED LAYERS
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
# 20. SAVE OPTIONS
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
# 21. WRITE GDS / OASIS
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
# 22. READ-BACK
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
# 23. OUTPUT MANIFEST
# ================================================================

output_manifest = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "revision":
        "vbias_v1",

    "top_cell":
        NEW_TOP_NAME,

    "parent_cell":
        INPUT_TOP_NAME,

    "routed_nets": [

        "VDD",

        "VBIAS",

    ],

    "unrouted_nets": [

        "P_U0_TO_SW0",

        "P_U1A_TO_SW1A",

        "P_U1B_TO_SW1B",

        "GATE_W0",

        "GATE_W1",

        "VMEM",

        "VSS",

    ],

    "vbias_topology": {

        "P_REF_gate":
            "VBIAS",

        "P_REF_drain":
            "VBIAS",

        "P_U0_gate":
            "VBIAS",

        "P_U1A_gate":
            "VBIAS",

        "P_U1B_gate":
            "VBIAS",

        "gate_contact_used":
            "bottom",

        "metal":
            "metal1",

        "bus_y_um":
            VBIAS_BUS_Y,

    },

    "checks": {

        "all_four_pmos_gates_connected":
            ALL_GATES_CONNECTED,

        "pref_drain_connected":
            PREF_DRAIN_CONNECTED,

        "other_pmos_drains_clear":
            OTHER_DRAINS_CLEAR,

        "pmos_sources_clear_of_vbias":
            SOURCES_CLEAR,

        "vdd_vbias_geometrically_separate":
            VDD_VBIAS_CLEAR,

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
# 24. FINAL GATE
# ================================================================

STEP20C_PASS = bool(

    ALL_GATES_CONNECTED

    and

    PREF_DRAIN_CONNECTED

    and

    OTHER_DRAINS_CLEAR

    and

    SOURCES_CLEAR

    and

    VDD_VBIAS_CLEAR

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
print("STEP 20C RESULT")
print("=" * 80)


print(
    "All PMOS gates connected  :",
    ALL_GATES_CONNECTED
)

print(
    "P_REF drain connected      :",
    PREF_DRAIN_CONNECTED
)

print(
    "Other PMOS drains clear    :",
    OTHER_DRAINS_CLEAR
)

print(
    "PMOS sources clear         :",
    SOURCES_CLEAR
)

print(
    "VDD/VBIAS separate         :",
    VDD_VBIAS_CLEAR
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
    "STEP20C_PASS =",
    STEP20C_PASS
)


if not STEP20C_PASS:

    raise RuntimeError(
        "STEP 20C failed."
    )


print()
print(
    "VBIAS ROUTING V1 GENERATED"
)

print(
    "Routed nets are now: VDD, VBIAS"
)

print()
print(
    "P_REF is diode-connected:"
)

print(
    "P_REF gate = P_REF drain = VBIAS"
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)