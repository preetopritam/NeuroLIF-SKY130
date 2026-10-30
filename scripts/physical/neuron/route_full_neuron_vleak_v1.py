# ================================================================
# NeuroLIF-SKY130
# STEP 33A — Full-neuron VLEAK routing V1
#
# Routing Stage 4/9
#
# Input:
#   neurolif_full_neuron_vmem_v1.gds
#
# Frozen topology:
#
#   MN_LEAK VMEM VLEAK VSS VSS
#
# Therefore VLEAK connects ONLY:
#
#   MN_LEAK gate -> external VLEAK access
#
# Routing layer:
#   MET1 68/20
#
# No VIA1 or M2 added.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 33A: FULL-NEURON VLEAK ROUTING V1")
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
    / "neurolif_full_neuron_vmem_v1.gds"
)

INPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vmem_v1.json"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "reference"
    / "neurolif_full_neuron_reference_v1.spice"
)

VMEM_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_vmem_v1_drc.lyrdb"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_vleak_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_vleak_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_vleak_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VMEM_V1"
)

OUTPUT_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_VLEAK_V1"
)


for path in [
    INPUT_GDS,
    INPUT_MANIFEST,
    REFERENCE_SPICE,
    VMEM_DRC_REPORT,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. HASH
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
# 3. REFERENCE CHECK
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


EXPECTED_MN_LEAK = (
    "MN_LEAK VMEM VLEAK VSS VSS"
)


REFERENCE_OK = (
    EXPECTED_MN_LEAK
    in reference_text
)


print()
print("=" * 80)
print("REFERENCE TOPOLOGY CHECK")
print("=" * 80)

print(
    "MN_LEAK VMEM VLEAK VSS VSS found:",
    REFERENCE_OK
)


if not REFERENCE_OK:

    raise RuntimeError(
        "Frozen MN_LEAK reference topology mismatch."
    )


# ================================================================
# 4. LOAD CANONICAL STAGE-3 GDS
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
# 5. LAYERS / DEVICE
# ================================================================

M1_LAYER = layout.find_layer(
    68,
    20
)


if M1_LAYER is None:

    raise RuntimeError(
        "MET1 68/20 missing."
    )


N_LEAK_NAME = (
    "N_LEAK_W0420_L1000"
)


n_leak = layout.cell(
    N_LEAK_NAME
)


if n_leak is None:

    raise RuntimeError(
        f"Missing primitive: {N_LEAK_NAME}"
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
            min(
                y1,
                y2
            )
        ),

        to_dbu(
            x + width / 2
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
    size,
):

    return kdb.Box(

        to_dbu(
            x - size / 2
        ),

        to_dbu(
            y - size / 2
        ),

        to_dbu(
            x + size / 2
        ),

        to_dbu(
            y + size / 2
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


    if len(boxes) < 4:

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

        for box in boxes

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


TERMS = primitive_terminal_boxes(
    n_leak
)


print()
print("=" * 80)
print("N_LEAK TERMINAL GEOMETRY")
print("=" * 80)


for name, box in TERMS.items():

    print(
        f"{name:12s}",
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
        ")",
        "center=",
        tuple(
            round(
                v,
                3
            )

            for v in center_um(
                box
            )
        ),
    )


# ================================================================
# 8. INSTANCE ORIGIN
# ================================================================

MN_LEAK_ORIGIN = (
    32.0,
    7.0,
)


def abs_terminal_box(
    terminal,
):

    return translate_box(

        TERMS[
            terminal
        ],

        MN_LEAK_ORIGIN,

    )


SOURCE_BOX = abs_terminal_box(
    "LEFT_SD"
)

DRAIN_BOX = abs_terminal_box(
    "RIGHT_SD"
)

BOTTOM_GATE_BOX = abs_terminal_box(
    "BOTTOM_GATE"
)

TOP_GATE_BOX = abs_terminal_box(
    "TOP_GATE"
)


SOURCE_POINT = center_um(
    SOURCE_BOX
)

DRAIN_POINT = center_um(
    DRAIN_BOX
)

BOTTOM_GATE_POINT = center_um(
    BOTTOM_GATE_BOX
)

TOP_GATE_POINT = center_um(
    TOP_GATE_BOX
)


print()
print("=" * 80)
print("MN_LEAK ABSOLUTE TERMINALS")
print("=" * 80)

print(
    "Source / VSS :",
    tuple(
        round(v, 3)
        for v in SOURCE_POINT
    )
)

print(
    "Drain / VMEM :",
    tuple(
        round(v, 3)
        for v in DRAIN_POINT
    )
)

print(
    "Gate bottom  :",
    tuple(
        round(v, 3)
        for v in BOTTOM_GATE_POINT
    )
)

print(
    "Gate top     :",
    tuple(
        round(v, 3)
        for v in TOP_GATE_POINT
    )
)


# ================================================================
# 9. VLEAK ROUTE
#
# Vertical M1 line at gate X.
#
# Starts at lower gate contact.
# Passes through upper gate contact, which is the SAME MOS gate.
# Ends above the NMOS row as an external VLEAK access point.
# ================================================================

VLEAK_X = (
    BOTTOM_GATE_POINT[0]
)

VLEAK_EXTERNAL_Y = (
    11.500
)

VLEAK_EXTERNAL_POINT = (
    VLEAK_X,
    VLEAK_EXTERNAL_Y,
)


ROUTE_WIDTH = (
    0.230
)


VLEAK_ROUTE_BOX = vertical_box(

    VLEAK_X,

    BOTTOM_GATE_POINT[1],

    VLEAK_EXTERNAL_Y,

    ROUTE_WIDTH,

)


print()
print("=" * 80)
print("VLEAK ROUTE GEOMETRY")
print("=" * 80)

print(
    "Route X:",
    round(
        VLEAK_X,
        3
    ),
    "um"
)

print(
    "Start Y:",
    round(
        BOTTOM_GATE_POINT[1],
        3
    ),
    "um"
)

print(
    "End Y:",
    VLEAK_EXTERNAL_Y,
    "um"
)

print(
    "Width:",
    ROUTE_WIDTH,
    "um"
)


# ================================================================
# 10. PRE-EXISTING M1
# ================================================================

PRE_M1 = kdb.Region(

    input_top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


# ================================================================
# 11. REQUIRED EXISTING LANDINGS
# ================================================================

BOTTOM_GATE_EXISTS = not (

    PRE_M1

    &

    probe_region(
        BOTTOM_GATE_POINT[0],
        BOTTOM_GATE_POINT[1],
    )

).is_empty()


TOP_GATE_EXISTS = not (

    PRE_M1

    &

    probe_region(
        TOP_GATE_POINT[0],
        TOP_GATE_POINT[1],
    )

).is_empty()


print()
print("=" * 80)
print("GATE LANDING PRECHECK")
print("=" * 80)

print(
    "Bottom gate M1 exists:",
    BOTTOM_GATE_EXISTS
)

print(
    "Top gate M1 exists   :",
    TOP_GATE_EXISTS
)


if not (
    BOTTOM_GATE_EXISTS
    and
    TOP_GATE_EXISTS
):

    raise RuntimeError(
        "MN_LEAK gate contacts not found."
    )


# ================================================================
# 12. CREATE OUTPUT WRAPPER
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


top.shapes(
    M1_LAYER
).insert(
    VLEAK_ROUTE_BOX
)


NEW_VLEAK = kdb.Region(
    VLEAK_ROUTE_BOX
)


# ================================================================
# 13. ALLOWED PRE-EXISTING M1 OVERLAPS
#
# Only the two gate M1 contacts of MN_LEAK are permitted.
# ================================================================

ALLOWED_OVERLAP = kdb.Region()

ALLOWED_OVERLAP.insert(
    BOTTOM_GATE_BOX
)

ALLOWED_OVERLAP.insert(
    TOP_GATE_BOX
)

ALLOWED_OVERLAP.merge()


ACTUAL_OVERLAP = (

    NEW_VLEAK
    &
    PRE_M1

)


UNEXPECTED_OVERLAP = (

    ACTUAL_OVERLAP
    -
    ALLOWED_OVERLAP

)


NO_UNEXPECTED_M1_OVERLAP = (
    UNEXPECTED_OVERLAP.is_empty()
)


print()
print("=" * 80)
print("GLOBAL M1 OVERLAP AUDIT")
print("=" * 80)

print(
    "Unexpected pre-existing M1 overlap:",
    not NO_UNEXPECTED_M1_OVERLAP
)

print(
    "Only MN_LEAK gate contacts touched:",
    NO_UNEXPECTED_M1_OVERLAP
)


# ================================================================
# 14. EXPLICIT SOURCE/DRAIN PROTECTION
# ================================================================

SOURCE_CLEAR = (

    NEW_VLEAK
    &
    kdb.Region(
        SOURCE_BOX
    )

).is_empty()


DRAIN_CLEAR = (

    NEW_VLEAK
    &
    kdb.Region(
        DRAIN_BOX
    )

).is_empty()


print()
print("=" * 80)
print("SOURCE / DRAIN PROTECTION")
print("=" * 80)

print(
    "Source/VSS clear:",
    SOURCE_CLEAR
)

print(
    "Drain/VMEM clear:",
    DRAIN_CLEAR
)


# ================================================================
# 15. GATE CONTACT CONNECTIVITY
# ================================================================

BOTTOM_GATE_TOUCH = not (

    NEW_VLEAK

    &

    kdb.Region(
        BOTTOM_GATE_BOX
    )

).is_empty()


TOP_GATE_TOUCH = not (

    NEW_VLEAK

    &

    kdb.Region(
        TOP_GATE_BOX
    )

).is_empty()


GATE_CONTACTS_CONNECTED = bool(

    BOTTOM_GATE_TOUCH
    and
    TOP_GATE_TOUCH

)


print()
print("=" * 80)
print("VLEAK GATE CONNECTIVITY")
print("=" * 80)

print(
    "Bottom gate touched:",
    BOTTOM_GATE_TOUCH
)

print(
    "Top gate touched   :",
    TOP_GATE_TOUCH
)

print(
    "Both gate contacts :",
    GATE_CONTACTS_CONNECTED
)


# ================================================================
# 16. FULL-M1 ELECTRICAL ROOT AUDIT
# ================================================================

FULL_M1 = (

    PRE_M1
    +
    NEW_VLEAK

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
        y,
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


VLEAK_ROOT_BOTTOM = root_at_point(

    BOTTOM_GATE_POINT[0],
    BOTTOM_GATE_POINT[1],

)


VLEAK_ROOT_TOP = root_at_point(

    TOP_GATE_POINT[0],
    TOP_GATE_POINT[1],

)


VLEAK_ROOT_EXTERNAL = root_at_point(

    VLEAK_EXTERNAL_POINT[0],
    VLEAK_EXTERNAL_POINT[1],

)


VLEAK_ROOT_CONNECTED = bool(

    VLEAK_ROOT_BOTTOM is not None

    and

    VLEAK_ROOT_BOTTOM
    ==
    VLEAK_ROOT_TOP
    ==
    VLEAK_ROOT_EXTERNAL

)


print()
print("=" * 80)
print("VLEAK ROOT AUDIT")
print("=" * 80)

print(
    "Bottom gate root:",
    VLEAK_ROOT_BOTTOM
)

print(
    "Top gate root   :",
    VLEAK_ROOT_TOP
)

print(
    "External root   :",
    VLEAK_ROOT_EXTERNAL
)

print(
    "VLEAK one root  :",
    VLEAK_ROOT_CONNECTED
)


# ================================================================
# 17. SUPPLY SEPARATION
# ================================================================

VDD_PROBES = {

    "SYNAPSE_VDD":
        (
            8.5,
            10.0,
        ),

    "HIGH_VDD":
        (
            25.35,
            18.22,
        ),

}


VSS_PROBES = {

    "SYNAPSE_VSS":
        (
            -3.0,
            3.0,
        ),

    "LOW_VSS":
        (
            30.0,
            0.0,
        ),

}


VDD_ROOTS = {

    name:
        root_at_point(
            point[0],
            point[1],
        )

    for name, point
    in VDD_PROBES.items()

}


VSS_ROOTS = {

    name:
        root_at_point(
            point[0],
            point[1],
        )

    for name, point
    in VSS_PROBES.items()

}


vdd_set = set(
    VDD_ROOTS.values()
)

vss_set = set(
    VSS_ROOTS.values()
)


VDD_VALID = bool(

    None not in vdd_set

    and

    len(
        vdd_set
    ) == 1

)


VSS_VALID = bool(

    None not in vss_set

    and

    len(
        vss_set
    ) == 1

)


VDD_ROOT = (
    next(iter(vdd_set))
    if VDD_VALID
    else None
)

VSS_ROOT = (
    next(iter(vss_set))
    if VSS_VALID
    else None
)


VLEAK_SUPPLY_CLEAR = bool(

    VLEAK_ROOT_CONNECTED

    and

    VLEAK_ROOT_EXTERNAL
    !=
    VDD_ROOT

    and

    VLEAK_ROOT_EXTERNAL
    !=
    VSS_ROOT

)


print()
print("=" * 80)
print("SUPPLY-SEPARATION AUDIT")
print("=" * 80)

print(
    "VDD root:",
    VDD_ROOT
)

print(
    "VSS root:",
    VSS_ROOT
)

print(
    "VLEAK root:",
    VLEAK_ROOT_EXTERNAL
)

print(
    "VLEAK distinct from VDD/VSS:",
    VLEAK_SUPPLY_CLEAR
)


# ================================================================
# 18. EXTERNAL ACCESS
# ================================================================

EXTERNAL_ACCESS_OK = not (

    NEW_VLEAK

    &

    probe_region(
        VLEAK_EXTERNAL_POINT[0],
        VLEAK_EXTERNAL_POINT[1],
    )

).is_empty()


print()
print("=" * 80)
print("EXTERNAL VLEAK ACCESS")
print("=" * 80)

print(
    "Access point:",
    VLEAK_EXTERNAL_POINT
)

print(
    "Accessible:",
    EXTERNAL_ACCESS_OK
)


# ================================================================
# 19. NEW TOP-LEVEL SHAPE COUNT
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        M1_LAYER
    ).each()

)


EXPECTED_TOP_M1_COUNT = (
    1
)


TOP_M1_COUNT_OK = (

    TOP_M1_COUNT
    ==
    EXPECTED_TOP_M1_COUNT

)


print()
print("=" * 80)
print("TOP-LEVEL VLEAK SHAPE COUNT")
print("=" * 80)

print(
    "M1 shapes:",
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
# 20. SERIALIZATION LAYERS
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
# 21. WRITE
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
# 22. READBACK
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
# 23. INPUT INTEGRITY
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
# 24. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "33A",

    "routing_stage":
        "4_of_9_VLEAK",

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
        "VLEAK",

    "topology": {

        "device":
            EXPECTED_MN_LEAK,

        "target":
            "MN_LEAK gate",

    },

    "routing": {

        "layer":
            "MET1 68/20",

        "x_um":
            VLEAK_X,

        "start_um":
            list(
                BOTTOM_GATE_POINT
            ),

        "external_access_um":
            list(
                VLEAK_EXTERNAL_POINT
            ),

        "width_um":
            ROUTE_WIDTH,

    },

    "checks": {

        "reference_topology":
            REFERENCE_OK,

        "bottom_gate_exists":
            BOTTOM_GATE_EXISTS,

        "top_gate_exists":
            TOP_GATE_EXISTS,

        "no_unexpected_m1_overlap":
            NO_UNEXPECTED_M1_OVERLAP,

        "source_clear":
            SOURCE_CLEAR,

        "drain_clear":
            DRAIN_CLEAR,

        "both_gate_contacts":
            GATE_CONTACTS_CONNECTED,

        "vleak_single_root":
            VLEAK_ROOT_CONNECTED,

        "vdd_valid":
            VDD_VALID,

        "vss_valid":
            VSS_VALID,

        "vleak_supply_clear":
            VLEAK_SUPPLY_CLEAR,

        "external_access":
            EXTERNAL_ACCESS_OK,

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
# 25. FINAL GATE
# ================================================================

STEP33A_PASS = bool(

    REFERENCE_OK

    and

    BOTTOM_GATE_EXISTS

    and

    TOP_GATE_EXISTS

    and

    NO_UNEXPECTED_M1_OVERLAP

    and

    SOURCE_CLEAR

    and

    DRAIN_CLEAR

    and

    GATE_CONTACTS_CONNECTED

    and

    VLEAK_ROOT_CONNECTED

    and

    VDD_VALID

    and

    VSS_VALID

    and

    VLEAK_SUPPLY_CLEAR

    and

    EXTERNAL_ACCESS_OK

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
print("STEP 33A RESULT")
print("=" * 80)

print(
    "Reference VLEAK topology    :",
    REFERENCE_OK
)

print(
    "Bottom gate contact exists  :",
    BOTTOM_GATE_EXISTS
)

print(
    "Top gate contact exists     :",
    TOP_GATE_EXISTS
)

print(
    "No unexpected M1 overlap    :",
    NO_UNEXPECTED_M1_OVERLAP
)

print(
    "MN_LEAK source/VSS clear    :",
    SOURCE_CLEAR
)

print(
    "MN_LEAK drain/VMEM clear    :",
    DRAIN_CLEAR
)

print(
    "Both gate contacts connected:",
    GATE_CONTACTS_CONNECTED
)

print(
    "VLEAK one conductor root    :",
    VLEAK_ROOT_CONNECTED
)

print(
    "VDD remains valid           :",
    VDD_VALID
)

print(
    "VSS remains valid           :",
    VSS_VALID
)

print(
    "VLEAK distinct from supplies:",
    VLEAK_SUPPLY_CLEAR
)

print(
    "External VLEAK accessible   :",
    EXTERNAL_ACCESS_OK
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
    "Stage-3 source unchanged    :",
    INPUT_UNCHANGED
)

print(
    "Manifest write              :",
    MANIFEST_OK
)

print()

print(
    "STEP33A_PASS =",
    STEP33A_PASS
)


if not STEP33A_PASS:

    raise RuntimeError(
        "STEP 33A VLEAK construction failed."
    )


print()
print("=" * 80)
print("ROUTING STAGE 4/9 — VLEAK CONSTRUCTION COMPLETE")
print("=" * 80)

print()
print(
    "Connected:"
)

print(
    "  MN_LEAK gate"
)

print(
    "  external VLEAK access"
)

print()
print(
    "Preserved:"
)

print(
    "  VDD"
)

print(
    "  VSS"
)

print(
    "  VMEM"
)

print(
    "  MN_LEAK source and drain"
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
    "  Official SKY130 DRC on VLEAK V1."
)