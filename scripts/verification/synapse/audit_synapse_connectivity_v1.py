# ================================================================
# NeuroLIF-SKY130
# STEP 26A — FINAL CONNECTIVITY / TOPOLOGY AUDIT
#
# Input:
#   neurolif_synapse_vss_v1.gds
#
# This script DOES NOT modify the GDS.
#
# It audits actual recursive GDS conductor geometry:
#
#   M1   68/20
#   VIA1 68/44
#   M2   69/20
#
# and explicitly models the fact that the two M1 gate-contact
# landings of each MOS device belong to the same polysilicon gate.
#
# It then checks:
#
#   VDD
#   VBIAS
#   P_U1A_TO_SW1A
#   P_U0_TO_SW0
#   P_U1B_TO_SW1B
#   VMEM
#   GATE_W0
#   GATE_W1
#   VSS
#
# for:
#
#   1. intended terminal connectivity
#   2. no cross-net shorts
#   3. expected number of conductor networks
#   4. M1/VIA1/M2 transition integrity
#   5. PMOS common-NWELL body connectivity
#   6. correct n-tap / p-tap implant context
#
# This is NOT LVS.
# This is the final pre-LVS topology audit.
# ================================================================

from pathlib import Path
import json

import klayout.db as kdb


print("=" * 80)
print("NEUROLIF-SKY130 — STEP 26A: FINAL CONNECTIVITY / TOPOLOGY AUDIT")
print("=" * 80)


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_GDS = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vss_v1.gds"
)

PLACEMENT_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_placement_v1.json"
)

BRANCH_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_branches_v2.json"
)

VMEM_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vmem_v1.json"
)

VSS_MANIFEST = (
    PROJECT_ROOT
    / "layout"
    / "synapse"
    / "neurolif_synapse_vss_v1.json"
)

OUTPUT_AUDIT = (
    PROJECT_ROOT
    / "verification"
    / "synapse"
    / "connectivity"
    / "neurolif_synapse_final_connectivity_audit.json"
)


TOP_CELL_NAME = (
    "NEUROLIF_WEIGHTED_SYNAPSE_VSS_V1"
)

P_SYN_NAME = (
    "P_SYN_W0840_L0500"
)

N_SWITCH_NAME = (
    "N_LOGIC_W1000_L0150"
)


for path in [
    INPUT_GDS,
    PLACEMENT_MANIFEST,
    BRANCH_MANIFEST,
    VMEM_MANIFEST,
    VSS_MANIFEST,
]:

    if not path.exists():
        raise FileNotFoundError(path)


# ================================================================
# 2. LOAD GDS
# ================================================================

layout = kdb.Layout()

layout.read(
    str(INPUT_GDS)
)

DBU = layout.dbu


top = layout.cell(
    TOP_CELL_NAME
)

p_syn = layout.cell(
    P_SYN_NAME
)

n_switch = layout.cell(
    N_SWITCH_NAME
)


if top is None:

    raise RuntimeError(
        f"Missing top cell: {TOP_CELL_NAME}"
    )


if p_syn is None:

    raise RuntimeError(
        f"Missing primitive: {P_SYN_NAME}"
    )


if n_switch is None:

    raise RuntimeError(
        f"Missing primitive: {N_SWITCH_NAME}"
    )


print()
print("=" * 80)
print("DATABASE")
print("=" * 80)

print(
    "Input GDS:",
    INPUT_GDS
)

print(
    "Top cell:",
    TOP_CELL_NAME
)

print(
    "DBU:",
    DBU,
    "um"
)

print(
    "Step 25B DRC status: CLEAN / 0 violations"
)


# ================================================================
# 3. LOAD MANIFESTS
# ================================================================

placement_data = json.loads(
    PLACEMENT_MANIFEST.read_text(
        encoding="utf-8"
    )
)

branch_data = json.loads(
    BRANCH_MANIFEST.read_text(
        encoding="utf-8"
    )
)

vmem_data = json.loads(
    VMEM_MANIFEST.read_text(
        encoding="utf-8"
    )
)

vss_data = json.loads(
    VSS_MANIFEST.read_text(
        encoding="utf-8"
    )
)


placements = placement_data[
    "placement_um"
]

branches = branch_data[
    "branches"
]


# ================================================================
# 4. LAYERS
# ================================================================

DIFF_LAYER = layout.find_layer(
    65,
    20
)

TAP_LAYER = layout.find_layer(
    65,
    44
)

NWELL_LAYER = layout.find_layer(
    64,
    20
)

NSDM_LAYER = layout.find_layer(
    93,
    44
)

PSDM_LAYER = layout.find_layer(
    94,
    20
)

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


required_layers = {

    "DIFF":
        DIFF_LAYER,

    "TAP":
        TAP_LAYER,

    "NWELL":
        NWELL_LAYER,

    "NSDM":
        NSDM_LAYER,

    "PSDM":
        PSDM_LAYER,

    "M1":
        M1_LAYER,

    "VIA1":
        VIA1_LAYER,

    "M2":
        M2_LAYER,

}


print()
print("=" * 80)
print("REQUIRED LAYERS")
print("=" * 80)


LAYERS_OK = True


for name, index in required_layers.items():

    present = (
        index is not None
    )

    print(
        f"{name:6s}:",
        present,
        f"(index={index})"
    )

    LAYERS_OK &= present


if not LAYERS_OK:

    raise RuntimeError(
        "Required physical layers are missing."
    )


# ================================================================
# 5. HELPERS
# ================================================================

def to_dbu(
    value_um,
):

    return int(
        round(
            value_um / DBU
        )
    )


def center(
    box,
):

    return (

        (
            box.left
            + box.right
        ) / 2.0,

        (
            box.bottom
            + box.top
        ) / 2.0,

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


def translate_box(
    box,
    dx,
    dy,
):

    return kdb.Box(

        box.left + dx,

        box.bottom + dy,

        box.right + dx,

        box.top + dy,

    )


def make_box_um(
    x1,
    y1,
    x2,
    y2,
):

    return kdb.Box(

        to_dbu(
            min(x1, x2)
        ),

        to_dbu(
            min(y1, y2)
        ),

        to_dbu(
            max(x1, x2)
        ),

        to_dbu(
            max(y1, y2)
        ),

    )


def tiny_probe_um(
    x,
    y,
    half=0.025,
):

    return make_box_um(

        x - half,

        y - half,

        x + half,

        y + half,

    )


# ================================================================
# 6. EXTRACT MOS TERMINALS FROM ACTUAL PRIMITIVES
# ================================================================

def extract_mos_terminals(
    cell,
):

    diff_boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            DIFF_LAYER
        ).each()

    ]


    m1_boxes = [

        shape.bbox()

        for shape
        in cell.shapes(
            M1_LAYER
        ).each()

    ]


    if len(diff_boxes) != 1:

        raise RuntimeError(

            f"{cell.name}: expected "
            "exactly one DIFF region."

        )


    diff = diff_boxes[0]


    sd_boxes = [

        box

        for box
        in m1_boxes

        if overlaps(
            box,
            diff,
        )

    ]


    gate_boxes = [

        box

        for box
        in m1_boxes

        if not overlaps(
            box,
            diff,
        )

    ]


    sd_boxes.sort(
        key=lambda box:
            center(box)[0]
    )


    gate_boxes.sort(
        key=lambda box:
            center(box)[1]
    )


    if len(sd_boxes) != 2:

        raise RuntimeError(

            f"{cell.name}: expected "
            "two S/D M1 contacts."

        )


    if len(gate_boxes) != 2:

        raise RuntimeError(

            f"{cell.name}: expected "
            "two gate M1 contacts."

        )


    return {

        "left_sd":
            sd_boxes[0],

        "right_sd":
            sd_boxes[1],

        "bottom_gate":
            gate_boxes[0],

        "top_gate":
            gate_boxes[1],

    }


P_TERM = extract_mos_terminals(
    p_syn
)

N_TERM = extract_mos_terminals(
    n_switch
)


def absolute_terminal(
    role,
    local_box,
):

    origin = placements[
        role
    ][
        "origin_um"
    ]


    return translate_box(

        local_box,

        to_dbu(
            float(
                origin[0]
            )
        ),

        to_dbu(
            float(
                origin[1]
            )
        ),

    )


print()
print("=" * 80)
print("DEVICE TERMINAL EXTRACTION")
print("=" * 80)

print(
    "P_SYN terminals: PASS"
)

print(
    "N_SWITCH terminals: PASS"
)


# ================================================================
# 7. BUILD RECURSIVE CONDUCTOR REGIONS
#
# Region(cell.begin_shapes_rec(layer)) gives us the actual
# hierarchical shapes transformed into top-cell coordinates.
# ================================================================

def recursive_region(
    layer_index,
):

    region = kdb.Region(

        top.begin_shapes_rec(
            layer_index
        )

    )

    return region.merged()


M1_REGION = recursive_region(
    M1_LAYER
)

VIA1_REGION = recursive_region(
    VIA1_LAYER
)

M2_REGION = recursive_region(
    M2_LAYER
)

NWELL_REGION = recursive_region(
    NWELL_LAYER
)

TAP_REGION = recursive_region(
    TAP_LAYER
)

NSDM_REGION = recursive_region(
    NSDM_LAYER
)

PSDM_REGION = recursive_region(
    PSDM_LAYER
)


M1_COMPONENTS = list(
    M1_REGION.each()
)

M2_COMPONENTS = list(
    M2_REGION.each()
)

VIA1_COMPONENTS = list(
    VIA1_REGION.each()
)

NWELL_COMPONENTS = list(
    NWELL_REGION.each()
)


print()
print("=" * 80)
print("RECURSIVE GEOMETRY INVENTORY")
print("=" * 80)

print(
    "Merged M1 components  :",
    len(M1_COMPONENTS)
)

print(
    "Merged VIA1 components:",
    len(VIA1_COMPONENTS)
)

print(
    "Merged M2 components  :",
    len(M2_COMPONENTS)
)

print(
    "Merged NWELL regions   :",
    len(NWELL_COMPONENTS)
)


# ================================================================
# 8. COMPONENT INTERSECTION HELPERS
# ================================================================

def polygon_intersects_box(
    polygon,
    box,
):

    intersection = (

        kdb.Region(
            polygon
        )

        &

        kdb.Region(
            box
        )

    )

    return not intersection.is_empty()


def component_hits(
    components,
    box,
):

    hits = []


    for index, polygon in enumerate(
        components
    ):

        if polygon_intersects_box(
            polygon,
            box,
        ):

            hits.append(
                index
            )


    return hits


# ================================================================
# 9. UNION-FIND
#
# Nodes:
#
#   0 ... N_M1-1              = M1 components
#
#   N_M1 ... N_M1+N_M2-1      = M2 components
#
# Via1 creates electrical edges between M1 and M2.
#
# Later we explicitly union the two M1 gate-contact landings
# belonging to each transistor because they are tied through
# the same polysilicon gate.
# ================================================================

N_M1 = len(
    M1_COMPONENTS
)

N_M2 = len(
    M2_COMPONENTS
)

TOTAL_NODES = (
    N_M1
    + N_M2
)


parent = list(
    range(
        TOTAL_NODES
    )
)

rank = [
    0
    for _
    in range(
        TOTAL_NODES
    )
]


def uf_find(
    node,
):

    if parent[node] != node:

        parent[node] = uf_find(
            parent[node]
        )


    return parent[node]


def uf_union(
    a,
    b,
):

    root_a = uf_find(
        a
    )

    root_b = uf_find(
        b
    )


    if root_a == root_b:

        return


    if rank[root_a] < rank[root_b]:

        parent[root_a] = root_b

    elif rank[root_a] > rank[root_b]:

        parent[root_b] = root_a

    else:

        parent[root_b] = root_a

        rank[root_a] += 1


def m1_node(
    index,
):

    return index


def m2_node(
    index,
):

    return (
        N_M1
        + index
    )


# ================================================================
# 10. CONNECT M1 <-> M2 THROUGH ACTUAL VIA1 SHAPES
# ================================================================

print()
print("=" * 80)
print("VIA1 CONNECTIVITY AUDIT")
print("=" * 80)


VIA_CONNECTIVITY_OK = True

via_records = []


for via_index, via_polygon in enumerate(
    VIA1_COMPONENTS,
    start=1,
):

    via_region = kdb.Region(
        via_polygon
    )


    m1_hits = []


    for index, polygon in enumerate(
        M1_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            & via_region

        ).is_empty():

            m1_hits.append(
                index
            )


    m2_hits = []


    for index, polygon in enumerate(
        M2_COMPONENTS
    ):

        if not (

            kdb.Region(
                polygon
            )

            & via_region

        ).is_empty():

            m2_hits.append(
                index
            )


    valid = bool(

        len(m1_hits) == 1

        and

        len(m2_hits) == 1

    )


    VIA_CONNECTIVITY_OK &= valid


    via_records.append({

        "via":
            via_index,

        "m1_hits":
            m1_hits,

        "m2_hits":
            m2_hits,

        "valid":
            valid,

    })


    print(

        f"VIA1[{via_index:02d}] "

        f"M1={m1_hits} "

        f"M2={m2_hits} "

        f"valid={valid}"

    )


    if valid:

        uf_union(

            m1_node(
                m1_hits[0]
            ),

            m2_node(
                m2_hits[0]
            ),

        )


print()
print(
    "All VIA1 transitions valid:",
    VIA_CONNECTIVITY_OK
)


# ================================================================
# 11. DEVICE-GATE INTERNAL TIES
#
# Each MOS has two gate-contact M1 landings:
#
#   bottom gate contact
#   top gate contact
#
# They are the same transistor gate through poly.
#
# Add that electrical relation to the conductor graph.
# ================================================================

print()
print("=" * 80)
print("MOS GATE INTERNAL-TIE AUDIT")
print("=" * 80)


GATE_TIE_OK = True


MOS_GATE_ROLES = [

    (
        "P_U1A",
        P_TERM,
    ),

    (
        "P_REF",
        P_TERM,
    ),

    (
        "P_U0",
        P_TERM,
    ),

    (
        "P_U1B",
        P_TERM,
    ),

    (
        "SW1A",
        N_TERM,
    ),

    (
        "SW0",
        N_TERM,
    ),

    (
        "SW1B",
        N_TERM,
    ),

]


for role, terminal_set in MOS_GATE_ROLES:

    bottom = absolute_terminal(

        role,

        terminal_set[
            "bottom_gate"
        ],

    )

    top_gate = absolute_terminal(

        role,

        terminal_set[
            "top_gate"
        ],

    )


    bottom_hits = component_hits(

        M1_COMPONENTS,

        bottom,

    )

    top_hits = component_hits(

        M1_COMPONENTS,

        top_gate,

    )


    valid = bool(

        len(bottom_hits) == 1

        and

        len(top_hits) == 1

    )


    GATE_TIE_OK &= valid


    print(

        f"{role:6s} "

        f"bottom={bottom_hits} "

        f"top={top_hits} "

        f"valid={valid}"

    )


    if valid:

        uf_union(

            m1_node(
                bottom_hits[0]
            ),

            m1_node(
                top_hits[0]
            ),

        )


print()
print(
    "All MOS gate ties valid:",
    GATE_TIE_OK
)


# ================================================================
# 12. PROBE HELPERS
# ================================================================

probe_failures = []


def root_from_m1_box(
    name,
    box,
):

    hits = component_hits(

        M1_COMPONENTS,

        box,

    )


    if len(hits) != 1:

        probe_failures.append({

            "probe":
                name,

            "layer":
                "M1",

            "hits":
                hits,

        })

        return None


    return uf_find(

        m1_node(
            hits[0]
        )

    )


def root_from_m2_box(
    name,
    box,
):

    hits = component_hits(

        M2_COMPONENTS,

        box,

    )


    if len(hits) != 1:

        probe_failures.append({

            "probe":
                name,

            "layer":
                "M2",

            "hits":
                hits,

        })

        return None


    return uf_find(

        m2_node(
            hits[0]
        )

    )


# ================================================================
# 13. EXTERNAL/ROUTE ANCHORS
# ================================================================

# VDD rail
VDD_ANCHOR = tiny_probe_um(
    0.0,
    10.0,
)

# VBIAS bus
VBIAS_ANCHOR = tiny_probe_um(
    5.0,
    6.800,
)

# GATE_W1 bus
GATE_W1_ANCHOR = tiny_probe_um(
    5.0,
    4.700,
)

# Corrected GATE_W0 bus
GATE_W0_ANCHOR = tiny_probe_um(
    7.0,
    1.700,
)

# VMEM bus, use actual manifest bbox midpoint
vmem_bus_bbox = vmem_data[
    "vmem"
][
    "bus_bbox_um"
]

vmem_bus_cx = (
    float(
        vmem_bus_bbox[0]
    )
    +
    float(
        vmem_bus_bbox[2]
    )
) / 2.0

vmem_bus_cy = (
    float(
        vmem_bus_bbox[1]
    )
    +
    float(
        vmem_bus_bbox[3]
    )
) / 2.0


VMEM_ANCHOR = tiny_probe_um(
    vmem_bus_cx,
    vmem_bus_cy,
)

# VSS rail
vss_bbox = vss_data[
    "vss"
][
    "rail_bbox_um"
]

vss_cx = (
    float(
        vss_bbox[0]
    )
    +
    float(
        vss_bbox[2]
    )
) / 2.0

vss_cy = (
    float(
        vss_bbox[1]
    )
    +
    float(
        vss_bbox[3]
    )
) / 2.0


VSS_ANCHOR = tiny_probe_um(
    vss_cx,
    vss_cy,
)


# ================================================================
# 14. BODY-TAP M1 BOXES
# ================================================================

# Package-native tap cells were validated in Step 18E:
# local M1 bbox = (0,0)-(1,1) um.

ntap_origin = placements[
    "N_TAP_VDD"
][
    "origin_um"
]

ptap_origin = placements[
    "P_TAP_VSS"
][
    "origin_um"
]


N_TAP_VDD_M1 = make_box_um(

    float(
        ntap_origin[0]
    ),

    float(
        ntap_origin[1]
    ),

    float(
        ntap_origin[0]
    ) + 1.0,

    float(
        ntap_origin[1]
    ) + 1.0,

)


P_TAP_VSS_M1 = make_box_um(

    float(
        ptap_origin[0]
    ),

    float(
        ptap_origin[1]
    ),

    float(
        ptap_origin[0]
    ) + 1.0,

    float(
        ptap_origin[1]
    ) + 1.0,

)


# ================================================================
# 15. LOGICAL NET PROBES
# ================================================================

net_probes = {

    "VDD": [

        (
            "VDD_RAIL",
            "M1",
            VDD_ANCHOR,
        ),

        (
            "N_TAP_VDD",
            "M1",
            N_TAP_VDD_M1,
        ),

        (
            "P_U1A_SOURCE",
            "M1",
            absolute_terminal(
                "P_U1A",
                P_TERM[
                    "left_sd"
                ],
            ),
        ),

        (
            "P_REF_SOURCE",
            "M1",
            absolute_terminal(
                "P_REF",
                P_TERM[
                    "left_sd"
                ],
            ),
        ),

        (
            "P_U0_SOURCE",
            "M1",
            absolute_terminal(
                "P_U0",
                P_TERM[
                    "left_sd"
                ],
            ),
        ),

        (
            "P_U1B_SOURCE",
            "M1",
            absolute_terminal(
                "P_U1B",
                P_TERM[
                    "left_sd"
                ],
            ),
        ),

    ],


    "VBIAS": [

        (
            "VBIAS_BUS",
            "M1",
            VBIAS_ANCHOR,
        ),

        (
            "P_REF_DRAIN",
            "M1",
            absolute_terminal(
                "P_REF",
                P_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "P_REF_GATE",
            "M1",
            absolute_terminal(
                "P_REF",
                P_TERM[
                    "bottom_gate"
                ],
            ),
        ),

        (
            "P_U1A_GATE",
            "M1",
            absolute_terminal(
                "P_U1A",
                P_TERM[
                    "bottom_gate"
                ],
            ),
        ),

        (
            "P_U0_GATE",
            "M1",
            absolute_terminal(
                "P_U0",
                P_TERM[
                    "bottom_gate"
                ],
            ),
        ),

        (
            "P_U1B_GATE",
            "M1",
            absolute_terminal(
                "P_U1B",
                P_TERM[
                    "bottom_gate"
                ],
            ),
        ),

    ],


    "P_U1A_TO_SW1A": [

        (
            "P_U1A_DRAIN",
            "M1",
            absolute_terminal(
                "P_U1A",
                P_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "SW1A_RIGHT_DIFF",
            "M1",
            absolute_terminal(
                "SW1A",
                N_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "U1A_M2_MID",
            "M2",
            tiny_probe_um(

                float(
                    branches[
                        "P_U1A_TO_SW1A"
                    ][
                        "m2_x_um"
                    ]
                ),

                5.500,

            ),
        ),

    ],


    "P_U0_TO_SW0": [

        (
            "P_U0_DRAIN",
            "M1",
            absolute_terminal(
                "P_U0",
                P_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "SW0_RIGHT_DIFF",
            "M1",
            absolute_terminal(
                "SW0",
                N_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "U0_M2_MID",
            "M2",
            tiny_probe_um(

                float(
                    branches[
                        "P_U0_TO_SW0"
                    ][
                        "m2_x_um"
                    ]
                ),

                5.500,

            ),
        ),

    ],


    "P_U1B_TO_SW1B": [

        (
            "P_U1B_DRAIN",
            "M1",
            absolute_terminal(
                "P_U1B",
                P_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "SW1B_RIGHT_DIFF",
            "M1",
            absolute_terminal(
                "SW1B",
                N_TERM[
                    "right_sd"
                ],
            ),
        ),

        (
            "U1B_M2_MID",
            "M2",
            tiny_probe_um(

                float(
                    branches[
                        "P_U1B_TO_SW1B"
                    ][
                        "m2_x_um"
                    ]
                ),

                5.500,

            ),
        ),

    ],


    "VMEM": [

        (
            "VMEM_BUS",
            "M2",
            VMEM_ANCHOR,
        ),

        (
            "SW1A_LEFT_DIFF",
            "M1",
            absolute_terminal(
                "SW1A",
                N_TERM[
                    "left_sd"
                ],
            ),
        ),

        (
            "SW0_LEFT_DIFF",
            "M1",
            absolute_terminal(
                "SW0",
                N_TERM[
                    "left_sd"
                ],
            ),
        ),

        (
            "SW1B_LEFT_DIFF",
            "M1",
            absolute_terminal(
                "SW1B",
                N_TERM[
                    "left_sd"
                ],
            ),
        ),

    ],


    "GATE_W0": [

        (
            "GATE_W0_BUS",
            "M1",
            GATE_W0_ANCHOR,
        ),

        (
            "SW0_GATE",
            "M1",
            absolute_terminal(
                "SW0",
                N_TERM[
                    "bottom_gate"
                ],
            ),
        ),

    ],


    "GATE_W1": [

        (
            "GATE_W1_BUS",
            "M1",
            GATE_W1_ANCHOR,
        ),

        (
            "SW1A_GATE",
            "M1",
            absolute_terminal(
                "SW1A",
                N_TERM[
                    "top_gate"
                ],
            ),
        ),

        (
            "SW1B_GATE",
            "M1",
            absolute_terminal(
                "SW1B",
                N_TERM[
                    "top_gate"
                ],
            ),
        ),

    ],


    "VSS": [

        (
            "VSS_RAIL",
            "M1",
            VSS_ANCHOR,
        ),

        (
            "P_TAP_VSS",
            "M1",
            P_TAP_VSS_M1,
        ),

    ],

}


# ================================================================
# 16. RESOLVE ALL PROBES TO CONDUCTOR ROOTS
# ================================================================

print()
print("=" * 80)
print("LOGICAL NET CONNECTIVITY")
print("=" * 80)


resolved_nets = {}

NET_INTERNAL_CONNECTIVITY_OK = True


for net_name, probes in net_probes.items():

    roots = []

    probe_results = []


    print()
    print(
        net_name
    )

    print(
        "-" * 80
    )


    for (
        probe_name,
        layer_name,
        box,
    ) in probes:

        if layer_name == "M1":

            root = root_from_m1_box(
                probe_name,
                box,
            )

        elif layer_name == "M2":

            root = root_from_m2_box(
                probe_name,
                box,
            )

        else:

            raise RuntimeError(
                f"Unsupported probe layer: {layer_name}"
            )


        roots.append(
            root
        )


        probe_results.append({

            "name":
                probe_name,

            "layer":
                layer_name,

            "root":
                root,

        })


        print(

            f"{probe_name:24s} "

            f"{layer_name:2s} "

            f"root={root}"

        )


    valid_roots = [

        root

        for root
        in roots

        if root is not None

    ]


    unique_roots = sorted(
        set(
            valid_roots
        )
    )


    connected = bool(

        len(valid_roots)
        == len(roots)

        and

        len(unique_roots)
        == 1

    )


    NET_INTERNAL_CONNECTIVITY_OK &= connected


    resolved_nets[
        net_name
    ] = {

        "roots":
            unique_roots,

        "connected":
            connected,

        "probes":
            probe_results,

    }


    print(
        "CONNECTED:",
        connected
    )


# ================================================================
# 17. DIFFERENT LOGICAL NETS MUST HAVE DIFFERENT ROOTS
# ================================================================

print()
print("=" * 80)
print("CROSS-NET SHORT AUDIT")
print("=" * 80)


net_root = {}

for net_name, data in resolved_nets.items():

    if (
        data[
            "connected"
        ]

        and

        len(
            data[
                "roots"
            ]
        ) == 1

    ):

        net_root[
            net_name
        ] = data[
            "roots"
        ][0]


root_to_nets = {}


for net_name, root in net_root.items():

    root_to_nets.setdefault(
        root,
        []
    ).append(
        net_name
    )


shorted_groups = {

    root:
        nets

    for root, nets
    in root_to_nets.items()

    if len(
        nets
    ) > 1

}


NO_CROSS_NET_SHORTS = (
    len(
        shorted_groups
    ) == 0
)


if NO_CROSS_NET_SHORTS:

    print(
        "No logical-net root collisions."
    )

else:

    print(
        "SHORTED LOGICAL NET GROUPS:"
    )


    for root, nets in shorted_groups.items():

        print(
            "  root",
            root,
            "->",
            nets
        )


print()
print(
    "NO_CROSS_NET_SHORTS =",
    NO_CROSS_NET_SHORTS
)


# ================================================================
# 18. EXPECTED CONDUCTOR-NET COUNT
#
# After:
#
#   - same-layer polygon merging
#   - VIA1 M1<->M2 unions
#   - top/bottom MOS gate-contact poly unions
#
# this synapse should contain exactly nine electrical
# conductor networks.
# ================================================================

all_roots = sorted(
    set(

        uf_find(
            node
        )

        for node
        in range(
            TOTAL_NODES
        )

    )
)


EXPECTED_NET_COUNT = 9


CONDUCTOR_NET_COUNT_OK = (
    len(
        all_roots
    )
    == EXPECTED_NET_COUNT
)


print()
print("=" * 80)
print("CONDUCTOR NETWORK COUNT")
print("=" * 80)


print(
    "Actual conductor roots:",
    len(
        all_roots
    )
)

print(
    "Expected logical nets :",
    EXPECTED_NET_COUNT
)

print(
    "Count correct         :",
    CONDUCTOR_NET_COUNT_OK
)


# ================================================================
# 19. EXPECTED NET-ROOT COVERAGE
#
# All conductor roots should correspond to one of the nine
# intended logical nets.
# ================================================================

expected_roots = sorted(
    set(
        net_root.values()
    )
)


UNACCOUNTED_ROOTS = [

    root

    for root
    in all_roots

    if root not in expected_roots

]


ALL_ROOTS_ACCOUNTED = (
    len(
        UNACCOUNTED_ROOTS
    ) == 0
)


print()
print("=" * 80)
print("UNACCOUNTED CONDUCTOR AUDIT")
print("=" * 80)


print(
    "Intended-net roots:",
    len(
        expected_roots
    )
)

print(
    "Unaccounted roots:",
    UNACCOUNTED_ROOTS
)

print(
    "All conductor roots accounted:",
    ALL_ROOTS_ACCOUNTED
)


# ================================================================
# 20. NWELL BODY-CONNECTIVITY AUDIT
#
# Probe:
#
#   N_TAP_VDD
#   P_U1A
#   P_REF
#   P_U0
#   P_U1B
#
# They must all lie in one common NWELL component.
# ================================================================

print()
print("=" * 80)
print("PMOS COMMON-NWELL AUDIT")
print("=" * 80)


nwell_probe_boxes = {


    "N_TAP_VDD": tiny_probe_um(

        float(
            ntap_origin[0]
        ) + 0.500,

        float(
            ntap_origin[1]
        ) + 0.500,

    ),


    "P_U1A": tiny_probe_um(

        float(
            placements[
                "P_U1A"
            ][
                "origin_um"
            ][0]
        ) + 0.550,

        float(
            placements[
                "P_U1A"
            ][
                "origin_um"
            ][1]
        ) + 0.420,

    ),


    "P_REF": tiny_probe_um(

        float(
            placements[
                "P_REF"
            ][
                "origin_um"
            ][0]
        ) + 0.550,

        float(
            placements[
                "P_REF"
            ][
                "origin_um"
            ][1]
        ) + 0.420,

    ),


    "P_U0": tiny_probe_um(

        float(
            placements[
                "P_U0"
            ][
                "origin_um"
            ][0]
        ) + 0.550,

        float(
            placements[
                "P_U0"
            ][
                "origin_um"
            ][1]
        ) + 0.420,

    ),


    "P_U1B": tiny_probe_um(

        float(
            placements[
                "P_U1B"
            ][
                "origin_um"
            ][0]
        ) + 0.550,

        float(
            placements[
                "P_U1B"
            ][
                "origin_um"
            ][1]
        ) + 0.420,

    ),

}


nwell_hits_by_probe = {}


for name, box in nwell_probe_boxes.items():

    hits = component_hits(

        NWELL_COMPONENTS,

        box,

    )


    nwell_hits_by_probe[
        name
    ] = hits


    print(
        f"{name:10s}:",
        hits
    )


valid_nwell_hits = [

    hits[0]

    for hits
    in nwell_hits_by_probe.values()

    if len(
        hits
    ) == 1

]


PMOS_COMMON_NWELL_OK = bool(

    len(
        valid_nwell_hits
    )
    == len(
        nwell_probe_boxes
    )

    and

    len(
        set(
            valid_nwell_hits
        )
    )
    == 1

)


print()
print(
    "PMOS + N_TAP share one NWELL:",
    PMOS_COMMON_NWELL_OK
)


# ================================================================
# 21. NMOS DEVICES MUST NOT BE INSIDE NWELL
# ================================================================

print()
print("=" * 80)
print("NMOS / NWELL ISOLATION AUDIT")
print("=" * 80)


NMOS_OUTSIDE_NWELL_OK = True


for role in [
    "SW1A",
    "SW0",
    "SW1B",
]:

    origin = placements[
        role
    ][
        "origin_um"
    ]


    probe = tiny_probe_um(

        float(
            origin[0]
        ) + 0.375,

        float(
            origin[1]
        ) + 0.500,

    )


    hits = component_hits(

        NWELL_COMPONENTS,

        probe,

    )


    outside = (
        len(
            hits
        ) == 0
    )


    print(
        f"{role:6s} outside NWELL:",
        outside,
        "hits=",
        hits
    )


    NMOS_OUTSIDE_NWELL_OK &= outside


# ================================================================
# 22. BODY-TAP TYPE AUDIT
#
# N_TAP_VDD:
#   TAP + NSDM + NWELL
#
# P_TAP_VSS:
#   TAP + PSDM
#   no NWELL
# ================================================================

def region_hits_box(
    region,
    box,
):

    return not (

        region

        &

        kdb.Region(
            box
        )

    ).is_empty()


ntap_probe = tiny_probe_um(

    float(
        ntap_origin[0]
    ) + 0.500,

    float(
        ntap_origin[1]
    ) + 0.500,

)


ptap_probe = tiny_probe_um(

    float(
        ptap_origin[0]
    ) + 0.500,

    float(
        ptap_origin[1]
    ) + 0.500,

)


NTAP_HAS_TAP = region_hits_box(
    TAP_REGION,
    ntap_probe,
)

NTAP_HAS_NSDM = region_hits_box(
    NSDM_REGION,
    ntap_probe,
)

NTAP_HAS_NWELL = region_hits_box(
    NWELL_REGION,
    ntap_probe,
)


PTAP_HAS_TAP = region_hits_box(
    TAP_REGION,
    ptap_probe,
)

PTAP_HAS_PSDM = region_hits_box(
    PSDM_REGION,
    ptap_probe,
)

PTAP_HAS_NWELL = region_hits_box(
    NWELL_REGION,
    ptap_probe,
)


BODY_TAP_TYPES_OK = bool(

    NTAP_HAS_TAP

    and

    NTAP_HAS_NSDM

    and

    NTAP_HAS_NWELL

    and

    PTAP_HAS_TAP

    and

    PTAP_HAS_PSDM

    and

    not PTAP_HAS_NWELL

)


print()
print("=" * 80)
print("BODY-TAP TYPE AUDIT")
print("=" * 80)


print(
    "N_TAP_VDD TAP  :",
    NTAP_HAS_TAP
)

print(
    "N_TAP_VDD NSDM :",
    NTAP_HAS_NSDM
)

print(
    "N_TAP_VDD NWELL:",
    NTAP_HAS_NWELL
)

print()

print(
    "P_TAP_VSS TAP  :",
    PTAP_HAS_TAP
)

print(
    "P_TAP_VSS PSDM :",
    PTAP_HAS_PSDM
)

print(
    "P_TAP_VSS NWELL:",
    PTAP_HAS_NWELL,
    "(expected False)"
)

print()

print(
    "Body-tap types correct:",
    BODY_TAP_TYPES_OK
)


# ================================================================
# 23. PROBE-RESOLUTION STATUS
# ================================================================

PROBE_RESOLUTION_OK = (
    len(
        probe_failures
    ) == 0
)


print()
print("=" * 80)
print("PROBE RESOLUTION")
print("=" * 80)


print(
    "Probe failures:",
    len(
        probe_failures
    )
)


if probe_failures:

    for failure in probe_failures:

        print(
            failure
        )


print(
    "All probes uniquely resolved:",
    PROBE_RESOLUTION_OK
)


# ================================================================
# 24. FINAL PASS GATE
# ================================================================

STEP26A_PASS = bool(

    LAYERS_OK

    and

    VIA_CONNECTIVITY_OK

    and

    GATE_TIE_OK

    and

    PROBE_RESOLUTION_OK

    and

    NET_INTERNAL_CONNECTIVITY_OK

    and

    NO_CROSS_NET_SHORTS

    and

    CONDUCTOR_NET_COUNT_OK

    and

    ALL_ROOTS_ACCOUNTED

    and

    PMOS_COMMON_NWELL_OK

    and

    NMOS_OUTSIDE_NWELL_OK

    and

    BODY_TAP_TYPES_OK

)


# ================================================================
# 25. WRITE AUDIT JSON
# ================================================================

audit_data = {

    "project":
        "NeuroLIF-SKY130",

    "step":
        "26A",

    "audit":
        "final_connectivity_topology",

    "input_gds":
        str(
            INPUT_GDS
        ),

    "top_cell":
        TOP_CELL_NAME,

    "drc_status":
        "Step 25B CLEAN, 0 violations",

    "expected_logical_nets": [
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

    "actual_conductor_root_count":
        len(
            all_roots
        ),

    "expected_conductor_root_count":
        EXPECTED_NET_COUNT,

    "logical_nets":
        resolved_nets,

    "shorted_groups":
        shorted_groups,

    "unaccounted_roots":
        UNACCOUNTED_ROOTS,

    "body": {

        "pmos_common_nwell":
            PMOS_COMMON_NWELL_OK,

        "nmos_outside_nwell":
            NMOS_OUTSIDE_NWELL_OK,

        "body_tap_types":
            BODY_TAP_TYPES_OK,

    },

    "checks": {

        "layers":
            LAYERS_OK,

        "via_connectivity":
            VIA_CONNECTIVITY_OK,

        "mos_gate_internal_ties":
            GATE_TIE_OK,

        "probe_resolution":
            PROBE_RESOLUTION_OK,

        "net_internal_connectivity":
            NET_INTERNAL_CONNECTIVITY_OK,

        "no_cross_net_shorts":
            NO_CROSS_NET_SHORTS,

        "conductor_net_count":
            CONDUCTOR_NET_COUNT_OK,

        "all_roots_accounted":
            ALL_ROOTS_ACCOUNTED,

        "pmos_common_nwell":
            PMOS_COMMON_NWELL_OK,

        "nmos_outside_nwell":
            NMOS_OUTSIDE_NWELL_OK,

        "body_tap_types":
            BODY_TAP_TYPES_OK,

    },

    "STEP26A_PASS":
        STEP26A_PASS,

}


OUTPUT_AUDIT.write_text(

    json.dumps(
        audit_data,
        indent=2,
    ),

    encoding="utf-8",

)


AUDIT_JSON_OK = bool(

    OUTPUT_AUDIT.exists()

    and

    OUTPUT_AUDIT.stat().st_size > 0

)


# ================================================================
# 26. FINAL RESULT
# ================================================================

print()
print("=" * 80)
print("STEP 26A RESULT")
print("=" * 80)


print(
    "Required layers            :",
    LAYERS_OK
)

print(
    "VIA1 connectivity          :",
    VIA_CONNECTIVITY_OK
)

print(
    "MOS gate internal ties     :",
    GATE_TIE_OK
)

print(
    "Probe resolution           :",
    PROBE_RESOLUTION_OK
)

print(
    "Net internal connectivity  :",
    NET_INTERNAL_CONNECTIVITY_OK
)

print(
    "No cross-net shorts        :",
    NO_CROSS_NET_SHORTS
)

print(
    "Conductor net count        :",
    CONDUCTOR_NET_COUNT_OK
)

print(
    "All roots accounted        :",
    ALL_ROOTS_ACCOUNTED
)

print(
    "PMOS common NWELL          :",
    PMOS_COMMON_NWELL_OK
)

print(
    "NMOS outside NWELL         :",
    NMOS_OUTSIDE_NWELL_OK
)

print(
    "Body-tap types             :",
    BODY_TAP_TYPES_OK
)

print(
    "Audit JSON written         :",
    AUDIT_JSON_OK
)

print()
print(
    "STEP26A_PASS =",
    STEP26A_PASS
)


if not STEP26A_PASS:

    raise RuntimeError(
        "STEP 26A final connectivity/topology audit failed."
    )


print()
print("=" * 80)
print("FINAL WEIGHTED-SYNAPSE STATUS")
print("=" * 80)

print()
print(
    "Physical routing : COMPLETE"
)

print(
    "Official DRC     : CLEAN (0 violations)"
)

print(
    "Connectivity     : PASS"
)

print(
    "Cross-net shorts : NONE DETECTED"
)

print(
    "PMOS body/NWELL  : PASS"
)

print(
    "NMOS body strategy: PASS"
)

print()
print(
    "WEIGHTED SYNAPSE IS READY FOR LVS-ORIENTED WORK."
)

print()
print(
    "GDS remains unchanged:"
)

print(
    INPUT_GDS
)

print()
print(
    "Audit record:"
)

print(
    OUTPUT_AUDIT
)