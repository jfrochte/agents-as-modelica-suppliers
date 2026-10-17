# Task 2 — Build and calibrate a Modelica model from description and measurements

## System description (as provided)

A sled sits on a rail and is connected to the frame by some springy element.
If you push it, it swings back and forth a few times and then stops. The
input is the force applied to the sled; the only measured signal is the sled
position. Every experiment starts at rest at position zero.

## Domain restriction

Mechanics. Build the physical part of the model from `Modelica.Mechanics`;
`Modelica.Blocks` may be used for signal input/output and routing. Generic
curve-fitting blocks (transfer functions, state-space blocks, lookup tables,
user-defined equation systems) must not be used to represent the physics.

## Measurements

Directory `data/`, CSV with header `time,u,y_s`:

| File | Role | Input signal u(t) |
|---|---|---|
| `exp1_fit.csv` | fitting | short force pulse |
| `exp2_fit.csv` | fitting | small force step |
| `exp3_fit.csv` | fitting | larger force step |
| `exp4_validation.csv` | validation only | sinusoidal force |

Units: time in s, u in N, y_s in m. Sample interval 0.05 s, duration 25 s.
Sensor noise on y_s is approximately Gaussian with standard deviation
2e-3 m. There is no velocity measurement.

Use only the three fitting experiments to estimate parameters. The
validation experiment must not be used for fitting — only to report
validation error.

## Required output package

1. an executable Modelica model (`model.mo`) with `RealInput u` and
   `RealOutput y_s`, built only from the admissible library subset;
2. the list of free parameters with the bounds and initial values you used;
3. the fitted parameter values;
4. fit metrics (RMSE on y_s per experiment) on the fitting experiments and,
   separately, on the validation experiment;
5. a short record of the physical assumptions you made, including anything
   you added that the description does not mention explicitly;
6. if several structures are plausible, say so, explain how the data
   discriminate between them, and justify your choice;
7. the model must be visually usable in a diagram editor: component
   placements and `Line` annotations for all connections, with a readable
   layout.
