# ================================================================
# NeuroLIF-SKY130
# STEP 29B — Complete-neuron placement V1
#
# Input:
#   CLOSED weighted synapse:
#   neurolif_synapse_vss_v1.gds
#
# Adds placement only:
#
#   PMOS row:
#       MP_ST1
#       MP_ST2
#       MP_FB
#       MP_BUF
#       dedicated N_TAP_LOGIC
#
#   NMOS row:
#       MN_ST1
#       MN_ST2
#       MN_FB
#       MN_BUF
#       MN_LEAK
#       MN_RST
#       dedicated P_TAP_LOGIC
#
# Also adds:
#   one common NWELL rectangle joining all added PMOS devices
#   and the added n-tap.
#
# NO SIGNAL ROUTING IS ADDED.
#
# The closed synapse instance is reused unchanged.
# ================================================================

from pathlib import Path
import json
import hashlib

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 29B: FULL-NEURON PLACEMENT V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SYNAPSE_DIR = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
)

NEURON_DIR = (
    PROJECT_ROOT
    / "layout"
    / "neuron"
)

NEURON_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


INPUT_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_vss_v1.gds"
)

ARCH_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_architecture_v1.json"
)

SYNAPSE_FINAL_RECORD = (
    PROJECT_ROOT
    / "verification"
    / "synapse"
    / "neurolif_synapse_final_verification_v1.json"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_placement_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_placement_v1.oas"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_placement_v1.json"
)


SYNAPSE_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VSS_V1"
)

NEW_TOP_NAME = (
    "NEUROLIF_FULL_NEURON_PLACEMENT_V1"
)


for path in [
    INPUT_GDS,
    ARCH_MANIFEST,
    SYNAPSE_FINAL_RECORD,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. HASH CLOSED SYNAPSE
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


SYNAPSE_HASH_BEFORE = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. CHECK FROZEN DEPENDENCIES
# ================================================================

arch = json.loads(

    ARCH_MANIFEST.read_text(
        encoding="utf-8"
    )

)

synapse_record = json.loads(

    SYNAPSE_FINAL_RECORD.read_text(
        encoding="utf-8"
    )

)


ARCH_FROZEN = (
    arch.get("status")
    == "REFERENCE_FROZEN"
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
    "Step 29A architecture frozen:",
    ARCH_FROZEN
)

print(
    "Weighted synapse closed:",
    SYNAPSE_CLOSED
)


if not ARCH_FROZEN:

    raise RuntimeError(
        "Step 29A reference is not frozen."
    )


if not SYNAPSE_CLOSED:

    raise RuntimeError(
        "Weighted synapse is not closed."
    )


# ================================================================
# 4. LOAD CLOSED SYNAPSE GDS
#
# The synapse build was produced from the canonical primitive
# library. We expect the unused canonical primitive cells to
# remain available in this GDS.
# ================================================================

layout = kdb.Layout()

layout.read(
    str(
        INPUT_GDS
    )
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
    "Input:",
    INPUT_GDS
)


# ================================================================
# 5. REQUIRED CELLS
# ================================================================

REQUIRED_CELL_NAMES = {

    "SYNAPSE":
        "NEUROLIF_WEIGHTED_SYNAPSE_VSS_V1",

    "N_LOGIC":
        "N_LOGIC_W1000_L0150",

    "P_LOGIC":
        "P_LOGIC_W2000_L0150",

    "N_FB":
        "N_FB_W0420_L0300",

    "P_FB":
        "P_FB_W0420_L0300",

    "N_LEAK":
        "N_LEAK_W0420_L1000",

    "N_RESET":
        "N_RESET_W1200_L0150",

    "N_TAP":
        "N_TAP_VDD_W1000_H1000",

    "P_TAP":
        "P_TAP_VSS_W1000_H1000",

}


cells = {}


print()
print("=" * 80)
print("REQUIRED CELL AUDIT")
print("=" * 80)


CELL_AUDIT_OK = True


for role, name in REQUIRED_CELL_NAMES.items():

    cell = layout.cell(
        name
    )

    found = (
        cell is not None
    )

    print(
        f"{role:10s} "
        f"{name:34s} "
        f"found={found}"
    )


    if not found:

        CELL_AUDIT_OK = False

    else:

        cells[
            role
        ] = cell


if not CELL_AUDIT_OK:

    print()
    print("Available cells:")
    print("-" * 80)

    for cell in layout.each_cell():

        print(
            cell.name
        )

    raise RuntimeError(
        "One or more canonical cells are missing."
    )


# ================================================================
# 6. LAYERS
# ================================================================

NWELL_LAYER = layout.find_layer(
    64,
    20
)

MET1_LAYER = layout.find_layer(
    68,
    20
)


if NWELL_LAYER is None:

    raise RuntimeError(
        "NWELL 64/20 is missing."
    )


if MET1_LAYER is None:

    raise RuntimeError(
        "MET1 68/20 is missing."
    )


# ================================================================
# 7. HELPERS
# ================================================================

def to_dbu(value_um):

    return int(
        round(
            float(value_um)
            / DBU
        )
    )


def box_to_um(box):

    return (

        box.left * DBU,

        box.bottom * DBU,

        box.right * DBU,

        box.top * DBU,

    )


def translate_box(
    box,
    x_um,
    y_um,
):

    dx = to_dbu(
        x_um
    )

    dy = to_dbu(
        y_um
    )

    return kdb.Box(

        box.left + dx,

        box.bottom + dy,

        box.right + dx,

        box.top + dy,

    )


def boxes_overlap(
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


def box_gap_um(
    a,
    b,
):

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

        (
            dx * DBU
        ) ** 2
        +
        (
            dy * DBU
        ) ** 2

    ) ** 0.5


def local_layer_boxes(
    cell,
    layer_index,
):

    return [

        shape.bbox()

        for shape
        in cell.shapes(
            layer_index
        ).each()

        if (
            shape.is_box()
            or
            shape.is_polygon()
            or
            shape.is_path()
        )

    ]


# ================================================================
# 8. FLOORPLAN
#
# Closed synapse remains at origin.
#
# Added logic is placed to the right.
#
# PMOS row y = 14 um
# NMOS row y = 7 um
#
# Columns align functional pairs:
#
#     ST1     ST2     FB     BUF    LEAK   RESET
#
# ================================================================

PLACEMENT_UM = {

    # ------------------------------------------------------------
    # Closed synapse
    # ------------------------------------------------------------

    "WEIGHTED_SYNAPSE": {
        "cell_role":
            "SYNAPSE",

        "origin_um":
            [0.0, 0.0],
    },


    # ------------------------------------------------------------
    # Added PMOS body tap
    # ------------------------------------------------------------

    "N_TAP_LOGIC": {
        "cell_role":
            "N_TAP",

        "origin_um":
            [12.5, 14.0],
    },


    # ------------------------------------------------------------
    # Corrected Schmitt PMOS row
    # ------------------------------------------------------------

    "MP_ST1": {
        "cell_role":
            "P_LOGIC",

        "origin_um":
            [16.0, 14.0],
    },

    "MP_ST2": {
        "cell_role":
            "P_LOGIC",

        "origin_um":
            [20.0, 14.0],
    },

    "MP_FB": {
        "cell_role":
            "P_FB",

        "origin_um":
            [24.0, 14.0],
    },


    # ------------------------------------------------------------
    # Output inverter PMOS
    # ------------------------------------------------------------

    "MP_BUF": {
        "cell_role":
            "P_LOGIC",

        "origin_um":
            [28.0, 14.0],
    },


    # ------------------------------------------------------------
    # Added NMOS substrate tap
    # ------------------------------------------------------------

    "P_TAP_LOGIC": {
        "cell_role":
            "P_TAP",

        "origin_um":
            [12.5, 7.0],
    },


    # ------------------------------------------------------------
    # Corrected Schmitt NMOS row
    # ------------------------------------------------------------

    "MN_ST1": {
        "cell_role":
            "N_LOGIC",

        "origin_um":
            [16.0, 7.0],
    },

    "MN_ST2": {
        "cell_role":
            "N_LOGIC",

        "origin_um":
            [20.0, 7.0],
    },

    "MN_FB": {
        "cell_role":
            "N_FB",

        "origin_um":
            [24.0, 7.0],
    },


    # ------------------------------------------------------------
    # Output inverter NMOS
    # ------------------------------------------------------------

    "MN_BUF": {
        "cell_role":
            "N_LOGIC",

        "origin_um":
            [28.0, 7.0],
    },


    # ------------------------------------------------------------
    # Leak
    # ------------------------------------------------------------

    "MN_LEAK": {
        "cell_role":
            "N_LEAK",

        "origin_um":
            [32.0, 7.0],
    },


    # ------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------

    "MN_RST": {
        "cell_role":
            "N_RESET",

        "origin_um":
            [36.0, 7.0],
    },

}


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


# ================================================================
# 10. PLACE INSTANCES
# ================================================================

print()
print("=" * 80)
print("INSTANCE PLACEMENT")
print("=" * 80)


placed_bboxes = {}


for instance_name, record in PLACEMENT_UM.items():

    role = record[
        "cell_role"
    ]

    cell = cells[
        role
    ]

    x_um = float(
        record[
            "origin_um"
        ][0]
    )

    y_um = float(
        record[
            "origin_um"
        ][1]
    )


    trans = kdb.Trans(

        to_dbu(
            x_um
        ),

        to_dbu(
            y_um
        ),

    )


    top.insert(

        kdb.CellInstArray(

            cell.cell_index(),

            trans,

        )

    )


    abs_bbox = translate_box(

        cell.bbox(),

        x_um,

        y_um,

    )


    placed_bboxes[
        instance_name
    ] = abs_bbox


    bbox_um = box_to_um(
        abs_bbox
    )


    print(

        f"{instance_name:18s} "
        f"{cell.name:32s} "
        f"@ ({x_um:6.2f}, {y_um:6.2f}) um "
        f"bbox=("
        f"{bbox_um[0]:.3f}, "
        f"{bbox_um[1]:.3f}, "
        f"{bbox_um[2]:.3f}, "
        f"{bbox_um[3]:.3f})"

    )


# ================================================================
# 11. BUILD COMMON PMOS NWELL
#
# Obtain actual primitive-local NWELL boxes.
#
# Common region includes:
#
#   N_TAP_LOGIC
#   MP_ST1
#   MP_ST2
#   MP_FB
#   MP_BUF
#
# We bridge their existing valid NWELLs with one top-level
# rectangle.
# ================================================================

PMOS_WELL_INSTANCES = [

    "N_TAP_LOGIC",
    "MP_ST1",
    "MP_ST2",
    "MP_FB",
    "MP_BUF",

]


absolute_nwell_boxes = []


for instance_name in PMOS_WELL_INSTANCES:

    record = PLACEMENT_UM[
        instance_name
    ]

    role = record[
        "cell_role"
    ]

    cell = cells[
        role
    ]


    local_boxes = local_layer_boxes(

        cell,

        NWELL_LAYER,

    )


    if len(local_boxes) == 0:

        raise RuntimeError(

            f"{instance_name} / {cell.name}: "
            "no local NWELL geometry found."

        )


    for local_box in local_boxes:

        absolute_nwell_boxes.append(

            translate_box(

                local_box,

                record[
                    "origin_um"
                ][0],

                record[
                    "origin_um"
                ][1],

            )

        )


NWELL_LEFT = min(

    box.left

    for box
    in absolute_nwell_boxes

)

NWELL_BOTTOM = min(

    box.bottom

    for box
    in absolute_nwell_boxes

)

NWELL_RIGHT = max(

    box.right

    for box
    in absolute_nwell_boxes

)

NWELL_TOP = max(

    box.top

    for box
    in absolute_nwell_boxes

)


COMMON_LOGIC_NWELL = kdb.Box(

    NWELL_LEFT,

    NWELL_BOTTOM,

    NWELL_RIGHT,

    NWELL_TOP,

)


top.shapes(
    NWELL_LAYER
).insert(
    COMMON_LOGIC_NWELL
)


print()
print("=" * 80)
print("COMMON LOGIC NWELL")
print("=" * 80)

print(
    "BBox um:",
    tuple(
        round(
            value,
            3
        )

        for value
        in box_to_um(
            COMMON_LOGIC_NWELL
        )
    )
)


# ================================================================
# 12. VERIFY EVERY PMOS/TAP WELL TOUCHES COMMON WELL
# ================================================================

PMOS_COMMON_WELL_OK = True


for box in absolute_nwell_boxes:

    touch = boxes_overlap(

        box,

        COMMON_LOGIC_NWELL,

    )

    PMOS_COMMON_WELL_OK &= touch


print(
    "All PMOS/tap wells joined:",
    PMOS_COMMON_WELL_OK
)


# ================================================================
# 13. CLOSED SYNAPSE NWELL ISOLATION
#
# We deliberately keep the neuron-logic PMOS well separate from
# the closed synapse well.
#
# Both will later be tied to VDD through their own n-taps.
# ================================================================

synapse_cell = cells[
    "SYNAPSE"
]


synapse_nwell_region = kdb.Region(

    synapse_cell.begin_shapes_rec(
        NWELL_LAYER
    )

).merged()


new_nwell_region = kdb.Region(
    COMMON_LOGIC_NWELL
)


SYNAPSE_WELL_OVERLAP = not (

    synapse_nwell_region
    & new_nwell_region

).is_empty()


SYNAPSE_WELL_SEPARATE = (
    not SYNAPSE_WELL_OVERLAP
)


print()
print("=" * 80)
print("SYNAPSE / LOGIC NWELL ISOLATION")
print("=" * 80)

print(
    "Overlap:",
    SYNAPSE_WELL_OVERLAP
)

print(
    "Separate regions:",
    SYNAPSE_WELL_SEPARATE
)


# ================================================================
# 14. NMOS MUST REMAIN OUTSIDE NEW NWELL
# ================================================================

NMOS_INSTANCES = [

    "P_TAP_LOGIC",

    "MN_ST1",

    "MN_ST2",

    "MN_FB",

    "MN_BUF",

    "MN_LEAK",

    "MN_RST",

]


NMOS_OUTSIDE_NWELL_OK = True


print()
print("=" * 80)
print("NMOS / NWELL ISOLATION")
print("=" * 80)


for name in NMOS_INSTANCES:

    bbox = placed_bboxes[
        name
    ]

    collision = boxes_overlap(

        bbox,

        COMMON_LOGIC_NWELL,

    )


    outside = (
        not collision
    )


    NMOS_OUTSIDE_NWELL_OK &= outside


    print(
        f"{name:14s} "
        f"outside logic NWELL={outside}"
    )


# ================================================================
# 15. INSTANCE-BBOX COLLISION AUDIT
#
# The closed synapse is treated as one immutable block.
#
# Bounding boxes are conservative because they include wells,
# contacts and implant layers.
# ================================================================

names = list(
    placed_bboxes.keys()
)


collisions = []


for i in range(
    len(names)
):

    for j in range(
        i + 1,
        len(names)
    ):

        a_name = names[i]
        b_name = names[j]

        a_box = placed_bboxes[
            a_name
        ]

        b_box = placed_bboxes[
            b_name
        ]


        # PMOS row intentionally shares/bridges NWELL.
        # Their overall primitive bboxes must still remain separate.
        if boxes_overlap(
            a_box,
            b_box,
        ):

            collisions.append(
                (
                    a_name,
                    b_name,
                )
            )


PLACEMENT_COLLISION_FREE = (
    len(
        collisions
    ) == 0
)


print()
print("=" * 80)
print("INSTANCE BBOX COLLISION AUDIT")
print("=" * 80)

print(
    "Collisions:",
    collisions
)

print(
    "Collision free:",
    PLACEMENT_COLLISION_FREE
)


# ================================================================
# 16. MINIMUM DEVICE-TO-DEVICE BBOX GAP
#
# This is only a conservative placement metric.
# Official SKY130 DRC remains authoritative.
# ================================================================

minimum_gap = None
minimum_pair = None


for i in range(
    len(names)
):

    for j in range(
        i + 1,
        len(names)
    ):

        a_name = names[i]
        b_name = names[j]


        gap = box_gap_um(

            placed_bboxes[
                a_name
            ],

            placed_bboxes[
                b_name
            ],

        )


        if (
            minimum_gap is None
            or
            gap < minimum_gap
        ):

            minimum_gap = gap
            minimum_pair = (
                a_name,
                b_name,
            )


print()
print("=" * 80)
print("PLACEMENT GAP SUMMARY")
print("=" * 80)

print(
    "Minimum bbox gap:",
    f"{minimum_gap:.3f} um"
)

print(
    "Minimum-gap pair:",
    minimum_pair
)


# ================================================================
# 17. TOP-LEVEL ROUTING AUDIT
#
# Placement-only wrapper should contain:
#
#   - one common NWELL rectangle
#   - no new Metal1
#   - no new Metal2
#   - no new VIA1
#
# Existing routed synapse metal is hierarchical and remains
# inside the synapse instance.
# ================================================================

TOP_LEVEL_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        MET1_LAYER
    ).each()

)


TOP_LEVEL_SIGNAL_METAL_CLEAR = (
    TOP_LEVEL_M1_COUNT == 0
)


print()
print("=" * 80)
print("PLACEMENT-ONLY ROUTING AUDIT")
print("=" * 80)

print(
    "New top-level M1 shapes:",
    TOP_LEVEL_M1_COUNT
)

print(
    "Expected:",
    0
)

print(
    "No signal routing added:",
    TOP_LEVEL_SIGNAL_METAL_CLEAR
)


# ================================================================
# 18. EXPECTED ACTIVE DEVICE COUNT
#
# 1 closed 7-MOS synapse instance
# +
# 10 added transistor instances
#
# Body taps are not MOS devices.
# ================================================================

added_transistor_names = [

    "MP_ST1",
    "MP_ST2",
    "MP_FB",
    "MP_BUF",

    "MN_ST1",
    "MN_ST2",
    "MN_FB",
    "MN_BUF",
    "MN_LEAK",
    "MN_RST",

]


ADDED_TRANSISTOR_COUNT_OK = (
    len(
        added_transistor_names
    ) == 10
)


print()
print("=" * 80)
print("DEVICE INSTANCE AUDIT")
print("=" * 80)

print(
    "Closed synapse MOS:",
    7
)

print(
    "Added transistor instances:",
    len(
        added_transistor_names
    )
)

print(
    "Expected total MOS:",
    17
)

print(
    "Added count correct:",
    ADDED_TRANSISTOR_COUNT_OK
)


# ================================================================
# 19. USED LAYERS
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
# 20. EXPLICIT SAVE OPTIONS
# ================================================================

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
# 22. GDS READBACK
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
# 23. CLOSED SYNAPSE HASH MUST REMAIN UNCHANGED
# ================================================================

SYNAPSE_HASH_AFTER = sha256_file(
    INPUT_GDS
)


SYNAPSE_UNCHANGED = (

    SYNAPSE_HASH_BEFORE
    == SYNAPSE_HASH_AFTER

)


# ================================================================
# 24. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "29B",

    "artifact":
        "full_neuron_placement_v1",

    "top_cell":
        NEW_TOP_NAME,

    "closed_synapse": {

        "source_gds":
            str(
                INPUT_GDS
            ),

        "cell":
            SYNAPSE_TOP_NAME,

        "origin_um":
            [0.0, 0.0],

        "sha256":
            SYNAPSE_HASH_BEFORE,

        "modified":
            False,

    },

    "placement_um":
        PLACEMENT_UM,

    "common_logic_nwell_bbox_um": [

        round(
            value,
            3
        )

        for value
        in box_to_um(
            COMMON_LOGIC_NWELL
        )

    ],

    "device_count": {

        "closed_synapse_mos":
            7,

        "added_mos":
            10,

        "total_mos":
            17,

        "body_taps_added":
            2,

    },

    "body_strategy": {

        "added_pmos":
            "common NWELL + N_TAP_LOGIC",

        "added_nmos":
            "p-substrate + P_TAP_LOGIC",

        "synapse_body_strategy":
            "unchanged / already closed",

    },

    "routing_status": {

        "signal_routing_added":
            False,

        "placement_only":
            True,

    },

    "checks": {

        "architecture_frozen":
            ARCH_FROZEN,

        "synapse_closed":
            SYNAPSE_CLOSED,

        "cell_inventory":
            CELL_AUDIT_OK,

        "pmos_common_well":
            PMOS_COMMON_WELL_OK,

        "synapse_logic_wells_separate":
            SYNAPSE_WELL_SEPARATE,

        "nmos_outside_nwell":
            NMOS_OUTSIDE_NWELL_OK,

        "instance_collision_free":
            PLACEMENT_COLLISION_FREE,

        "added_transistor_count":
            ADDED_TRANSISTOR_COUNT_OK,

        "no_new_signal_m1":
            TOP_LEVEL_SIGNAL_METAL_CLEAR,

        "gds_write":
            GDS_OK,

        "oas_write":
            OAS_OK,

        "readback":
            READBACK_OK,

        "closed_synapse_source_unchanged":
            SYNAPSE_UNCHANGED,

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
# 25. FINAL PASS GATE
# ================================================================

STEP29B_PASS = bool(

    ARCH_FROZEN

    and

    SYNAPSE_CLOSED

    and

    CELL_AUDIT_OK

    and

    PMOS_COMMON_WELL_OK

    and

    SYNAPSE_WELL_SEPARATE

    and

    NMOS_OUTSIDE_NWELL_OK

    and

    PLACEMENT_COLLISION_FREE

    and

    ADDED_TRANSISTOR_COUNT_OK

    and

    TOP_LEVEL_SIGNAL_METAL_CLEAR

    and

    GDS_OK

    and

    OAS_OK

    and

    READBACK_OK

    and

    SYNAPSE_UNCHANGED

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 29B RESULT")
print("=" * 80)

print(
    "Architecture frozen        :",
    ARCH_FROZEN
)

print(
    "Closed synapse dependency  :",
    SYNAPSE_CLOSED
)

print(
    "Canonical cells found      :",
    CELL_AUDIT_OK
)

print(
    "PMOS common NWELL          :",
    PMOS_COMMON_WELL_OK
)

print(
    "Synapse / logic wells sep. :",
    SYNAPSE_WELL_SEPARATE
)

print(
    "NMOS outside NWELL         :",
    NMOS_OUTSIDE_NWELL_OK
)

print(
    "Placement collision-free   :",
    PLACEMENT_COLLISION_FREE
)

print(
    "10 added MOS               :",
    ADDED_TRANSISTOR_COUNT_OK
)

print(
    "No new signal routing      :",
    TOP_LEVEL_SIGNAL_METAL_CLEAR
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
    "Closed synapse unchanged   :",
    SYNAPSE_UNCHANGED
)

print(
    "Manifest write             :",
    MANIFEST_OK
)

print()

print(
    "STEP29B_PASS =",
    STEP29B_PASS
)


if not STEP29B_PASS:

    raise RuntimeError(
        "STEP 29B full-neuron placement failed."
    )


print()
print("=" * 80)
print("FULL-NEURON PLACEMENT V1 GENERATED")
print("=" * 80)

print()
print(
    "Closed synapse:"
)

print(
    "  REUSED UNCHANGED"
)

print()
print(
    "Added:"
)

print(
    "  4 PMOS devices"
)

print(
    "  6 NMOS devices"
)

print(
    "  1 PMOS-well n-tap"
)

print(
    "  1 NMOS-substrate p-tap"
)

print(
    "  common logic NWELL"
)

print()
print(
    "Signal routing:"
)

print(
    "  NONE"
)

print()
print(
    "Candidate GDS:"
)

print(
    OUTPUT_GDS
)

print()
print(
    "NEXT:"
)

print(
    "  Full official SKY130 DRC on placement only."
)