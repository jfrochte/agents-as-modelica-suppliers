# Task 3 — Build and calibrate a Modelica model from description and measurements

## System description (as provided)

An electric drive spins a flywheel. When a supply voltage is applied, the
wheel speeds up and settles at a steady speed; when the voltage is removed,
it slows down again. The input is the supply voltage; measured are the motor
current and the rotational speed of the wheel. Every experiment starts at
standstill.

## Domain restriction

Electrical and rotational mechanics. Build the physical part of the model
from `Modelica.Electrical` and `Modelica.Mechanics`; `Modelica.Blocks` may
be used for signal input/output and routing. Generic curve-fitting blocks
(transfer functions, state-space blocks, lookup tables, user-defined
equation systems) must not be used to represent the physics.

## Measurements

Directory `data/`, CSV with header `time,u,y_i,y_w`:

| File | Role | Input signal u(t) |
|---|---|---|
| `exp1_fit.csv` | fitting | voltage step |
| `exp2_fit.csv` | fitting | voltage step, later switched off |
| `exp3_fit.csv` | fitting | slow sinusoidal voltage |
| `exp4_validation.csv` | validation only | faster sinusoidal voltage |

Units: time in s, u in V, y_i in A, y_w in rad/s. Sample interval 0.05 s,
duration 25 s. Sensor noise is approximately Gaussian with standard
deviation 0.01 A on y_i and 0.05 rad/s on y_w.

Use only the three fitting experiments to estimate parameters. The
validation experiment must not be used for fitting, only to report
validation error.

## Required output package

1. an executable Modelica model (`model.mo`) with `RealInput u` and
   `RealOutput y_i, y_w`, built only from the admissible library subset;
2. the list of free parameters with the bounds and initial values you used;
3. the fitted parameter values;
4. fit metrics (RMSE per output and experiment) on the fitting experiments
   and, separately, on the validation experiment;
5. a short record of the physical assumptions you made, including anything
   you added that the description does not mention explicitly;
6. if several structures are plausible, say so, explain how the data
   discriminate between them, and justify your choice;
7. if a parameter cannot be reliably determined from the data, say so
   explicitly, fix it to a justified value or report bounds, and state the
   limitation in your report;
8. the model must be visually usable in a diagram editor: component
   placements and `Line` annotations for all connections, with a readable
   layout.
