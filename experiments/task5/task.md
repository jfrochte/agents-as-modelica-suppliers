# Task 5 — Build and calibrate a Modelica model from description and measurements

## System description (as provided)

A switching electromagnet of the flat-armature type. The yoke is a cylinder
of 25 mm diameter and 12.5 mm height with an embedded coil of 131 turns; the
armature is a flat disc above it. The magnet is closed actively by the coil
and opened passively by a return spring. Yoke and armature are made from the
same steel; its magnetisation characteristic was measured and is supplied.
The moving assembly (armature with needle and reflector) weighs 18.6 g, the
return spring 2.6 g. The spring rate is (0.7854 ± 0.0026) N/mm over the
stroke used. The armature travels between two mechanical end positions.

Two kinds of measurements exist. The static attractive force was measured
over the air gap on a tensile testing machine, with the return spring
removed, at coil currents from 1 A to 8 A. The dynamic switching behaviour
was recorded with a laser vibrometer while a four-quadrant amplifier drove
the coil, once in voltage control and twice in current control. No external
load was attached; only the spring and the inertia of the armature act.

## Domain restriction

Magnetic, translational mechanics and electrical. Build the physical part of
the model from `Modelica.Magnetic.FluxTubes`, `Modelica.Mechanics.Translational`
and `Modelica.Electrical.Analog`; `Modelica.Blocks` may be used for signal
input/output and routing.

A tabulated characteristic is admissible for the supplied material
magnetisation curve, because it is a measured property of a component, and
you must say which quantity the table represents. Tables must not replace
dynamics or forces: no table that maps the input signal, the current, the
position or time onto an output or a force. Transfer functions, state-space
blocks and user-defined equation systems must not be used to represent the
physics.

## Measurements

Directory `data/`. All dynamic files are CSV with header `time,u,y_i,y_x,y_v`:

| File | Role | Excitation | Duration | Sample interval |
|---|---|---|---|---|
| `exp1_fit.csv` | fitting | voltage step of 6 V for 9 ms, then a small residual voltage | 102 ms | 0.1 ms |
| `exp2_fit.csv` | fitting | current-controlled square pulse, 4 A for 13 ms | 50 ms | 0.02 ms |
| `exp3_validation.csv` | validation only | current-controlled square pulse, 8 A for 13 ms | 50 ms | 0.02 ms |

Units: time in s, u in V, y_i in A, y_x in m, y_v in m/s. `u` is the coil
voltage as measured across the coil in every experiment, including the
current-controlled ones, so the amplifier and its controller are outside the
model. `y_x` is the working air gap between armature and yoke: zero in the
closed, energised end position, about 0.53 mm at the open end stop. `y_v` is
the armature velocity, the time derivative of `y_x`, so it is negative while
the magnet closes. Every experiment starts with the armature at rest at the
open end stop and the coil current near zero. The traces are as recorded; at rest
the sensors show a standard deviation of about 0.6 µm on y_x, 0.5 mm/s on
y_v and 8 mA on y_i, and the velocity channel of `exp1_fit` carries a small
constant offset.

Component characteristics, to be used for modelling and calibration:

| File | Content |
|---|---|
| `static_force_1A.csv` … `static_force_8A.csv` | static attractive force in N over the air gap in m at 1 A … 8 A, without the return spring and without the open end stop, so the travel exceeds the dynamic stroke; each file runs from the largest gap to contact and back |
| `material_BH.csv` | initial magnetisation curve of the steel: H in A/m, B in T, J in T |

The static files come from a tensile testing machine that pulls the armature
away from the yoke. When the armature touches the yoke the load cell is
unloaded, so the force reading near zero gap does not represent the magnetic
force there.

Use only the two fitting experiments and the component characteristics to
estimate parameters. The validation experiment must not be used for fitting,
only to report validation error.

## Required output package

1. an executable Modelica model (`model.mo`) with `RealInput u` and
   `RealOutput y_i, y_x, y_v`, built only from the admissible library subset;
2. a structure that reflects the physical layout: magnetic circuit, coil,
   armature with spring and end stops as distinct components rather than
   one flat network;
3. the list of free parameters with the bounds and initial values you used;
4. the fitted parameter values;
5. fit metrics (RMSE per output and experiment) on the fitting experiments
   and, separately, on the validation experiment;
6. a short record of the physical assumptions you made, including anything
   you added that the description does not mention explicitly, and any
   effect in the data your model does not reproduce;
7. if several structures are plausible, say so, explain how the data
   discriminate between them, and justify your choice;
8. if a parameter cannot be reliably determined from the data, say so
   explicitly, fix it to a justified value or report bounds, and state the
   limitation in your report. If two parameters are only determined in
   combination, report the combination rather than two invented values;
9. the model must be visually usable in a diagram editor: component
   placements and `Line` annotations for all connections, with a readable
   layout.
