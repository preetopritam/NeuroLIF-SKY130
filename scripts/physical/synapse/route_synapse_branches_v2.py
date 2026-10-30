# ================================================================
# NeuroLIF-SKY130
# STEP 22D — Corrected PMOS -> switch branches V2
#
# Root cause from Step 22C:
#
#   old VIA_X_OFFSET = 0.500 um
#   PMOS drain right edge = x + 0.115
#   via pad left edge      = via_x - 0.250
#
#   resulting notch = 0.135 um
#   m1.2 minimum    = 0.140 um
#
# Correction:
#
#   VIA_X_OFFSET = 0.600 um
#
# resulting PMOS-side notch:
#
#   0.235 um > 0.140 um
#
# IMPORTANT:
#   Build from last DRC-clean VDD+VBIAS file,
#   NOT from failing branches_v1.
# ================================================================

from pathlib import Path
import json
import sys

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 22D: CORRECTED BRANCHES V2")
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

# Last known-clean circuit-level GDS.
INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vbias_v1.gds"
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
    / "neurolif_synapse_branches_v2.gds"
)

OUTPUT_OAS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_branches_v2.oas"
)

OUTPUT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_branches_v2.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VBIAS_V1"
)

NEW_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_BRANCHES_V2"
)

P_SYN_NAME = (
    "P_SYN_W0840_L0500"
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
    SKY130_PYTHON_ROOT,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


if str(
    SKY130_PYTHON_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            SKY130_PYTHON_ROOT
        )
    )


from cells.via_generator import (
    vias_gen_draw,
)


# ================================================================
# 2. LOAD CLEAN VDD + VBIAS DATABASE
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

p_syn = layout.cell(
    P_SYN_NAME
)

n_switch = layout.cell(
    N_SWITCH_NAME
)


if input_top is None:

    raise RuntimeError(
        f"Missing top cell: {INPUT_TOP_NAME}"
    )


if p_syn is None:

    raise RuntimeError(
        f"Missing primitive: {P_SYN_NAME}"
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
    "Clean input top:",
    INPUT_TOP_NAME
)

print(
    "Failing branches_v1 is NOT used as input."
)


# ================================================================
# 3. LOAD PLACEMENT DATA
# ================================================================

placement_data = json.loads(

    PLACEMENT_MANIFEST.read_text(
        encoding="utf-8"
    )

)


placements = placement_data[
    "placement_um"
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


def box_um(
    box,
):

    return (

        box.left * DBU,

        box.bottom * DBU,

        box.right * DBU,

        box.top * DBU,

    )


# ================================================================
# 6. TERMINAL EXTRACTION
# ================================================================

def extract_terminals(
    cell,
):

    diff_boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            DIFF_LAYER
        ).each()

    ]


    m1_boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            MET1_LAYER
        ).each()

    ]


    if len(
        diff_boxes
    ) != 1:

        raise RuntimeError(
            f"{cell.name}: expected one DIFF region."
        )


    diff = diff_boxes[
        0
    ]


    sd = [

        box

        for box
        in m1_boxes

        if overlaps(
            box,
            diff,
        )

    ]


    gates = [

        box

        for box
        in m1_boxes

        if not overlaps(
            box,
            diff,
        )

    ]


    sd.sort(
        key=lambda box:
            center(
                box
            )[0]
    )


    gates.sort(
        key=lambda box:
            center(
                box
            )[1]
    )


    if len(
        sd
    ) != 2:

        raise RuntimeError(
            f"{cell.name}: expected two S/D M1 landings."
        )


    if len(
        gates
    ) != 2:

        raise RuntimeError(
            f"{cell.name}: expected two gate M1 landings."
        )


    return {

        "left_sd":
            sd[0],

        "right_sd":
            sd[1],

        "bottom_gate":
            gates[0],

        "top_gate":
            gates[1],

    }


p_term_local = extract_terminals(
    p_syn
)

n_term_local = extract_terminals(
    n_switch
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


# ================================================================
# 8. BRANCH MAP
# ================================================================

BRANCHES = [

    (
        "P_U1A",
        "SW1A",
    ),

    (
        "P_U0",
        "SW0",
    ),

    (
        "P_U1B",
        "SW1B",
    ),

]


# ================================================================
# 9. VALIDATED VIA CELL
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
    "Via bbox:",
    via_cell.bbox()
)

print(
    "Status from Step 21B: DRC CLEAN"
)


# ================================================================
# 10. NEW TOP
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
# 11. ROUTING PARAMETERS
# ================================================================

M1_ROUTE_WIDTH = 0.230

M2_ROUTE_WIDTH = 0.300

VIA_SIZE = 0.500

VIA_HALF = (
    VIA_SIZE / 2.0
)


# ================================================================
# CRITICAL CORRECTION
# ================================================================

OLD_VIA_X_OFFSET = 0.500

VIA_X_OFFSET = 0.600


M1_MIN_SPACING = 0.140


print()
print("=" * 80)
print("STEP 22C CORRECTION")
print("=" * 80)

print(
    "Old VIA_X_OFFSET:",
    OLD_VIA_X_OFFSET,
    "um"
)

print(
    "New VIA_X_OFFSET:",
    VIA_X_OFFSET,
    "um"
)

print(
    "Required m1.2 spacing:",
    M1_MIN_SPACING,
    "um"
)


# ================================================================
# 12. RECONSTRUCT FROZEN VDD GEOMETRY
# ================================================================

PMOS_ROLES = [

    "P_U1A",

    "P_REF",

    "P_U0",

    "P_U1B",

]


vdd_boxes = []


VDD_RAIL_CENTER_Y = 10.000

VDD_RAIL_WIDTH = 0.400

VDD_SOURCE_WIDTH = 0.230

VDD_ESCAPE_OFFSET_X = 0.500


vdd_escape_x = []


for role in PMOS_ROLES:

    source_box = absolute_terminal(

        role,

        p_term_local[
            "left_sd"
        ],

    )


    cx_dbu, cy_dbu = center(
        source_box
    )


    cx = (
        cx_dbu
        * DBU
    )

    cy = (
        cy_dbu
        * DBU
    )


    escape_x = (
        cx
        - VDD_ESCAPE_OFFSET_X
    )


    vdd_escape_x.append(
        escape_x
    )


    vdd_boxes.append(

        make_box_um(

            escape_x
            - VDD_SOURCE_WIDTH / 2.0,

            cy
            - VDD_SOURCE_WIDTH / 2.0,

            cx
            + VDD_SOURCE_WIDTH / 2.0,

            cy
            + VDD_SOURCE_WIDTH / 2.0,

        )

    )


    vdd_boxes.append(

        make_box_um(

            escape_x
            - VDD_SOURCE_WIDTH / 2.0,

            cy
            - VDD_SOURCE_WIDTH / 2.0,

            escape_x
            + VDD_SOURCE_WIDTH / 2.0,

            VDD_RAIL_CENTER_Y
            + VDD_RAIL_WIDTH / 2.0,

        )

    )


VDD_TAP_CX = -2.000

VDD_TAP_CY = 8.500


vdd_boxes.append(

    make_box_um(

        VDD_TAP_CX
        - 0.200,

        VDD_TAP_CY
        - 0.200,

        VDD_TAP_CX
        + 0.200,

        VDD_RAIL_CENTER_Y
        + VDD_RAIL_WIDTH / 2.0,

    )

)


vdd_boxes.append(

    make_box_um(

        min(
            VDD_TAP_CX,
            *vdd_escape_x
        ) - 0.200,

        VDD_RAIL_CENTER_Y
        - VDD_RAIL_WIDTH / 2.0,

        max(
            vdd_escape_x
        ) + 0.200,

        VDD_RAIL_CENTER_Y
        + VDD_RAIL_WIDTH / 2.0,

    )

)


# ================================================================
# 13. RECONSTRUCT FROZEN VBIAS GEOMETRY
# ================================================================

vbias_boxes = []


VBIAS_BUS_Y = 6.800

VBIAS_WIDTH = 0.230


vbias_boxes.append(

    make_box_um(

        0.300,

        VBIAS_BUS_Y
        - VBIAS_WIDTH / 2.0,

        9.800,

        VBIAS_BUS_Y
        + VBIAS_WIDTH / 2.0,

    )

)


for role in PMOS_ROLES:

    gate_box = absolute_terminal(

        role,

        p_term_local[
            "bottom_gate"
        ],

    )


    gx_dbu, gy_dbu = center(
        gate_box
    )


    gx = (
        gx_dbu
        * DBU
    )

    gy = (
        gy_dbu
        * DBU
    )


    vbias_boxes.append(

        make_box_um(

            gx
            - VBIAS_WIDTH / 2.0,

            VBIAS_BUS_Y
            - VBIAS_WIDTH / 2.0,

            gx
            + VBIAS_WIDTH / 2.0,

            gy
            + VBIAS_WIDTH / 2.0,

        )

    )


pref_drain = absolute_terminal(

    "P_REF",

    p_term_local[
        "right_sd"
    ],

)


pref_cx_dbu, pref_cy_dbu = center(
    pref_drain
)


pref_cx = (
    pref_cx_dbu
    * DBU
)

pref_cy = (
    pref_cy_dbu
    * DBU
)


PREF_ESCAPE_X = 4.450


vbias_boxes.append(

    make_box_um(

        pref_cx
        - VBIAS_WIDTH / 2.0,

        pref_cy
        - VBIAS_WIDTH / 2.0,

        PREF_ESCAPE_X
        + VBIAS_WIDTH / 2.0,

        pref_cy
        + VBIAS_WIDTH / 2.0,

    )

)


vbias_boxes.append(

    make_box_um(

        PREF_ESCAPE_X
        - VBIAS_WIDTH / 2.0,

        VBIAS_BUS_Y
        - VBIAS_WIDTH / 2.0,

        PREF_ESCAPE_X
        + VBIAS_WIDTH / 2.0,

        pref_cy
        + VBIAS_WIDTH / 2.0,

    )

)


# ================================================================
# 14. ROUTE CORRECTED BRANCHES
# ================================================================

new_m1_boxes = []

new_m2_boxes = []

via_pad_boxes = []

branch_manifest = {}

notch_results = []


print()
print("=" * 80)
print("CORRECTED PMOS -> SWITCH BRANCHES")
print("=" * 80)


for pmos_role, sw_role in BRANCHES:

    pmos_drain = absolute_terminal(

        pmos_role,

        p_term_local[
            "right_sd"
        ],

    )


    pdx_dbu, pdy_dbu = center(
        pmos_drain
    )


    pmos_x = (
        pdx_dbu
        * DBU
    )

    pmos_y = (
        pdy_dbu
        * DBU
    )


    sw_input = absolute_terminal(

        sw_role,

        n_term_local[
            "right_sd"
        ],

    )


    six_dbu, siy_dbu = center(
        sw_input
    )


    switch_x = (
        six_dbu
        * DBU
    )

    switch_y = (
        siy_dbu
        * DBU
    )


    # Corrected transition X.
    via_x = (
        pmos_x
        + VIA_X_OFFSET
    )


    # ------------------------------------------------------------
    # Explicit PMOS-side notch calculation
    # ------------------------------------------------------------

    pmos_drain_right = (
        pmos_drain.right
        * DBU
    )

    top_pad_left = (
        via_x
        - VIA_HALF
    )

    top_notch = (
        top_pad_left
        - pmos_drain_right
    )


    top_notch_ok = (
        top_notch
        >= M1_MIN_SPACING
    )


    # ------------------------------------------------------------
    # Explicit switch-side notch calculation
    # ------------------------------------------------------------

    switch_input_right = (
        sw_input.right
        * DBU
    )

    bottom_pad_left = (
        via_x
        - VIA_HALF
    )

    bottom_notch = (
        bottom_pad_left
        - switch_input_right
    )


    bottom_notch_ok = (
        bottom_notch
        >= M1_MIN_SPACING
    )


    notch_results.extend(
        [
            top_notch_ok,
            bottom_notch_ok,
        ]
    )


    # ------------------------------------------------------------
    # PMOS M1 escape
    # ------------------------------------------------------------

    top_m1 = make_box_um(

        pmos_x
        - M1_ROUTE_WIDTH / 2.0,

        pmos_y
        - M1_ROUTE_WIDTH / 2.0,

        via_x
        + M1_ROUTE_WIDTH / 2.0,

        pmos_y
        + M1_ROUTE_WIDTH / 2.0,

    )


    # ------------------------------------------------------------
    # NMOS M1 escape
    # ------------------------------------------------------------

    bottom_m1 = make_box_um(

        switch_x
        - M1_ROUTE_WIDTH / 2.0,

        switch_y
        - M1_ROUTE_WIDTH / 2.0,

        via_x
        + M1_ROUTE_WIDTH / 2.0,

        switch_y
        + M1_ROUTE_WIDTH / 2.0,

    )


    # ------------------------------------------------------------
    # M2 vertical
    # ------------------------------------------------------------

    m2_vertical = make_box_um(

        via_x
        - M2_ROUTE_WIDTH / 2.0,

        switch_y
        - VIA_HALF,

        via_x
        + M2_ROUTE_WIDTH / 2.0,

        pmos_y
        + VIA_HALF,

    )


    # ------------------------------------------------------------
    # Via pad audit boxes
    # ------------------------------------------------------------

    top_pad = make_box_um(

        via_x
        - VIA_HALF,

        pmos_y
        - VIA_HALF,

        via_x
        + VIA_HALF,

        pmos_y
        + VIA_HALF,

    )


    bottom_pad = make_box_um(

        via_x
        - VIA_HALF,

        switch_y
        - VIA_HALF,

        via_x
        + VIA_HALF,

        switch_y
        + VIA_HALF,

    )


    # ------------------------------------------------------------
    # Add route geometry
    # ------------------------------------------------------------

    top.shapes(
        MET1_LAYER
    ).insert(
        top_m1
    )


    top.shapes(
        MET1_LAYER
    ).insert(
        bottom_m1
    )


    top.shapes(
        MET2_LAYER
    ).insert(
        m2_vertical
    )


    # ------------------------------------------------------------
    # Top M1-M2 transition
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
                    pmos_y
                    - VIA_HALF
                ),

            ),

        )

    )


    # ------------------------------------------------------------
    # Bottom M1-M2 transition
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
                    switch_y
                    - VIA_HALF
                ),

            ),

        )

    )


    new_m1_boxes.extend(
        [
            top_m1,
            bottom_m1,
        ]
    )


    new_m2_boxes.append(
        m2_vertical
    )


    via_pad_boxes.extend(
        [
            top_pad,
            bottom_pad,
        ]
    )


    branch_manifest[
        f"{pmos_role}_TO_{sw_role}"
    ] = {

        "pmos_drain_center_um": [
            round(
                pmos_x,
                3,
            ),
            round(
                pmos_y,
                3,
            ),
        ],

        "switch_input_center_um": [
            round(
                switch_x,
                3,
            ),
            round(
                switch_y,
                3,
            ),
        ],

        "m2_x_um":
            round(
                via_x,
                3,
            ),

        "pmos_side_notch_um":
            round(
                top_notch,
                3,
            ),

        "pmos_side_notch_pass":
            top_notch_ok,

        "switch_side_notch_um":
            round(
                bottom_notch,
                3,
            ),

        "switch_side_notch_pass":
            bottom_notch_ok,

    }


    print()
    print(
        f"{pmos_role} -> {sw_role}"
    )

    print(
        f"  PMOS drain center   : "
        f"({pmos_x:.3f}, "
        f"{pmos_y:.3f}) um"
    )

    print(
        f"  Switch input center : "
        f"({switch_x:.3f}, "
        f"{switch_y:.3f}) um"
    )

    print(
        f"  Corrected M2 X      : "
        f"{via_x:.3f} um"
    )

    print(
        f"  PMOS notch          : "
        f"{top_notch:.3f} um "
        f"(pass={top_notch_ok})"
    )

    print(
        f"  Switch notch        : "
        f"{bottom_notch:.3f} um "
        f"(pass={bottom_notch_ok})"
    )


NOTCH_AUDIT_OK = all(
    notch_results
)


# ================================================================
# 15. TERMINAL CONNECTIVITY AUDIT
# ================================================================

TERMINAL_CONNECTIONS_OK = True


print()
print("=" * 80)
print("TERMINAL CONNECTIVITY AUDIT")
print("=" * 80)


for index, (
    pmos_role,
    sw_role,
) in enumerate(
    BRANCHES
):

    pmos_drain = absolute_terminal(

        pmos_role,

        p_term_local[
            "right_sd"
        ],

    )


    sw_input = absolute_terminal(

        sw_role,

        n_term_local[
            "right_sd"
        ],

    )


    top_route = new_m1_boxes[
        index * 2
    ]

    bottom_route = new_m1_boxes[
        index * 2 + 1
    ]


    pmos_ok = overlaps(
        pmos_drain,
        top_route,
    )


    switch_ok = overlaps(
        sw_input,
        bottom_route,
    )


    print(
        f"{pmos_role:6s} drain touched:",
        pmos_ok
    )

    print(
        f"{sw_role:6s} input touched:",
        switch_ok
    )


    TERMINAL_CONNECTIONS_OK &= (
        pmos_ok
        and
        switch_ok
    )


# ================================================================
# 16. VMEM TERMINALS REMAIN CLEAR
# ================================================================

VMEM_CLEAR = True


print()
print("=" * 80)
print("RESERVED VMEM TERMINAL AUDIT")
print("=" * 80)


for _, sw_role in BRANCHES:

    vmem_terminal = absolute_terminal(

        sw_role,

        n_term_local[
            "left_sd"
        ],

    )


    touched = any(

        overlaps(
            vmem_terminal,
            route,
        )

        for route
        in (
            new_m1_boxes
            + via_pad_boxes
        )

    )


    clear = not touched


    print(
        f"{sw_role:6s} left diffusion clear:",
        clear
    )


    VMEM_CLEAR &= clear


# ================================================================
# 17. NMOS GATES REMAIN CLEAR
# ================================================================

NMOS_GATES_CLEAR = True


print()
print("=" * 80)
print("NMOS GATE COLLISION AUDIT")
print("=" * 80)


for _, sw_role in BRANCHES:

    gates = [

        absolute_terminal(
            sw_role,
            n_term_local[
                "bottom_gate"
            ],
        ),

        absolute_terminal(
            sw_role,
            n_term_local[
                "top_gate"
            ],
        ),

    ]


    touched = any(

        overlaps(
            gate,
            route,
        )

        for gate
        in gates

        for route
        in (
            new_m1_boxes
            + via_pad_boxes
        )

    )


    clear = not touched


    print(
        f"{sw_role:6s} gates clear:",
        clear
    )


    NMOS_GATES_CLEAR &= clear


# ================================================================
# 18. PMOS RESERVED TERMINALS CLEAR
# ================================================================

PMOS_RESERVED_CLEAR = True


print()
print("=" * 80)
print("PMOS RESERVED TERMINAL AUDIT")
print("=" * 80)


for pmos_role, _ in BRANCHES:

    reserved = [

        absolute_terminal(
            pmos_role,
            p_term_local[
                "left_sd"
            ],
        ),

        absolute_terminal(
            pmos_role,
            p_term_local[
                "bottom_gate"
            ],
        ),

        absolute_terminal(
            pmos_role,
            p_term_local[
                "top_gate"
            ],
        ),

    ]


    touched = any(

        overlaps(
            terminal,
            route,
        )

        for terminal
        in reserved

        for route
        in (
            new_m1_boxes
            + via_pad_boxes
        )

    )


    clear = not touched


    print(
        f"{pmos_role:6s} reserved clear:",
        clear
    )


    PMOS_RESERVED_CLEAR &= clear


# ================================================================
# 19. FROZEN VDD COLLISION AUDIT
# ================================================================

VDD_COLLISIONS = 0


for new_box in (
    new_m1_boxes
    + via_pad_boxes
):

    for old_box in vdd_boxes:

        if overlaps(
            new_box,
            old_box,
        ):

            VDD_COLLISIONS += 1


VDD_CLEAR = (
    VDD_COLLISIONS == 0
)


print()
print("=" * 80)
print("FROZEN VDD COLLISION AUDIT")
print("=" * 80)

print(
    "New M1 / VDD overlaps:",
    VDD_COLLISIONS
)

print(
    "VDD remains isolated:",
    VDD_CLEAR
)


# ================================================================
# 20. FROZEN VBIAS SAME-LAYER AUDIT
# ================================================================

VBIAS_COLLISIONS = 0


for new_box in (
    new_m1_boxes
    + via_pad_boxes
):

    for old_box in vbias_boxes:

        if overlaps(
            new_box,
            old_box,
        ):

            VBIAS_COLLISIONS += 1


VBIAS_CLEAR = (
    VBIAS_COLLISIONS == 0
)


print()
print("=" * 80)
print("FROZEN VBIAS SAME-LAYER COLLISION AUDIT")
print("=" * 80)

print(
    "New M1 / VBIAS overlaps:",
    VBIAS_COLLISIONS
)

print(
    "M1 isolated from VBIAS:",
    VBIAS_CLEAR
)


# ================================================================
# 21. M2 CROSSING INFORMATION
# ================================================================

VBIAS_BUS_BOX = vbias_boxes[
    0
]


print()
print("=" * 80)
print("M2 / VBIAS CROSSING AUDIT")
print("=" * 80)


for index, (
    pmos_role,
    sw_role,
) in enumerate(
    BRANCHES
):

    crosses = overlaps(

        new_m2_boxes[
            index
        ],

        VBIAS_BUS_BOX,

    )


    print(
        f"{pmos_role:6s} -> "
        f"{sw_role:6s} crosses VBIAS XY region:",
        crosses
    )


# ================================================================
# 22. SHAPE COUNTS
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
    TOP_M1_COUNT == 6
)

M2_COUNT_OK = (
    TOP_M2_COUNT == 3
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
    VIA_INSTANCE_COUNT == 6
)


print()
print("=" * 80)
print("SHAPE / INSTANCE AUDIT")
print("=" * 80)

print(
    "Top-level M1:",
    TOP_M1_COUNT,
    "(expected 6)"
)

print(
    "Top-level M2:",
    TOP_M2_COUNT,
    "(expected 3)"
)

print(
    "Via instances:",
    VIA_INSTANCE_COUNT,
    "(expected 6)"
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
# 24. SAVE OPTIONS
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
        "branches_v2",

    "top_cell":
        NEW_TOP_NAME,

    "parent_cell":
        INPUT_TOP_NAME,

    "correction": {

        "reason":
            "Step 22C confirmed six m1.2 notch-spacing "
            "violations at PMOS-side M1/via transitions",

        "old_via_x_offset_um":
            OLD_VIA_X_OFFSET,

        "new_via_x_offset_um":
            VIA_X_OFFSET,

        "m1_min_spacing_um":
            M1_MIN_SPACING,

    },

    "routed_nets": [

        "VDD",

        "VBIAS",

        "P_U1A_TO_SW1A",

        "P_U0_TO_SW0",

        "P_U1B_TO_SW1B",

    ],

    "unrouted_nets": [

        "GATE_W0",

        "GATE_W1",

        "VMEM",

        "VSS",

    ],

    "branches":
        branch_manifest,

    "checks": {

        "notch_spacing":
            NOTCH_AUDIT_OK,

        "terminal_connections":
            TERMINAL_CONNECTIONS_OK,

        "vmem_clear":
            VMEM_CLEAR,

        "nmos_gates_clear":
            NMOS_GATES_CLEAR,

        "pmos_reserved_clear":
            PMOS_RESERVED_CLEAR,

        "vdd_clear":
            VDD_CLEAR,

        "vbias_clear":
            VBIAS_CLEAR,

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
# 28. FINAL GATE
# ================================================================

STEP22D_PASS = bool(

    NOTCH_AUDIT_OK

    and

    TERMINAL_CONNECTIONS_OK

    and

    VMEM_CLEAR

    and

    NMOS_GATES_CLEAR

    and

    PMOS_RESERVED_CLEAR

    and

    VDD_CLEAR

    and

    VBIAS_CLEAR

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
print("STEP 22D RESULT")
print("=" * 80)


print(
    "Corrected notch spacing :",
    NOTCH_AUDIT_OK
)

print(
    "Terminal connections    :",
    TERMINAL_CONNECTIONS_OK
)

print(
    "VMEM terminals clear    :",
    VMEM_CLEAR
)

print(
    "NMOS gates clear        :",
    NMOS_GATES_CLEAR
)

print(
    "PMOS reserved clear     :",
    PMOS_RESERVED_CLEAR
)

print(
    "Frozen VDD clear        :",
    VDD_CLEAR
)

print(
    "Frozen VBIAS clear      :",
    VBIAS_CLEAR
)

print(
    "M1 shape audit          :",
    M1_COUNT_OK
)

print(
    "M2 shape audit          :",
    M2_COUNT_OK
)

print(
    "Via instance audit      :",
    VIA_COUNT_OK
)

print(
    "GDS write               :",
    GDS_OK
)

print(
    "OASIS write             :",
    OAS_OK
)

print(
    "GDS read-back           :",
    READBACK_OK
)

print(
    "Manifest write          :",
    MANIFEST_OK
)

print()
print(
    "STEP22D_PASS =",
    STEP22D_PASS
)


if not STEP22D_PASS:

    raise RuntimeError(
        "STEP 22D failed."
    )


print()
print(
    "CORRECTED THREE-BRANCH ROUTING GENERATED"
)

print()
print(
    "Old failing branches_v1 remains unchanged."
)

print(
    "New candidate: branches_v2"
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)