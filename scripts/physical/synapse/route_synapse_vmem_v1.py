# ================================================================
# NeuroLIF-SKY130
# STEP 23A — Shared VMEM routing V1
#
# Input:
#   neurolif_synapse_branches_v2.gds
#
# Existing frozen nets:
#   VDD
#   VBIAS
#   P_U1A -> SW1A
#   P_U0  -> SW0
#   P_U1B -> SW1B
#
# Adds:
#   SW1A left diffusion
#   SW0  left diffusion
#   SW1B left diffusion
#          -> shared VMEM
#
# VMEM uses Metal2 below the NMOS row.
#
# Still unrouted:
#   GATE_W0
#   GATE_W1
#   VSS
# ================================================================

from pathlib import Path
import json
import sys

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 23A: VMEM ROUTING V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SKY130_PYTHON_ROOT = (
    Path.home()
    / "KLayout"
    / "salt"
    / "Efabless_sky130"
    / "tech"
    / "sky130"
    / "python"
)

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_branches_v2.gds"
)

PLACEMENT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_placement_v1.json"
)

BRANCH_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_branches_v2.json"
)

OUTPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vmem_v1.gds"
)

OUTPUT_OAS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vmem_v1.oas"
)

OUTPUT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vmem_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_BRANCHES_V2"
)

NEW_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VMEM_V1"
)

N_SWITCH_NAME = (
    "N_LOGIC_W1000_L0150"
)

VIA_CELL_NAME = (
    "NEUROLIF_M1_M2_TRANSITION_W0500_H0500"
)


for path in [
    INPUT_GDS,
    PLACEMENT_MANIFEST,
    BRANCH_MANIFEST,
    SKY130_PYTHON_ROOT,
]:

    if not path.exists():
        raise FileNotFoundError(path)


if str(SKY130_PYTHON_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(SKY130_PYTHON_ROOT),
    )


from cells.via_generator import (
    vias_gen_draw,
)


# ================================================================
# 2. LOAD CANONICAL BRANCHES V2
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)

DBU = layout.dbu


input_top = layout.cell(
    INPUT_TOP_NAME
)

n_switch = layout.cell(
    N_SWITCH_NAME
)


if input_top is None:

    raise RuntimeError(
        f"Missing top cell: {INPUT_TOP_NAME}"
    )


if n_switch is None:

    raise RuntimeError(
        f"Missing primitive: {N_SWITCH_NAME}"
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
    "Canonical input:",
    INPUT_TOP_NAME
)

print(
    "branches_v2 status: DRC CLEAN"
)


# ================================================================
# 3. LOAD MANIFEST DATA
# ================================================================

placement_data = json.loads(

    PLACEMENT_MANIFEST.read_text(
        encoding="utf-8"
    )

)

branch_data = json.loads(

    BRANCH_MANIFEST.read_text(
        encoding="utf-8"
    )

)


placements = placement_data[
    "placement_um"
]

existing_branches = branch_data[
    "branches"
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
        "DIFF 65/20 missing."
    )

if MET1_LAYER is None:
    raise RuntimeError(
        "MET1 68/20 missing."
    )


# ================================================================
# 5. HELPERS
# ================================================================

def to_dbu(value_um):

    return int(
        round(
            value_um / DBU
        )
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


def box_um(box):

    return (

        box.left * DBU,
        box.bottom * DBU,
        box.right * DBU,
        box.top * DBU,

    )


# ================================================================
# 6. EXTRACT NMOS TERMINALS
# ================================================================

diff_boxes = [

    shape.bbox()

    for shape
    in n_switch.shapes(
        DIFF_LAYER
    ).each()

]

m1_boxes = [

    shape.bbox()

    for shape
    in n_switch.shapes(
        MET1_LAYER
    ).each()

]


if len(diff_boxes) != 1:

    raise RuntimeError(
        "N_LOGIC expected one DIFF region."
    )


diff_box = diff_boxes[0]


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
        center(box)[0]
)

gate_boxes.sort(
    key=lambda box:
        center(box)[1]
)


if len(sd_boxes) != 2:

    raise RuntimeError(
        "Expected two NMOS S/D landings."
    )


if len(gate_boxes) != 2:

    raise RuntimeError(
        "Expected two NMOS gate landings."
    )


LEFT_SD_LOCAL = sd_boxes[0]
RIGHT_SD_LOCAL = sd_boxes[1]

BOTTOM_GATE_LOCAL = gate_boxes[0]
TOP_GATE_LOCAL = gate_boxes[1]


print()
print("=" * 80)
print("NMOS TERMINAL ASSIGNMENT")
print("=" * 80)

print(
    "LEFT diffusion  = VMEM"
)

print(
    "RIGHT diffusion = PMOS input (already frozen)"
)

print(
    "Bottom/top gates remain reserved."
)

print()
print(
    "Left diffusion bbox um:",
    tuple(
        round(v, 3)
        for v
        in box_um(
            LEFT_SD_LOCAL
        )
    )
)

print(
    "Right diffusion bbox um:",
    tuple(
        round(v, 3)
        for v
        in box_um(
            RIGHT_SD_LOCAL
        )
    )
)


# ================================================================
# 7. ABSOLUTE TERMINAL HELPER
# ================================================================

def absolute_terminal(
    role,
    local_box,
):

    origin = placements[
        role
    ][
        "origin_um"
    ]


    return translate_box(

        local_box,

        to_dbu(
            float(
                origin[0]
            )
        ),

        to_dbu(
            float(
                origin[1]
            )
        ),

    )


SWITCHES = [
    "SW1A",
    "SW0",
    "SW1B",
]


# ================================================================
# 8. VALIDATED VIA CELL
# ================================================================

via_cell = layout.cell(
    VIA_CELL_NAME
)


if via_cell is None:

    via_cell = layout.create_cell(
        VIA_CELL_NAME
    )


    vias_gen_draw(

        cell=via_cell,

        l=0.50,

        w=0.50,

        start_layer="metal1",

        end_layer="metal2",

    )


MET2_LAYER = layout.find_layer(
    69,
    20
)

VIA1_LAYER = layout.find_layer(
    68,
    44
)


if MET2_LAYER is None:

    raise RuntimeError(
        "MET2 69/20 missing."
    )


if VIA1_LAYER is None:

    raise RuntimeError(
        "VIA1 68/44 missing."
    )


print()
print("=" * 80)
print("VALIDATED M1-M2 TRANSITION")
print("=" * 80)

print(
    "Via cell:",
    VIA_CELL_NAME
)

print(
    "Step 21B DRC status: CLEAN"
)


# ================================================================
# 9. CREATE NEW PARENT CELL
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
# 10. VMEM ROUTING PARAMETERS
# ================================================================

M1_ROUTE_WIDTH = 0.230

M2_ROUTE_WIDTH = 0.300

VIA_SIZE = 0.500

VIA_HALF = (
    VIA_SIZE / 2.0
)

M1_MIN_SPACING = 0.140


# Move VMEM via LEFT of each NMOS left diffusion.
VMEM_VIA_X_OFFSET = 0.600


# Shared Metal2 VMEM bus below NMOS gates.
VMEM_BUS_Y = 1.000


print()
print("=" * 80)
print("VMEM ROUTING PARAMETERS")
print("=" * 80)

print(
    "M1 route width:",
    M1_ROUTE_WIDTH,
    "um"
)

print(
    "M2 route width:",
    M2_ROUTE_WIDTH,
    "um"
)

print(
    "Via size:",
    VIA_SIZE,
    "um"
)

print(
    "VMEM via offset:",
    VMEM_VIA_X_OFFSET,
    "um LEFT"
)

print(
    "VMEM bus Y:",
    VMEM_BUS_Y,
    "um"
)


# ================================================================
# 11. RECONSTRUCT EXISTING BOTTOM BRANCH M1
#
# Needed to ensure new VMEM M1 stubs do not touch the frozen
# PMOS-input routes.
# ================================================================

existing_branch_m1 = []

existing_branch_m2 = []


for branch_name, data in existing_branches.items():

    switch_x = float(
        data[
            "switch_input_center_um"
        ][0]
    )

    switch_y = float(
        data[
            "switch_input_center_um"
        ][1]
    )

    pmos_y = float(
        data[
            "pmos_drain_center_um"
        ][1]
    )

    m2_x = float(
        data[
            "m2_x_um"
        ]
    )


    # Existing bottom M1 stub
    existing_branch_m1.append(

        make_box_um(

            switch_x
            - M1_ROUTE_WIDTH / 2.0,

            switch_y
            - M1_ROUTE_WIDTH / 2.0,

            m2_x
            + M1_ROUTE_WIDTH / 2.0,

            switch_y
            + M1_ROUTE_WIDTH / 2.0,

        )

    )


    # Existing M2 vertical
    existing_branch_m2.append(

        make_box_um(

            m2_x
            - M2_ROUTE_WIDTH / 2.0,

            switch_y
            - VIA_HALF,

            m2_x
            + M2_ROUTE_WIDTH / 2.0,

            pmos_y
            + VIA_HALF,

        )

    )


# ================================================================
# 12. ROUTE THREE VMEM TERMINALS
# ================================================================

new_m1_boxes = []

new_m2_verticals = []

via_pad_boxes = []

vmem_manifest = {}

via_x_values = []

NOTCH_AUDIT_OK = True

TERMINAL_CONNECTIONS_OK = True


print()
print("=" * 80)
print("ROUTING SWITCH LEFT DIFFUSIONS -> VMEM")
print("=" * 80)


for sw_role in SWITCHES:

    vmem_terminal = absolute_terminal(

        sw_role,

        LEFT_SD_LOCAL,

    )


    cx_dbu, cy_dbu = center(
        vmem_terminal
    )


    terminal_x = (
        cx_dbu * DBU
    )

    terminal_y = (
        cy_dbu * DBU
    )


    via_x = (
        terminal_x
        - VMEM_VIA_X_OFFSET
    )


    via_x_values.append(
        via_x
    )


    # ------------------------------------------------------------
    # Explicit Metal1 notch spacing
    #
    # Via is to LEFT of terminal.
    #
    # spacing =
    #   terminal LEFT edge
    #   -
    #   via pad RIGHT edge
    # ------------------------------------------------------------

    terminal_left = (
        vmem_terminal.left
        * DBU
    )

    pad_right = (
        via_x
        + VIA_HALF
    )

    notch = (
        terminal_left
        - pad_right
    )


    notch_ok = (
        notch
        >= M1_MIN_SPACING
    )


    NOTCH_AUDIT_OK &= notch_ok


    # ------------------------------------------------------------
    # M1 horizontal escape:
    #
    # via pad -> left diffusion landing
    # ------------------------------------------------------------

    m1_stub = make_box_um(

        via_x
        - M1_ROUTE_WIDTH / 2.0,

        terminal_y
        - M1_ROUTE_WIDTH / 2.0,

        terminal_x
        + M1_ROUTE_WIDTH / 2.0,

        terminal_y
        + M1_ROUTE_WIDTH / 2.0,

    )


    # ------------------------------------------------------------
    # M2 vertical to shared bus
    # ------------------------------------------------------------

    m2_vertical = make_box_um(

        via_x
        - M2_ROUTE_WIDTH / 2.0,

        VMEM_BUS_Y
        - M2_ROUTE_WIDTH / 2.0,

        via_x
        + M2_ROUTE_WIDTH / 2.0,

        terminal_y
        + VIA_HALF,

    )


    # ------------------------------------------------------------
    # Via-pad audit box
    # ------------------------------------------------------------

    via_pad = make_box_um(

        via_x
        - VIA_HALF,

        terminal_y
        - VIA_HALF,

        via_x
        + VIA_HALF,

        terminal_y
        + VIA_HALF,

    )


    # ------------------------------------------------------------
    # Insert M1 + M2
    # ------------------------------------------------------------

    top.shapes(
        MET1_LAYER
    ).insert(
        m1_stub
    )


    top.shapes(
        MET2_LAYER
    ).insert(
        m2_vertical
    )


    # ------------------------------------------------------------
    # Insert validated M1-M2 transition
    # ------------------------------------------------------------

    top.insert(

        kdb.CellInstArray(

            via_cell.cell_index(),

            kdb.Trans(

                to_dbu(
                    via_x
                    - VIA_HALF
                ),

                to_dbu(
                    terminal_y
                    - VIA_HALF
                ),

            ),

        )

    )


    new_m1_boxes.append(
        m1_stub
    )

    new_m2_verticals.append(
        m2_vertical
    )

    via_pad_boxes.append(
        via_pad
    )


    terminal_connected = overlaps(

        vmem_terminal,

        m1_stub,

    )


    TERMINAL_CONNECTIONS_OK &= (
        terminal_connected
    )


    vmem_manifest[
        sw_role
    ] = {

        "terminal_center_um": [

            round(
                terminal_x,
                3,
            ),

            round(
                terminal_y,
                3,
            ),

        ],

        "via_center_um": [

            round(
                via_x,
                3,
            ),

            round(
                terminal_y,
                3,
            ),

        ],

        "m1_notch_um":
            round(
                notch,
                3,
            ),

        "m1_notch_pass":
            notch_ok,

        "terminal_connected":
            terminal_connected,

    }


    print()
    print(
        sw_role
    )

    print(
        f"  VMEM terminal center : "
        f"({terminal_x:.3f}, "
        f"{terminal_y:.3f}) um"
    )

    print(
        f"  Via center           : "
        f"({via_x:.3f}, "
        f"{terminal_y:.3f}) um"
    )

    print(
        f"  M1 notch             : "
        f"{notch:.3f} um "
        f"(pass={notch_ok})"
    )

    print(
        "  Terminal connected   :",
        terminal_connected
    )


# ================================================================
# 13. SHARED VMEM M2 BUS
# ================================================================

VMEM_BUS_LEFT = (
    min(
        via_x_values
    )
    - M2_ROUTE_WIDTH / 2.0
)

VMEM_BUS_RIGHT = (
    max(
        via_x_values
    )
    + M2_ROUTE_WIDTH / 2.0
)


VMEM_BUS = make_box_um(

    VMEM_BUS_LEFT,

    VMEM_BUS_Y
    - M2_ROUTE_WIDTH / 2.0,

    VMEM_BUS_RIGHT,

    VMEM_BUS_Y
    + M2_ROUTE_WIDTH / 2.0,

)


top.shapes(
    MET2_LAYER
).insert(
    VMEM_BUS
)


print()
print("=" * 80)
print("SHARED VMEM BUS")
print("=" * 80)

print(
    "VMEM bus bbox um:",
    tuple(
        round(
            value,
            3,
        )
        for value
        in box_um(
            VMEM_BUS
        )
    )
)


# ================================================================
# 14. RIGHT DIFFUSIONS MUST REMAIN CLEAR
# ================================================================

print()
print("=" * 80)
print("FROZEN PMOS-INPUT TERMINAL AUDIT")
print("=" * 80)


RIGHT_DIFF_CLEAR = True


for sw_role in SWITCHES:

    right_diff = absolute_terminal(

        sw_role,

        RIGHT_SD_LOCAL,

    )


    touched = any(

        overlaps(
            right_diff,
            shape,
        )

        for shape
        in (
            new_m1_boxes
            + via_pad_boxes
        )

    )


    clear = not touched


    print(
        f"{sw_role:6s} right diffusion clear:",
        clear
    )


    RIGHT_DIFF_CLEAR &= clear


# ================================================================
# 15. NMOS GATE CONTACTS MUST REMAIN CLEAR
# ================================================================

print()
print("=" * 80)
print("NMOS GATE COLLISION AUDIT")
print("=" * 80)


NMOS_GATES_CLEAR = True


for sw_role in SWITCHES:

    gates = [

        absolute_terminal(

            sw_role,

            BOTTOM_GATE_LOCAL,

        ),

        absolute_terminal(

            sw_role,

            TOP_GATE_LOCAL,

        ),

    ]


    touched = any(

        overlaps(
            gate,
            shape,
        )

        for gate
        in gates

        for shape
        in (
            new_m1_boxes
            + via_pad_boxes
        )

    )


    clear = not touched


    print(
        f"{sw_role:6s} gate landings clear:",
        clear
    )


    NMOS_GATES_CLEAR &= clear


# ================================================================
# 16. NEW M1 vs EXISTING BRANCH M1
# ================================================================

print()
print("=" * 80)
print("EXISTING BRANCH M1 COLLISION AUDIT")
print("=" * 80)


M1_BRANCH_COLLISIONS = 0


for new_shape in (
    new_m1_boxes
    + via_pad_boxes
):

    for old_shape in existing_branch_m1:

        if overlaps(
            new_shape,
            old_shape,
        ):

            M1_BRANCH_COLLISIONS += 1


EXISTING_M1_CLEAR = (
    M1_BRANCH_COLLISIONS == 0
)


print(
    "VMEM M1 / frozen branch M1 overlaps:",
    M1_BRANCH_COLLISIONS
)

print(
    "Existing branch M1 remains isolated:",
    EXISTING_M1_CLEAR
)


# ================================================================
# 17. NEW M2 vs EXISTING BRANCH M2
# ================================================================

print()
print("=" * 80)
print("EXISTING BRANCH M2 COLLISION AUDIT")
print("=" * 80)


M2_BRANCH_COLLISIONS = 0


for new_shape in (

    new_m2_verticals
    + [
        VMEM_BUS
    ]

):

    for old_shape in existing_branch_m2:

        if overlaps(
            new_shape,
            old_shape,
        ):

            M2_BRANCH_COLLISIONS += 1


EXISTING_M2_CLEAR = (
    M2_BRANCH_COLLISIONS == 0
)


print(
    "VMEM M2 / frozen branch M2 overlaps:",
    M2_BRANCH_COLLISIONS
)

print(
    "Existing branch M2 remains isolated:",
    EXISTING_M2_CLEAR
)


# ================================================================
# 18. ALL THREE VERTICALS MUST TOUCH BUS
# ================================================================

print()
print("=" * 80)
print("VMEM BUS CONNECTIVITY AUDIT")
print("=" * 80)


BUS_CONNECTIONS_OK = True


for index, sw_role in enumerate(
    SWITCHES
):

    connected = overlaps(

        new_m2_verticals[
            index
        ],

        VMEM_BUS,

    )


    print(
        f"{sw_role:6s} M2 branch touches VMEM bus:",
        connected
    )


    BUS_CONNECTIONS_OK &= connected


# ================================================================
# 19. TOP-LEVEL SHAPE COUNTS
#
# New parent:
#
#   3 M1 terminal escapes
#   3 M2 verticals
#   1 M2 VMEM bus
#
# Via geometry is hierarchical:
#   3 via instances
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        MET1_LAYER
    ).each()

)

TOP_M2_COUNT = sum(

    1

    for _
    in top.shapes(
        MET2_LAYER
    ).each()

)


M1_COUNT_OK = (
    TOP_M1_COUNT == 3
)

M2_COUNT_OK = (
    TOP_M2_COUNT == 4
)


VIA_INSTANCE_COUNT = 0


for inst in top.each_inst():

    try:

        child = layout.cell(
            inst.cell_index
        )

    except Exception:

        try:

            child = layout.cell(
                inst.cell_index()
            )

        except Exception:

            child = None


    if (
        child is not None
        and
        child.name == VIA_CELL_NAME
    ):

        VIA_INSTANCE_COUNT += 1


VIA_COUNT_OK = (
    VIA_INSTANCE_COUNT == 3
)


print()
print("=" * 80)
print("SHAPE / INSTANCE AUDIT")
print("=" * 80)

print(
    "Top-level M1:",
    TOP_M1_COUNT,
    "(expected 3)"
)

print(
    "Top-level M2:",
    TOP_M2_COUNT,
    "(expected 4)"
)

print(
    "Via instances:",
    VIA_INSTANCE_COUNT,
    "(expected 3)"
)

print(
    "M1 count correct:",
    M1_COUNT_OK
)

print(
    "M2 count correct:",
    M2_COUNT_OK
)

print(
    "Via count correct:",
    VIA_COUNT_OK
)


# ================================================================
# 20. USED LAYERS
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
# 21. SAVE OPTIONS
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
# 22. WRITE GDS / OASIS
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
# 23. READBACK
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
# 24. MANIFEST
# ================================================================

output_manifest = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "revision":
        "vmem_v1",

    "top_cell":
        NEW_TOP_NAME,

    "parent_cell":
        INPUT_TOP_NAME,

    "canonical_input":
        "neurolif_synapse_branches_v2.gds",

    "routed_nets": [

        "VDD",

        "VBIAS",

        "P_U1A_TO_SW1A",

        "P_U0_TO_SW0",

        "P_U1B_TO_SW1B",

        "VMEM",

    ],

    "unrouted_nets": [

        "GATE_W0",

        "GATE_W1",

        "VSS",

    ],

    "vmem": {

        "switch_terminal":
            "left diffusion",

        "routing_layer":
            "metal2",

        "bus_y_um":
            VMEM_BUS_Y,

        "bus_bbox_um": [

            round(
                value,
                3,
            )

            for value
            in box_um(
                VMEM_BUS
            )

        ],

        "via_offset_left_um":
            VMEM_VIA_X_OFFSET,

        "branches":
            vmem_manifest,

    },

    "checks": {

        "notch_spacing":
            NOTCH_AUDIT_OK,

        "terminal_connections":
            TERMINAL_CONNECTIONS_OK,

        "right_diffusions_clear":
            RIGHT_DIFF_CLEAR,

        "nmos_gates_clear":
            NMOS_GATES_CLEAR,

        "existing_m1_clear":
            EXISTING_M1_CLEAR,

        "existing_m2_clear":
            EXISTING_M2_CLEAR,

        "vmem_bus_connections":
            BUS_CONNECTIONS_OK,

        "m1_count":
            M1_COUNT_OK,

        "m2_count":
            M2_COUNT_OK,

        "via_count":
            VIA_COUNT_OK,

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
# 25. FINAL GATE
# ================================================================

STEP23A_PASS = bool(

    NOTCH_AUDIT_OK

    and

    TERMINAL_CONNECTIONS_OK

    and

    RIGHT_DIFF_CLEAR

    and

    NMOS_GATES_CLEAR

    and

    EXISTING_M1_CLEAR

    and

    EXISTING_M2_CLEAR

    and

    BUS_CONNECTIONS_OK

    and

    M1_COUNT_OK

    and

    M2_COUNT_OK

    and

    VIA_COUNT_OK

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
print("STEP 23A RESULT")
print("=" * 80)


print(
    "VMEM notch spacing       :",
    NOTCH_AUDIT_OK
)

print(
    "VMEM terminals connected :",
    TERMINAL_CONNECTIONS_OK
)

print(
    "Right diffusions clear   :",
    RIGHT_DIFF_CLEAR
)

print(
    "NMOS gates clear         :",
    NMOS_GATES_CLEAR
)

print(
    "Frozen branch M1 clear   :",
    EXISTING_M1_CLEAR
)

print(
    "Frozen branch M2 clear   :",
    EXISTING_M2_CLEAR
)

print(
    "VMEM bus connectivity    :",
    BUS_CONNECTIONS_OK
)

print(
    "M1 shape audit           :",
    M1_COUNT_OK
)

print(
    "M2 shape audit           :",
    M2_COUNT_OK
)

print(
    "Via instance audit       :",
    VIA_COUNT_OK
)

print(
    "GDS write                :",
    GDS_OK
)

print(
    "OASIS write              :",
    OAS_OK
)

print(
    "GDS read-back            :",
    READBACK_OK
)

print(
    "Manifest write           :",
    MANIFEST_OK
)

print()
print(
    "STEP23A_PASS =",
    STEP23A_PASS
)


if not STEP23A_PASS:

    raise RuntimeError(
        "STEP 23A failed."
    )


print()
print(
    "SHARED VMEM ROUTING V1 GENERATED"
)

print()
print(
    "Connected:"
)

print(
    "  SW1A left diffusion -> VMEM"
)

print(
    "  SW0  left diffusion -> VMEM"
)

print(
    "  SW1B left diffusion -> VMEM"
)

print()
print(
    "NMOS gate landings remain free."
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)