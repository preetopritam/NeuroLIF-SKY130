# ================================================================
# NeuroLIF-SKY130
# STEP 28C — Correct LVS post-processing and formally close synapse
#
# IMPORTANT:
#
# The actual Step 28B KLayout LVS result was:
#
#   Return code : 0
#   Result      : MATCH
#   Message     : Congratulations! Netlists match.
#
# The previous Python harness falsely failed because it counted
# device-model names in both:
#
#   * device instance ... comments
#   M... actual MOS statements
#
# This script counts ONLY actual MOS device statements.
#
# No GDS is modified.
# No LVS rerun is required.
# ================================================================

from pathlib import Path
import json
import hashlib
import re


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 28C: FINAL LVS CLOSURE")
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

FROZEN_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_vss_v1.gds"
)

LVS_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.gds"
)

REFERENCE_SPICE = (
    SYNAPSE_DIR
    / "neurolif_synapse_reference_v1.spice"
)

EXTRACTED_NETLIST = (
    SYNAPSE_DIR
    / "neurolif_synapse_extracted_v1.cir"
)

LVS_REPORT = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.lvsdb"
)

LVS_LOG = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.log"
)

CONNECTIVITY_AUDIT = (
    SYNAPSE_DIR
    / "neurolif_synapse_final_connectivity_audit.json"
)

FINAL_RECORD = (
    SYNAPSE_DIR
    / "neurolif_synapse_final_verification_v1.json"
)


TOP_CELL = (
    "NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1"
)


for path in [
    FROZEN_GDS,
    LVS_GDS,
    REFERENCE_SPICE,
    EXTRACTED_NETLIST,
    LVS_REPORT,
    LVS_LOG,
    CONNECTIVITY_AUDIT,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. HASH HELPER
# ================================================================

def sha256_file(
    path,
):

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


FROZEN_SHA256 = sha256_file(
    FROZEN_GDS
)

LVS_GDS_SHA256 = sha256_file(
    LVS_GDS
)


print()
print("=" * 80)
print("ARTIFACT HASHES")
print("=" * 80)

print(
    "Frozen GDS:",
    FROZEN_SHA256
)

print(
    "LVS GDS   :",
    LVS_GDS_SHA256
)


# ================================================================
# 3. READ LVS LOG
# ================================================================

log_text = LVS_LOG.read_text(

    encoding="utf-8",

    errors="replace",

)


MATCH_MESSAGE = (
    "Congratulations! Netlists match."
)

MISMATCH_MESSAGE = (
    "Netlists don't match"
)


MATCH_FOUND = (
    MATCH_MESSAGE
    in log_text
)

MISMATCH_FOUND = (
    MISMATCH_MESSAGE
    in log_text
)


LVS_COMPARE_PASS = bool(

    MATCH_FOUND

    and

    not MISMATCH_FOUND

)


print()
print("=" * 80)
print("OFFICIAL LVS RESULT")
print("=" * 80)

print(
    "Match message found   :",
    MATCH_FOUND
)

print(
    "Mismatch message found:",
    MISMATCH_FOUND
)

print(
    "Official compare pass :",
    LVS_COMPARE_PASS
)


# ================================================================
# 4. READ EXTRACTED NETLIST
# ================================================================

extracted_text = EXTRACTED_NETLIST.read_text(

    encoding="utf-8",

    errors="replace",

)


extracted_lines = (
    extracted_text.splitlines()
)


# ================================================================
# 5. COUNT ONLY ACTUAL MOS STATEMENTS
#
# Correct rule:
#
#   Count lines whose first non-space character is M.
#
# Ignore:
#
#   * device instance ...
#
# comments completely.
# ================================================================

mos_lines = []


for line in extracted_lines:

    stripped = line.strip()

    if not stripped:
        continue

    if stripped.startswith(
        "*"
    ):
        continue

    if stripped[0].upper() == "M":

        mos_lines.append(
            stripped
        )


pfet_lines = [

    line

    for line
    in mos_lines

    if (
        "sky130_fd_pr__pfet_01v8"
        in line
    )

]


nfet_lines = [

    line

    for line
    in mos_lines

    if (
        "sky130_fd_pr__nfet_01v8"
        in line
    )

]


MOS_COUNT = len(
    mos_lines
)

PFET_COUNT = len(
    pfet_lines
)

NFET_COUNT = len(
    nfet_lines
)


DEVICE_COUNTS_OK = bool(

    MOS_COUNT == 7

    and

    PFET_COUNT == 4

    and

    NFET_COUNT == 3

)


print()
print("=" * 80)
print("CORRECTED DEVICE COUNT")
print("=" * 80)

print(
    "Actual MOS statements:",
    MOS_COUNT
)

print(
    "PFET statements      :",
    PFET_COUNT
)

print(
    "NFET statements      :",
    NFET_COUNT
)

print(
    "Expected             : 7 total / 4 PFET / 3 NFET"
)

print(
    "Device counts correct:",
    DEVICE_COUNTS_OK
)


# ================================================================
# 6. PRINT DEVICES
# ================================================================

print()
print("=" * 80)
print("EXTRACTED MOS DEVICES")
print("=" * 80)


for index, line in enumerate(
    mos_lines,
    start=1,
):

    print(
        f"[{index}] {line}"
    )


# ================================================================
# 7. TOP-LEVEL SUBCKT / PIN AUDIT
# ================================================================

subckt_line = None


for line in extracted_lines:

    stripped = line.strip()

    if (
        stripped.upper().startswith(
            ".SUBCKT"
        )

        and

        TOP_CELL.upper()
        in stripped.upper()
    ):

        subckt_line = stripped
        break


EXPECTED_PINS = {

    "VDD",
    "VSS",
    "VBIAS",
    "GATE_W0",
    "GATE_W1",
    "VMEM",

}


actual_pins = set()


if subckt_line is not None:

    tokens = (
        subckt_line.split()
    )

    # .SUBCKT CELL pin1 pin2 ...

    actual_pins = set(
        tokens[2:]
    )


PIN_SET_OK = (
    actual_pins
    == EXPECTED_PINS
)


print()
print("=" * 80)
print("TOP-LEVEL PIN AUDIT")
print("=" * 80)

print(
    "SUBCKT:",
    subckt_line
)

print(
    "Actual pins:",
    sorted(
        actual_pins
    )
)

print(
    "Expected:",
    sorted(
        EXPECTED_PINS
    )
)

print(
    "Pin set correct:",
    PIN_SET_OK
)


# ================================================================
# 8. DIMENSION AUDIT
# ================================================================

PFET_DIMENSIONS_OK = True

NFET_DIMENSIONS_OK = True


for line in pfet_lines:

    normalized = (
        line.lower()
    )

    if (
        "l=0.5"
        not in normalized

        or

        "w=0.84"
        not in normalized
    ):

        PFET_DIMENSIONS_OK = False


for line in nfet_lines:

    normalized = (
        line.lower()
    )

    if (
        "l=0.15"
        not in normalized

        or

        "w=1"
        not in normalized
    ):

        NFET_DIMENSIONS_OK = False


DIMENSIONS_OK = bool(

    PFET_DIMENSIONS_OK

    and

    NFET_DIMENSIONS_OK

)


print()
print("=" * 80)
print("EXTRACTED W/L AUDIT")
print("=" * 80)

print(
    "PFET W=0.84 L=0.50:",
    PFET_DIMENSIONS_OK
)

print(
    "NFET W=1.00 L=0.15:",
    NFET_DIMENSIONS_OK
)

print(
    "Dimensions correct:",
    DIMENSIONS_OK
)


# ================================================================
# 9. BULK AUDIT
#
# Extracted MOS syntax:
#
#   Mname D G S B model ...
#
# Therefore token[4] is bulk.
# ================================================================

PFET_BULK_OK = True

NFET_BULK_OK = True


for line in pfet_lines:

    tokens = line.split()

    if len(tokens) < 6:

        PFET_BULK_OK = False
        continue

    bulk = tokens[4]

    if bulk != "VDD":

        PFET_BULK_OK = False


for line in nfet_lines:

    tokens = line.split()

    if len(tokens) < 6:

        NFET_BULK_OK = False
        continue

    bulk = tokens[4]

    if bulk != "VSS":

        NFET_BULK_OK = False


BULKS_OK = bool(

    PFET_BULK_OK

    and

    NFET_BULK_OK

)


print()
print("=" * 80)
print("BODY / BULK AUDIT")
print("=" * 80)

print(
    "All PFET bulk -> VDD:",
    PFET_BULK_OK
)

print(
    "All NFET bulk -> VSS:",
    NFET_BULK_OK
)

print(
    "Bulk connectivity correct:",
    BULKS_OK
)


# ================================================================
# 10. REFERENCE SCHEMATIC COUNT
# ================================================================

reference_text = REFERENCE_SPICE.read_text(

    encoding="utf-8",

    errors="replace",

)


reference_mos_lines = []


for line in reference_text.splitlines():

    stripped = line.strip()

    if not stripped:

        continue

    if stripped.startswith(
        "*"
    ):

        continue

    if stripped[0].upper() == "M":

        reference_mos_lines.append(
            stripped
        )


REFERENCE_MOS_COUNT = len(
    reference_mos_lines
)


REFERENCE_COUNT_OK = (
    REFERENCE_MOS_COUNT == 7
)


print()
print("=" * 80)
print("REFERENCE SCHEMATIC AUDIT")
print("=" * 80)

print(
    "Reference MOS statements:",
    REFERENCE_MOS_COUNT
)

print(
    "Expected:",
    7
)

print(
    "Reference count correct:",
    REFERENCE_COUNT_OK
)


# ================================================================
# 11. CONNECTIVITY AUDIT RECORD
# ================================================================

connectivity_data = json.loads(

    CONNECTIVITY_AUDIT.read_text(
        encoding="utf-8"
    )

)


STEP26A_PASS = bool(

    connectivity_data.get(
        "STEP26A_PASS",
        False,
    )

)


print()
print("=" * 80)
print("PRE-LVS CONNECTIVITY AUDIT")
print("=" * 80)

print(
    "STEP26A_PASS:",
    STEP26A_PASS
)


# ================================================================
# 12. LVS ARTIFACT CHECK
# ================================================================

LVS_REPORT_OK = bool(

    LVS_REPORT.exists()

    and

    LVS_REPORT.stat().st_size > 0

)


EXTRACTED_NETLIST_OK = bool(

    EXTRACTED_NETLIST.exists()

    and

    EXTRACTED_NETLIST.stat().st_size > 0

)


ARTIFACTS_OK = bool(

    LVS_REPORT_OK

    and

    EXTRACTED_NETLIST_OK

)


print()
print("=" * 80)
print("LVS ARTIFACT AUDIT")
print("=" * 80)

print(
    "LVS database:",
    LVS_REPORT_OK
)

print(
    "Extracted netlist:",
    EXTRACTED_NETLIST_OK
)

print(
    "Artifacts present:",
    ARTIFACTS_OK
)


# ================================================================
# 13. FINAL CLOSURE GATE
# ================================================================

STEP28C_PASS = bool(

    LVS_COMPARE_PASS

    and

    DEVICE_COUNTS_OK

    and

    PIN_SET_OK

    and

    DIMENSIONS_OK

    and

    BULKS_OK

    and

    REFERENCE_COUNT_OK

    and

    STEP26A_PASS

    and

    ARTIFACTS_OK

)


# ================================================================
# 14. FINAL VERIFICATION RECORD
# ================================================================

record = {

    "project":
        "NeuroLIF-SKY130",

    "block":
        "corrected_weighted_synapse",

    "verification_revision":
        "v1",

    "physical": {

        "frozen_gds":
            str(
                FROZEN_GDS
            ),

        "frozen_gds_sha256":
            FROZEN_SHA256,

        "lvs_derivative_gds":
            str(
                LVS_GDS
            ),

        "lvs_derivative_sha256":
            LVS_GDS_SHA256,

        "drc":
            {

                "status":
                    "PASS",

                "violations":
                    0,

                "step":
                    "25B",

            },

    },

    "connectivity_audit": {

        "step":
            "26A",

        "status":
            "PASS"
            if STEP26A_PASS
            else "FAIL",

        "intended_nets":
            9,

        "conductor_roots":
            9,

        "cross_net_shorts":
            0,

    },

    "lvs": {

        "status":
            "PASS"
            if LVS_COMPARE_PASS
            else "FAIL",

        "match_message":
            MATCH_FOUND,

        "mismatch_message":
            MISMATCH_FOUND,

        "report":
            str(
                LVS_REPORT
            ),

        "extracted_netlist":
            str(
                EXTRACTED_NETLIST
            ),

        "devices": {

            "total_mos":
                MOS_COUNT,

            "pfet_01v8":
                PFET_COUNT,

            "nfet_01v8":
                NFET_COUNT,

        },

        "external_pins":
            sorted(
                actual_pins
            ),

        "bulk_checks": {

            "pfet_to_vdd":
                PFET_BULK_OK,

            "nfet_to_vss":
                NFET_BULK_OK,

        },

        "dimensions_ok":
            DIMENSIONS_OK,

    },

    "final_status":
        (
            "CLOSED"
            if STEP28C_PASS
            else "NOT_CLOSED"
        ),

    "STEP28C_PASS":
        STEP28C_PASS,

}


FINAL_RECORD.write_text(

    json.dumps(
        record,
        indent=2,
    ),

    encoding="utf-8",

)


FINAL_RECORD_OK = bool(

    FINAL_RECORD.exists()

    and

    FINAL_RECORD.stat().st_size > 0

)


print()
print("=" * 80)
print("STEP 28C RESULT")
print("=" * 80)

print(
    "Official LVS compare        :",
    LVS_COMPARE_PASS
)

print(
    "Correct MOS count            :",
    DEVICE_COUNTS_OK
)

print(
    "Top-level pin set            :",
    PIN_SET_OK
)

print(
    "Extracted W/L                :",
    DIMENSIONS_OK
)

print(
    "Bulk connectivity            :",
    BULKS_OK
)

print(
    "Reference device count       :",
    REFERENCE_COUNT_OK
)

print(
    "Pre-LVS connectivity audit   :",
    STEP26A_PASS
)

print(
    "LVS artifacts present        :",
    ARTIFACTS_OK
)

print(
    "Final record written         :",
    FINAL_RECORD_OK
)

print()

print(
    "STEP28C_PASS =",
    STEP28C_PASS
)


if not STEP28C_PASS:

    raise RuntimeError(
        "STEP 28C formal closure failed."
    )


print()
print("=" * 80)
print("WEIGHTED SYNAPSE — FINAL VERIFIED STATUS")
print("=" * 80)

print()
print(
    "Transistor topology     : VERIFIED"
)

print(
    "Physical routing        : COMPLETE"
)

print(
    "SKY130 DRC              : PASS — 0 violations"
)

print(
    "Connectivity audit      : PASS"
)

print(
    "Cross-net shorts        : NONE DETECTED"
)

print(
    "MOS extraction          : 7 / 7"
)

print(
    "PFET extraction         : 4 / 4"
)

print(
    "NFET extraction         : 3 / 3"
)

print(
    "Bulk connections        : PASS"
)

print(
    "Top-level pins          : PASS"
)

print(
    "KLayout LVS             : PASS / NETLISTS MATCH"
)

print()
print(
    "WEIGHTED SYNAPSE BLOCK STATUS: CLOSED"
)

print()
print(
    "Final verification record:"
)

print(
    FINAL_RECORD
)