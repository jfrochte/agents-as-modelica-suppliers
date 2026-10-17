# Task 1 — Build and calibrate a Modelica model from description and measurements

## System description (as provided)

A carriage is connected to the test-rig frame through an elastic element.
When a force is applied to the carriage and released, the measured position
oscillates and slowly returns to rest. The input is the force applied to the
carriage; measured outputs are the carriage position and its velocity.
At the start of every experiment the carriage is at rest at position zero.

## Domain restriction

Translational mechanics. The model must be assembled from components of
`Modelica.Mechanics.Translational` (Components, Sources, Sensors) plus
`Modelica.Blocks.Interfaces` for the input/output signals. Generic
signal-processing blocks (transfer functions, state-space blocks, lookup
tables, user-defined equation blocks) are not allowed.

## Measurements

Directory `data/`, CSV with header `time,u,y_s,y_v`:

| File | Role | Input signal u(t) |
|---|---|---|
| `exp1_fit.csv` | fitting | short force pulse |
| `exp2_fit.csv` | fitting | force step |
| `exp3_validation.csv` | validation only | sinusoidal force |

Units: time in s, u in N, y_s in m, y_v in m/s. Sample interval 0.05 s,
duration 25 s. Sensor noise is approximately Gaussian with standard
deviation 3e-3 m on y_s and 1e-2 m/s on y_v.

Use only the two fitting experiments to estimate parameters. The validation
experiment must not be used for fitting — only to report validation error.

## Required output package

1. an executable Modelica model (`model.mo`) with `RealInput u` and
   `RealOutput y_s, y_v`, built only from the admissible library subset;
2. the list of free parameters with the bounds and initial values you used;
3. the fitted parameter values;
4. fit metrics (RMSE per output and experiment) on both fitting experiments
   and, separately, on the validation experiment;
5. a short record of the physical assumptions you made, including anything
   you added that the description does not mention explicitly;
6. if several structures are plausible, say so and justify your choice.
