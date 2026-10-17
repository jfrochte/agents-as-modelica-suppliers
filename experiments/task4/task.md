# Task 4 — Build and calibrate a Modelica model from description and measurements

## System description (as provided)

A test rig for a battery-powered drive train. A battery pack feeds a direct
current machine; the machine drives a load through a fixed reduction stage.
The data plate gives the reduction ratio as 5.2 to 1, motor side to output
side. The load is a brake that applies a commanded torque, so the rig can be
run against a load profile.

Every experiment starts from standstill with the circuit closed, so the
machine accelerates from rest as soon as the recording begins. The input is
the commanded brake torque at the output shaft; measured are the battery
current and the rotational speed of the output shaft. The rig documentation
notes that during long runs the speed at a given load setting slowly falls
off, and that the effect disappears after the pack has been serviced.

## Domain restriction

Electrical and rotational mechanics. Build the physical part of the model
from `Modelica.Electrical` and `Modelica.Mechanics`; `Modelica.Blocks` may be
used for signal input/output and routing.

Tabulated characteristics from `Modelica.Blocks.Tables` are admissible where a
component genuinely has a measured characteristic curve and you say which
physical quantity the table represents. They must not be used to replace
dynamics: no table that maps the input signal, or time, onto an output.
Transfer functions, state space blocks and user defined equation systems must
not be used to represent the physics.

## Measurements

Directory `data/`, CSV with header `time,u,y_i,y_w`:

| File | Role | Input signal u(t) | Duration | Sample interval |
|---|---|---|---|---|
| `exp1_fit.csv` | fitting | small constant brake torque, run up from rest | 20 s | 0.02 s |
| `exp2_fit.csv` | fitting | staircase of brake torque steps | 120 s | 0.05 s |
| `exp3_fit.csv` | fitting | long load profile | 1800 s | 0.5 s |
| `exp4_validation.csv` | validation only | different load profile | 900 s | 0.5 s |

Units: time in s, u in Nm, y_i in A, y_w in rad/s. Sensor noise is
approximately Gaussian with standard deviation 0.5 A on y_i and 0.2 rad/s on
y_w. The current sensor is rated for the run up transient; its readings are
trustworthy over the full range.

Use only the three fitting experiments to estimate parameters. The validation
experiment must not be used for fitting, only to report validation error.

## Required output package

1. an executable Modelica model (`model.mo`) with `RealInput u` and
   `RealOutput y_i, y_w`, built only from the admissible library subset;
2. a structure that reflects the physical layout of the rig: where the
   description suggests distinct assemblies, model them as distinct
   components rather than as one flat network;
3. the list of free parameters with the bounds and initial values you used;
4. the fitted parameter values;
5. fit metrics (RMSE per output and experiment) on the fitting experiments
   and, separately, on the validation experiment;
6. a short record of the physical assumptions you made, including anything
   you added that the description does not mention explicitly;
7. if several structures are plausible, say so, explain how the data
   discriminate between them, and justify your choice;
8. if a parameter cannot be reliably determined from the data, say so
   explicitly, fix it to a justified value or report bounds, and state the
   limitation in your report. If two parameters are only determined in
   combination, report the combination rather than two invented values;
9. the model must be visually usable in a diagram editor: component
   placements and `Line` annotations for all connections, with a readable
   layout.
