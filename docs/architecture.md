# NeuroLIF-SKY130 Architecture

## Overview

NeuroLIF-SKY130 is a transistor-level **leaky integrate-and-fire (LIF) neuron** implemented with **SKY130 1.8 V CMOS devices**.

The frozen neuron core contains:

- **17 MOS transistors**
- **8 PFET**
- **9 NFET**

The architecture combines:

- a weighted synaptic current source
- membrane integration and leak
- a CMOS Schmitt-trigger threshold detector
- a CMOS output buffer
- a spike-controlled membrane reset

The membrane capacitor is intentionally **external to the physical core**.

---

## Functional Architecture

The neuron signal flow is:

```text
Reference current
      |
      v
PMOS current mirror
      |
      v
2-bit weighted synapse
      |
      v
     VMEM
      |
      +--------> NMOS leak controlled by VLEAK
      |
      v
6T CMOS Schmitt detector
      |
      v
     VRAW
      |
      v
CMOS output inverter
      |
      v
    SPIKE
      |
      +--------> NMOS reset transistor
                       |
                       v
                      VMEM
```

The synaptic current charges the membrane node, while the leak transistor continuously provides a discharge path. Once `VMEM` crosses the Schmitt-trigger switching threshold, the circuit generates a digital output spike and activates the reset path.

---

## Weighted Synaptic Input

The final weighted synapse uses **three identical PMOS unit-current cells**.

The two digital control inputs are:

```text
GATE_W0
GATE_W1
```

The implemented weight encoding is:

| Weight code | Active PMOS unit cells | Relative weight |
|---|---:|---:|
| `00` | 0 | 0× |
| `01` | 1 | 1× |
| `10` | 2 | 2× |
| `11` | 3 | 3× |

The 2× state is implemented using **two identical unit PMOS devices in parallel**, rather than one geometrically wider PMOS device.

This implementation choice was based on transistor-level characterization of the selected SKY130 device configuration.

---

## Membrane Node

`VMEM` is the main internal state of the LIF neuron.

Synaptic current charges the membrane node while the leak path simultaneously discharges it.

The nominal membrane capacitance used during transistor-level simulation is:

```text
Cmem = 5 pF
```

The capacitor is intentionally external and is **not physically instantiated inside the final neuron layout**.

Therefore, `VMEM` remains available as a top-level terminal.

---

## Leak Path

The membrane leak is implemented with an NMOS transistor connected between `VMEM` and `VSS`.

Its gate is controlled by:

```text
VLEAK
```

The leak device dimensions are:

```text
W = 0.42 µm
L = 1.00 µm
```

Changing `VLEAK` changes the effective membrane discharge behavior and therefore influences the firing dynamics of the neuron.

---

## Schmitt Threshold Detector

Threshold detection is implemented using a corrected **six-transistor CMOS Schmitt-trigger topology**.

The important internal nodes are:

```text
P_MID
N_MID
VRAW
```

The final transistor-level simulation produced approximately:

```text
VTH_UP     = 1.023948 V
VTH_DOWN   = 0.824096 V
Hysteresis = 199.852 mV
```

The approximately 200 mV hysteresis window reduces sensitivity to small voltage fluctuations around the switching threshold.

The final corrected feedback topology is:

```text
MN_FB: VDD  VRAW  N_MID  VSS
MP_FB: VSS  VRAW  P_MID  VDD
```

The earlier crossed-feedback implementation is not part of the final design.

---

## Output Buffer

The Schmitt detector produces the internal signal:

```text
VRAW
```

A CMOS inverter converts this internal state into the externally available positive-going output:

```text
SPIKE
```

The output stage therefore provides a conventional digital spike signal for downstream circuitry or measurement.

---

## Reset Path

`SPIKE` directly controls the gate of the reset NMOS transistor.

When `SPIKE` goes high, the reset device discharges `VMEM` toward `VSS`.

This returns the membrane node toward its lower state and allows the next integrate-and-fire cycle to begin.

The current core does **not** include a dedicated refractory-delay circuit.

---

## Top-Level Interface

The final physical core exposes eight top-level pins:

| Pin | Function |
|---|---|
| `VDD` | 1.8 V supply |
| `VSS` | Ground |
| `VBIAS` | PMOS current-mirror bias |
| `GATE_W0` | 1× synaptic-weight control |
| `GATE_W1` | 2× synaptic-weight control |
| `VLEAK` | Leak-transistor bias |
| `VMEM` | Membrane node / external capacitor terminal |
| `SPIKE` | Digital neuron output |

---

## Internal Nets

Important internal neuron nets include:

```text
P_MID
N_MID
VRAW
```

The weighted synapse additionally contains three internal branch nets associated with the three unit-current paths.

The final geometry-based connectivity audit identified:

```text
14 logical conductor nets
```

with no detected cross-net shorts or unexplained floating conductor networks.

---

## Physical Scope

The frozen full-neuron layout contains:

| Property | Value |
|---|---:|
| Total MOS devices | 17 |
| PFET | 8 |
| NFET | 9 |
| External pins | 8 |
| Logical conductor nets | 14 |
| Physical membrane capacitor | External |

The final physical core includes:

```text
7-MOS weighted synapse
1-MOS membrane leak
6-MOS Schmitt detector
2-MOS output inverter
1-MOS reset
--------------------------
17 MOS total
```

---

## Design Boundary

NeuroLIF-SKY130 is a **pre-silicon educational neuromorphic circuit-design project** implemented using the open SKY130 PDK.

The current project demonstrates:

- transistor-level LIF neuron design
- weighted synaptic current generation
- membrane integration and leak
- hysteretic threshold detection
- spike generation and reset
- physical layout construction
- DRC verification
- geometry-based connectivity verification
- LVS verification

The project does **not** claim:

- fabricated silicon
- tapeout
- measured post-silicon performance
- production manufacturing signoff
- parasitic-extracted post-layout transient simulation

The membrane capacitor remains an external ideal `5 pF` element in the current design revision.
