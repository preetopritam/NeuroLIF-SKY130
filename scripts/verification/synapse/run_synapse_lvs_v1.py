# ================================================================
# NeuroLIF-SKY130
# STEP 28B — First real LVS run for weighted synapse
#
# Layout:
#   neurolif_synapse_lvs_v1.gds
#
# Top:
#   NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1
#
# Schematic:
#   neurolif_synapse_reference_v1.spice
#
# Installed deck:
#   sky130.lvs
#
# Important:
#   - top_cell is passed explicitly
#   - substrate is explicitly named VSS
#   - top-level pins are generated from labeled nets
#   - extracted netlist is preserved for diagnosis
#   - frozen physical GDS is not modified
# ================================================================

from pathlib import Path
import subprocess
import hashlib
import re


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 28B: FIRST REAL LVS")
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

LAYOUT_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.gds"
)

REFERENCE_SPICE = (
    SYNAPSE_DIR
    / "neurolif_synapse_reference_v1.spice"
)

FROZEN_GDS = (
    SYNAPSE_DIR
    / "neurolif_synapse_vss_v1.gds"
)

LVS_DECK = (
    Path.home()
    / "KLayout"
    / "salt"
    / "Efabless_sky130"
    / "tech"
    / "sky130"
    / "lvs"
    / "sky130.lvs"
)

KLAYOUT_EXE = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "KLayout"
    / "klayout_app.exe"
)

TOP_CELL = (
    "NEUROLIF_WEIGHTED_SYNAPSE_LVS_V1"
)

LVS_REPORT = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.lvsdb"
)

EXTRACTED_NETLIST = (
    SYNAPSE_DIR
    / "neurolif_synapse_extracted_v1.cir"
)

LVS_LOG = (
    SYNAPSE_DIR
    / "neurolif_synapse_lvs_v1.log"
)


for path in [
    LAYOUT_GDS,
    REFERENCE_SPICE,
    FROZEN_GDS,
    LVS_DECK,
    KLAYOUT_EXE,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. HASH FROZEN GDS
# ================================================================

def sha256_file(
    path,
):

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            data = handle.read(
                1024 * 1024
            )

            if not data:
                break

            digest.update(
                data
            )


    return digest.hexdigest()


FROZEN_HASH_BEFORE = sha256_file(
    FROZEN_GDS
)


print()
print("=" * 80)
print("INPUTS")
print("=" * 80)

print(
    "Layout:",
    LAYOUT_GDS
)

print(
    "Top cell:",
    TOP_CELL
)

print(
    "Reference:",
    REFERENCE_SPICE
)

print(
    "LVS deck:",
    LVS_DECK
)

print(
    "KLayout:",
    KLAYOUT_EXE
)

print(
    "Substrate name: VSS"
)

print(
    "Top-level pins: ENABLED"
)


# ================================================================
# 3. REMOVE PREVIOUS LVS OUTPUTS
# ================================================================

for path in [
    LVS_REPORT,
    EXTRACTED_NETLIST,
    LVS_LOG,
]:

    path.unlink(
        missing_ok=True
    )


# ================================================================
# 4. BUILD DIRECT KLAYOUT LVS COMMAND
#
# These options mirror the installed run_lvs.py behavior,
# with two deliberate additions:
#
#   1. explicit top_cell
#   2. explicit absolute KLayout executable
#
# top_lvl_pins=true:
#   KLayout creates pins for named top-level nets.
#
# Since only six external nets are labeled, the intended
# top-level interface is:
#
#   VDD
#   VSS
#   VBIAS
#   GATE_W0
#   GATE_W1
#   VMEM
# ================================================================

command = [

    str(
        KLAYOUT_EXE
    ),

    "-b",

    "-r",
    str(
        LVS_DECK
    ),

    "-rd",
    f"input={LAYOUT_GDS}",

    "-rd",
    f"top_cell={TOP_CELL}",

    "-rd",
    f"report={LVS_REPORT}",

    "-rd",
    f"schematic={REFERENCE_SPICE}",

    "-rd",
    f"target_netlist={EXTRACTED_NETLIST}",

    "-rd",
    "thr=4",

    "-rd",
    "run_mode=deep",

    "-rd",
    "lvs_sub=VSS",

    "-rd",
    "spice_net_names=true",

    "-rd",
    "spice_comments=true",

    "-rd",
    "scale=false",

    "-rd",
    "verbose=true",

    "-rd",
    "schematic_simplify=false",

    "-rd",
    "net_only=false",

    "-rd",
    "top_lvl_pins=true",

    "-rd",
    "combine=false",

    "-rd",
    "purge=false",

    "-rd",
    "purge_nets=false",

    "-rd",
    "convert_subckts=false",

]


print()
print("=" * 80)
print("LVS COMMAND")
print("=" * 80)


for token in command:

    print(
        token
    )


# ================================================================
# 5. RUN LVS
# ================================================================

print()
print("=" * 80)
print("RUNNING LVS")
print("=" * 80)


result = subprocess.run(

    command,

    capture_output=True,

    text=True,

    errors="replace",

    cwd=str(
        SYNAPSE_DIR
    ),

)


combined_log = (

    "STDOUT\n"
    + "=" * 80
    + "\n"
    + result.stdout

    + "\n\nSTDERR\n"
    + "=" * 80
    + "\n"
    + result.stderr

)


LVS_LOG.write_text(

    combined_log,

    encoding="utf-8",

    errors="replace",

)


print(
    "Return code:",
    result.returncode
)

print(
    "Log written:",
    LVS_LOG.exists()
)


# ================================================================
# 6. OUTPUT EXISTENCE
# ================================================================

REPORT_EXISTS = bool(

    LVS_REPORT.exists()

    and

    LVS_REPORT.stat().st_size > 0

)


EXTRACTED_EXISTS = bool(

    EXTRACTED_NETLIST.exists()

    and

    EXTRACTED_NETLIST.stat().st_size > 0

)


print()
print("=" * 80)
print("LVS OUTPUT FILES")
print("=" * 80)

print(
    "LVS report exists:",
    REPORT_EXISTS
)

if LVS_REPORT.exists():

    print(
        "LVS report size:",
        LVS_REPORT.stat().st_size,
        "bytes"
    )


print(
    "Extracted netlist exists:",
    EXTRACTED_EXISTS
)

if EXTRACTED_NETLIST.exists():

    print(
        "Extracted netlist size:",
        EXTRACTED_NETLIST.stat().st_size,
        "bytes"
    )


# ================================================================
# 7. CLASSIFY RESULT FROM RUNSET LOG
#
# sky130.lvs itself emits:
#
#   INFO : Congratulations! Netlists match.
#
# or:
#
#   ERROR : Netlists don't match
#
# Do not interpret every nonzero process return as an
# infrastructure failure because the runset intentionally exits
# with code 1 on an LVS mismatch.
# ================================================================

MATCH_PATTERN = (
    "Congratulations! Netlists match."
)

MISMATCH_PATTERN = (
    "Netlists don't match"
)


LVS_MATCH = (
    MATCH_PATTERN
    in combined_log
)


LVS_MISMATCH = (
    MISMATCH_PATTERN
    in combined_log
)


if LVS_MATCH:

    RESULT_CLASS = (
        "MATCH"
    )

elif LVS_MISMATCH:

    RESULT_CLASS = (
        "MISMATCH"
    )

else:

    RESULT_CLASS = (
        "RUNSET_OR_INFRASTRUCTURE_ERROR"
    )


print()
print("=" * 80)
print("LVS CLASSIFICATION")
print("=" * 80)

print(
    "Match message found:",
    LVS_MATCH
)

print(
    "Mismatch message found:",
    LVS_MISMATCH
)

print(
    "Result class:",
    RESULT_CLASS
)


# ================================================================
# 8. PRINT IMPORTANT LOG LINES
# ================================================================

important_patterns = [

    re.compile(
        r"netlists?\s+(?:do not|don't)\s+match",
        re.IGNORECASE,
    ),

    re.compile(
        r"netlists?\s+match",
        re.IGNORECASE,
    ),

    re.compile(
        r"congratulations",
        re.IGNORECASE,
    ),

    re.compile(
        r"\berror\b",
        re.IGNORECASE,
    ),

    re.compile(
        r"\bwarning\b",
        re.IGNORECASE,
    ),

    re.compile(
        r"substrate",
        re.IGNORECASE,
    ),

    re.compile(
        r"schematic",
        re.IGNORECASE,
    ),

    re.compile(
        r"extracted netlist",
        re.IGNORECASE,
    ),

]


important_lines = []


for line in combined_log.splitlines():

    if any(
        pattern.search(
            line
        )
        for pattern
        in important_patterns
    ):

        important_lines.append(
            line
        )


print()
print("=" * 80)
print("IMPORTANT LVS LOG LINES")
print("=" * 80)


if important_lines:

    for line in important_lines[-120:]:

        print(
            line
        )

else:

    print(
        "No important-pattern log lines detected."
    )


# ================================================================
# 9. LOG TAIL
# ================================================================

print()
print("=" * 80)
print("LVS LOG TAIL — LAST 100 LINES")
print("=" * 80)


for line in combined_log.splitlines()[-100:]:

    print(
        line
    )


# ================================================================
# 10. EXTRACTED NETLIST AUDIT
# ================================================================

EXTRACTED_MOS_COUNT = 0
EXTRACTED_PFET_COUNT = 0
EXTRACTED_NFET_COUNT = 0

EXTRACTED_SUBCKTS = []
EXTRACTED_PIN_LINE = None
EXTRACTED_TEXT = ""


if EXTRACTED_EXISTS:

    EXTRACTED_TEXT = EXTRACTED_NETLIST.read_text(

        encoding="utf-8",

        errors="replace",

    )


    extracted_lines = (
        EXTRACTED_TEXT.splitlines()
    )


    for line in extracted_lines:

        stripped = line.strip()


        if not stripped:

            continue


        upper = stripped.upper()


        if upper.startswith(
            ".SUBCKT"
        ):

            EXTRACTED_SUBCKTS.append(
                stripped
            )


            if (
                TOP_CELL.upper()
                in upper
            ):

                EXTRACTED_PIN_LINE = stripped


        if (
            stripped[0].upper()
            == "M"
        ):

            EXTRACTED_MOS_COUNT += 1


        if (
            "sky130_fd_pr__pfet_01v8"
            in stripped
        ):

            EXTRACTED_PFET_COUNT += 1


        if (
            "sky130_fd_pr__nfet_01v8"
            in stripped
        ):

            EXTRACTED_NFET_COUNT += 1


print()
print("=" * 80)
print("EXTRACTED NETLIST SUMMARY")
print("=" * 80)

print(
    "MOS statements:",
    EXTRACTED_MOS_COUNT
)

print(
    "PFET 01v8 statements:",
    EXTRACTED_PFET_COUNT
)

print(
    "NFET 01v8 statements:",
    EXTRACTED_NFET_COUNT
)

print(
    "SUBCKT declarations:"
)

for line in EXTRACTED_SUBCKTS:

    print(
        " ",
        line
    )


print(
    "Top SUBCKT line:",
    EXTRACTED_PIN_LINE
)


DEVICE_COUNT_EXPECTED = bool(

    EXTRACTED_PFET_COUNT == 4

    and

    EXTRACTED_NFET_COUNT == 3

)


print(
    "Expected 4 PFET + 3 NFET:",
    DEVICE_COUNT_EXPECTED
)


# ================================================================
# 11. PRINT EXTRACTED NETLIST
#
# The synapse is small, so printing it is useful if first-pass
# LVS does not match.
# ================================================================

print()
print("=" * 80)
print("EXTRACTED NETLIST")
print("=" * 80)


if EXTRACTED_EXISTS:

    print(
        EXTRACTED_TEXT
    )

else:

    print(
        "<not generated>"
    )


# ================================================================
# 12. FROZEN GDS INTEGRITY
# ================================================================

FROZEN_HASH_AFTER = sha256_file(
    FROZEN_GDS
)


FROZEN_UNCHANGED = (

    FROZEN_HASH_BEFORE
    == FROZEN_HASH_AFTER

)


print()
print("=" * 80)
print("FROZEN GDS INTEGRITY")
print("=" * 80)

print(
    "Before:",
    FROZEN_HASH_BEFORE
)

print(
    "After :",
    FROZEN_HASH_AFTER
)

print(
    "Frozen source unchanged:",
    FROZEN_UNCHANGED
)


# ================================================================
# 13. FINAL RESULT
#
# A full PASS requires:
#
#   - runset explicitly says netlists match
#   - process exits cleanly
#   - LVSDB exists
#   - extracted netlist exists
#   - extracted device count is 4 PFET + 3 NFET
#   - frozen physical GDS unchanged
# ================================================================

STEP28B_PASS = bool(

    LVS_MATCH

    and

    result.returncode == 0

    and

    REPORT_EXISTS

    and

    EXTRACTED_EXISTS

    and

    DEVICE_COUNT_EXPECTED

    and

    FROZEN_UNCHANGED

)


print()
print("=" * 80)
print("STEP 28B RESULT")
print("=" * 80)

print(
    "Process return code       :",
    result.returncode
)

print(
    "LVS result class         :",
    RESULT_CLASS
)

print(
    "LVS report written       :",
    REPORT_EXISTS
)

print(
    "Extracted netlist written:",
    EXTRACTED_EXISTS
)

print(
    "Expected device count    :",
    DEVICE_COUNT_EXPECTED
)

print(
    "Frozen GDS unchanged     :",
    FROZEN_UNCHANGED
)

print()

print(
    "STEP28B_PASS =",
    STEP28B_PASS
)


# ================================================================
# 14. INTERPRETATION
# ================================================================

if STEP28B_PASS:

    print()
    print("=" * 80)
    print("LVS STATUS")
    print("=" * 80)

    print()
    print(
        "WEIGHTED SYNAPSE LVS = CLEAN"
    )

    print()
    print(
        "Reference schematic and extracted layout netlist match."
    )

    print()
    print(
        "The frozen physical GDS remains unchanged."
    )

elif LVS_MISMATCH:

    print()
    print("=" * 80)
    print("LVS STATUS")
    print("=" * 80)

    print()
    print(
        "WEIGHTED SYNAPSE LVS = FIRST-PASS MISMATCH"
    )

    print()
    print(
        "This is now an electrical/netlist diagnosis problem,"
    )

    print(
        "not a DRC or physical-routing problem."
    )

    print()
    print(
        "Do NOT modify the frozen GDS yet."
    )

    print(
        "Use the extracted netlist and LVSDB to identify"
    )

    print(
        "the exact mismatch first."
    )

else:

    print()
    print("=" * 80)
    print("LVS STATUS")
    print("=" * 80)

    print()
    print(
        "LVS run did not reach a valid compare result."
    )

    print()
    print(
        "Treat this as runset/infrastructure failure,"
    )

    print(
        "not as an electrical mismatch."
    )


print()
print("=" * 80)
print("ARTIFACTS")
print("=" * 80)

print(
    "LVS report:"
)

print(
    LVS_REPORT
)

print()

print(
    "Extracted netlist:"
)

print(
    EXTRACTED_NETLIST
)

print()

print(
    "Log:"
)

print(
    LVS_LOG
)