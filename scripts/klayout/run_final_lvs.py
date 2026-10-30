from pathlib import Path
import subprocess
import sys


# ============================================================
# Repository
# ============================================================

ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# LVS input
#
# IMPORTANT:
# LVS uses the verification-only labelled derivative.
# It does NOT replace the canonical final physical GDS.
# ============================================================

INPUT_GDS = (
    ROOT
    / "layout"
    / "neuron"
    / "neurolif_full_neuron_lvs_v1.gds"
)

TOP_CELL = "NEUROLIF_FULL_NEURON_LVS_V1"

SCHEMATIC = (
    ROOT
    / "circuit"
    / "lvs"
    / "neurolif_full_neuron_lvs_reference_v1.spice"
)


# ============================================================
# Local KLayout / SKY130 installation
# ============================================================

KLAYOUT_EXE = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "KLayout"
    / "klayout_app.exe"
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


# ============================================================
# Reproduced outputs
#
# Frozen verification evidence is intentionally preserved.
# ============================================================

OUTPUT_DIR = (
    ROOT
    / "verification"
    / "neuron"
    / "lvs"
    / "reproduced"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


REPORT = (
    OUTPUT_DIR
    / "neurolif_full_neuron_lvs_reproduced.lvsdb"
)

EXTRACTED_NETLIST = (
    OUTPUT_DIR
    / "neurolif_full_neuron_extracted_reproduced.cir"
)

LOG = (
    OUTPUT_DIR
    / "neurolif_full_neuron_lvs_reproduced.log"
)


# ============================================================
# Preconditions
# ============================================================

required = {
    "KLayout executable":
        KLAYOUT_EXE,

    "SKY130 LVS deck":
        LVS_DECK,

    "LVS layout":
        INPUT_GDS,

    "Reference schematic":
        SCHEMATIC,
}


print()
print("=" * 72)
print("NeuroLIF-SKY130 — FINAL LVS REPRODUCTION")
print("=" * 72)


for label, path in required.items():

    exists = path.exists()

    print(
        f"{label:24s}: "
        f"{'FOUND' if exists else 'MISSING'}"
    )

    print(
        f"  {path}"
    )

    if not exists:

        print()
        print(
            "[FAIL] Required file was not found."
        )

        sys.exit(1)


# ============================================================
# Remove only previous REPRODUCED outputs
# ============================================================

for path in (
    REPORT,
    EXTRACTED_NETLIST,
    LOG,
):

    if path.exists():
        path.unlink()


# ============================================================
# Official SKY130 KLayout LVS invocation
# ============================================================

cmd = [

    str(KLAYOUT_EXE),

    "-b",

    "-rd",
    f"input={INPUT_GDS}",

    "-rd",
    f"top_cell={TOP_CELL}",

    "-rd",
    f"report={REPORT}",

    "-rd",
    f"schematic={SCHEMATIC}",

    "-rd",
    f"target_netlist={EXTRACTED_NETLIST}",

    "-rd",
    "thr=4",

    "-r",
    str(LVS_DECK),
]


print()
print("Running official SKY130 LVS...")
print()


process = subprocess.run(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)


LOG.write_text(
    process.stdout,
    encoding="utf-8",
)


print(
    process.stdout
)


# ============================================================
# Basic process checks
# ============================================================

print()
print(
    "KLayout return code:",
    process.returncode,
)


if process.returncode != 0:

    print()
    print(
        "[FAIL] KLayout LVS returned "
        "a non-zero exit code."
    )

    print(
        "Log:",
        LOG,
    )

    sys.exit(1)


# ============================================================
# Expected output files
# ============================================================

report_created = REPORT.exists()

netlist_created = (
    EXTRACTED_NETLIST.exists()
)


print(
    "LVS report created :",
    report_created,
)

print(
    "Extracted netlist  :",
    netlist_created,
)


if not report_created:

    print()
    print(
        "[FAIL] LVS report database "
        "was not created."
    )

    sys.exit(1)


if not netlist_created:

    print()
    print(
        "[FAIL] Extracted netlist "
        "was not created."
    )

    sys.exit(1)


# ============================================================
# Determine LVS result from official KLayout output
# ============================================================

log_text = process.stdout


SUCCESS_TEXT = (
    "Congratulations! Netlists match."
)


success_message_found = (
    SUCCESS_TEXT.lower()
    in
    log_text.lower()
)


mismatch_markers = [

    "netlists do not match",

    "netlists don't match",

    "mismatch detected",

    "netlist mismatch",
]


mismatch_message_found = any(

    marker.lower()
    in
    log_text.lower()

    for marker
    in mismatch_markers
)


# ============================================================
# Lightweight extracted-device inventory
# ============================================================

extracted_text = (
    EXTRACTED_NETLIST.read_text(
        encoding="utf-8",
        errors="ignore",
    )
)


mos_lines = []

for raw_line in extracted_text.splitlines():

    line = raw_line.strip()

    if not line:
        continue

    if line.startswith("*"):
        continue

    if line[0].upper() == "M":
        mos_lines.append(line)


mos_count = len(mos_lines)


# ============================================================
# Top-pin presence audit
# ============================================================

expected_pins = [

    "VDD",
    "VSS",
    "VBIAS",
    "GATE_W0",
    "GATE_W1",
    "VLEAK",
    "VMEM",
    "SPIKE",
]


pin_presence = {

    pin:
        pin.lower()
        in extracted_text.lower()

    for pin in expected_pins
}


all_pins_present = all(
    pin_presence.values()
)


# ============================================================
# Final result
# ============================================================

LVS_PASS = (

    process.returncode == 0

    and

    report_created

    and

    netlist_created

    and

    success_message_found

    and

    not mismatch_message_found

    and

    mos_count == 17

    and

    all_pins_present
)


print()
print("=" * 72)
print("LVS RESULT")
print("=" * 72)

print(
    "Input GDS          :",
    INPUT_GDS.relative_to(ROOT),
)

print(
    "Top cell           :",
    TOP_CELL,
)

print(
    "Reference schematic:",
    SCHEMATIC.relative_to(ROOT),
)

print(
    "LVS report         :",
    REPORT.relative_to(ROOT),
)

print(
    "Extracted netlist  :",
    EXTRACTED_NETLIST.relative_to(ROOT),
)

print(
    "LVS log            :",
    LOG.relative_to(ROOT),
)


print()
print(
    "Success message found  :",
    success_message_found,
)

print(
    "Mismatch message found :",
    mismatch_message_found,
)

print(
    "Extracted MOS count    :",
    mos_count,
    "/ 17",
)


print()
print("Top-level pins:")

for pin in expected_pins:

    print(
        f"  {pin:8s} : "
        f"{pin_presence[pin]}"
    )


print()
print(
    "LVS_PASS =",
    LVS_PASS,
)


if not LVS_PASS:

    print()
    print(
        "[FAIL] Full-neuron LVS reproduction "
        "did not satisfy all expected checks."
    )

    sys.exit(1)


print()
print(
    "OFFICIAL RESULT: NETLISTS MATCH"
)

print(
    "FINAL_LVS_REPRODUCTION_PASS = True"
)

print("=" * 72)