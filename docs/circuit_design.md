# NeuroLIF-SKY130 Circuit Design

## Overview

The NeuroLIF-SKY130 neuron was developed as a transistor-level leaky integrate-and-fire circuit using SKY130 1.8 V CMOS devices.

The final electrical architecture contains five functional blocks:

1. PMOS current-mirror synaptic source
2. 2-bit weighted electronic synapse
3. membrane integration and leak
4. six-transistor CMOS Schmitt threshold detector
5. output buffer and spike-controlled reset

The frozen full-neuron core contains 17 MOS transistors.

## Nominal Electrical Conditions

The final validation used the following nominal conditions:

```text
VDD = 1.80 V
IREF = 100 nA
Cmem = 5 pF
VLEAK nominal bias = 0.50 V
```

Production transient simulation:

```text
tran 10n 0.0004 0 1n
```

The external membrane capacitor is ideal and is not physically implemented inside the final layout.

## Device Dimensions

The principal device dimensions are:

| Device role | Width (µm) | Length (µm) |
|---|---:|---:|
| NMOS logic | 1.00 | 0.15 |
| PMOS logic | 2.00 | 0.15 |
| NMOS feedback | 0.42 | 0.30 |
| PMOS feedback | 0.42 | 0.30 |
| PMOS synaptic unit | 0.84 | 0.50 |
| NMOS leak | 0.42 | 1.00 |
| NMOS reset | 1.20 | 0.15 |

All physical MOS primitives used in the final layout are single-finger devices.

## Weighted Synapse

The final 2-bit synapse uses three identical PMOS unit-current cells.

The nominal delivered currents from the final simulation data are approximately:

```text
00 =   0.002 nA
01 = 103.734 nA
10 = 207.470 nA
11 = 311.206 nA
```

Normalized current ratios are approximately:

```text
10 / 01 = 2.0000
11 / 01 = 3.0000
```

This unit-cell approach was selected after direct characterization showed that a single PMOS device with twice the width did not produce twice the unit current in the tested SKY130 implementation.

Observed comparison:

```text
Unit PMOS current       ≈ 103.738 nA
Single 2×-wide PMOS     ≈ 98.196 nA
Two identical unit PMOS ≈ 207.476 nA
```

The final design therefore implements the 2× state using two identical devices in parallel.

No claim is made that transistor width is generally ineffective for current scaling. The observation is specific to the tested implementation and bias conditions.

## Membrane Integration

The main neuron state is the voltage:

```text
VMEM
```

Synaptic current charges the external membrane capacitor while the leak transistor continuously provides a discharge path.

The nominal membrane capacitor is:

```text
Cmem = 5 pF
```

The physical capacitor is intentionally external to the transistor core.

## Leak Device

The leak path is implemented using:

```text
MN_LEAK VMEM VLEAK VSS VSS
```

The device dimensions are:

```text
W = 0.42 µm
L = 1.00 µm
```

The external `VLEAK` bias controls the effective leakage strength.

## Corrected Schmitt Threshold Detector

The final six-transistor Schmitt detector is:

```spice
MP_ST1 P_MID VMEM VDD VDD
MP_ST2 VRAW VMEM P_MID VDD

MN_ST1 VRAW VMEM N_MID VSS
MN_ST2 N_MID VMEM VSS VSS

MN_FB VDD VRAW N_MID VSS
MP_FB VSS VRAW P_MID VDD
```

The feedback devices use:

```text
W = 0.42 µm
L = 0.30 µm
```

The final simulated threshold values are:

```text
VTH_UP     = 1.023948 V
VTH_DOWN   = 0.824096 V
Hysteresis = 199.852 mV
```

An earlier crossed-feedback implementation was rejected and is not part of the final design.

## Output Buffer

The Schmitt detector generates:

```text
VRAW
```

The positive-going output spike is produced by a CMOS inverter:

```spice
MP_BUF SPIKE VRAW VDD VDD
MN_BUF SPIKE VRAW VSS VSS
```

This converts the internal threshold-detector state into the external `SPIKE` signal.

## Reset Circuit

The reset device is:

```spice
MN_RST VMEM SPIKE VSS VSS
```

Its gate is driven directly by `SPIKE`.

When the output rises, the reset NMOS discharges the membrane node toward `VSS`.

The current implementation does not include a separate refractory-delay circuit.

## Nominal Functional Response

The final post-patch nominal simulation produced:

| Weight | Spike count | Firing rate |
|---|---:|---:|
| `00` | 0 | 0 Hz |
| `01` | 16 | 42.1 kHz |
| `10` | 39 | 102.6 kHz |
| `11` | 65 | 171.1 kHz |

Under nominal conditions, the firing response is monotonic with the number of active synaptic unit cells.

## Robustness Validation

Before physical implementation, the transistor-level circuit passed:

```text
Post-patch nominal validation        PASS
Functional numerical convergence    PASS
27-point PVT sweep                   27 / 27 PASS
Deterministic variation sweep        13 / 13 PASS
```

The PVT acceptance criterion was defined per operating point as follows:

- the simulation completes successfully
- weight `00` remains silent
- weight `11` produces at least one valid output spike
- the firing response is nondecreasing with increasing synaptic weight, i.e. `00 ≤ 01 ≤ 10 ≤ 11`

Therefore, `27/27 PASS` means that all 27 PVT operating points satisfied these defined acceptance criteria. It does not imply that intermediate weights `01` and `10` produced spikes at every PVT corner.

The final robustness status was:

```text
FINAL_ROBUSTNESS_PASS = True
```

The deterministic variation study is not a Monte Carlo mismatch analysis.

## Design Boundary

The circuit results are pre-silicon simulation results.

The project does not claim:

- fabricated silicon
- tapeout
- measured post-silicon behavior
- extracted post-layout transient simulation

Parasitic extraction and post-layout simulation remain possible future extensions.
