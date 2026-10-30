# ================================================================
# NeuroLIF-SKY130
# STEP 17C — Audit corrected nf=1 terminal landings
#
# Checks:
#   - P_SYN_W0840_L0500
#   - N_LOGIC_W1000_L0150
#
# Identifies:
#   - gate finger
#   - diffusion Metal1 landings
#   - gate Metal1 landings
#   - body/well tap geometry
#
# No geometry is modified.
# ================================================================

from pathlib import Path

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 17C: NF1 TERMINAL AUDIT")
print("=" * 80)


# ================================================================
# 1. INPUT
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "primitives"
    / "neurolif_mos_primitives_nf1.gds"
)


TARGET_CELLS = [

    "P_SYN_W0840_L0500",

    "N_LOGIC_W1000_L0150",

]


print()
print(
    "Input GDS:",
    INPUT_GDS
)

print(
    "Exists:",
    INPUT_GDS.exists()
)


if not INPUT_GDS.exists():

    raise FileNotFoundError(
        INPUT_GDS
    )


# ================================================================
# 2. LOAD DATABASE
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)


DBU = layout.dbu


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
    "Cell count:",
    layout.cells()
)


# ================================================================
# 3. SKY130 LAYERS
# ================================================================

L_DIFF = layout.find_layer(
    65,
    20
)

L_TAP = layout.find_layer(
    65,
    44
)

L_POLY = layout.find_layer(
    66,
    20
)

L_MET1 = layout.find_layer(
    68,
    20
)

L_NWELL = layout.find_layer(
    64,
    20
)


# ================================================================
# 4. HELPERS
# ================================================================

def um(
    value,
):

    return (
        value
        * DBU
    )


def center(
    bbox,
):

    return (

        (
            bbox.left
            + bbox.right
        ) / 2.0,

        (
            bbox.bottom
            + bbox.top
        ) / 2.0,

    )


def center_um(
    bbox,
):

    cx, cy = center(
        bbox
    )

    return (
        um(cx),
        um(cy),
    )


def bbox_um(
    bbox,
):

    return (

        um(
            bbox.left
        ),

        um(
            bbox.bottom
        ),

        um(
            bbox.right
        ),

        um(
            bbox.top
        ),

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


def shapes_as_boxes(
    cell,
    layer_index,
):

    if layer_index is None:

        return []


    return [

        shape.bbox()

        for shape
        in cell.shapes(
            layer_index
        ).each()

    ]


# ================================================================
# 5. AUDIT EACH TARGET
# ================================================================

results = {}


for cell_name in TARGET_CELLS:

    print()
    print("=" * 80)
    print(
        "CELL:",
        cell_name
    )
    print("=" * 80)


    cell = layout.cell(
        cell_name
    )


    if cell is None:

        raise RuntimeError(
            f"Missing cell: {cell_name}"
        )


    diff_boxes = shapes_as_boxes(
        cell,
        L_DIFF
    )

    poly_boxes = shapes_as_boxes(
        cell,
        L_POLY
    )

    met1_boxes = shapes_as_boxes(
        cell,
        L_MET1
    )

    tap_boxes = shapes_as_boxes(
        cell,
        L_TAP
    )

    nwell_boxes = shapes_as_boxes(
        cell,
        L_NWELL
    )


    if len(diff_boxes) != 1:

        raise RuntimeError(
            f"{cell_name}: expected exactly "
            f"one diffusion shape, got "
            f"{len(diff_boxes)}"
        )


    diff = diff_boxes[0]


    # ------------------------------------------------------------
    # Find actual gate poly crossing diffusion
    # ------------------------------------------------------------

    gate_poly = [

        poly

        for poly in poly_boxes

        if overlaps(
            poly,
            diff
        )

    ]


    print(
        "DIFF shapes       :",
        len(diff_boxes)
    )

    print(
        "POLY shapes       :",
        len(poly_boxes)
    )

    print(
        "Gate fingers      :",
        len(gate_poly)
    )

    print(
        "MET1 shapes       :",
        len(met1_boxes)
    )

    print(
        "TAP shapes 65/44  :",
        len(tap_boxes)
    )

    print(
        "NWELL shapes      :",
        len(nwell_boxes)
    )


    if len(gate_poly) != 1:

        raise RuntimeError(
            f"{cell_name}: expected one "
            f"physical gate finger."
        )


    gate = gate_poly[0]


    print()
    print(
        "Gate poly bbox:",
        tuple(
            round(
                value,
                3
            )

            for value
            in bbox_um(
                gate
            )
        ),
        "um"
    )


    # ------------------------------------------------------------
    # Classify Metal1
    #
    # Any M1 overlapping diffusion = source/drain landing.
    # Remaining M1 shapes = gate landing(s).
    # ------------------------------------------------------------

    diffusion_m1 = []

    gate_m1 = []


    for box in met1_boxes:

        if overlaps(
            box,
            diff
        ):

            diffusion_m1.append(
                box
            )

        else:

            gate_m1.append(
                box
            )


    diffusion_m1.sort(
        key=lambda box: center(
            box
        )
    )

    gate_m1.sort(
        key=lambda box: center(
            box
        )
    )


    print()
    print(
        "DIFFUSION MET1 LANDINGS"
    )

    print(
        "-" * 80
    )


    for index, box in enumerate(
        diffusion_m1,
        start=1,
    ):

        cx, cy = center_um(
            box
        )

        print(

            f"D{index}: "

            f"center=({cx:.3f}, "
            f"{cy:.3f}) um | "

            f"bbox="
            f"{tuple(round(v, 3) for v in bbox_um(box))}"

        )


    print()
    print(
        "GATE MET1 LANDINGS"
    )

    print(
        "-" * 80
    )


    for index, box in enumerate(
        gate_m1,
        start=1,
    ):

        cx, cy = center_um(
            box
        )

        print(

            f"G{index}: "

            f"center=({cx:.3f}, "
            f"{cy:.3f}) um | "

            f"bbox="
            f"{tuple(round(v, 3) for v in bbox_um(box))}"

        )


    # ------------------------------------------------------------
    # Identify left/right diffusion landing
    # ------------------------------------------------------------

    if len(
        diffusion_m1
    ) == 2:

        diffusion_m1.sort(
            key=lambda box:
                center(box)[0]
        )


        left_sd = diffusion_m1[
            0
        ]

        right_sd = diffusion_m1[
            1
        ]


        left_cx, left_cy = (
            center_um(
                left_sd
            )
        )

        right_cx, right_cy = (
            center_um(
                right_sd
            )
        )


        print()
        print(
            "SYMMETRIC S/D ACCESS"
        )

        print(
            "-" * 80
        )

        print(

            "LEFT_SD  : "

            f"({left_cx:.3f}, "
            f"{left_cy:.3f}) um"

        )

        print(

            "RIGHT_SD : "

            f"({right_cx:.3f}, "
            f"{right_cy:.3f}) um"

        )


    # ------------------------------------------------------------
    # Gate contact positional classification
    # ------------------------------------------------------------

    print()
    print(
        "GATE ACCESS POSITION"
    )

    print(
        "-" * 80
    )


    diff_cx, diff_cy = center(
        diff
    )


    gate_positions = []


    for box in gate_m1:

        cx, cy = center(
            box
        )


        if cy > diff.top:

            position = "TOP"

        elif cy < diff.bottom:

            position = "BOTTOM"

        elif cx < diff.left:

            position = "LEFT"

        elif cx > diff.right:

            position = "RIGHT"

        else:

            position = "OTHER"


        gate_positions.append(
            position
        )


        cx_um, cy_um = center_um(
            box
        )


        print(

            f"{position:7s} "

            f"({cx_um:.3f}, "
            f"{cy_um:.3f}) um"

        )


    # ------------------------------------------------------------
    # Body/well observation
    # ------------------------------------------------------------

    print()
    print(
        "BODY / WELL OBSERVATION"
    )

    print(
        "-" * 80
    )


    if nwell_boxes:

        print(
            "NWELL present : YES"
        )

    else:

        print(
            "NWELL present : NO"
        )


    if tap_boxes:

        print(
            "TAP geometry  : PRESENT"
        )

    else:

        print(
            "TAP geometry  : NOT PRESENT"
        )


    results[
        cell_name
    ] = {

        "gate_fingers":
            len(
                gate_poly
            ),

        "met1_total":
            len(
                met1_boxes
            ),

        "diffusion_m1":
            len(
                diffusion_m1
            ),

        "gate_m1":
            len(
                gate_m1
            ),

        "tap_shapes":
            len(
                tap_boxes
            ),

        "nwell_shapes":
            len(
                nwell_boxes
            ),

        "gate_positions":
            gate_positions,

    }


# ================================================================
# 6. FINAL EXPECTATION CHECK
#
# Correct nf=1 transistor geometry should expose:
#
#   2 diffusion M1 landings
#   2 gate M1 landings
#
# Gate can be contacted from top and bottom.
# ================================================================

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)


for cell_name, data in results.items():

    print()

    print(
        cell_name
    )

    print(
        "  gate fingers   :",
        data[
            "gate_fingers"
        ]
    )

    print(
        "  MET1 total     :",
        data[
            "met1_total"
        ]
    )

    print(
        "  diffusion M1   :",
        data[
            "diffusion_m1"
        ]
    )

    print(
        "  gate M1        :",
        data[
            "gate_m1"
        ]
    )

    print(
        "  TAP shapes     :",
        data[
            "tap_shapes"
        ]
    )

    print(
        "  NWELL shapes   :",
        data[
            "nwell_shapes"
        ]
    )

    print(
        "  gate positions :",
        data[
            "gate_positions"
        ]
    )


P_SYN_OK = (

    results[
        "P_SYN_W0840_L0500"
    ][
        "gate_fingers"
    ] == 1

    and

    results[
        "P_SYN_W0840_L0500"
    ][
        "diffusion_m1"
    ] == 2

    and

    results[
        "P_SYN_W0840_L0500"
    ][
        "gate_m1"
    ] == 2

)


N_LOGIC_OK = (

    results[
        "N_LOGIC_W1000_L0150"
    ][
        "gate_fingers"
    ] == 1

    and

    results[
        "N_LOGIC_W1000_L0150"
    ][
        "diffusion_m1"
    ] == 2

    and

    results[
        "N_LOGIC_W1000_L0150"
    ][
        "gate_m1"
    ] == 2

)


STEP17C_PASS = bool(

    P_SYN_OK

    and

    N_LOGIC_OK

)


print()
print("=" * 80)
print("STEP 17C RESULT")
print("=" * 80)


print(
    "P_SYN terminal geometry :",
    P_SYN_OK
)

print(
    "N_LOGIC terminal geometry:",
    N_LOGIC_OK
)

print(
    "STEP17C_PASS            :",
    STEP17C_PASS
)


if not STEP17C_PASS:

    raise RuntimeError(
        "Corrected terminal geometry did not "
        "match expected nf=1 structure."
    )


print()
print(
    "Canonical primitive terminal audit: PASS"
)

print()
print(
    "NOTE:"
)

print(
    "LEFT_SD and RIGHT_SD are intentionally "
    "not yet labelled source versus drain."
)

print(
    "The MOS diffusion terminals are physically "
    "symmetric here; circuit connectivity will "
    "assign their roles during placement/routing."
)