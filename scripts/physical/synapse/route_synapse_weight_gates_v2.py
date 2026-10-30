# ================================================================
# NeuroLIF-SKY130
# STEP 24D — Corrected weight-control routing V2
#
# Root cause confirmed by Step 24C:
#
#   GATE_W0 bus top edge = 1.915 um
#   SW0 bottom gate lower edge = 2.020 um
#
#   notch = 0.105 um
#   required m1.2 = 0.140 um
#
# Correction:
#
#   GATE_W0_BUS_Y:
#       1.800 -> 1.700 um
#
# New notch:
#
#   2.020 - (1.700 + 0.115)
#   = 0.205 um
#
# GATE_W1 is unchanged.
#
# IMPORTANT:
#   Rebuild from DRC-clean VMEM V1.
#   Do NOT use failing weight_gates_v1 as input.
# ================================================================

from pathlib import Path
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 24D: CORRECTED WEIGHT-GATE ROUTING V2")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vmem_v1.gds"
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

VMEM_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vmem_v1.json"
)

OUTPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_weight_gates_v2.gds"
)

OUTPUT_OAS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_weight_gates_v2.oas"
)

OUTPUT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_weight_gates_v2.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VMEM_V1"
)

NEW_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_WEIGHT_GATES_V2"
)

N_SWITCH_NAME = (
    "N_LOGIC_W1000_L0150"
)


for path in [
    INPUT_GDS,
    PLACEMENT_MANIFEST,
    BRANCH_MANIFEST,
    VMEM_MANIFEST,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. LOAD CLEAN VMEM VERSION
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
        f"Missing input top: {INPUT_TOP_NAME}"
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
    "Clean input:",
    INPUT_TOP_NAME
)

print(
    "Step 23B status: DRC CLEAN"
)

print(
    "Failing weight_gates_v1 is NOT used as input."
)


# ================================================================
# 3. MANIFEST DATA
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

vmem_data = json.loads(

    VMEM_MANIFEST.read_text(
        encoding="utf-8"
    )

)


placements = placement_data[
    "placement_um"
]

existing_branches = branch_data[
    "branches"
]

existing_vmem = vmem_data[
    "vmem"
][
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
        (box.left + box.right) / 2.0,
        (box.bottom + box.top) / 2.0,
    )


def overlaps(a, b):

    return not (
        a.right <= b.left
        or a.left >= b.right
        or a.top <= b.bottom
        or a.bottom >= b.top
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

        to_dbu(min(x1, x2)),
        to_dbu(min(y1, y2)),
        to_dbu(max(x1, x2)),
        to_dbu(max(y1, y2)),

    )


def box_um(box):

    return (
        box.left * DBU,
        box.bottom * DBU,
        box.right * DBU,
        box.top * DBU,
    )


def box_distance_um(a, b):

    dx = max(
        b.left - a.right,
        a.left - b.right,
        0,
    )

    dy = max(
        b.bottom - a.top,
        a.bottom - b.top,
        0,
    )

    return (
        (dx * DBU) ** 2
        +
        (dy * DBU) ** 2
    ) ** 0.5


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
        "Expected exactly one N_LOGIC DIFF region."
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
        "Expected two S/D M1 landings."
    )


if len(gate_boxes) != 2:

    raise RuntimeError(
        "Expected two gate M1 landings."
    )


LEFT_SD_LOCAL = sd_boxes[0]
RIGHT_SD_LOCAL = sd_boxes[1]

BOTTOM_GATE_LOCAL = gate_boxes[0]
TOP_GATE_LOCAL = gate_boxes[1]


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
            float(origin[0])
        ),

        to_dbu(
            float(origin[1])
        ),

    )


SWITCHES = [
    "SW1A",
    "SW0",
    "SW1B",
]


# ================================================================
# 8. PRINT TERMINALS
# ================================================================

print()
print("=" * 80)
print("ABSOLUTE SWITCH GATES")
print("=" * 80)


for role in SWITCHES:

    bottom_gate = absolute_terminal(
        role,
        BOTTOM_GATE_LOCAL,
    )

    top_gate = absolute_terminal(
        role,
        TOP_GATE_LOCAL,
    )


    bcx, bcy = center(
        bottom_gate
    )

    tcx, tcy = center(
        top_gate
    )


    print()
    print(role)

    print(
        "  bottom center:",
        f"({bcx * DBU:.3f}, "
        f"{bcy * DBU:.3f}) um"
    )

    print(
        "  top center   :",
        f"({tcx * DBU:.3f}, "
        f"{tcy * DBU:.3f}) um"
    )


# ================================================================
# 9. CREATE NEW TOP
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
# 10. ROUTING PARAMETERS
# ================================================================

M1_WIDTH = 0.230

M1_HALF = (
    M1_WIDTH / 2.0
)

M1_MIN_SPACING = 0.140


# ------------------------------------------------
# GATE_W1 — unchanged from V1
# ------------------------------------------------

GATE_W1_BUS_Y = 4.700

GATE_W1_LEFT = 0.300

GATE_W1_RIGHT = 9.800


# ------------------------------------------------
# GATE_W0 — corrected
# ------------------------------------------------

OLD_GATE_W0_BUS_Y = 1.800

GATE_W0_BUS_Y = 1.700

GATE_W0_LEFT = 6.300

GATE_W0_RIGHT = 7.300


print()
print("=" * 80)
print("STEP 24C CORRECTION")
print("=" * 80)

print(
    "Old GATE_W0 bus Y:",
    OLD_GATE_W0_BUS_Y,
    "um"
)

print(
    "New GATE_W0 bus Y:",
    GATE_W0_BUS_Y,
    "um"
)

print(
    "m1.2 required spacing:",
    M1_MIN_SPACING,
    "um"
)

print(
    "GATE_W1 geometry unchanged."
)


# ================================================================
# 11. GATE_W1
# ================================================================

gate_w1_boxes = []


GATE_W1_BUS = make_box_um(

    GATE_W1_LEFT,

    GATE_W1_BUS_Y
    - M1_HALF,

    GATE_W1_RIGHT,

    GATE_W1_BUS_Y
    + M1_HALF,

)


top.shapes(
    MET1_LAYER
).insert(
    GATE_W1_BUS
)


gate_w1_boxes.append(
    GATE_W1_BUS
)


for role in [
    "SW1A",
    "SW1B",
]:

    gate = absolute_terminal(
        role,
        TOP_GATE_LOCAL,
    )


    cx_dbu, cy_dbu = center(
        gate
    )


    cx = cx_dbu * DBU

    cy = cy_dbu * DBU


    branch = make_box_um(

        cx - M1_HALF,

        cy - M1_HALF,

        cx + M1_HALF,

        GATE_W1_BUS_Y
        + M1_HALF,

    )


    top.shapes(
        MET1_LAYER
    ).insert(
        branch
    )


    gate_w1_boxes.append(
        branch
    )


# ================================================================
# 12. CORRECTED GATE_W0
# ================================================================

gate_w0_boxes = []


GATE_W0_BUS = make_box_um(

    GATE_W0_LEFT,

    GATE_W0_BUS_Y
    - M1_HALF,

    GATE_W0_RIGHT,

    GATE_W0_BUS_Y
    + M1_HALF,

)


top.shapes(
    MET1_LAYER
).insert(
    GATE_W0_BUS
)


gate_w0_boxes.append(
    GATE_W0_BUS
)


sw0_bottom = absolute_terminal(

    "SW0",

    BOTTOM_GATE_LOCAL,

)


sw0_cx_dbu, sw0_cy_dbu = center(
    sw0_bottom
)


sw0_cx = (
    sw0_cx_dbu
    * DBU
)

sw0_cy = (
    sw0_cy_dbu
    * DBU
)


GATE_W0_BRANCH = make_box_um(

    sw0_cx
    - M1_HALF,

    GATE_W0_BUS_Y
    - M1_HALF,

    sw0_cx
    + M1_HALF,

    sw0_cy
    + M1_HALF,

)


top.shapes(
    MET1_LAYER
).insert(
    GATE_W0_BRANCH
)


gate_w0_boxes.append(
    GATE_W0_BRANCH
)


# ================================================================
# 13. EXPLICIT W0 NOTCH AUDIT
# ================================================================

SW0_GATE_BOTTOM_EDGE = (
    sw0_bottom.bottom
    * DBU
)

W0_BUS_TOP_EDGE = (
    GATE_W0_BUS.top
    * DBU
)


W0_NOTCH_SPACING = (

    SW0_GATE_BOTTOM_EDGE
    - W0_BUS_TOP_EDGE

)


W0_NOTCH_OK = (
    W0_NOTCH_SPACING
    >= M1_MIN_SPACING
)


print()
print("=" * 80)
print("CORRECTED GATE_W0 NOTCH AUDIT")
print("=" * 80)


print(
    "SW0 bottom-gate lower edge:",
    f"{SW0_GATE_BOTTOM_EDGE:.3f} um"
)

print(
    "GATE_W0 bus upper edge    :",
    f"{W0_BUS_TOP_EDGE:.3f} um"
)

print(
    "Notch spacing             :",
    f"{W0_NOTCH_SPACING:.3f} um"
)

print(
    "m1.2 requirement          :",
    f"{M1_MIN_SPACING:.3f} um"
)

print(
    "Notch pass                :",
    W0_NOTCH_OK
)


# ================================================================
# 14. W1 NOTCH / SPACING AUDIT
# ================================================================

W1_NOTCH_OK = True


print()
print("=" * 80)
print("GATE_W1 SPACING AUDIT")
print("=" * 80)


for role in [
    "SW1A",
    "SW1B",
]:

    gate = absolute_terminal(
        role,
        TOP_GATE_LOCAL,
    )


    gate_top = (
        gate.top
        * DBU
    )

    bus_bottom = (
        GATE_W1_BUS.bottom
        * DBU
    )


    spacing = (
        bus_bottom
        - gate_top
    )


    ok = (
        spacing
        >= M1_MIN_SPACING
    )


    print(
        f"{role:6s} side-notch spacing:",
        f"{spacing:.3f} um",
        f"(pass={ok})"
    )


    W1_NOTCH_OK &= ok


# ================================================================
# 15. TARGET CONNECTIVITY AUDIT
# ================================================================

sw1a_top = absolute_terminal(
    "SW1A",
    TOP_GATE_LOCAL,
)

sw1b_top = absolute_terminal(
    "SW1B",
    TOP_GATE_LOCAL,
)


SW1A_W1_CONNECTED = any(

    overlaps(
        sw1a_top,
        shape,
    )

    for shape
    in gate_w1_boxes

)


SW1B_W1_CONNECTED = any(

    overlaps(
        sw1b_top,
        shape,
    )

    for shape
    in gate_w1_boxes

)


SW0_W0_CONNECTED = any(

    overlaps(
        sw0_bottom,
        shape,
    )

    for shape
    in gate_w0_boxes

)


TARGET_CONNECTIONS_OK = bool(

    SW1A_W1_CONNECTED

    and

    SW1B_W1_CONNECTED

    and

    SW0_W0_CONNECTED

)


print()
print("=" * 80)
print("TARGET GATE CONNECTIVITY AUDIT")
print("=" * 80)


print(
    "SW1A -> GATE_W1:",
    SW1A_W1_CONNECTED
)

print(
    "SW1B -> GATE_W1:",
    SW1B_W1_CONNECTED
)

print(
    "SW0  -> GATE_W0:",
    SW0_W0_CONNECTED
)


# ================================================================
# 16. WRONG-GATE AUDIT
# ================================================================

WRONG_GATE_CLEAR = True


print()
print("=" * 80)
print("WRONG-GATE CONNECTION AUDIT")
print("=" * 80)


for side_name, local in [

    (
        "bottom",
        BOTTOM_GATE_LOCAL,
    ),

    (
        "top",
        TOP_GATE_LOCAL,
    ),

]:

    terminal = absolute_terminal(
        "SW0",
        local,
    )


    touched = any(

        overlaps(
            terminal,
            shape,
        )

        for shape
        in gate_w1_boxes

    )


    clear = not touched


    print(
        f"GATE_W1 clear of SW0 {side_name}:",
        clear
    )


    WRONG_GATE_CLEAR &= clear


for role in [
    "SW1A",
    "SW1B",
]:

    for side_name, local in [

        (
            "bottom",
            BOTTOM_GATE_LOCAL,
        ),

        (
            "top",
            TOP_GATE_LOCAL,
        ),

    ]:

        terminal = absolute_terminal(
            role,
            local,
        )


        touched = any(

            overlaps(
                terminal,
                shape,
            )

            for shape
            in gate_w0_boxes

        )


        clear = not touched


        print(
            f"GATE_W0 clear of "
            f"{role} {side_name}:",
            clear
        )


        WRONG_GATE_CLEAR &= clear


# ================================================================
# 17. CONTROL NET ISOLATION
# ================================================================

CONTROL_COLLISIONS = 0


for w0_box in gate_w0_boxes:

    for w1_box in gate_w1_boxes:

        if overlaps(
            w0_box,
            w1_box,
        ):

            CONTROL_COLLISIONS += 1


CONTROL_NETS_SEPARATE = (
    CONTROL_COLLISIONS == 0
)


print()
print("=" * 80)
print("GATE_W0 / GATE_W1 ISOLATION")
print("=" * 80)


print(
    "Overlap count:",
    CONTROL_COLLISIONS
)

print(
    "Control nets separate:",
    CONTROL_NETS_SEPARATE
)


# ================================================================
# 18. SWITCH S/D COLLISION AUDIT
# ================================================================

all_control_boxes = (
    gate_w0_boxes
    + gate_w1_boxes
)


SD_CLEAR = True


print()
print("=" * 80)
print("SWITCH S/D COLLISION AUDIT")
print("=" * 80)


for role in SWITCHES:

    left_sd = absolute_terminal(
        role,
        LEFT_SD_LOCAL,
    )

    right_sd = absolute_terminal(
        role,
        RIGHT_SD_LOCAL,
    )


    left_touched = any(

        overlaps(
            left_sd,
            shape,
        )

        for shape
        in all_control_boxes

    )


    right_touched = any(

        overlaps(
            right_sd,
            shape,
        )

        for shape
        in all_control_boxes

    )


    clear = bool(

        not left_touched

        and

        not right_touched

    )


    print(
        f"{role:6s} S/D clear:",
        clear
    )


    SD_CLEAR &= clear


# ================================================================
# 19. RECONSTRUCT EXISTING SIGNAL M1
# ================================================================

existing_signal_m1 = []


# Existing PMOS -> switch bottom M1 routes
for _, data in existing_branches.items():

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

    m2_x = float(
        data[
            "m2_x_um"
        ]
    )


    existing_signal_m1.append(

        make_box_um(

            switch_x
            - M1_HALF,

            switch_y
            - M1_HALF,

            m2_x
            + M1_HALF,

            switch_y
            + M1_HALF,

        )

    )


# Existing VMEM M1 routes
for _, data in existing_vmem.items():

    terminal_x = float(
        data[
            "terminal_center_um"
        ][0]
    )

    terminal_y = float(
        data[
            "terminal_center_um"
        ][1]
    )

    via_x = float(
        data[
            "via_center_um"
        ][0]
    )


    existing_signal_m1.append(

        make_box_um(

            via_x
            - M1_HALF,

            terminal_y
            - M1_HALF,

            terminal_x
            + M1_HALF,

            terminal_y
            + M1_HALF,

        )

    )


# ================================================================
# 20. EXISTING M1 COLLISION / SPACING
# ================================================================

EXISTING_M1_COLLISIONS = 0

minimum_existing_gap = None


for new_box in all_control_boxes:

    for old_box in existing_signal_m1:

        if overlaps(
            new_box,
            old_box,
        ):

            EXISTING_M1_COLLISIONS += 1


        gap = box_distance_um(
            new_box,
            old_box,
        )


        if minimum_existing_gap is None:

            minimum_existing_gap = gap

        else:

            minimum_existing_gap = min(
                minimum_existing_gap,
                gap,
            )


EXISTING_SIGNAL_M1_CLEAR = (
    EXISTING_M1_COLLISIONS == 0
)


EXISTING_SPACING_OK = bool(

    minimum_existing_gap is not None

    and

    minimum_existing_gap
    >= M1_MIN_SPACING

)


print()
print("=" * 80)
print("EXISTING SIGNAL-M1 AUDIT")
print("=" * 80)


print(
    "Control / existing-M1 overlaps:",
    EXISTING_M1_COLLISIONS
)

print(
    "Minimum spacing:",
    f"{minimum_existing_gap:.3f} um"
)

print(
    "Required m1.2:",
    f"{M1_MIN_SPACING:.3f} um"
)

print(
    "Collision clear:",
    EXISTING_SIGNAL_M1_CLEAR
)

print(
    "Spacing pre-check:",
    EXISTING_SPACING_OK
)


# ================================================================
# 21. W1 vs SW0 TOP GATE
# ================================================================

sw0_top = absolute_terminal(
    "SW0",
    TOP_GATE_LOCAL,
)


W1_TO_SW0_TOP_GAP = box_distance_um(
    GATE_W1_BUS,
    sw0_top,
)


W1_SW0_SPACING_OK = (
    W1_TO_SW0_TOP_GAP
    >= M1_MIN_SPACING
)


print()
print("=" * 80)
print("GATE_W1 / SW0 TOP-GATE SPACING")
print("=" * 80)


print(
    "Gap:",
    f"{W1_TO_SW0_TOP_GAP:.3f} um"
)

print(
    "Required:",
    f"{M1_MIN_SPACING:.3f} um"
)

print(
    "Pass:",
    W1_SW0_SPACING_OK
)


# ================================================================
# 22. SHAPE COUNT
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        MET1_LAYER
    ).each()

)


M1_COUNT_OK = (
    TOP_M1_COUNT == 5
)


print()
print("=" * 80)
print("TOP-LEVEL SHAPE AUDIT")
print("=" * 80)


print(
    "Top-level new M1 shapes:",
    TOP_M1_COUNT
)

print(
    "Expected:",
    5
)

print(
    "M1 count correct:",
    M1_COUNT_OK
)


# ================================================================
# 23. USED LAYERS
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
            int(layer_index),
            int(info.layer),
            int(info.datatype),
        )

    )


# ================================================================
# 24. SAVE OPTIONS
# ================================================================

def make_save_options(
    fmt,
):

    options = kdb.SaveLayoutOptions()

    options.format = fmt

    options.deselect_all_layers()


    for (
        internal,
        layer,
        datatype,
    ) in used_layers:

        options.add_layer(

            internal,

            kdb.LayerInfo(
                layer,
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
# 26. READBACK
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
# 27. MANIFEST
# ================================================================

output_manifest = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "revision":
        "weight_gates_v2",

    "top_cell":
        NEW_TOP_NAME,

    "parent_cell":
        INPUT_TOP_NAME,

    "canonical_input":
        "neurolif_synapse_vmem_v1.gds",

    "correction": {

        "reason":
            "Step 24C confirmed two m1.2 violations "
            "at GATE_W0 bus-to-SW0-gate side notches",

        "old_gate_w0_bus_y_um":
            OLD_GATE_W0_BUS_Y,

        "new_gate_w0_bus_y_um":
            GATE_W0_BUS_Y,

        "new_notch_spacing_um":
            round(
                W0_NOTCH_SPACING,
                3,
            ),

        "m1_min_spacing_um":
            M1_MIN_SPACING,

    },

    "routed_nets": [

        "VDD",

        "VBIAS",

        "P_U1A_TO_SW1A",

        "P_U0_TO_SW0",

        "P_U1B_TO_SW1B",

        "VMEM",

        "GATE_W0",

        "GATE_W1",

    ],

    "unrouted_nets": [
        "VSS",
    ],

    "gate_routing": {

        "GATE_W0": {

            "target":
                "SW0",

            "contact":
                "bottom gate",

            "metal":
                "metal1",

            "bus_y_um":
                GATE_W0_BUS_Y,

        },

        "GATE_W1": {

            "targets": [
                "SW1A",
                "SW1B",
            ],

            "contacts":
                "top gates",

            "metal":
                "metal1",

            "bus_y_um":
                GATE_W1_BUS_Y,

        },

    },

    "checks": {

        "w0_notch_spacing":
            W0_NOTCH_OK,

        "w1_notch_spacing":
            W1_NOTCH_OK,

        "target_connections":
            TARGET_CONNECTIONS_OK,

        "wrong_gate_clear":
            WRONG_GATE_CLEAR,

        "control_nets_separate":
            CONTROL_NETS_SEPARATE,

        "switch_sd_clear":
            SD_CLEAR,

        "existing_signal_m1_clear":
            EXISTING_SIGNAL_M1_CLEAR,

        "existing_signal_spacing":
            EXISTING_SPACING_OK,

        "w1_sw0_spacing":
            W1_SW0_SPACING_OK,

        "m1_count":
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
# 28. FINAL GATE
# ================================================================

STEP24D_PASS = bool(

    W0_NOTCH_OK

    and

    W1_NOTCH_OK

    and

    TARGET_CONNECTIONS_OK

    and

    WRONG_GATE_CLEAR

    and

    CONTROL_NETS_SEPARATE

    and

    SD_CLEAR

    and

    EXISTING_SIGNAL_M1_CLEAR

    and

    EXISTING_SPACING_OK

    and

    W1_SW0_SPACING_OK

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
print("STEP 24D RESULT")
print("=" * 80)


print(
    "Corrected W0 notch       :",
    W0_NOTCH_OK
)

print(
    "W1 notch spacing         :",
    W1_NOTCH_OK
)

print(
    "Target gate connections  :",
    TARGET_CONNECTIONS_OK
)

print(
    "Wrong gates clear        :",
    WRONG_GATE_CLEAR
)

print(
    "GATE_W0/W1 separate      :",
    CONTROL_NETS_SEPARATE
)

print(
    "Switch S/D clear         :",
    SD_CLEAR
)

print(
    "Existing M1 clear        :",
    EXISTING_SIGNAL_M1_CLEAR
)

print(
    "Existing M1 spacing      :",
    EXISTING_SPACING_OK
)

print(
    "W1 / SW0 spacing         :",
    W1_SW0_SPACING_OK
)

print(
    "M1 shape audit           :",
    M1_COUNT_OK
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
    "STEP24D_PASS =",
    STEP24D_PASS
)


if not STEP24D_PASS:

    raise RuntimeError(
        "STEP 24D failed."
    )


print()
print(
    "CORRECTED WEIGHT-GATE ROUTING V2 GENERATED"
)

print()
print(
    "GATE_W0 -> SW0"
)

print(
    "GATE_W1 -> SW1A + SW1B"
)

print()
print(
    "Old weight_gates_v1 remains diagnostic only."
)

print()
print(
    "New candidate:"
)

print(
    OUTPUT_GDS
)