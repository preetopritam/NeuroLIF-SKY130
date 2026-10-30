# ================================================================
# NeuroLIF-SKY130
# STEP 30E — VDD completeness repair V3
#
# Reason:
#
# Frozen full-neuron reference contains:
#
#   MN_FB VDD VRAW N_MID VSS
#
# Therefore MN_FB drain must connect to VDD.
#
# VDD V2 was geometrically/DRC clean but omitted this connection.
#
# Input:
#   neurolif_full_neuron_vdd_v2.gds
#
# Adds ONLY:
#   MN_FB right diffusion (drain) -> existing VDD rail
#
# Routing:
#   drain -> RIGHT 0.600 um escape -> vertical to VDD rail
#
# No VSS or signal routing is introduced.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 30E: VDD COMPLETENESS REPAIR V3")
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
    / "neurolif_full_neuron_vdd_v2.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v2.json"
)

REFERENCE_SPICE = (
    NEURON_DIR
    / "neurolif_full_neuron_reference_v1.spice"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v3.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v3.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vdd_v3.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VDD_V2"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VDD_V3"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
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

    with path.open(
        "rb"
    ) as handle:

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
# 3. CONFIRM REFERENCE REQUIRES MN_FB DRAIN -> VDD
# ================================================================

reference_text = REFERENCE_SPICE.read_text(

    encoding="utf-8",

    errors="replace",

)


REFERENCE_MN_FB_OK = (

    "MN_FB VDD VRAW N_MID VSS"
    in reference_text

)


print()
print("=" * 80)
print("REFERENCE TOPOLOGY CHECK")
print("=" * 80)

print(
    "MN_FB D=VDD requirement found:",
    REFERENCE_MN_FB_OK
)


if not REFERENCE_MN_FB_OK:

    raise RuntimeError(
        "Frozen reference does not contain expected MN_FB topology."
    )


# ================================================================
# 4. LOAD VDD V2
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
# 5. REQUIRED CELLS / LAYER
# ================================================================

N_FB_NAME = (
    "N_FB_W0420_L0300"
)

P_FB_NAME = (
    "P_FB_W0420_L0300"
)

P_LOGIC_NAME = (
    "P_LOGIC_W2000_L0150"
)


n_fb = layout.cell(
    N_FB_NAME
)

p_fb = layout.cell(
    P_FB_NAME
)

p_logic = layout.cell(
    P_LOGIC_NAME
)


for name, cell in [

    (
        N_FB_NAME,
        n_fb,
    ),

    (
        P_FB_NAME,
        p_fb,
    ),

    (
        P_LOGIC_NAME,
        p_logic,
    ),

]:

    if cell is None:

        raise RuntimeError(
            f"Missing required cell: {name}"
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


def probe_region(
    x,
    y,
    half=0.010,
):

    return kdb.Region(

        kdb.Box(

            to_dbu(
                x - half
            ),

            to_dbu(
                y - half
            ),

            to_dbu(
                x + half
            ),

            to_dbu(
                y + half
            ),

        )

    )


def horizontal_gap_um(
    a,
    b,
):

    if a.right < b.left:

        return to_um(
            b.left
            -
            a.right
        )

    if b.right < a.left:

        return to_um(
            a.left
            -
            b.right
        )

    return 0.0


# ================================================================
# 7. TERMINAL EXTRACTION
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


N_FB_TERMS = primitive_terminal_boxes(
    n_fb
)

P_FB_TERMS = primitive_terminal_boxes(
    p_fb
)

P_LOGIC_TERMS = primitive_terminal_boxes(
    p_logic
)


print()
print("=" * 80)
print("N_FB TERMINAL GEOMETRY")
print("=" * 80)


for name, box in N_FB_TERMS.items():

    print(
        f"{name:12s}",
        "bbox_um=(",
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
        ")",
        "center=",
        tuple(
            round(
                value,
                3
            )

            for value
            in center_um(
                box
            )
        ),
    )


# ================================================================
# 8. FROZEN PLACEMENT ORIGINS
# ================================================================

ORIGINS = {

    "MN_FB":
        (
            24.0,
            7.0,
        ),

    "MP_FB":
        (
            24.0,
            14.0,
        ),

    "MP_BUF":
        (
            28.0,
            14.0,
        ),

}


# ================================================================
# 9. MN_FB DRAIN
#
# Frozen physical convention:
#
#   LEFT_SD  = source = N_MID
#   RIGHT_SD = drain  = VDD
# ================================================================

MN_FB_SOURCE_BOX = translate_box(

    N_FB_TERMS[
        "LEFT_SD"
    ],

    ORIGINS[
        "MN_FB"
    ],

)


MN_FB_DRAIN_BOX = translate_box(

    N_FB_TERMS[
        "RIGHT_SD"
    ],

    ORIGINS[
        "MN_FB"
    ],

)


MN_FB_GATE_B_BOX = translate_box(

    N_FB_TERMS[
        "BOTTOM_GATE"
    ],

    ORIGINS[
        "MN_FB"
    ],

)


MN_FB_GATE_T_BOX = translate_box(

    N_FB_TERMS[
        "TOP_GATE"
    ],

    ORIGINS[
        "MN_FB"
    ],

)


MN_FB_DRAIN = center_um(
    MN_FB_DRAIN_BOX
)


print()
print("=" * 80)
print("MN_FB ELECTRICAL ASSIGNMENT")
print("=" * 80)

print(
    "LEFT_SD  : N_MID"
)

print(
    "RIGHT_SD : VDD"
)

print(
    "Drain center:",
    tuple(
        round(
            v,
            3
        )
        for v in MN_FB_DRAIN
    )
)


# ================================================================
# 10. EXISTING VDD RAIL
#
# Frozen from accepted VDD V2:
#
#   center Y = 18.220 um
#   X range  = 8.500 ... 28.950 um
# ================================================================

VDD_RAIL_Y = (
    18.220
)

VDD_RAIL_PROBE = (
    25.350,
    VDD_RAIL_Y,
)

SYNAPSE_VDD_PROBE = (
    8.500,
    10.000,
)


PRE_M1 = kdb.Region(

    input_top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


VDD_RAIL_EXISTS = not (

    PRE_M1

    &

    probe_region(
        VDD_RAIL_PROBE[0],
        VDD_RAIL_PROBE[1],
    )

).is_empty()


SYNAPSE_VDD_EXISTS = not (

    PRE_M1

    &

    probe_region(
        SYNAPSE_VDD_PROBE[0],
        SYNAPSE_VDD_PROBE[1],
    )

).is_empty()


print()
print("=" * 80)
print("EXISTING VDD AUDIT")
print("=" * 80)

print(
    "High VDD rail probe:",
    VDD_RAIL_EXISTS
)

print(
    "Synapse VDD probe :",
    SYNAPSE_VDD_EXISTS
)


if not (
    VDD_RAIL_EXISTS
    and
    SYNAPSE_VDD_EXISTS
):

    raise RuntimeError(
        "Expected VDD V2 conductor not found."
    )


# ================================================================
# 11. CORRECTED MN_FB VDD ESCAPE
#
# Drain -> RIGHT 0.600 um -> vertical to existing VDD rail.
# ================================================================

ESCAPE_UM = (
    0.600
)


MN_FB_ESCAPE = (

    MN_FB_DRAIN[0]
    +
    ESCAPE_UM,

    MN_FB_DRAIN[1],

)


ROUTE_WIDTH = (
    0.230
)


print()
print("=" * 80)
print("MN_FB VDD ESCAPE")
print("=" * 80)

print(
    "Drain :",
    tuple(
        round(
            v,
            3
        )
        for v in MN_FB_DRAIN
    )
)

print(
    "Escape:",
    tuple(
        round(
            v,
            3
        )
        for v in MN_FB_ESCAPE
    )
)


# ================================================================
# 12. CREATE V3 WRAPPER
# ================================================================

if layout.cell(
    OUTPUT_TOP_NAME
) is not None:

    raise RuntimeError(
        f"Cell already exists: {OUTPUT_TOP_NAME}"
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
# 13. ADD TWO M1 SHAPES
# ================================================================

route_boxes = {


    "MN_FB_DRAIN_STUB":

        horizontal_box(

            MN_FB_DRAIN[0],

            MN_FB_ESCAPE[0],

            MN_FB_DRAIN[1],

            ROUTE_WIDTH,

        ),


    "MN_FB_VDD_VERTICAL":

        vertical_box(

            MN_FB_ESCAPE[0],

            MN_FB_ESCAPE[1],

            VDD_RAIL_Y,

            ROUTE_WIDTH,

        ),

}


for name, box in route_boxes.items():

    top.shapes(
        M1_LAYER
    ).insert(
        box
    )


print()
print("=" * 80)
print("NEW VDD V3 SHAPES")
print("=" * 80)


for name, box in route_boxes.items():

    print(

        f"{name:22s}",
        "bbox_um=(",
        round(
            to_um(
                box.left
            ),
            3
        ),
        ",",
        round(
            to_um(
                box.bottom
            ),
            3
        ),
        ",",
        round(
            to_um(
                box.right
            ),
            3
        ),
        ",",
        round(
            to_um(
                box.top
            ),
            3
        ),
        ")"

    )


# ================================================================
# 14. NEW ROUTE CONTINUITY
# ================================================================

NEW_ROUTE = kdb.Region()


for box in route_boxes.values():

    NEW_ROUTE.insert(
        box
    )


NEW_ROUTE.merge()


NEW_ROUTE_COMPONENTS = len(

    list(
        NEW_ROUTE.each_merged()
    )

)


NEW_ROUTE_CONNECTED = (
    NEW_ROUTE_COMPONENTS == 1
)


print()
print("=" * 80)
print("NEW ROUTE CONNECTIVITY")
print("=" * 80)

print(
    "Components:",
    NEW_ROUTE_COMPONENTS
)

print(
    "Connected:",
    NEW_ROUTE_CONNECTED
)


# ================================================================
# 15. FULL M1 ROOT AUDIT
# ================================================================

FULL_M1 = (

    PRE_M1
    +
    NEW_ROUTE

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

            hits.append(
                index
            )


    if len(
        hits
    ) != 1:

        return None


    return hits[0]


VDD_ROOT_SYN = root_at_point(

    SYNAPSE_VDD_PROBE[0],

    SYNAPSE_VDD_PROBE[1],

)


VDD_ROOT_RAIL = root_at_point(

    VDD_RAIL_PROBE[0],

    VDD_RAIL_PROBE[1],

)


VDD_ROOT_MNFB = root_at_point(

    MN_FB_DRAIN[0],

    MN_FB_DRAIN[1],

)


VDD_COMPLETENESS_OK = bool(

    VDD_ROOT_SYN is not None

    and

    VDD_ROOT_SYN
    ==
    VDD_ROOT_RAIL
    ==
    VDD_ROOT_MNFB

)


print()
print("=" * 80)
print("VDD COMPLETENESS ROOT AUDIT")
print("=" * 80)

print(
    "Synapse VDD root:",
    VDD_ROOT_SYN
)

print(
    "High rail root  :",
    VDD_ROOT_RAIL
)

print(
    "MN_FB drain root:",
    VDD_ROOT_MNFB
)

print(
    "MN_FB now on VDD:",
    VDD_COMPLETENESS_OK
)


# ================================================================
# 16. MN_FB PROTECTED TERMINALS
# ================================================================

protected_boxes = {

    "MN_FB_SOURCE_NMID":
        MN_FB_SOURCE_BOX,

    "MN_FB_GATE_B_VRAW":
        MN_FB_GATE_B_BOX,

    "MN_FB_GATE_T_VRAW":
        MN_FB_GATE_T_BOX,

}


PROTECTED_DIRECT_CLEAR = True

PROTECTED_ROOT_CLEAR = True


print()
print("=" * 80)
print("MN_FB PROTECTED TERMINAL AUDIT")
print("=" * 80)


for name, box in protected_boxes.items():

    direct_overlap = not (

        NEW_ROUTE

        &

        kdb.Region(
            box
        )

    ).is_empty()


    point = center_um(
        box
    )


    root = root_at_point(

        point[0],

        point[1],

    )


    shorted_to_vdd = bool(

        VDD_ROOT_SYN is not None

        and

        root == VDD_ROOT_SYN

    )


    clear = bool(

        not direct_overlap

        and

        not shorted_to_vdd

    )


    PROTECTED_DIRECT_CLEAR &= (
        not direct_overlap
    )

    PROTECTED_ROOT_CLEAR &= (
        not shorted_to_vdd
    )


    print(
        f"{name:20s} "
        f"direct_overlap={direct_overlap} "
        f"root={root} "
        f"clear={clear}"
    )


# ================================================================
# 17. CHECK PMOS ROW FOR INTERSECTION
#
# Vertical VDD path passes upward between MP_FB and MP_BUF.
# Audit relevant PMOS terminal boxes explicitly.
# ================================================================

def abs_terminal_box(
    terms,
    terminal,
    origin,
):

    return translate_box(

        terms[
            terminal
        ],

        origin,

    )


PMOS_PROTECTED = {


    "MP_FB_LEFT_SD":

        abs_terminal_box(

            P_FB_TERMS,

            "LEFT_SD",

            ORIGINS[
                "MP_FB"
            ],

        ),


    "MP_FB_RIGHT_SD":

        abs_terminal_box(

            P_FB_TERMS,

            "RIGHT_SD",

            ORIGINS[
                "MP_FB"
            ],

        ),


    "MP_FB_GATE_B":

        abs_terminal_box(

            P_FB_TERMS,

            "BOTTOM_GATE",

            ORIGINS[
                "MP_FB"
            ],

        ),


    "MP_FB_GATE_T":

        abs_terminal_box(

            P_FB_TERMS,

            "TOP_GATE",

            ORIGINS[
                "MP_FB"
            ],

        ),


    "MP_BUF_DRAIN":

        abs_terminal_box(

            P_LOGIC_TERMS,

            "RIGHT_SD",

            ORIGINS[
                "MP_BUF"
            ],

        ),


    "MP_BUF_GATE_B":

        abs_terminal_box(

            P_LOGIC_TERMS,

            "BOTTOM_GATE",

            ORIGINS[
                "MP_BUF"
            ],

        ),


    "MP_BUF_GATE_T":

        abs_terminal_box(

            P_LOGIC_TERMS,

            "TOP_GATE",

            ORIGINS[
                "MP_BUF"
            ],

        ),

}


PMOS_PROTECTED_CLEAR = True


print()
print("=" * 80)
print("PMOS-ROW CLEARANCE AUDIT")
print("=" * 80)


for name, box in PMOS_PROTECTED.items():

    overlap = not (

        NEW_ROUTE

        &

        kdb.Region(
            box
        )

    ).is_empty()


    clear = (
        not overlap
    )


    PMOS_PROTECTED_CLEAR &= clear


    print(
        f"{name:18s}: "
        f"overlap={overlap} "
        f"clear={clear}"
    )


# ================================================================
# 18. NUMERIC CLEARANCE TO NEAREST PMOS METAL
# ================================================================

VERTICAL_BOX = route_boxes[
    "MN_FB_VDD_VERTICAL"
]


clearance_values = {}


for name, box in PMOS_PROTECTED.items():

    gap = horizontal_gap_um(

        VERTICAL_BOX,

        box,

    )


    clearance_values[
        name
    ] = gap


MIN_P_M1_GAP = min(
    clearance_values.values()
)


DIAGNOSTIC_MIN = (
    0.140
)


NUMERIC_CLEARANCE_OK = (
    MIN_P_M1_GAP
    >=
    DIAGNOSTIC_MIN
)


print()
print("=" * 80)
print("VERTICAL / PMOS M1 HORIZONTAL CLEARANCE")
print("=" * 80)


for name, gap in clearance_values.items():

    print(
        f"{name:18s}: "
        f"{gap:.3f} um"
    )


print(
    "Minimum:",
    round(
        MIN_P_M1_GAP,
        3
    ),
    "um"
)

print(
    "Diagnostic threshold:",
    DIAGNOSTIC_MIN,
    "um"
)

print(
    "Clearance valid:",
    NUMERIC_CLEARANCE_OK
)


# ================================================================
# 19. TOP-LEVEL ROUTE COUNT
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        M1_LAYER
    ).each()

)


EXPECTED_TOP_M1_COUNT = (
    2
)


TOP_M1_COUNT_OK = (

    TOP_M1_COUNT
    ==
    EXPECTED_TOP_M1_COUNT

)


print()
print("=" * 80)
print("TOP-LEVEL V3 SHAPE COUNT")
print("=" * 80)

print(
    "New M1 shapes:",
    TOP_M1_COUNT
)

print(
    "Expected:",
    EXPECTED_TOP_M1_COUNT
)

print(
    "Correct:",
    TOP_M1_COUNT_OK
)


# ================================================================
# 20. POPULATED LAYERS
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


# ================================================================
# 21. SAVE OPTIONS
# ================================================================

def make_save_options(
    fmt
):

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
# 22. WRITE
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


READBACK_M1_COUNT = 0


if (
    verify_top is not None
    and
    verify_m1 is not None
):

    READBACK_M1_COUNT = sum(

        1

        for _
        in verify_top.shapes(
            verify_m1
        ).each()

    )


READBACK_COUNT_OK = (

    READBACK_M1_COUNT
    ==
    EXPECTED_TOP_M1_COUNT

)


# ================================================================
# 24. INPUT INTEGRITY
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
# 25. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "30E",

    "routing_stage":
        "1_of_9_VDD_completeness_repair",

    "revision":
        "v3",

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

    "reason":

        "Frozen topology requires MN_FB drain on VDD; "
        "VDD V2 omitted that diffusion connection.",

    "mn_fb": {

        "spice":
            "MN_FB VDD VRAW N_MID VSS",

        "left_sd":
            "N_MID",

        "right_sd":
            "VDD",

        "drain_center_um":
            list(
                MN_FB_DRAIN
            ),

        "escape_um":
            ESCAPE_UM,

        "escape_direction":
            "RIGHT",

        "escape_point_um":
            list(
                MN_FB_ESCAPE
            ),

    },

    "checks": {

        "reference_requirement":
            REFERENCE_MN_FB_OK,

        "new_route_connected":
            NEW_ROUTE_CONNECTED,

        "vdd_complete":
            VDD_COMPLETENESS_OK,

        "mnfb_protected_direct_clear":
            PROTECTED_DIRECT_CLEAR,

        "mnfb_protected_roots_clear":
            PROTECTED_ROOT_CLEAR,

        "pmos_row_clear":
            PMOS_PROTECTED_CLEAR,

        "numeric_clearance":
            NUMERIC_CLEARANCE_OK,

        "top_m1_count":
            TOP_M1_COUNT_OK,

        "gds_write":
            GDS_OK,

        "oas_write":
            OAS_OK,

        "readback":
            READBACK_OK,

        "readback_count":
            READBACK_COUNT_OK,

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
# 26. FINAL GATE
# ================================================================

STEP30E_PASS = bool(

    REFERENCE_MN_FB_OK

    and

    NEW_ROUTE_CONNECTED

    and

    VDD_COMPLETENESS_OK

    and

    PROTECTED_DIRECT_CLEAR

    and

    PROTECTED_ROOT_CLEAR

    and

    PMOS_PROTECTED_CLEAR

    and

    NUMERIC_CLEARANCE_OK

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
print("STEP 30E RESULT")
print("=" * 80)

print(
    "Reference MN_FB D=VDD      :",
    REFERENCE_MN_FB_OK
)

print(
    "New route connected        :",
    NEW_ROUTE_CONNECTED
)

print(
    "MN_FB drain joins VDD       :",
    VDD_COMPLETENESS_OK
)

print(
    "MN_FB protected boxes clear :",
    PROTECTED_DIRECT_CLEAR
)

print(
    "MN_FB protected roots clear :",
    PROTECTED_ROOT_CLEAR
)

print(
    "PMOS-row terminals clear    :",
    PMOS_PROTECTED_CLEAR
)

print(
    "Numeric clearance valid     :",
    NUMERIC_CLEARANCE_OK
)

print(
    "Top-level M1 count          :",
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
    "Read-back M1 count          :",
    READBACK_COUNT_OK
)

print(
    "VDD V2 input unchanged      :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP30E_PASS =",
    STEP30E_PASS
)


if not STEP30E_PASS:

    raise RuntimeError(
        "STEP 30E VDD completeness repair failed."
    )


print()
print("=" * 80)
print("VDD V3 CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "VDD V1 : REJECTED — gate shorts"
)

print(
    "VDD V2 : DRC CLEAN — but electrically incomplete"
)

print(
    "VDD V3 : construction complete"
)

print()
print(
    "New VDD terminal:"
)

print(
    "  MN_FB drain -> VDD"
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
    "  Official SKY130 DRC on VDD V3."
)