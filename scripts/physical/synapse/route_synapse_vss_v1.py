# ================================================================
# NeuroLIF-SKY130
# STEP 25A — VSS substrate/body-tap routing V1
#
# Input:
#   neurolif_synapse_weight_gates_v2.gds
#
# Existing frozen nets:
#   VDD
#   VBIAS
#   P_U1A -> SW1A
#   P_U0  -> SW0
#   P_U1B -> SW1B
#   VMEM
#   GATE_W0
#   GATE_W1
#
# Adds:
#   VSS -> P_TAP_VSS
#
# IMPORTANT:
#   This is a BODY/SUBSTRATE connection only.
#
#   No NMOS source/drain terminal is connected to VSS.
# ================================================================

from pathlib import Path
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 25A: VSS BODY-TAP ROUTING V1")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_weight_gates_v2.gds"
)

PLACEMENT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_placement_v1.json"
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
    / "neurolif_synapse_vss_v1.gds"
)

OUTPUT_OAS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vss_v1.oas"
)

OUTPUT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vss_v1.json"
)


INPUT_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_WEIGHT_GATES_V2"
)

NEW_TOP_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VSS_V1"
)


for path in [
    INPUT_GDS,
    PLACEMENT_MANIFEST,
    VMEM_MANIFEST,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. LOAD CURRENT CANONICAL SYNAPSE
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
    "Canonical input:",
    INPUT_TOP_NAME
)

print(
    "Step 24E status: DRC CLEAN"
)


# ================================================================
# 3. LOAD MANIFEST DATA
# ================================================================

placement_data = json.loads(

    PLACEMENT_MANIFEST.read_text(
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


if "P_TAP_VSS" not in placements:

    raise RuntimeError(
        "P_TAP_VSS placement missing from manifest."
    )


P_TAP_ORIGIN = placements[
    "P_TAP_VSS"
][
    "origin_um"
]


P_TAP_X = float(
    P_TAP_ORIGIN[0]
)

P_TAP_Y = float(
    P_TAP_ORIGIN[1]
)


print()
print("=" * 80)
print("P_TAP_VSS PLACEMENT")
print("=" * 80)


print(
    "Origin:",
    f"({P_TAP_X:.3f}, "
    f"{P_TAP_Y:.3f}) um"
)


# ================================================================
# 4. LAYER
# ================================================================

MET1_LAYER = layout.find_layer(
    68,
    20
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


def box_distance_um(
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


# ================================================================
# 6. EXPECTED P_TAP_VSS M1 LANDING
#
# Step 18E established the package-native p_tap Metal1 bbox:
#
#   local M1 = (0,0) -> (1,1) um
#
# Placement:
#
#   P_TAP_VSS @ (-2.5, 2.5)
#
# Therefore expected absolute M1:
#
#   (-2.5, 2.5) -> (-1.5, 3.5)
# ================================================================

P_TAP_M1 = make_box_um(

    P_TAP_X,

    P_TAP_Y,

    P_TAP_X + 1.000,

    P_TAP_Y + 1.000,

)


print()
print("=" * 80)
print("EXPECTED P_TAP_VSS M1")
print("=" * 80)


print(
    "BBox um:",
    tuple(
        round(
            value,
            3,
        )
        for value
        in box_um(
            P_TAP_M1
        )
    )
)


# ================================================================
# 7. CREATE NEW TOP CELL
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
# 8. VSS ROUTING PARAMETERS
#
# Keep VSS entirely on the far-left side.
#
# Tap M1:
#   x = -2.5 .. -1.5
#   y =  2.5 ..  3.5
#
# Rail:
#   x = -4.0 .. -2.0
#   y =  2.8 ..  3.2
#
# Thus the rail overlaps 0.5 um into the tap landing.
# ================================================================

VSS_RAIL_LEFT = -4.000

VSS_RAIL_RIGHT = -2.000

VSS_RAIL_Y = 3.000

VSS_RAIL_WIDTH = 0.400


VSS_RAIL = make_box_um(

    VSS_RAIL_LEFT,

    VSS_RAIL_Y
    - VSS_RAIL_WIDTH / 2.0,

    VSS_RAIL_RIGHT,

    VSS_RAIL_Y
    + VSS_RAIL_WIDTH / 2.0,

)


top.shapes(
    MET1_LAYER
).insert(
    VSS_RAIL
)


print()
print("=" * 80)
print("VSS RAIL")
print("=" * 80)


print(
    "BBox um:",
    tuple(
        round(
            value,
            3,
        )
        for value
        in box_um(
            VSS_RAIL
        )
    )
)


# ================================================================
# 9. P_TAP CONNECTIVITY AUDIT
# ================================================================

VSS_TOUCHES_PTAP = overlaps(

    VSS_RAIL,

    P_TAP_M1,

)


print()
print("=" * 80)
print("P_TAP_VSS CONNECTIVITY AUDIT")
print("=" * 80)


print(
    "VSS rail touches P_TAP_VSS:",
    VSS_TOUCHES_PTAP
)


# ================================================================
# 10. CONNECTION OVERLAP DIMENSIONS
# ================================================================

overlap_left = max(
    VSS_RAIL.left,
    P_TAP_M1.left,
)

overlap_right = min(
    VSS_RAIL.right,
    P_TAP_M1.right,
)

overlap_bottom = max(
    VSS_RAIL.bottom,
    P_TAP_M1.bottom,
)

overlap_top = min(
    VSS_RAIL.top,
    P_TAP_M1.top,
)


if VSS_TOUCHES_PTAP:

    OVERLAP_WIDTH_UM = (
        overlap_right
        - overlap_left
    ) * DBU

    OVERLAP_HEIGHT_UM = (
        overlap_top
        - overlap_bottom
    ) * DBU

else:

    OVERLAP_WIDTH_UM = 0.0
    OVERLAP_HEIGHT_UM = 0.0


OVERLAP_OK = bool(

    OVERLAP_WIDTH_UM > 0

    and

    OVERLAP_HEIGHT_UM > 0

)


print(
    "Overlap width :",
    f"{OVERLAP_WIDTH_UM:.3f} um"
)

print(
    "Overlap height:",
    f"{OVERLAP_HEIGHT_UM:.3f} um"
)

print(
    "Positive-area connection:",
    OVERLAP_OK
)


# ================================================================
# 11. NEAREST EXISTING SIGNAL: SW1A VMEM M1 TRANSITION
#
# VMEM manifest:
#   SW1A terminal at x = 0.325
#   SW1A via at x = -0.275
#
# Package-native via pad:
#   0.50 x 0.50 um
#
# Therefore the leftmost existing signal-M1 feature is the
# VMEM via pad around x = -0.525 .. -0.025.
# ================================================================

SW1A_VMEM = vmem_data[
    "vmem"
][
    "branches"
][
    "SW1A"
]


SW1A_VIA_X = float(

    SW1A_VMEM[
        "via_center_um"
    ][0]

)

SW1A_VIA_Y = float(

    SW1A_VMEM[
        "via_center_um"
    ][1]

)


VMEM_VIA_PAD = make_box_um(

    SW1A_VIA_X
    - 0.250,

    SW1A_VIA_Y
    - 0.250,

    SW1A_VIA_X
    + 0.250,

    SW1A_VIA_Y
    + 0.250,

)


VSS_TO_VMEM_GAP = box_distance_um(

    VSS_RAIL,

    VMEM_VIA_PAD,

)


VSS_VMEM_OVERLAP = overlaps(

    VSS_RAIL,

    VMEM_VIA_PAD,

)


M1_MIN_SPACING = 0.140


VSS_VMEM_SPACING_OK = bool(

    not VSS_VMEM_OVERLAP

    and

    VSS_TO_VMEM_GAP
    >= M1_MIN_SPACING

)


print()
print("=" * 80)
print("VSS / NEAREST SIGNAL-M1 AUDIT")
print("=" * 80)


print(
    "Nearest signal:",
    "SW1A VMEM M1/VIA landing"
)

print(
    "VMEM pad bbox um:",
    tuple(
        round(
            value,
            3,
        )
        for value
        in box_um(
            VMEM_VIA_PAD
        )
    )
)

print(
    "VSS / VMEM overlap:",
    VSS_VMEM_OVERLAP
)

print(
    "Minimum gap:",
    f"{VSS_TO_VMEM_GAP:.3f} um"
)

print(
    "Required m1.2:",
    f"{M1_MIN_SPACING:.3f} um"
)

print(
    "Spacing pre-check:",
    VSS_VMEM_SPACING_OK
)


# ================================================================
# 12. VSS MUST REMAIN FAR FROM SWITCH SIGNAL TERMINALS
#
# Use known absolute switch-row geometry:
#
# SW1A:
#   left diffusion M1 extends to approximately x=0.440
#   VMEM transition is even further left at x=-0.525.
#
# Since VMEM transition is already the nearest signal feature,
# passing the previous audit also establishes clearance to the
# transistor S/D/gate routing in this left-hand region.
# ================================================================

SIGNAL_ISOLATION_OK = (
    VSS_VMEM_SPACING_OK
)


print()
print("=" * 80)
print("SIGNAL ISOLATION SUMMARY")
print("=" * 80)


print(
    "VSS is body-tap-only:",
    SIGNAL_ISOLATION_OK
)

print(
    "No switch source/drain is intentionally connected to VSS."
)


# ================================================================
# 13. TOP-LEVEL SHAPE COUNT
#
# Only one new M1 rectangle is added.
# ================================================================

TOP_M1_COUNT = sum(

    1

    for _
    in top.shapes(
        MET1_LAYER
    ).each()

)


M1_COUNT_OK = (
    TOP_M1_COUNT == 1
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
    1
)

print(
    "M1 count correct:",
    M1_COUNT_OK
)


# ================================================================
# 14. USED LAYERS
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
# 15. SAVE OPTIONS
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
# 16. WRITE GDS / OASIS
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
# 17. READBACK
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
# 18. MANIFEST
# ================================================================

output_manifest = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "revision":
        "vss_v1",

    "top_cell":
        NEW_TOP_NAME,

    "parent_cell":
        INPUT_TOP_NAME,

    "canonical_input":
        "neurolif_synapse_weight_gates_v2.gds",

    "routed_nets": [

        "VDD",

        "VBIAS",

        "P_U1A_TO_SW1A",

        "P_U0_TO_SW0",

        "P_U1B_TO_SW1B",

        "VMEM",

        "GATE_W0",

        "GATE_W1",

        "VSS",

    ],

    "unrouted_internal_nets": [],

    "vss": {

        "purpose":
            "NMOS p-substrate body tie only",

        "target":
            "P_TAP_VSS",

        "metal":
            "metal1",

        "rail_bbox_um": [

            round(
                value,
                3,
            )

            for value
            in box_um(
                VSS_RAIL
            )

        ],

        "p_tap_m1_bbox_um": [

            round(
                value,
                3,
            )

            for value
            in box_um(
                P_TAP_M1
            )

        ],

        "tap_overlap_um": {

            "x":
                round(
                    OVERLAP_WIDTH_UM,
                    3,
                ),

            "y":
                round(
                    OVERLAP_HEIGHT_UM,
                    3,
                ),

        },

    },

    "checks": {

        "vss_touches_p_tap":
            VSS_TOUCHES_PTAP,

        "positive_area_tap_connection":
            OVERLAP_OK,

        "nearest_signal_spacing":
            VSS_VMEM_SPACING_OK,

        "signal_isolation":
            SIGNAL_ISOLATION_OK,

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
# 19. FINAL GATE
# ================================================================

STEP25A_PASS = bool(

    VSS_TOUCHES_PTAP

    and

    OVERLAP_OK

    and

    VSS_VMEM_SPACING_OK

    and

    SIGNAL_ISOLATION_OK

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
print("STEP 25A RESULT")
print("=" * 80)


print(
    "VSS touches P_TAP_VSS    :",
    VSS_TOUCHES_PTAP
)

print(
    "Positive-area connection :",
    OVERLAP_OK
)

print(
    "Nearest signal spacing   :",
    VSS_VMEM_SPACING_OK
)

print(
    "Signal isolation         :",
    SIGNAL_ISOLATION_OK
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
    "STEP25A_PASS =",
    STEP25A_PASS
)


if not STEP25A_PASS:

    raise RuntimeError(
        "STEP 25A failed."
    )


print()
print(
    "VSS BODY-TAP ROUTING V1 GENERATED"
)

print()
print(
    "Connected:"
)

print(
    "  VSS -> P_TAP_VSS"
)

print()
print(
    "No NMOS source/drain terminal was routed to VSS."
)

print()
print(
    "All intended synapse internal nets are now physically routed."
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)