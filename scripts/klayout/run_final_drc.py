from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


# ============================================================
# Repository paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INPUT_GDS = (
    ROOT
    / "layout"
    / "neuron"
    / "neurolif_full_neuron_final_routed_v1.gds"
)

TOP_CELL = "NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1"


# ============================================================
# Local KLayout / SKY130 installation
#
# These are user-relative rather than hard-coded to C:\Users\...
# ============================================================

KLAYOUT_EXE = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "KLayout"
    / "klayout_app.exe"
)

DRC_DECK = (
    Path.home()
    / "KLayout"
    / "salt"
    / "Efabless_sky130"
    / "tech"
    / "sky130"
    / "drc"
    / "sky130A_mr.drc"
)


# ============================================================
# Reproduction output
#
# Do NOT overwrite the frozen verification evidence committed
# under verification/neuron/drc/.
# ============================================================

OUTPUT_DIR = (
    ROOT
    / "verification"
    / "neuron"
    / "drc"
    / "reproduced"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT = (
    OUTPUT_DIR
    / "neurolif_full_neuron_final_routed_v1_drc_reproduced.lyrdb"
)

LOG = (
    OUTPUT_DIR
    / "neurolif_full_neuron_final_routed_v1_drc_reproduced.log"
)


# ============================================================
# Preconditions
# ============================================================

required = {
    "KLayout executable": KLAYOUT_EXE,
    "SKY130 DRC deck": DRC_DECK,
    "Final canonical GDS": INPUT_GDS,
}


print()
print("=" * 72)
print("NeuroLIF-SKY130 — FINAL DRC REPRODUCTION")
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
# Official KLayout/SKY130 DRC command
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
    "feol=true",

    "-rd",
    "beol=true",

    "-rd",
    "offgrid=true",

    "-rd",
    "seal=false",

    "-rd",
    "floating_met=false",

    "-rd",
    "sram_exclude=false",

    "-rd",
    "thr=4",

    "-r",
    str(DRC_DECK),
]


print()
print("Running official SKY130 DRC...")
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

print()
print(
    "KLayout return code:",
    process.returncode,
)


if process.returncode != 0:

    print()
    print(
        "[FAIL] KLayout DRC process returned "
        "a non-zero exit code."
    )

    print(
        "Log:",
        LOG,
    )

    sys.exit(1)


if not REPORT.exists():

    print()
    print(
        "[FAIL] DRC report database was not created."
    )

    sys.exit(1)


# ============================================================
# Count DRC violations from the .lyrdb XML report
# ============================================================

try:

    tree = ET.parse(REPORT)
    root = tree.getroot()

except ET.ParseError as exc:

    print()
    print(
        "[FAIL] Could not parse DRC report database:"
    )
    print(exc)

    sys.exit(1)


def local_tag(tag):
    return tag.rsplit("}", 1)[-1]


items = [
    element
    for element in root.iter()
    if local_tag(element.tag) == "item"
]


violation_count = len(items)


# ============================================================
# Final report
# ============================================================

print()
print("=" * 72)
print("DRC RESULT")
print("=" * 72)

print(
    "Input GDS       :",
    INPUT_GDS.relative_to(ROOT),
)

print(
    "Top cell        :",
    TOP_CELL,
)

print(
    "DRC report      :",
    REPORT.relative_to(ROOT),
)

print(
    "DRC log         :",
    LOG.relative_to(ROOT),
)

print(
    "Violation count :",
    violation_count,
)


DRC_CLEAN = (
    process.returncode == 0
    and
    violation_count == 0
)


print()
print(
    "DRC_CLEAN =",
    DRC_CLEAN,
)


if not DRC_CLEAN:

    print()
    print(
        "[FAIL] Final layout is not DRC-clean "
        "under this reproduction run."
    )

    sys.exit(1)


print()
print(
    "FINAL_DRC_REPRODUCTION_PASS = True"
)

print("=" * 72)