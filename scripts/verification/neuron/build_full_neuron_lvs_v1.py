# ================================================================
# NeuroLIF-SKY130
# STEP 40A — Build FULL-NEURON LVS derivative + reference SPICE
#
# Input physical GDS:
#   neurolif_full_neuron_final_routed_v1.gds
#
# Output LVS-only GDS:
#   neurolif_full_neuron_lvs_v1.gds
#
# Output reference:
#   neurolif_full_neuron_lvs_reference_v1.spice
#
# IMPORTANT:
#   NO physical geometry may be changed.
#
#   The derivative adds ONLY text labels on MET1 label layer 68/5:
#
#       VDD
#       VSS
#       VBIAS
#       GATE_W0
#       GATE_W1
#       VLEAK
#       VMEM
#       SPIKE
#
# Physical Cmem remains external and is NOT included as a device.
#
# Expected extracted MOS:
#   PFET = 8
#   NFET = 9
#   TOTAL = 17
# ================================================================

from pathlib import Path
import hashlib
import json
import re

import klayout.db as kdb


print("=" * 80)
print("STEP 40A — FULL-NEURON LVS DERIVATIVE + REFERENCE")
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
    / "neurolif_full_neuron_final_routed_v1.gds"
)

FINAL_DRC_REPORT = (
    PROJECT_ROOT
    / "verification"
    / "neuron"
    / "drc"
    / "neurolif_full_neuron_final_routed_v1_drc.lyrdb"
)

CONNECTIVITY_AUDIT = (
    PROJECT_ROOT
    / "verification"
    / "neuron"
    / "connectivity"
    / "neurolif_full_neuron_final_connectivity_audit_v1.json"
)


OUTPUT_GDS = (
    NEURON_DIR
    / "neurolif_full_neuron_lvs_v1.gds"
)

OUTPUT_OAS = (
    NEURON_DIR
    / "neurolif_full_neuron_lvs_v1.oas"
)

REFERENCE_SPICE = (
    PROJECT_ROOT
    / "circuit"
    / "lvs"
    / "neurolif_full_neuron_lvs_reference_v1.spice"
)

OUTPUT_MANIFEST = (
    NEURON_DIR
    / "neurolif_full_neuron_lvs_v1.json"
)


INPUT_TOP = (
    "NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1"
)

OUTPUT_TOP = (
    "NEUROLIF_FULL_NEURON_LVS_V1"
)


for path in [
    INPUT_GDS,
    FINAL_DRC_REPORT,
    CONNECTIVITY_AUDIT,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. HASH
# ================================================================

def sha256_file(path):

    h = hashlib.sha256()

    with path.open("rb") as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            h.update(block)

    return h.hexdigest()


INPUT_HASH = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. VERIFY STEP 39A CHAIN OF CUSTODY
# ================================================================

audit = json.loads(

    CONNECTIVITY_AUDIT.read_text(
        encoding="utf-8"
    )

)


AUDIT_PASS = bool(
    audit.get(
        "step39a_pass",
        False
    )
)


AUDIT_GDS_HASH = (

    audit
    .get(
        "input",
        {}
    )
    .get(
        "sha256"
    )

)


AUDIT_HASH_MATCH = (
    AUDIT_GDS_HASH
    ==
    INPUT_HASH
)


print()
print("=" * 80)
print("PRE-LVS VERIFICATION CHAIN")
print("=" * 80)

print(
    "Step 39A audit PASS :",
    AUDIT_PASS
)

print(
    "Audit GDS hash match:",
    AUDIT_HASH_MATCH
)

print(
    "Final DRC exists    :",
    FINAL_DRC_REPORT.exists()
)


if not (
    AUDIT_PASS
    and
    AUDIT_HASH_MATCH
):

    raise RuntimeError(
        "Final GDS does not match the passed Step-39A audit."
    )


# ================================================================
# 4. LOAD FINAL PHYSICAL GDS
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)


DBU = layout.dbu


input_top = layout.cell(
    INPUT_TOP
)


if input_top is None:

    raise RuntimeError(
        f"Missing input top: {INPUT_TOP}"
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
    INPUT_TOP
)


# ================================================================
# 5. PHYSICAL + LABEL LAYERS
# ================================================================

M1_LAYER = layout.find_layer(
    68,
    20
)

M2_LAYER = layout.find_layer(
    69,
    20
)


if M1_LAYER is None:

    raise RuntimeError(
        "Missing MET1 68/20."
    )


if M2_LAYER is None:

    raise RuntimeError(
        "Missing MET2 69/20."
    )


# Official SKY130 LVS label purposes discovered during synapse LVS.
M1_LABEL_LAYER = layout.layer(
    kdb.LayerInfo(
        68,
        5
    )
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


def centered_box(
    x,
    y,
    width,
):

    return kdb.Box(

        to_dbu(
            x - width / 2
        ),

        to_dbu(
            y - width / 2
        ),

        to_dbu(
            x + width / 2
        ),

        to_dbu(
            y + width / 2
        ),

    )


# ================================================================
# 7. LVS PIN LABEL LOCATIONS
#
# Every coordinate lies directly on an already-verified M1
# terminal belonging to the corresponding electrical net.
#
# These labels are extraction aids only.
# ================================================================

LABEL_POINTS = {

    # MP_ST1 source = VDD
    "VDD":
        (
            16.150,
            15.000,
        ),

    # MN_ST2 source = VSS
    "VSS":
        (
            20.150,
            7.500,
        ),

    # P_REF gate/drain network
    "VBIAS":
        (
            3.550,
            7.635,
        ),

    # SW0 gate
    "GATE_W0":
        (
            6.550,
            2.135,
        ),

    # SW1A gate, same net as SW1B gate
    "GATE_W1":
        (
            0.550,
            2.135,
        ),

    # MN_LEAK gate
    "VLEAK":
        (
            32.800,
            6.635,
        ),

    # MN_LEAK drain = VMEM
    "VMEM":
        (
            33.450,
            7.210,
        ),

    # MN_BUF drain = SPIKE
    "SPIKE":
        (
            28.600,
            7.500,
        ),

}


EXPECTED_LABELS = [

    "VDD",
    "VSS",
    "VBIAS",
    "GATE_W0",
    "GATE_W1",
    "VLEAK",
    "VMEM",
    "SPIKE",

]


LABEL_SET_OK = (
    list(
        LABEL_POINTS.keys()
    )
    ==
    EXPECTED_LABELS
)


# ================================================================
# 8. VERIFY EVERY LABEL POINT IS ON M1
# ================================================================

M1_REGION = kdb.Region(

    input_top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


LABEL_ON_M1 = {}


for name, point in LABEL_POINTS.items():

    probe = kdb.Region(

        centered_box(

            point[0],

            point[1],

            0.020,

        )

    )


    LABEL_ON_M1[
        name
    ] = not (

        probe
        &
        M1_REGION

    ).is_empty()


LABEL_POINTS_VALID = all(
    LABEL_ON_M1.values()
)


print()
print("=" * 80)
print("LVS LABEL LANDING AUDIT")
print("=" * 80)


for name in EXPECTED_LABELS:

    print(
        f"{name:10s}: "
        f"point={LABEL_POINTS[name]} "
        f"on_M1={LABEL_ON_M1[name]}"
    )


print(
    "All labels land on MET1:",
    LABEL_POINTS_VALID
)


if not (
    LABEL_SET_OK
    and
    LABEL_POINTS_VALID
):

    raise RuntimeError(
        "One or more LVS labels do not land on verified MET1."
    )


# ================================================================
# 9. SAVE ORIGINAL PHYSICAL REGIONS
#
# Snapshot every populated layer except LVS text-label layers.
# This lets us prove that the derivative changes no physical
# geometry.
# ================================================================

ORIGINAL_LAYER_REGIONS = {}


for layer_index in layout.layer_indexes():

    info = layout.get_info(
        layer_index
    )


    key = (
        int(
            info.layer
        ),
        int(
            info.datatype
        ),
    )


    if key in {
        (68, 5),
        (69, 5),
    }:

        continue


    region = kdb.Region(

        input_top.begin_shapes_rec(
            layer_index
        )

    ).merged()


    if region.is_empty():

        continue


    ORIGINAL_LAYER_REGIONS[
        key
    ] = region


print()
print(
    "Original populated physical layers:",
    len(
        ORIGINAL_LAYER_REGIONS
    )
)


# ================================================================
# 10. CREATE LVS WRAPPER TOP
#
# The verified physical core remains an unchanged child instance.
# Only labels are added in this new wrapper.
# ================================================================

if layout.cell(
    OUTPUT_TOP
) is not None:

    raise RuntimeError(
        f"Output top already exists: {OUTPUT_TOP}"
    )


lvs_top = layout.create_cell(
    OUTPUT_TOP
)


lvs_top.insert(

    kdb.CellInstArray(

        input_top.cell_index(),

        kdb.Trans(
            0,
            0
        ),

    )

)


# ================================================================
# 11. ADD LABELS — MET1 LABEL 68/5 ONLY
# ================================================================

for name, point in LABEL_POINTS.items():

    x = to_dbu(
        point[0]
    )

    y = to_dbu(
        point[1]
    )


    text = kdb.Text(

        name,

        kdb.Trans(
            x,
            y
        ),

    )


    lvs_top.shapes(
        M1_LABEL_LAYER
    ).insert(
        text
    )


DIRECT_LABEL_COUNT = sum(

    1

    for shape
    in lvs_top.shapes(
        M1_LABEL_LAYER
    ).each()

    if shape.is_text()

)


LABEL_COUNT_OK = (
    DIRECT_LABEL_COUNT
    ==
    8
)


print()
print("=" * 80)
print("LVS LABEL INSERTION")
print("=" * 80)

print(
    "MET1 labels inserted:",
    DIRECT_LABEL_COUNT
)

print(
    "Expected:",
    8
)

print(
    "Label count correct:",
    LABEL_COUNT_OK
)


# ================================================================
# 12. BUILD FROZEN 17-MOS REFERENCE SPICE
#
# Standard device syntax:
#
#   Mname D G S B model W=... L=...
#
# Internal synapse branch names are arbitrary reference-net names.
# KLayout LVS compares topology.
#
# Source/drain symmetry is handled by the standard MOS LVS model.
# ================================================================

spice_lines = [

    "* ============================================================",
    "* NeuroLIF-SKY130 — full-neuron LVS reference v1",
    "*",
    "* Pre-silicon educational SKY130 neuron core.",
    "* Physical Cmem is intentionally external.",
    "* Expected MOS: 17 total = 8 PFET + 9 NFET.",
    "* ============================================================",
    "",

    ".subckt NEUROLIF_FULL_NEURON_LVS_V1 "
    "VDD VSS VBIAS GATE_W0 GATE_W1 VLEAK VMEM SPIKE",

    "",

    "* ------------------------------------------------------------",
    "* Corrected 2-bit weighted synapse — 7 MOS",
    "* ------------------------------------------------------------",

    "MP_REF VBIAS VBIAS VDD VDD "
    "sky130_fd_pr__pfet_01v8 w=0.84u l=0.50u",

    "MP_U1A SYN_BR_U1A VBIAS VDD VDD "
    "sky130_fd_pr__pfet_01v8 w=0.84u l=0.50u",

    "MP_U0 SYN_BR_U0 VBIAS VDD VDD "
    "sky130_fd_pr__pfet_01v8 w=0.84u l=0.50u",

    "MP_U1B SYN_BR_U1B VBIAS VDD VDD "
    "sky130_fd_pr__pfet_01v8 w=0.84u l=0.50u",

    "MN_SW1A SYN_BR_U1A GATE_W1 VMEM VSS "
    "sky130_fd_pr__nfet_01v8 w=1.00u l=0.15u",

    "MN_SW0 SYN_BR_U0 GATE_W0 VMEM VSS "
    "sky130_fd_pr__nfet_01v8 w=1.00u l=0.15u",

    "MN_SW1B SYN_BR_U1B GATE_W1 VMEM VSS "
    "sky130_fd_pr__nfet_01v8 w=1.00u l=0.15u",

    "",

    "* ------------------------------------------------------------",
    "* Corrected 6T Schmitt threshold detector",
    "* ------------------------------------------------------------",

    "MP_ST1 P_MID VMEM VDD VDD "
    "sky130_fd_pr__pfet_01v8 w=2.00u l=0.15u",

    "MP_ST2 VRAW VMEM P_MID VDD "
    "sky130_fd_pr__pfet_01v8 w=2.00u l=0.15u",

    "MN_ST1 VRAW VMEM N_MID VSS "
    "sky130_fd_pr__nfet_01v8 w=1.00u l=0.15u",

    "MN_ST2 N_MID VMEM VSS VSS "
    "sky130_fd_pr__nfet_01v8 w=1.00u l=0.15u",

    "MN_FB VDD VRAW N_MID VSS "
    "sky130_fd_pr__nfet_01v8 w=0.42u l=0.30u",

    "MP_FB VSS VRAW P_MID VDD "
    "sky130_fd_pr__pfet_01v8 w=0.42u l=0.30u",

    "",

    "* ------------------------------------------------------------",
    "* Output inverter",
    "* ------------------------------------------------------------",

    "MP_BUF SPIKE VRAW VDD VDD "
    "sky130_fd_pr__pfet_01v8 w=2.00u l=0.15u",

    "MN_BUF SPIKE VRAW VSS VSS "
    "sky130_fd_pr__nfet_01v8 w=1.00u l=0.15u",

    "",

    "* ------------------------------------------------------------",
    "* Leak + spike reset",
    "* ------------------------------------------------------------",

    "MN_LEAK VMEM VLEAK VSS VSS "
    "sky130_fd_pr__nfet_01v8 w=0.42u l=1.00u",

    "MN_RST VMEM SPIKE VSS VSS "
    "sky130_fd_pr__nfet_01v8 w=1.20u l=0.15u",

    "",

    ".ends NEUROLIF_FULL_NEURON_LVS_V1",
    "",

]


REFERENCE_SPICE.write_text(

    "\n".join(
        spice_lines
    ),

    encoding="utf-8",

)


REFERENCE_EXISTS = bool(

    REFERENCE_SPICE.exists()

    and

    REFERENCE_SPICE.stat().st_size > 0

)


# ================================================================
# 13. REFERENCE SPICE STRUCTURAL AUDIT
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8"
)


mos_lines = [

    line.strip()

    for line
    in reference_text.splitlines()

    if re.match(
        r"^[Mm]\S+\s+",
        line.strip()
    )

]


pfet_lines = [

    line

    for line
    in mos_lines

    if "sky130_fd_pr__pfet_01v8"
    in line

]


nfet_lines = [

    line

    for line
    in mos_lines

    if "sky130_fd_pr__nfet_01v8"
    in line

]


MOS_COUNT_OK = (
    len(
        mos_lines
    ) == 17
)


PFET_COUNT_OK = (
    len(
        pfet_lines
    ) == 8
)


NFET_COUNT_OK = (
    len(
        nfet_lines
    ) == 9
)


SUBCKT_OK = (

    ".subckt NEUROLIF_FULL_NEURON_LVS_V1 "
    "VDD VSS VBIAS GATE_W0 GATE_W1 VLEAK VMEM SPIKE"

    in reference_text
)


END_OK = (
    ".ends NEUROLIF_FULL_NEURON_LVS_V1"
    in reference_text
)


print()
print("=" * 80)
print("17-MOS REFERENCE SPICE AUDIT")
print("=" * 80)

print(
    "Total MOS:",
    len(
        mos_lines
    ),
    "/ 17"
)

print(
    "PFET:",
    len(
        pfet_lines
    ),
    "/ 8"
)

print(
    "NFET:",
    len(
        nfet_lines
    ),
    "/ 9"
)

print(
    "Subckt declaration valid:",
    SUBCKT_OK
)

print(
    "Subckt termination valid:",
    END_OK
)


# ================================================================
# 14. SERIALIZATION
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


def save_options(fmt):

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

    save_options(
        "GDS2"
    ),

)


layout.write(

    str(
        OUTPUT_OAS
    ),

    save_options(
        "OASIS"
    ),

)


GDS_WRITE_OK = bool(

    OUTPUT_GDS.exists()

    and

    OUTPUT_GDS.stat().st_size > 0

)


OAS_WRITE_OK = bool(

    OUTPUT_OAS.exists()

    and

    OUTPUT_OAS.stat().st_size > 0

)


# ================================================================
# 15. READ BACK LVS GDS
# ================================================================

verify = kdb.Layout()

verify.read(
    str(
        OUTPUT_GDS
    )
)


verify_top = verify.cell(
    OUTPUT_TOP
)


READBACK_OK = bool(

    verify_top is not None

    and

    not verify_top.bbox().empty()

)


verify_label_layer = verify.find_layer(
    68,
    5
)


READBACK_LABELS = []


if verify_label_layer is not None:

    for shape in verify_top.shapes(
        verify_label_layer
    ).each():

        if shape.is_text():

            READBACK_LABELS.append(
                shape.text.string
            )


READBACK_LABELS_SORTED = sorted(
    READBACK_LABELS
)


EXPECTED_LABELS_SORTED = sorted(
    EXPECTED_LABELS
)


READBACK_LABELS_OK = (
    READBACK_LABELS_SORTED
    ==
    EXPECTED_LABELS_SORTED
)


print()
print("=" * 80)
print("LVS LABEL READBACK")
print("=" * 80)

print(
    "Labels:",
    READBACK_LABELS_SORTED
)

print(
    "Expected:",
    EXPECTED_LABELS_SORTED
)

print(
    "Readback label set valid:",
    READBACK_LABELS_OK
)


# ================================================================
# 16. PROVE PHYSICAL GEOMETRY IS UNCHANGED
#
# Compare every original populated non-label layer against the
# LVS derivative hierarchy.
# ================================================================

PHYSICAL_LAYER_CHECKS = {}


for (
    layer_number,
    datatype
), original_region in ORIGINAL_LAYER_REGIONS.items():

    verify_index = verify.find_layer(
        layer_number,
        datatype
    )


    if verify_index is None:

        PHYSICAL_LAYER_CHECKS[
            f"{layer_number}/{datatype}"
        ] = False

        continue


    derivative_region = kdb.Region(

        verify_top.begin_shapes_rec(
            verify_index
        )

    ).merged()


    same = bool(

        (
            original_region
            -
            derivative_region
        ).is_empty()

        and

        (
            derivative_region
            -
            original_region
        ).is_empty()

    )


    PHYSICAL_LAYER_CHECKS[
        f"{layer_number}/{datatype}"
    ] = same


PHYSICAL_GEOMETRY_UNCHANGED = all(
    PHYSICAL_LAYER_CHECKS.values()
)


print()
print("=" * 80)
print("PHYSICAL-GEOMETRY IMMUTABILITY AUDIT")
print("=" * 80)

print(
    "Physical layers checked:",
    len(
        PHYSICAL_LAYER_CHECKS
    )
)

print(
    "All physical geometry unchanged:",
    PHYSICAL_GEOMETRY_UNCHANGED
)


if not PHYSICAL_GEOMETRY_UNCHANGED:

    print()

    for layer_name, status in PHYSICAL_LAYER_CHECKS.items():

        if not status:

            print(
                "Mismatch:",
                layer_name
            )


# ================================================================
# 17. INPUT PHYSICAL GDS MUST REMAIN UNTOUCHED
# ================================================================

INPUT_HASH_AFTER = sha256_file(
    INPUT_GDS
)


INPUT_UNCHANGED = (
    INPUT_HASH
    ==
    INPUT_HASH_AFTER
)


# ================================================================
# 18. MANIFEST
# ================================================================

manifest = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "40A",

    "artifact":
        "full_neuron_lvs_derivative",

    "input": {

        "physical_gds":
            str(
                INPUT_GDS
            ),

        "top":
            INPUT_TOP,

        "sha256":
            INPUT_HASH,

        "final_drc":
            str(
                FINAL_DRC_REPORT
            ),

        "connectivity_audit":
            str(
                CONNECTIVITY_AUDIT
            ),

    },

    "output": {

        "lvs_gds":
            str(
                OUTPUT_GDS
            ),

        "lvs_oas":
            str(
                OUTPUT_OAS
            ),

        "top":
            OUTPUT_TOP,

        "reference_spice":
            str(
                REFERENCE_SPICE
            ),

    },

    "labels": {

        name:
            list(
                point
            )

        for name, point
        in LABEL_POINTS.items()

    },

    "expected_extraction": {

        "mos_total":
            17,

        "pfet":
            8,

        "nfet":
            9,

        "physical_cmem":
            False,

    },

    "checks": {

        "step39a_pass":
            AUDIT_PASS,

        "step39a_hash_match":
            AUDIT_HASH_MATCH,

        "label_set":
            LABEL_SET_OK,

        "all_labels_on_m1":
            LABEL_POINTS_VALID,

        "label_count":
            LABEL_COUNT_OK,

        "reference_exists":
            REFERENCE_EXISTS,

        "mos_count":
            MOS_COUNT_OK,

        "pfet_count":
            PFET_COUNT_OK,

        "nfet_count":
            NFET_COUNT_OK,

        "subckt":
            SUBCKT_OK,

        "ends":
            END_OK,

        "gds_write":
            GDS_WRITE_OK,

        "oas_write":
            OAS_WRITE_OK,

        "readback":
            READBACK_OK,

        "label_readback":
            READBACK_LABELS_OK,

        "physical_geometry_unchanged":
            PHYSICAL_GEOMETRY_UNCHANGED,

        "input_gds_unchanged":
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
# 19. FINAL GATE
# ================================================================

STEP40A_PASS = bool(

    AUDIT_PASS

    and

    AUDIT_HASH_MATCH

    and

    LABEL_SET_OK

    and

    LABEL_POINTS_VALID

    and

    LABEL_COUNT_OK

    and

    REFERENCE_EXISTS

    and

    MOS_COUNT_OK

    and

    PFET_COUNT_OK

    and

    NFET_COUNT_OK

    and

    SUBCKT_OK

    and

    END_OK

    and

    GDS_WRITE_OK

    and

    OAS_WRITE_OK

    and

    READBACK_OK

    and

    READBACK_LABELS_OK

    and

    PHYSICAL_GEOMETRY_UNCHANGED

    and

    INPUT_UNCHANGED

    and

    MANIFEST_OK

)


print()
print("=" * 80)
print("STEP 40A RESULT")
print("=" * 80)

print(
    "Step 39A audit PASS         :",
    AUDIT_PASS
)

print(
    "Audited GDS hash match      :",
    AUDIT_HASH_MATCH
)

print(
    "All 8 labels on M1          :",
    LABEL_POINTS_VALID
)

print(
    "Label count                 :",
    LABEL_COUNT_OK
)

print(
    "Reference MOS total = 17    :",
    MOS_COUNT_OK
)

print(
    "Reference PFET total = 8    :",
    PFET_COUNT_OK
)

print(
    "Reference NFET total = 9    :",
    NFET_COUNT_OK
)

print(
    "LVS GDS write               :",
    GDS_WRITE_OK
)

print(
    "LVS OASIS write             :",
    OAS_WRITE_OK
)

print(
    "LVS GDS readback            :",
    READBACK_OK
)

print(
    "All labels survived readback:",
    READBACK_LABELS_OK
)

print(
    "Physical geometry unchanged :",
    PHYSICAL_GEOMETRY_UNCHANGED
)

print(
    "Canonical physical GDS intact:",
    INPUT_UNCHANGED
)

print(
    "Manifest written            :",
    MANIFEST_OK
)

print()

print(
    "STEP40A_PASS =",
    STEP40A_PASS
)


if not STEP40A_PASS:

    raise RuntimeError(
        "STEP 40A LVS derivative/reference generation failed."
    )


print()
print("=" * 80)
print("FULL-NEURON LVS INPUTS — READY")
print("=" * 80)

print()
print(
    "Physical geometry:"
)

print(
    "  UNCHANGED from final DRC-clean / connectivity-PASS core"
)

print()
print(
    "LVS labels:"
)

for name in EXPECTED_LABELS:

    print(
        " ",
        name
    )


print()
print(
    "Reference:"
)

print(
    "  17 MOS total"
)

print(
    "  8 PFET"
)

print(
    "  9 NFET"
)

print(
    "  Cmem external / excluded"
)

print()
print(
    "LVS derivative:"
)

print(
    OUTPUT_GDS
)

print()
print(
    "Reference SPICE:"
)

print(
    REFERENCE_SPICE
)

print()
print(
    "NEXT:"
)

print(
    "  Run official KLayout SKY130 LVS on the 17-MOS full neuron."
)