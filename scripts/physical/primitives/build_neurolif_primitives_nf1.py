# ================================================================
# NeuroLIF-SKY130
# STEP 17A — Corrected single-finger MOS primitive library
#
# CRITICAL FIX:
#   Explicit nf=1 for EVERY transistor.
#   Explicit interdig=0.
#
# Run:
#   python scripts\physical\primitives\build_neurolif_primitives_nf1.py
# ================================================================

from pathlib import Path
from importlib.metadata import version
import json
import sys
import traceback

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 17A: CORRECTED SINGLE-FINGER PRIMITIVES")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

SKY130_PYTHON_ROOT = (
    Path.home()
    / "KLayout"
    / "salt"
    / "Efabless_sky130"
    / "tech"
    / "sky130"
    / "python"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "layout"
    / "primitives"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT_GDS = (
    OUTPUT_DIR
    / "neurolif_mos_primitives_nf1.gds"
)

OUTPUT_OAS = (
    OUTPUT_DIR
    / "neurolif_mos_primitives_nf1.oas"
)

MANIFEST_FILE = (
    OUTPUT_DIR
    / "neurolif_mos_primitives_nf1.json"
)


print()
print("SKY130 Python root :", SKY130_PYTHON_ROOT)
print("Output GDS         :", OUTPUT_GDS)
print("Output OASIS       :", OUTPUT_OAS)
print("Manifest           :", MANIFEST_FILE)


if not SKY130_PYTHON_ROOT.exists():

    raise FileNotFoundError(
        SKY130_PYTHON_ROOT
    )


# ================================================================
# 2. IMPORT SKY130 GENERATOR
# ================================================================

sky130_path = str(
    SKY130_PYTHON_ROOT
)

if sky130_path not in sys.path:

    sys.path.insert(
        0,
        sky130_path
    )


try:

    import gdsfactory
    import kfactory

    from cells.draw_fet import (
        draw_nfet,
        draw_pfet,
    )

except Exception:

    print()
    print("IMPORT FAILURE")
    traceback.print_exc()

    raise


print()
print("=" * 80)
print("ENVIRONMENT")
print("=" * 80)

print(
    "gdsfactory :",
    version("gdsfactory")
)

print(
    "kfactory   :",
    version("kfactory")
)

print(
    "klayout    :",
    version("klayout")
)

print(
    "Generator import : PASS"
)


# ================================================================
# 3. FROZEN DEVICE DEFINITIONS
# ================================================================

DEVICES = [

    {
        "name": "N_LOGIC_W1000_L0150",
        "kind": "nfet",
        "type": "sky130_fd_pr__nfet_01v8",
        "w": 1.00,
        "l": 0.15,
        "roles": [
            "main Schmitt NMOS",
            "synapse switch NMOS",
            "output inverter NMOS",
        ],
    },

    {
        "name": "P_LOGIC_W2000_L0150",
        "kind": "pfet",
        "type": "sky130_fd_pr__pfet_01v8",
        "w": 2.00,
        "l": 0.15,
        "roles": [
            "main Schmitt PMOS",
            "output inverter PMOS",
        ],
    },

    {
        "name": "N_FB_W0420_L0300",
        "kind": "nfet",
        "type": "sky130_fd_pr__nfet_01v8",
        "w": 0.42,
        "l": 0.30,
        "roles": [
            "Schmitt NFET feedback",
        ],
    },

    {
        "name": "P_FB_W0420_L0300",
        "kind": "pfet",
        "type": "sky130_fd_pr__pfet_01v8",
        "w": 0.42,
        "l": 0.30,
        "roles": [
            "Schmitt PFET feedback",
        ],
    },

    {
        "name": "P_SYN_W0840_L0500",
        "kind": "pfet",
        "type": "sky130_fd_pr__pfet_01v8",
        "w": 0.84,
        "l": 0.50,
        "roles": [
            "PMOS current-mirror reference",
            "synaptic unit PMOS 0",
            "synaptic unit PMOS 1A",
            "synaptic unit PMOS 1B",
        ],
    },

    {
        "name": "N_LEAK_W0420_L1000",
        "kind": "nfet",
        "type": "sky130_fd_pr__nfet_01v8",
        "w": 0.42,
        "l": 1.00,
        "roles": [
            "membrane leak transistor",
        ],
    },

    {
        "name": "N_RESET_W1200_L0150",
        "kind": "nfet",
        "type": "sky130_fd_pr__nfet_01v8",
        "w": 1.20,
        "l": 0.15,
        "roles": [
            "SPIKE-controlled membrane reset",
        ],
    },

]


# ================================================================
# 4. CREATE DATABASE
# ================================================================

layout = kdb.Layout()

layout.dbu = 0.001


print()
print("=" * 80)
print("DATABASE")
print("=" * 80)

print(
    "DBU:",
    layout.dbu,
    "um"
)


# ================================================================
# 5. GENERATE ALL DEVICES
#
# IMPORTANT:
#   nf=1 is explicit for BOTH NFET and PFET.
#
#   interdig=0 is explicit.
#
# This prevents generator defaults from silently changing
# physical transistor multiplicity.
# ================================================================

generated = {}


print()
print("=" * 80)
print("GENERATING CORRECTED PRIMITIVES")
print("=" * 80)


for index, device in enumerate(
    DEVICES,
    start=1,
):

    name = device["name"]

    print()
    print(
        f"[{index}/{len(DEVICES)}] {name}"
    )

    print(
        f"    kind = {device['kind']}"
    )

    print(
        f"    W    = {device['w']:.3f} um"
    )

    print(
        f"    L    = {device['l']:.3f} um"
    )

    print(
        "    nf   = 1"
    )

    print(
        "    interdig = 0"
    )


    cell = layout.create_cell(
        name
    )


    try:

        if device["kind"] == "nfet":

            draw_nfet(

                cell=cell,

                l=device["l"],

                w=device["w"],

                nf=1,

                interdig=0,

                type=device["type"],

            )


        elif device["kind"] == "pfet":

            draw_pfet(

                cell=cell,

                l=device["l"],

                w=device["w"],

                nf=1,

                interdig=0,

                type=device["type"],

            )


        else:

            raise ValueError(
                device["kind"]
            )


    except Exception:

        print()
        print(
            "GENERATION FAILURE:",
            name
        )

        traceback.print_exc()

        raise


    bbox = cell.bbox()


    if bbox.empty():

        raise RuntimeError(
            f"{name} generated empty geometry."
        )


    generated[name] = {
        "cell": cell,
        "bbox": bbox,
        "definition": device,
    }


    print(
        "    bbox =",
        bbox
    )

    print(
        "    geometry = PASS"
    )


# ================================================================
# 6. CRITICAL PHYSICAL FINGER AUDIT
#
# Count POLY shapes actually crossing DIFF.
#
# Every primitive MUST have exactly one physical gate finger.
# ================================================================

print()
print("=" * 80)
print("PHYSICAL FINGER AUDIT")
print("=" * 80)


DIFF_LAYER = layout.find_layer(
    65,
    20
)

POLY_LAYER = layout.find_layer(
    66,
    20
)


def overlap(
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


finger_counts = {}


for device in DEVICES:

    name = device["name"]

    cell = generated[
        name
    ]["cell"]


    diff_boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            DIFF_LAYER
        ).each()

    ]


    poly_boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            POLY_LAYER
        ).each()

    ]


    crossing = [

        p

        for p in poly_boxes

        if any(
            overlap(
                p,
                d
            )

            for d in diff_boxes
        )

    ]


    finger_counts[
        name
    ] = len(
        crossing
    )


    print(
        f"{name:24s} -> "
        f"physical gate fingers = "
        f"{len(crossing)}"
    )


ALL_SINGLE_FINGER = all(

    count == 1

    for count
    in finger_counts.values()

)


print()
print(
    "ALL_SINGLE_FINGER =",
    ALL_SINGLE_FINGER
)


if not ALL_SINGLE_FINGER:

    raise RuntimeError(
        "One or more corrected primitives "
        "still contain multiple physical gate fingers."
    )


# ================================================================
# 7. CREATE AUDIT TOP CELL
# ================================================================

TOP_NAME = (
    "NEUROLIF_MOS_PRIMITIVES_NF1"
)

top = layout.create_cell(
    TOP_NAME
)


x_um = 0.0
SPACING_UM = 10.0


print()
print("=" * 80)
print("BUILDING AUDIT TOP CELL")
print("=" * 80)


for device in DEVICES:

    name = device["name"]

    primitive = generated[
        name
    ]["cell"]


    x_dbu = int(
        round(
            x_um
            / layout.dbu
        )
    )


    top.insert(

        kdb.CellInstArray(

            primitive.cell_index(),

            kdb.Trans(
                x_dbu,
                0
            ),

        )

    )


    print(
        f"{name} -> "
        f"x={x_um:.3f} um"
    )


    primitive_width_um = (

        primitive
        .bbox()
        .width()

        * layout.dbu

    )


    x_um += (
        primitive_width_um
        + SPACING_UM
    )


if top.bbox().empty():

    raise RuntimeError(
        "Audit top is empty."
    )


print()
print(
    "Audit bbox:",
    top.bbox()
)


# ================================================================
# 8. LAYER INVENTORY
# ================================================================

print()
print("=" * 80)
print("LAYER INVENTORY")
print("=" * 80)


used_layers = []


for layer_index in layout.layer_indexes():

    used = False


    for record in generated.values():

        shapes = record[
            "cell"
        ].shapes(
            layer_index
        )

        if not shapes.is_empty():

            used = True
            break


    if not used:

        continue


    info = layout.get_info(
        layer_index
    )


    entry = {

        "internal_index": int(
            layer_index
        ),

        "layer": int(
            info.layer
        ),

        "datatype": int(
            info.datatype
        ),

    }


    used_layers.append(
        entry
    )


    print(

        f"Internal "
        f"{entry['internal_index']} "

        f"-> GDS "
        f"{entry['layer']}/"
        f"{entry['datatype']}"

    )


# ================================================================
# 9. SANITY CHECK STREAM LAYERS
# ================================================================

for entry in used_layers:

    if not (
        0 <= entry["layer"] <= 65535
        and
        0 <= entry["datatype"] <= 65535
    ):

        raise RuntimeError(
            f"Illegal layer: {entry}"
        )


print()
print(
    "GDS stream layer sanity: PASS"
)


# ================================================================
# 10. EXPLICIT SAVE OPTIONS
# ================================================================

def save_options(
    fmt,
):

    options = (
        kdb.SaveLayoutOptions()
    )

    options.format = fmt

    options.deselect_all_layers()


    for entry in used_layers:

        options.add_layer(

            entry[
                "internal_index"
            ],

            kdb.LayerInfo(

                entry["layer"],

                entry["datatype"],

            ),

        )


    return options


# ================================================================
# 11. WRITE GDS
# ================================================================

OUTPUT_GDS.unlink(
    missing_ok=True
)


layout.write(

    str(
        OUTPUT_GDS
    ),

    save_options(
        "GDS2"
    ),

)


GDS_OK = bool(

    OUTPUT_GDS.exists()

    and

    OUTPUT_GDS.stat().st_size > 0

)


print()
print("=" * 80)
print("GDS OUTPUT")
print("=" * 80)

print(
    "GDS exists:",
    OUTPUT_GDS.exists()
)

if OUTPUT_GDS.exists():

    print(
        "GDS size:",
        OUTPUT_GDS.stat().st_size,
        "bytes"
    )


# ================================================================
# 12. WRITE OASIS
# ================================================================

OUTPUT_OAS.unlink(
    missing_ok=True
)


layout.write(

    str(
        OUTPUT_OAS
    ),

    save_options(
        "OASIS"
    ),

)


OAS_OK = bool(

    OUTPUT_OAS.exists()

    and

    OUTPUT_OAS.stat().st_size > 0

)


print(
    "OASIS output:",
    "PASS"
    if OAS_OK
    else "FAIL"
)


# ================================================================
# 13. READ-BACK CHECK
# ================================================================

verify = kdb.Layout()

verify.read(
    str(
        OUTPUT_GDS
    )
)


verify_top = verify.cell(
    TOP_NAME
)


READBACK_OK = bool(

    verify_top is not None

    and

    not verify_top.bbox().empty()

)


print()
print("=" * 80)
print("GDS READ-BACK")
print("=" * 80)

print(
    "Cell count:",
    verify.cells()
)

print(
    "Top found:",
    verify_top is not None
)

print(
    "Read-back:",
    "PASS"
    if READBACK_OK
    else "FAIL"
)


# ================================================================
# 14. MANIFEST
# ================================================================

manifest_devices = []


for device in DEVICES:

    name = device["name"]

    bbox = generated[
        name
    ]["bbox"]


    manifest_devices.append({

        **device,

        "nf": 1,

        "interdig": 0,

        "physical_gate_fingers":
            finger_counts[
                name
            ],

        "bbox_dbu": [

            int(
                bbox.left
            ),

            int(
                bbox.bottom
            ),

            int(
                bbox.right
            ),

            int(
                bbox.top
            ),

        ],

    })


manifest = {

    "project":
        "NeuroLIF-SKY130",

    "primitive_revision":
        "nf1_corrected",

    "technology":
        "SKY130",

    "dbu_um":
        layout.dbu,

    "generator_rule":
        "All MOS primitives generated "
        "with explicit nf=1 and interdig=0.",

    "deprecated_previous_library":
        "neurolif_mos_primitives.gds",

    "canonical_candidate":
        OUTPUT_GDS.name,

    "top_cell":
        TOP_NAME,

    "all_single_finger":
        ALL_SINGLE_FINGER,

    "devices":
        manifest_devices,

    "used_layers":
        used_layers,

    "synapse_constraint":
        (
            "P_SYN_W0840_L0500 is one "
            "W=0.84um L=0.50um PMOS. "
            "Weight 2 uses two identical "
            "instances in parallel. "
            "Weight 3 uses three identical "
            "instances."
        ),

}


MANIFEST_FILE.write_text(

    json.dumps(
        manifest,
        indent=2,
    ),

    encoding="utf-8",

)


MANIFEST_OK = bool(

    MANIFEST_FILE.exists()

    and

    MANIFEST_FILE.stat().st_size > 0

)


# ================================================================
# 15. FINAL RESULT
# ================================================================

STEP17A_PASS = bool(

    len(generated) == 7

    and

    ALL_SINGLE_FINGER

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
print("STEP 17A RESULT")
print("=" * 80)


print(
    "Primitive count       :",
    len(generated)
)

print(
    "All single-finger     :",
    ALL_SINGLE_FINGER
)

print(
    "GDS write             :",
    GDS_OK
)

print(
    "OASIS write           :",
    OAS_OK
)

print(
    "GDS read-back         :",
    READBACK_OK
)

print(
    "Manifest write        :",
    MANIFEST_OK
)

print()
print(
    "STEP17A_PASS =",
    STEP17A_PASS
)


if not STEP17A_PASS:

    raise RuntimeError(
        "STEP 17A failed."
    )


print()
print(
    "CORRECTED SINGLE-FINGER "
    "PRIMITIVE LIBRARY GENERATED"
)

print()
print(
    "GDS:"
)

print(
    OUTPUT_GDS
)

print()
print(
    "IMPORTANT:"
)

print(
    "Do not use the old "
    "neurolif_mos_primitives.gds "
    "for the final circuit."
)