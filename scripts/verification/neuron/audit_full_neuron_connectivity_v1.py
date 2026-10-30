# ================================================================
# NeuroLIF-SKY130
# STEP 39A — FINAL FULL-NEURON GEOMETRY / CONNECTIVITY /
#            TOPOLOGY AUDIT
#
# Input:
#   neurolif_full_neuron_final_routed_v1.gds
#
# Top:
#   NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1
#
# Purpose:
#   Independent geometry-based audit BEFORE LVS labels.
#
# Audits:
#   1. 17 MOS instances
#   2. M1 / VIA1 / M2 connectivity graph
#   3. virtual top/bottom gate-contact connection through poly
#   4. 14 intended logical conductor nets
#   5. exact added-neuron topology
#   6. weighted-synapse topology
#   7. no logical cross-net shorts
#   8. no unexplained/floating conductor roots
#   9. PMOS NWELL + n-tap -> VDD
#  10. NMOS substrate + p-tap -> VSS
#
# NOTE:
#   Physical Cmem = intentionally NOT implemented.
#   VMEM remains the external capacitor terminal.
# ================================================================

from pathlib import Path
import hashlib
import json

import klayout.db as kdb


print("=" * 80)
print("STEP 39A — FINAL FULL-NEURON CONNECTIVITY / TOPOLOGY AUDIT")
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

REFERENCE_SPICE = (
    NEURON_DIR
    / "neurolif_full_neuron_reference_v1.spice"
)

FINAL_DRC_REPORT = (
    NEURON_DIR
    / "neurolif_full_neuron_final_routed_v1_drc.lyrdb"
)

OUTPUT_JSON = (
    NEURON_DIR
    / "neurolif_full_neuron_final_connectivity_audit_v1.json"
)


TOP_NAME = (
    "NEUROLIF_FULL_NEURON_FINAL_ROUTED_V1"
)


for path in [
    INPUT_GDS,
    REFERENCE_SPICE,
    FINAL_DRC_REPORT,
]:

    if not path.exists():

        raise FileNotFoundError(
            path
        )


# ================================================================
# 2. INPUT HASH
# ================================================================

def sha256_file(path):

    h = hashlib.sha256()

    with path.open("rb") as f:

        while True:

            block = f.read(
                1024 * 1024
            )

            if not block:
                break

            h.update(block)

    return h.hexdigest()


INPUT_HASH_BEFORE = sha256_file(
    INPUT_GDS
)


# ================================================================
# 3. LOAD FINAL ROUTED GDS
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)


DBU = layout.dbu


top = layout.cell(
    TOP_NAME
)


if top is None:

    raise RuntimeError(
        f"Missing top cell: {TOP_NAME}"
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
    "Top:",
    TOP_NAME
)

print(
    "Final DRC report exists:",
    FINAL_DRC_REPORT.exists()
)


# ================================================================
# 4. LAYERS
# ================================================================

M1_LAYER = layout.find_layer(
    68,
    20
)

VIA1_LAYER = layout.find_layer(
    68,
    44
)

M2_LAYER = layout.find_layer(
    69,
    20
)

NWELL_LAYER = layout.find_layer(
    64,
    20
)

TAP_LAYER = layout.find_layer(
    65,
    44
)

NSDM_LAYER = layout.find_layer(
    93,
    44
)

PSDM_LAYER = layout.find_layer(
    94,
    20
)


required_layers = {

    "MET1 68/20":
        M1_LAYER,

    "VIA1 68/44":
        VIA1_LAYER,

    "MET2 69/20":
        M2_LAYER,

    "NWELL 64/20":
        NWELL_LAYER,

    "TAP 65/44":
        TAP_LAYER,

    "NSDM 93/44":
        NSDM_LAYER,

    "PSDM 94/20":
        PSDM_LAYER,

}


for name, index in required_layers.items():

    if index is None:

        raise RuntimeError(
            f"Missing required layer: {name}"
        )


# ================================================================
# 5. HELPERS
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


def translate_box(
    box,
    origin,
):

    return kdb.Box(

        box.left
        +
        to_dbu(
            origin[0]
        ),

        box.bottom
        +
        to_dbu(
            origin[1]
        ),

        box.right
        +
        to_dbu(
            origin[0]
        ),

        box.top
        +
        to_dbu(
            origin[1]
        ),

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


# ================================================================
# 6. UNION-FIND
# ================================================================

class UnionFind:

    def __init__(
        self,
        n,
    ):

        self.parent = list(
            range(n)
        )

        self.rank = [
            0
        ] * n


    def find(
        self,
        x,
    ):

        while (
            self.parent[x]
            != x
        ):

            self.parent[x] = (
                self.parent[
                    self.parent[x]
                ]
            )

            x = self.parent[x]

        return x


    def union(
        self,
        a,
        b,
    ):

        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return


        if (
            self.rank[ra]
            <
            self.rank[rb]
        ):

            ra, rb = rb, ra


        self.parent[rb] = ra


        if (
            self.rank[ra]
            ==
            self.rank[rb]
        ):

            self.rank[ra] += 1


# ================================================================
# 7. BUILD METAL COMPONENTS
# ================================================================

M1_REGION = kdb.Region(

    top.begin_shapes_rec(
        M1_LAYER
    )

).merged()


M2_REGION = kdb.Region(

    top.begin_shapes_rec(
        M2_LAYER
    )

).merged()


VIA1_REGION = kdb.Region(

    top.begin_shapes_rec(
        VIA1_LAYER
    )

).merged()


M1_COMPONENTS = list(
    M1_REGION.each_merged()
)

M2_COMPONENTS = list(
    M2_REGION.each_merged()
)

VIA1_COMPONENTS = list(
    VIA1_REGION.each_merged()
)


N_M1 = len(
    M1_COMPONENTS
)

N_M2 = len(
    M2_COMPONENTS
)


M2_OFFSET = N_M1


uf = UnionFind(
    N_M1
    +
    N_M2
)


print()
print("=" * 80)
print("RAW CONDUCTOR COMPONENTS")
print("=" * 80)

print(
    "M1 components  :",
    N_M1
)

print(
    "M2 components  :",
    N_M2
)

print(
    "VIA1 components:",
    len(
        VIA1_COMPONENTS
    )
)


# ================================================================
# 8. COMPONENT LOOKUP
# ================================================================

def m1_hits_region(
    region,
):

    hits = []


    for index, polygon in enumerate(
        M1_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            &

            region

        ).is_empty():

            hits.append(
                index
            )


    return hits


def m2_hits_region(
    region,
):

    hits = []


    for index, polygon in enumerate(
        M2_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            &

            region

        ).is_empty():

            hits.append(
                index
            )


    return hits


def m1_index_for_box(
    box,
):

    hits = m1_hits_region(

        kdb.Region(
            box
        )

    )


    if len(hits) != 1:

        raise RuntimeError(

            "Expected exactly one M1 component for terminal box; "
            f"got {hits}"

        )


    return hits[0]


# ================================================================
# 9. CONNECT M1 <-> M2 THROUGH VIA1
# ================================================================

VIA_MAPPING_OK = True

via_map = []


for via_number, via_polygon in enumerate(
    VIA1_COMPONENTS,
    start=1,
):

    via_region = kdb.Region(
        via_polygon
    )


    m1_hits = m1_hits_region(
        via_region
    )

    m2_hits = m2_hits_region(
        via_region
    )


    valid = bool(

        len(
            m1_hits
        ) == 1

        and

        len(
            m2_hits
        ) == 1

    )


    VIA_MAPPING_OK &= valid


    via_map.append({

        "via":
            via_number,

        "m1_hits":
            list(
                m1_hits
            ),

        "m2_hits":
            list(
                m2_hits
            ),

        "valid":
            valid,

    })


    if valid:

        uf.union(

            m1_hits[0],

            M2_OFFSET
            +
            m2_hits[0],

        )


print()
print("=" * 80)
print("VIA1 CONNECTIVITY AUDIT")
print("=" * 80)

print(
    "All VIA1 mappings exactly M1<->M2:",
    VIA_MAPPING_OK
)


if not VIA_MAPPING_OK:

    for record in via_map:

        if not record[
            "valid"
        ]:

            print(
                "Bad VIA:",
                record
            )


# ================================================================
# 10. FIND PRIMITIVE CELLS ROBUSTLY
# ================================================================

def resolve_cell(
    role,
    preferred_name,
):

    exact = layout.cell(
        preferred_name
    )


    if exact is not None:

        return exact


    candidates = []


    for cell in layout.each_cell():

        if cell.name.upper().startswith(
            role.upper()
        ):

            candidates.append(
                cell
            )


    if len(
        candidates
    ) != 1:

        raise RuntimeError(

            f"Could not resolve primitive {role}; "
            f"candidates={[c.name for c in candidates]}"

        )


    return candidates[0]


PRIMITIVES = {

    "P_SYN":

        resolve_cell(
            "P_SYN",
            "P_SYN_W0840_L0500",
        ),

    "N_LOGIC":

        resolve_cell(
            "N_LOGIC",
            "N_LOGIC_W1000_L0150",
        ),

    "P_LOGIC":

        resolve_cell(
            "P_LOGIC",
            "P_LOGIC_W2000_L0150",
        ),

    "N_FB":

        resolve_cell(
            "N_FB",
            "N_FB_W0420_L0300",
        ),

    "P_FB":

        resolve_cell(
            "P_FB",
            "P_FB_W0420_L0300",
        ),

    "N_LEAK":

        resolve_cell(
            "N_LEAK",
            "N_LEAK_W0420_L1000",
        ),

    "N_RESET":

        resolve_cell(
            "N_RESET",
            "N_RESET_W1200_L0150",
        ),

}


print()
print("=" * 80)
print("RESOLVED MOS PRIMITIVES")
print("=" * 80)


for role, cell in PRIMITIVES.items():

    print(
        f"{role:10s}:",
        cell.name
    )


# ================================================================
# 11. PRIMITIVE TERMINALS
# ================================================================

def primitive_terminal_boxes(
    cell,
):

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


PRIMITIVE_TERMS = {

    role:
        primitive_terminal_boxes(
            cell
        )

    for role, cell
    in PRIMITIVES.items()

}


# ================================================================
# 12. ALL 17 MOS DEVICES
# ================================================================

DEVICES = {

    # ------------------------------------------------------------
    # Closed 7-MOS weighted synapse
    # ------------------------------------------------------------

    "P_U1A": {
        "primitive": "P_SYN",
        "origin": (0.0, 8.0),
        "type": "PMOS",
    },

    "P_REF": {
        "primitive": "P_SYN",
        "origin": (3.0, 8.0),
        "type": "PMOS",
    },

    "P_U0": {
        "primitive": "P_SYN",
        "origin": (6.0, 8.0),
        "type": "PMOS",
    },

    "P_U1B": {
        "primitive": "P_SYN",
        "origin": (9.0, 8.0),
        "type": "PMOS",
    },

    "SW1A": {
        "primitive": "N_LOGIC",
        "origin": (0.175, 2.5),
        "type": "NMOS",
    },

    "SW0": {
        "primitive": "N_LOGIC",
        "origin": (6.175, 2.5),
        "type": "NMOS",
    },

    "SW1B": {
        "primitive": "N_LOGIC",
        "origin": (9.175, 2.5),
        "type": "NMOS",
    },


    # ------------------------------------------------------------
    # Added full-neuron devices
    # ------------------------------------------------------------

    "MP_ST1": {
        "primitive": "P_LOGIC",
        "origin": (16.0, 14.0),
        "type": "PMOS",
    },

    "MP_ST2": {
        "primitive": "P_LOGIC",
        "origin": (20.0, 14.0),
        "type": "PMOS",
    },

    "MP_FB": {
        "primitive": "P_FB",
        "origin": (24.0, 14.0),
        "type": "PMOS",
    },

    "MP_BUF": {
        "primitive": "P_LOGIC",
        "origin": (28.0, 14.0),
        "type": "PMOS",
    },

    "MN_ST1": {
        "primitive": "N_LOGIC",
        "origin": (16.0, 7.0),
        "type": "NMOS",
    },

    "MN_ST2": {
        "primitive": "N_LOGIC",
        "origin": (20.0, 7.0),
        "type": "NMOS",
    },

    "MN_FB": {
        "primitive": "N_FB",
        "origin": (24.0, 7.0),
        "type": "NMOS",
    },

    "MN_BUF": {
        "primitive": "N_LOGIC",
        "origin": (28.0, 7.0),
        "type": "NMOS",
    },

    "MN_LEAK": {
        "primitive": "N_LEAK",
        "origin": (32.0, 7.0),
        "type": "NMOS",
    },

    "MN_RST": {
        "primitive": "N_RESET",
        "origin": (36.0, 7.0),
        "type": "NMOS",
    },

}


DEVICE_COUNT_OK = (
    len(
        DEVICES
    ) == 17
)


print()
print("=" * 80)
print("MOS INVENTORY")
print("=" * 80)

print(
    "MOS count:",
    len(
        DEVICES
    )
)

print(
    "Expected : 17"
)

print(
    "Count valid:",
    DEVICE_COUNT_OK
)


# ================================================================
# 13. REFERENCE INSTANCE PRESENCE
# ================================================================

reference_text = REFERENCE_SPICE.read_text(
    encoding="utf-8",
    errors="replace",
)


REFERENCE_INSTANCE_CHECKS = {

    name:
        name in reference_text

    for name
    in DEVICES.keys()

}


REFERENCE_INSTANCE_PASS = all(
    REFERENCE_INSTANCE_CHECKS.values()
)


print()
print("=" * 80)
print("REFERENCE INSTANCE INVENTORY")
print("=" * 80)


for name, status in REFERENCE_INSTANCE_CHECKS.items():

    print(
        f"{name:10s}:",
        status
    )


print(
    "All 17 instances found in reference:",
    REFERENCE_INSTANCE_PASS
)


# ================================================================
# 14. ABSOLUTE TERMINAL BOXES
# ================================================================

DEVICE_TERMS = {}


for device_name, spec in DEVICES.items():

    local = PRIMITIVE_TERMS[
        spec[
            "primitive"
        ]
    ]


    origin = spec[
        "origin"
    ]


    DEVICE_TERMS[
        device_name
    ] = {

        terminal:
            translate_box(
                box,
                origin,
            )

        for terminal, box
        in local.items()

    }


# ================================================================
# 15. TERMINAL -> M1 COMPONENT MAPPING
# ================================================================

DEVICE_M1_COMPONENTS = {}

TERMINAL_MAPPING_OK = True


for device_name, terms in DEVICE_TERMS.items():

    DEVICE_M1_COMPONENTS[
        device_name
    ] = {}


    for terminal, box in terms.items():

        hits = m1_hits_region(

            kdb.Region(
                box
            )

        )


        valid = (
            len(
                hits
            ) == 1
        )


        TERMINAL_MAPPING_OK &= valid


        DEVICE_M1_COMPONENTS[
            device_name
        ][
            terminal
        ] = (

            hits[0]
            if valid
            else None

        )


print()
print("=" * 80)
print("MOS TERMINAL -> M1 COMPONENT MAPPING")
print("=" * 80)

print(
    "All terminal boxes map uniquely:",
    TERMINAL_MAPPING_OK
)


if not TERMINAL_MAPPING_OK:

    for device_name, terms in DEVICE_TERMS.items():

        for terminal, box in terms.items():

            hits = m1_hits_region(

                kdb.Region(
                    box
                )

            )


            if len(
                hits
            ) != 1:

                print(
                    device_name,
                    terminal,
                    "hits=",
                    hits
                )


# ================================================================
# 16. VIRTUAL GATE CONNECTIONS
#
# Primitive top and bottom gate M1 contacts are electrically
# connected through gate poly.
#
# Metal-only geometry does not show that connection, so add one
# explicit virtual connectivity edge per MOS.
# ================================================================

GATE_PAIR_MAPPING_OK = True


for device_name in DEVICES.keys():

    bottom = DEVICE_M1_COMPONENTS[
        device_name
    ][
        "BOTTOM_GATE"
    ]

    top_gate = DEVICE_M1_COMPONENTS[
        device_name
    ][
        "TOP_GATE"
    ]


    valid = bool(

        bottom is not None

        and

        top_gate is not None

    )


    GATE_PAIR_MAPPING_OK &= valid


    if valid:

        uf.union(
            bottom,
            top_gate,
        )


print()
print("=" * 80)
print("MOS GATE-POLY VIRTUAL CONNECTIONS")
print("=" * 80)

print(
    "All 17 gate pairs mapped:",
    GATE_PAIR_MAPPING_OK
)


# ================================================================
# 17. TERMINAL ROOTS
# ================================================================

def terminal_root(
    device,
    terminal,
):

    component = DEVICE_M1_COMPONENTS[
        device
    ][
        terminal
    ]


    if component is None:

        return None


    return uf.find(
        component
    )


def gate_root(
    device,
):

    bottom = terminal_root(
        device,
        "BOTTOM_GATE",
    )

    top_gate = terminal_root(
        device,
        "TOP_GATE",
    )


    if (
        bottom is None
        or
        top_gate is None
        or
        bottom != top_gate
    ):

        return None


    return bottom


ROOTS = {}


for device_name in DEVICES.keys():

    ROOTS[
        device_name
    ] = {

        "LEFT_SD":

            terminal_root(
                device_name,
                "LEFT_SD",
            ),

        "RIGHT_SD":

            terminal_root(
                device_name,
                "RIGHT_SD",
            ),

        "GATE":

            gate_root(
                device_name
            ),

    }


GATE_ROOTS_OK = all(

    ROOTS[
        device
    ][
        "GATE"
    ] is not None

    for device
    in DEVICES.keys()

)


# ================================================================
# 18. DEFINE MAJOR FULL-NEURON NET ROOTS
# ================================================================

NET_ROOTS = {

    # Supplies
    "VDD":

        ROOTS[
            "MP_ST1"
        ][
            "LEFT_SD"
        ],

    "VSS":

        ROOTS[
            "MN_ST2"
        ][
            "LEFT_SD"
        ],


    # Main functional nets
    "VMEM":

        ROOTS[
            "MP_ST1"
        ][
            "GATE"
        ],

    "P_MID":

        ROOTS[
            "MP_ST1"
        ][
            "RIGHT_SD"
        ],

    "N_MID":

        ROOTS[
            "MN_ST1"
        ][
            "LEFT_SD"
        ],

    "VRAW":

        ROOTS[
            "MP_ST2"
        ][
            "RIGHT_SD"
        ],

    "SPIKE":

        ROOTS[
            "MP_BUF"
        ][
            "RIGHT_SD"
        ],

    "VLEAK":

        ROOTS[
            "MN_LEAK"
        ][
            "GATE"
        ],


    # Synapse controls
    "VBIAS":

        ROOTS[
            "P_REF"
        ][
            "GATE"
        ],

    "GATE_W0":

        ROOTS[
            "SW0"
        ][
            "GATE"
        ],

    "GATE_W1":

        ROOTS[
            "SW1A"
        ][
            "GATE"
        ],

}


# ================================================================
# 19. CHECK ADDED 10-MOS TOPOLOGY
# ================================================================

ADDED_EXPECTED = {

    "MP_ST1": {
        "LEFT_SD": "VDD",
        "RIGHT_SD": "P_MID",
        "GATE": "VMEM",
    },

    "MP_ST2": {
        "LEFT_SD": "P_MID",
        "RIGHT_SD": "VRAW",
        "GATE": "VMEM",
    },

    "MP_FB": {
        "LEFT_SD": "P_MID",
        "RIGHT_SD": "VSS",
        "GATE": "VRAW",
    },

    "MP_BUF": {
        "LEFT_SD": "VDD",
        "RIGHT_SD": "SPIKE",
        "GATE": "VRAW",
    },

    "MN_ST1": {
        "LEFT_SD": "N_MID",
        "RIGHT_SD": "VRAW",
        "GATE": "VMEM",
    },

    "MN_ST2": {
        "LEFT_SD": "VSS",
        "RIGHT_SD": "N_MID",
        "GATE": "VMEM",
    },

    "MN_FB": {
        "LEFT_SD": "N_MID",
        "RIGHT_SD": "VDD",
        "GATE": "VRAW",
    },

    "MN_BUF": {
        "LEFT_SD": "VSS",
        "RIGHT_SD": "SPIKE",
        "GATE": "VRAW",
    },

    "MN_LEAK": {
        "LEFT_SD": "VSS",
        "RIGHT_SD": "VMEM",
        "GATE": "VLEAK",
    },

    "MN_RST": {
        "LEFT_SD": "VSS",
        "RIGHT_SD": "VMEM",
        "GATE": "SPIKE",
    },

}


ADDED_DEVICE_CHECKS = {}


for device, expected in ADDED_EXPECTED.items():

    terminal_checks = {}


    for terminal, net_name in expected.items():

        terminal_checks[
            terminal
        ] = (

            ROOTS[
                device
            ][
                terminal
            ]

            ==

            NET_ROOTS[
                net_name
            ]

        )


    ADDED_DEVICE_CHECKS[
        device
    ] = terminal_checks


ADDED_TOPOLOGY_PASS = all(

    all(
        terminal_checks.values()
    )

    for terminal_checks
    in ADDED_DEVICE_CHECKS.values()

)


print()
print("=" * 80)
print("ADDED 10-MOS NEURON TOPOLOGY")
print("=" * 80)


for device, terminal_checks in ADDED_DEVICE_CHECKS.items():

    device_pass = all(
        terminal_checks.values()
    )


    print(
        f"{device:10s}:",
        device_pass,
        terminal_checks
    )


print(
    "Added-neuron topology PASS:",
    ADDED_TOPOLOGY_PASS
)


# ================================================================
# 20. WEIGHTED SYNAPSE — DISCOVER THREE BRANCH ROOTS
#
# PMOS S/D orientation is treated as symmetric here.
#
# Each unit PMOS must have:
#       {VDD, BRANCH}
#
# Each switch must have:
#       {VMEM, BRANCH}
#
# This is intentionally orientation-independent because MOS
# source/drain are geometrically symmetric in these primitives.
# ================================================================

def sd_root_set(
    device,
):

    return {

        ROOTS[
            device
        ][
            "LEFT_SD"
        ],

        ROOTS[
            device
        ][
            "RIGHT_SD"
        ],

    }


def discover_branch(
    pmos,
    switch,
):

    p_roots = sd_root_set(
        pmos
    )

    s_roots = sd_root_set(
        switch
    )


    common = (

        p_roots

        &

        s_roots

    )


    candidates = {

        root

        for root in common

        if root
        not in {

            NET_ROOTS[
                "VDD"
            ],

            NET_ROOTS[
                "VMEM"
            ],

        }

    }


    if len(
        candidates
    ) != 1:

        return None


    branch = next(
        iter(
            candidates
        )
    )


    valid = bool(

        p_roots
        ==
        {

            NET_ROOTS[
                "VDD"
            ],

            branch,

        }

        and

        s_roots
        ==
        {

            NET_ROOTS[
                "VMEM"
            ],

            branch,

        }

    )


    if not valid:

        return None


    return branch


BR_U1A = discover_branch(
    "P_U1A",
    "SW1A",
)

BR_U0 = discover_branch(
    "P_U0",
    "SW0",
)

BR_U1B = discover_branch(
    "P_U1B",
    "SW1B",
)


BRANCH_DISCOVERY_PASS = bool(

    BR_U1A is not None

    and

    BR_U0 is not None

    and

    BR_U1B is not None

)


NET_ROOTS[
    "SYN_BRANCH_U1A"
] = BR_U1A

NET_ROOTS[
    "SYN_BRANCH_U0"
] = BR_U0

NET_ROOTS[
    "SYN_BRANCH_U1B"
] = BR_U1B


print()
print("=" * 80)
print("SYNAPSE BRANCH DISCOVERY")
print("=" * 80)

print(
    "P_U1A <-> SW1A:",
    BR_U1A
)

print(
    "P_U0  <-> SW0 :",
    BR_U0
)

print(
    "P_U1B <-> SW1B:",
    BR_U1B
)

print(
    "Branch discovery PASS:",
    BRANCH_DISCOVERY_PASS
)


# ================================================================
# 21. WEIGHTED SYNAPSE CONTROL / REFERENCE CHECKS
# ================================================================

P_REF_SD = sd_root_set(
    "P_REF"
)


P_REF_PASS = bool(

    ROOTS[
        "P_REF"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "VBIAS"
    ]

    and

    P_REF_SD
    ==
    {

        NET_ROOTS[
            "VDD"
        ],

        NET_ROOTS[
            "VBIAS"
        ],

    }

)


P_U_GATES_PASS = bool(

    ROOTS[
        "P_U1A"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "VBIAS"
    ]

    and

    ROOTS[
        "P_U0"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "VBIAS"
    ]

    and

    ROOTS[
        "P_U1B"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "VBIAS"
    ]

)


SWITCH_GATES_PASS = bool(

    ROOTS[
        "SW0"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "GATE_W0"
    ]

    and

    ROOTS[
        "SW1A"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "GATE_W1"
    ]

    and

    ROOTS[
        "SW1B"
    ][
        "GATE"
    ]
    ==
    NET_ROOTS[
        "GATE_W1"
    ]

)


SYNAPSE_TOPOLOGY_PASS = bool(

    BRANCH_DISCOVERY_PASS

    and

    P_REF_PASS

    and

    P_U_GATES_PASS

    and

    SWITCH_GATES_PASS

)


print()
print("=" * 80)
print("WEIGHTED SYNAPSE TOPOLOGY")
print("=" * 80)

print(
    "P_REF diode/reference topology:",
    P_REF_PASS
)

print(
    "All P-unit gates -> VBIAS    :",
    P_U_GATES_PASS
)

print(
    "Switch gate controls correct :",
    SWITCH_GATES_PASS
)

print(
    "Three branch nets valid      :",
    BRANCH_DISCOVERY_PASS
)

print(
    "Weighted synapse topology PASS:",
    SYNAPSE_TOPOLOGY_PASS
)


# ================================================================
# 22. LOGICAL NET INVENTORY
# ================================================================

EXPECTED_NET_NAMES = [

    "VDD",
    "VSS",
    "VBIAS",

    "SYN_BRANCH_U1A",
    "SYN_BRANCH_U0",
    "SYN_BRANCH_U1B",

    "VMEM",

    "GATE_W0",
    "GATE_W1",

    "VLEAK",

    "P_MID",
    "N_MID",

    "VRAW",

    "SPIKE",

]


NET_ROOTS_COMPLETE = all(

    NET_ROOTS.get(
        name
    ) is not None

    for name
    in EXPECTED_NET_NAMES

)


logical_roots = [

    NET_ROOTS[
        name
    ]

    for name
    in EXPECTED_NET_NAMES

    if NET_ROOTS.get(
        name
    ) is not None

]


LOGICAL_NET_COUNT = len(
    EXPECTED_NET_NAMES
)


UNIQUE_LOGICAL_ROOT_COUNT = len(
    set(
        logical_roots
    )
)


NO_LOGICAL_CROSS_NET_SHORTS = bool(

    NET_ROOTS_COMPLETE

    and

    UNIQUE_LOGICAL_ROOT_COUNT
    ==
    LOGICAL_NET_COUNT

)


print()
print("=" * 80)
print("FINAL LOGICAL NET INVENTORY")
print("=" * 80)


for net_name in EXPECTED_NET_NAMES:

    print(
        f"{net_name:18s}:",
        NET_ROOTS.get(
            net_name
        )
    )


print()
print(
    "Expected logical nets :",
    LOGICAL_NET_COUNT
)

print(
    "Unique logical roots  :",
    UNIQUE_LOGICAL_ROOT_COUNT
)

print(
    "All roots identified  :",
    NET_ROOTS_COMPLETE
)

print(
    "Cross-net shorts      :",
    not NO_LOGICAL_CROSS_NET_SHORTS
)


# ================================================================
# 23. ALL CONDUCTOR ROOTS
#
# After:
#   - M1/M2 VIA connections
#   - MOS gate-poly virtual unions
#
# every conductor root should correspond to exactly one of the
# 14 intended circuit nets.
# ================================================================

ALL_NODE_COUNT = (
    N_M1
    +
    N_M2
)


ALL_CONDUCTOR_ROOTS = {

    uf.find(
        node
    )

    for node
    in range(
        ALL_NODE_COUNT
    )

}


INTENDED_ROOT_SET = set(
    logical_roots
)


CONDUCTOR_ROOT_COUNT = len(
    ALL_CONDUCTOR_ROOTS
)


NO_UNACCOUNTED_ROOTS = bool(

    NET_ROOTS_COMPLETE

    and

    ALL_CONDUCTOR_ROOTS
    ==
    INTENDED_ROOT_SET

)


print()
print("=" * 80)
print("GLOBAL CONDUCTOR ROOT AUDIT")
print("=" * 80)

print(
    "Actual conductor roots :",
    CONDUCTOR_ROOT_COUNT
)

print(
    "Expected logical roots :",
    LOGICAL_NET_COUNT
)

print(
    "Unaccounted roots      :",
    len(
        ALL_CONDUCTOR_ROOTS
        -
        INTENDED_ROOT_SET
    )
)

print(
    "Missing intended roots :",
    len(
        INTENDED_ROOT_SET
        -
        ALL_CONDUCTOR_ROOTS
    )
)

print(
    "Exact root-set match   :",
    NO_UNACCOUNTED_ROOTS
)


# ================================================================
# 24. BODY / WELL AUDIT
# ================================================================

NWELL_REGION = kdb.Region(

    top.begin_shapes_rec(
        NWELL_LAYER
    )

).merged()


TAP_REGION = kdb.Region(

    top.begin_shapes_rec(
        TAP_LAYER
    )

).merged()


NSDM_REGION = kdb.Region(

    top.begin_shapes_rec(
        NSDM_LAYER
    )

).merged()


PSDM_REGION = kdb.Region(

    top.begin_shapes_rec(
        PSDM_LAYER
    )

).merged()


NWELL_COMPONENTS = list(
    NWELL_REGION.each_merged()
)


# n-tap = TAP + NSDM + NWELL
NTAP_REGION = (

    TAP_REGION

    &

    NSDM_REGION

    &

    NWELL_REGION

).merged()


# p-tap = TAP + PSDM outside NWELL
PTAP_REGION = (

    (
        TAP_REGION

        &

        PSDM_REGION

    )

    -

    NWELL_REGION

).merged()


NTAP_COMPONENTS = list(
    NTAP_REGION.each_merged()
)

PTAP_COMPONENTS = list(
    PTAP_REGION.each_merged()
)


print()
print("=" * 80)
print("BODY-TIE GEOMETRY INVENTORY")
print("=" * 80)

print(
    "NWELL components:",
    len(
        NWELL_COMPONENTS
    )
)

print(
    "n-tap components:",
    len(
        NTAP_COMPONENTS
    )
)

print(
    "p-tap components:",
    len(
        PTAP_COMPONENTS
    )
)


NWELL_COUNT_OK = (
    len(
        NWELL_COMPONENTS
    ) == 2
)


NTAP_COUNT_OK = (
    len(
        NTAP_COMPONENTS
    ) == 2
)


PTAP_COUNT_OK = (
    len(
        PTAP_COMPONENTS
    ) == 2
)


# ================================================================
# 25. TAP METAL ROOTS
# ================================================================

def root_for_region_on_m1(
    region,
):

    hits = m1_hits_region(
        region
    )


    if len(
        hits
    ) != 1:

        return None


    return uf.find(
        hits[0]
    )


NTAP_ROOTS = [

    root_for_region_on_m1(

        kdb.Region(
            polygon
        )

    )

    for polygon
    in NTAP_COMPONENTS

]


PTAP_ROOTS = [

    root_for_region_on_m1(

        kdb.Region(
            polygon
        )

    )

    for polygon
    in PTAP_COMPONENTS

]


NTAPS_TO_VDD = bool(

    NTAP_COUNT_OK

    and

    all(

        root
        ==
        NET_ROOTS[
            "VDD"
        ]

        for root
        in NTAP_ROOTS

    )

)


PTAPS_TO_VSS = bool(

    PTAP_COUNT_OK

    and

    all(

        root
        ==
        NET_ROOTS[
            "VSS"
        ]

        for root
        in PTAP_ROOTS

    )

)


print()
print("=" * 80)
print("BODY-TAP METAL CONNECTIVITY")
print("=" * 80)

print(
    "n-tap roots:",
    NTAP_ROOTS
)

print(
    "p-tap roots:",
    PTAP_ROOTS
)

print(
    "All n-taps -> VDD:",
    NTAPS_TO_VDD
)

print(
    "All p-taps -> VSS:",
    PTAPS_TO_VSS
)


# ================================================================
# 26. NWELL COMPONENT LOOKUP
# ================================================================

def nwell_component_at_point(
    point,
):

    probe = kdb.Region(

        centered_box(

            point[0],

            point[1],

            0.020,

        )

    )


    hits = []


    for index, polygon in enumerate(
        NWELL_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            &

            probe

        ).is_empty():

            hits.append(
                index
            )


    if len(
        hits
    ) == 1:

        return hits[0]


    return None


# ================================================================
# 27. ASSOCIATE n-TAPS WITH THEIR NWELL COMPONENT
# ================================================================

NTAP_NWELL_COMPONENTS = []


for tap_polygon in NTAP_COMPONENTS:

    bbox = tap_polygon.bbox()

    point = center_um(
        bbox
    )


    NTAP_NWELL_COMPONENTS.append(

        nwell_component_at_point(
            point
        )

    )


NTAP_NWELL_ASSOCIATION_OK = bool(

    NTAP_COUNT_OK

    and

    all(

        item is not None

        for item
        in NTAP_NWELL_COMPONENTS

    )

    and

    len(
        set(
            NTAP_NWELL_COMPONENTS
        )
    ) == 2

)


print()
print(
    "n-tap NWELL components:",
    NTAP_NWELL_COMPONENTS
)

print(
    "Each NWELL has its own n-tap:",
    NTAP_NWELL_ASSOCIATION_OK
)


# ================================================================
# 28. PMOS MUST RESIDE IN A TIED NWELL
# ================================================================

PMOS_DEVICES = [

    name

    for name, spec
    in DEVICES.items()

    if spec[
        "type"
    ] == "PMOS"

]


PMOS_NWELL_RESULTS = {}


for device in PMOS_DEVICES:

    left_point = center_um(

        DEVICE_TERMS[
            device
        ][
            "LEFT_SD"
        ]

    )


    right_point = center_um(

        DEVICE_TERMS[
            device
        ][
            "RIGHT_SD"
        ]

    )


    left_nwell = nwell_component_at_point(
        left_point
    )

    right_nwell = nwell_component_at_point(
        right_point
    )


    valid = bool(

        left_nwell is not None

        and

        right_nwell is not None

        and

        left_nwell
        ==
        right_nwell

        and

        left_nwell
        in
        NTAP_NWELL_COMPONENTS

    )


    PMOS_NWELL_RESULTS[
        device
    ] = {

        "left":
            left_nwell,

        "right":
            right_nwell,

        "valid":
            valid,

    }


PMOS_IN_TIED_NWELL = all(

    item[
        "valid"
    ]

    for item
    in PMOS_NWELL_RESULTS.values()

)


print()
print("=" * 80)
print("PMOS BODY / NWELL AUDIT")
print("=" * 80)


for device, result in PMOS_NWELL_RESULTS.items():

    print(
        f"{device:10s}:",
        result
    )


print(
    "All PMOS in VDD-tied NWELL:",
    PMOS_IN_TIED_NWELL
)


# ================================================================
# 29. NMOS MUST BE OUTSIDE NWELL
# ================================================================

NMOS_DEVICES = [

    name

    for name, spec
    in DEVICES.items()

    if spec[
        "type"
    ] == "NMOS"

]


NMOS_OUTSIDE_RESULTS = {}


for device in NMOS_DEVICES:

    left_point = center_um(

        DEVICE_TERMS[
            device
        ][
            "LEFT_SD"
        ]

    )


    right_point = center_um(

        DEVICE_TERMS[
            device
        ][
            "RIGHT_SD"
        ]

    )


    left_nwell = nwell_component_at_point(
        left_point
    )

    right_nwell = nwell_component_at_point(
        right_point
    )


    valid = bool(

        left_nwell is None

        and

        right_nwell is None

    )


    NMOS_OUTSIDE_RESULTS[
        device
    ] = {

        "left_nwell":
            left_nwell,

        "right_nwell":
            right_nwell,

        "valid":
            valid,

    }


NMOS_OUTSIDE_NWELL = all(

    item[
        "valid"
    ]

    for item
    in NMOS_OUTSIDE_RESULTS.values()

)


print()
print("=" * 80)
print("NMOS SUBSTRATE AUDIT")
print("=" * 80)


for device, result in NMOS_OUTSIDE_RESULTS.items():

    print(
        f"{device:10s}:",
        result
    )


print(
    "All NMOS outside NWELL:",
    NMOS_OUTSIDE_NWELL
)


BODY_TIE_PASS = bool(

    NWELL_COUNT_OK

    and

    NTAP_COUNT_OK

    and

    PTAP_COUNT_OK

    and

    NTAPS_TO_VDD

    and

    PTAPS_TO_VSS

    and

    NTAP_NWELL_ASSOCIATION_OK

    and

    PMOS_IN_TIED_NWELL

    and

    NMOS_OUTSIDE_NWELL

)


print()
print("=" * 80)
print("BODY-TIE FINAL STATUS")
print("=" * 80)

print(
    "NWELL count valid        :",
    NWELL_COUNT_OK
)

print(
    "n-tap count valid        :",
    NTAP_COUNT_OK
)

print(
    "p-tap count valid        :",
    PTAP_COUNT_OK
)

print(
    "n-taps connected to VDD  :",
    NTAPS_TO_VDD
)

print(
    "p-taps connected to VSS  :",
    PTAPS_TO_VSS
)

print(
    "PMOS well placement      :",
    PMOS_IN_TIED_NWELL
)

print(
    "NMOS substrate placement :",
    NMOS_OUTSIDE_NWELL
)

print(
    "BODY_TIE_PASS            :",
    BODY_TIE_PASS
)


# ================================================================
# 30. EXTERNAL / INTERNAL NET CLASSIFICATION
# ================================================================

EXTERNAL_NETS = [

    "VDD",
    "VSS",
    "VBIAS",
    "GATE_W0",
    "GATE_W1",
    "VLEAK",
    "VMEM",
    "SPIKE",

]


INTERNAL_NETS = [

    "SYN_BRANCH_U1A",
    "SYN_BRANCH_U0",
    "SYN_BRANCH_U1B",
    "P_MID",
    "N_MID",
    "VRAW",

]


EXTERNAL_ROOTS_DISTINCT = bool(

    len(
        {

            NET_ROOTS[
                name
            ]

            for name
            in EXTERNAL_NETS

        }
    )
    ==
    len(
        EXTERNAL_NETS
    )

)


print()
print("=" * 80)
print("TOP-LEVEL NET CLASSIFICATION")
print("=" * 80)

print(
    "External nets:",
    EXTERNAL_NETS
)

print(
    "Internal nets:",
    INTERNAL_NETS
)

print(
    "External roots distinct:",
    EXTERNAL_ROOTS_DISTINCT
)

print(
    "Physical Cmem:",
    "EXTERNAL / NOT PART OF CORE LAYOUT"
)


# ================================================================
# 31. INPUT INTEGRITY
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
# 32. FINAL PASS
# ================================================================

STEP39A_PASS = bool(

    DEVICE_COUNT_OK

    and

    REFERENCE_INSTANCE_PASS

    and

    VIA_MAPPING_OK

    and

    TERMINAL_MAPPING_OK

    and

    GATE_PAIR_MAPPING_OK

    and

    GATE_ROOTS_OK

    and

    ADDED_TOPOLOGY_PASS

    and

    SYNAPSE_TOPOLOGY_PASS

    and

    NET_ROOTS_COMPLETE

    and

    NO_LOGICAL_CROSS_NET_SHORTS

    and

    CONDUCTOR_ROOT_COUNT
    ==
    LOGICAL_NET_COUNT

    and

    NO_UNACCOUNTED_ROOTS

    and

    BODY_TIE_PASS

    and

    EXTERNAL_ROOTS_DISTINCT

    and

    INPUT_UNCHANGED

)


# ================================================================
# 33. WRITE AUDIT RECORD
# ================================================================

audit_record = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "39A",

    "audit":
        "full_neuron_geometry_connectivity_topology",

    "input": {

        "gds":
            str(
                INPUT_GDS
            ),

        "top":
            TOP_NAME,

        "sha256":
            INPUT_HASH_BEFORE,

        "final_drc_report":
            str(
                FINAL_DRC_REPORT
            ),

    },

    "design": {

        "mos_count":
            len(
                DEVICES
            ),

        "expected_mos_count":
            17,

        "expected_logical_conductor_nets":
            14,

        "physical_cmem":
            False,

        "cmem_policy":
            "external_ideal_5pF_from_VMEM_to_VSS",

    },

    "net_roots": {

        name:
            (
                int(
                    NET_ROOTS[
                        name
                    ]
                )

                if NET_ROOTS.get(
                    name
                ) is not None

                else None
            )

        for name
        in EXPECTED_NET_NAMES

    },

    "external_nets":
        EXTERNAL_NETS,

    "internal_nets":
        INTERNAL_NETS,

    "checks": {

        "device_count":
            DEVICE_COUNT_OK,

        "reference_instances":
            REFERENCE_INSTANCE_PASS,

        "via_mapping":
            VIA_MAPPING_OK,

        "terminal_mapping":
            TERMINAL_MAPPING_OK,

        "gate_pair_mapping":
            GATE_PAIR_MAPPING_OK,

        "gate_roots":
            GATE_ROOTS_OK,

        "added_10mos_topology":
            ADDED_TOPOLOGY_PASS,

        "weighted_synapse_topology":
            SYNAPSE_TOPOLOGY_PASS,

        "branch_discovery":
            BRANCH_DISCOVERY_PASS,

        "net_roots_complete":
            NET_ROOTS_COMPLETE,

        "logical_net_count":
            LOGICAL_NET_COUNT,

        "unique_logical_root_count":
            UNIQUE_LOGICAL_ROOT_COUNT,

        "no_cross_net_shorts":
            NO_LOGICAL_CROSS_NET_SHORTS,

        "actual_conductor_root_count":
            CONDUCTOR_ROOT_COUNT,

        "no_unaccounted_conductor_roots":
            NO_UNACCOUNTED_ROOTS,

        "nwell_count":
            NWELL_COUNT_OK,

        "ntap_count":
            NTAP_COUNT_OK,

        "ptap_count":
            PTAP_COUNT_OK,

        "ntaps_to_vdd":
            NTAPS_TO_VDD,

        "ptaps_to_vss":
            PTAPS_TO_VSS,

        "pmos_in_tied_nwell":
            PMOS_IN_TIED_NWELL,

        "nmos_outside_nwell":
            NMOS_OUTSIDE_NWELL,

        "body_ties":
            BODY_TIE_PASS,

        "external_roots_distinct":
            EXTERNAL_ROOTS_DISTINCT,

        "input_unchanged":
            INPUT_UNCHANGED,

    },

    "step39a_pass":
        STEP39A_PASS,

}


OUTPUT_JSON.write_text(

    json.dumps(
        audit_record,
        indent=2,
    ),

    encoding="utf-8",

)


AUDIT_RECORD_OK = bool(

    OUTPUT_JSON.exists()

    and

    OUTPUT_JSON.stat().st_size > 0

)


STEP39A_PASS = bool(

    STEP39A_PASS

    and

    AUDIT_RECORD_OK

)


# ================================================================
# 34. FINAL RESULT
# ================================================================

print()
print("=" * 80)
print("STEP 39A — FINAL RESULT")
print("=" * 80)

print(
    "MOS inventory                  :",
    DEVICE_COUNT_OK
)

print(
    "Reference inventory            :",
    REFERENCE_INSTANCE_PASS
)

print(
    "VIA1 connectivity              :",
    VIA_MAPPING_OK
)

print(
    "MOS terminal mapping           :",
    TERMINAL_MAPPING_OK
)

print(
    "Gate-poly logical connectivity :",
    GATE_PAIR_MAPPING_OK
)

print(
    "Weighted synapse topology      :",
    SYNAPSE_TOPOLOGY_PASS
)

print(
    "Added 10-MOS topology          :",
    ADDED_TOPOLOGY_PASS
)

print(
    "Logical nets identified        :",
    NET_ROOTS_COMPLETE
)

print(
    "Logical net count              :",
    LOGICAL_NET_COUNT
)

print(
    "Unique logical roots           :",
    UNIQUE_LOGICAL_ROOT_COUNT
)

print(
    "Cross-net shorts               :",
    not NO_LOGICAL_CROSS_NET_SHORTS
)

print(
    "Actual conductor roots         :",
    CONDUCTOR_ROOT_COUNT
)

print(
    "Expected conductor roots       :",
    LOGICAL_NET_COUNT
)

print(
    "Unaccounted conductor roots    :",
    not NO_UNACCOUNTED_ROOTS
)

print(
    "PMOS/NMOS body audit           :",
    BODY_TIE_PASS
)

print(
    "External pin roots distinct    :",
    EXTERNAL_ROOTS_DISTINCT
)

print(
    "Input GDS unchanged            :",
    INPUT_UNCHANGED
)

print(
    "Audit record written           :",
    AUDIT_RECORD_OK
)

print()

print(
    "STEP39A_PASS =",
    STEP39A_PASS
)


if not STEP39A_PASS:

    raise RuntimeError(
        "STEP 39A full-neuron connectivity/topology audit failed."
    )


print()
print("=" * 80)
print("FULL-NEURON CONNECTIVITY / TOPOLOGY AUDIT — PASS")
print("=" * 80)

print()
print(
    "17 MOS devices        : VERIFIED"
)

print(
    "14 logical nets       : VERIFIED"
)

print(
    "Cross-net shorts      : NONE DETECTED"
)

print(
    "Floating conductor nets: NONE DETECTED"
)

print(
    "Weighted synapse      : VERIFIED"
)

print(
    "Schmitt + buffer      : VERIFIED"
)

print(
    "Leak path             : VERIFIED"
)

print(
    "SPIKE reset feedback  : VERIFIED"
)

print(
    "PMOS body / NWELL     : VERIFIED"
)

print(
    "NMOS substrate / VSS  : VERIFIED"
)

print(
    "Physical Cmem         : EXTERNAL BY DESIGN"
)

print()
print(
    "Audit record:"
)

print(
    OUTPUT_JSON
)

print()
print(
    "NEXT:"
)

print(
    "Generate LVS-label derivative and run full 17-MOS KLayout LVS."
)