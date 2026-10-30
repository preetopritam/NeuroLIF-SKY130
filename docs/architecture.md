\# NeuroLIF-SKY130 Architecture



\## Overview



NeuroLIF-SKY130 is a transistor-level leaky integrate-and-fire neuron implemented with SKY130 1.8 V CMOS devices.



The frozen neuron core contains 17 MOS transistors:



\- 8 PFET

\- 9 NFET



The architecture combines a weighted synaptic current source, membrane integration and leak, a Schmitt-trigger threshold detector, an output buffer and a spike-controlled reset path.



The physical membrane capacitor is intentionally external to the core.



\## Signal Flow



The functional signal path is:



```text

Reference current

&#x20;     |

&#x20;     v

PMOS current mirror

&#x20;     |

&#x20;     v

2-bit weighted synapse

&#x20;     |

&#x20;     v

VMEM

&#x20;|  \\

&#x20;|   \\--> NMOS leak controlled by VLEAK

&#x20;|

&#x20;v

6T CMOS Schmitt detector

&#x20;     |

&#x20;     v

VRAW

&#x20;     |

&#x20;     v

CMOS output buffer

&#x20;     |

&#x20;     v

SPIKE

&#x20;     |

&#x20;     +----> NMOS reset transistor

&#x20;                  |

&#x20;                  v

&#x20;                 VMEM

```



\## Weighted Synaptic Input



The final weighted synapse uses three identical PMOS unit-current cells.



The two control inputs are:



\- `GATE\_W0`

\- `GATE\_W1`



The resulting weight encoding is:



| Weight | Active unit cells |

|---|---:|

| `00` | 0 |

| `01` | 1 |

| `10` | 2 |

| `11` | 3 |



The 2× state is implemented with two identical unit PMOS devices in parallel rather than one geometrically wider PMOS device.



This choice was based on transistor-level characterization of the SKY130 implementation.



\## Membrane Node



`VMEM` is the main neuron state node.



The membrane integrates synaptic current while simultaneously discharging through the leak path.



The nominal external membrane capacitance is:



```text

Cmem = 5 pF

```



The capacitor is external by design and is not included as a physical capacitor in the final core layout.



\## Leak Path



The membrane leak is implemented using an NMOS transistor connected between `VMEM` and `VSS`.



Its gate is controlled through:



```text

VLEAK

```



This allows the effective membrane discharge behavior to be adjusted externally.



\## Threshold Detector



Threshold detection uses a corrected six-transistor CMOS Schmitt-trigger topology.



The internal nodes are:



```text

P\_MID

N\_MID

VRAW

```



The final simulated switching points are approximately:



```text

VTH\_UP   = 1.023948 V

VTH\_DOWN = 0.824096 V

Hysteresis = 199.852 mV

```



The hysteresis reduces sensitivity to small voltage fluctuations around the switching threshold.



\## Output Buffer



The Schmitt detector produces the internal signal:



```text

VRAW

```



A CMOS inverter converts this into the externally available positive-going spike:



```text

SPIKE

```



\## Reset Path



`SPIKE` directly drives the gate of the reset NMOS transistor.



When a spike occurs, the reset device discharges `VMEM` toward `VSS`, allowing the neuron to begin the next integration cycle.



No separate refractory circuit is included in the current core.



\## Top-Level Pins



The final physical core exposes eight top-level pins:



```text

VDD

VSS

VBIAS

GATE\_W0

GATE\_W1

VLEAK

VMEM

SPIKE

```



\## Internal Nets



Important internal nets include:



```text

P\_MID

N\_MID

VRAW

```



along with three weighted-synapse branch nets.



The final geometry-based connectivity audit identified 14 logical conductor nets.



\## Physical Scope



The final layout contains:



```text

17 MOS

8 PFET

9 NFET

8 external pins

14 logical conductor nets

```



The project is a pre-silicon educational SKY130 implementation.



It does not claim fabricated silicon, tapeout or measured post-silicon performance.

