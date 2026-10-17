# Task 2 — Modelica model and calibration

## Deliverables

- Executable model: [`model.mo`](model.mo), top-level class `Sled`.
- Reproducible fitting script: [`calibrate.py`](calibrate.py).

`Sled.u` is a `RealInput` in N and `Sled.y_s` is a `RealOutput` in m. The
physical path is

```text
u -> Force -> Mass -> SupportFriction -> SpringDamper -> Fixed frame
```

The position sensor is connected to the sled node. All components have
diagram placements, and every `connect` equation has an explicit `Line`
annotation.

## Structure and assumptions

The selected structure is a single translating sled with a linear spring and
a parallel linear viscous damper, plus symmetric Coulomb friction against the
rail. During sliding its equation is

```text
m*s_ddot = u - c*s - d*s_dot - f_slide*sign(s_dot)
```

The MSL `SupportFriction` component supplies the stuck/sliding state logic.
Its constant sliding table is `[0, f_slide; 1, f_slide]`; `peak` specifies the
maximum static friction as `peak*f_slide`.
This two-row table is the native friction-characteristic input of that
mechanical component, not a generic lookup or curve-fitting block.

Additional assumptions are: the frame is fixed and inertial; the spring is
unstretched at `s=0` and has no preload; there are no travel stops or other
actuator dynamics; friction is independent of position and has the same
magnitude in both directions; the sled starts at `s=0`, `s_dot=0`; and the
position sensor has zero bias. Gravity along the rail is ignored.

The fitting CSVs show the old value at the exact timestamp of the force
step/pulse and the new value on the following sample. For the discontinuous
fitting inputs, I therefore applied the right-hand sample immediately after
the event (equivalent to shifting the tabulated step by one 0.05-s sample).
This convention is not stated explicitly in the task, so it is recorded here
as an added data-processing assumption. The validation sine was used at its
original timestamps with linear interpolation.

## Free parameters and calibration

The three fitting experiments only were used in the least-squares objective.
The bounds and initial values were:

| Parameter | Meaning | Bounds | Initial value |
|---|---|---:|---:|
| `m` | sled mass [kg] | 0.2 … 5.0 | 1.5 |
| `c` | spring constant [N/m] | 1.0 … 15.0 | 5.0 |
| `d` | viscous damping [N·s/m] | 0 … 5.0 | 0.3 |
| `f_slide` | sliding friction [N] | 0.05 … 3.0 | 0.6 |

`peak` is a public model parameter but was held at 1.2 during calibration.
The data identify the sliding force and only a threshold for static friction:
the 0.5-N experiment remains stuck, and the observed stopping trajectories do
not change when `peak` is varied over a broad range above that threshold.
Thus fitting `peak` would report an arbitrary value. The selected value gives
a static-friction limit of 0.719704 N and is explicitly an identifiability
assumption, not an independently identified quantity.

The fitted values used as the defaults in `model.mo` are:

| Parameter | Fitted value |
|---|---:|
| `m` | 1.500289283 kg |
| `c` | 5.000195346 N/m |
| `d` | 0.3003352219 N·s/m |
| `f_slide` | 0.599753559 N |
| `peak` | 1.2 (fixed assumption) |

## Fit and validation error

RMSE is calculated on all 501 sampled positions in each file. These numbers
come from OpenModelica simulations of `Sled` with the fitted defaults and a
0.05-s output interval.

| Experiment | Role | RMSE on `y_s` [m] |
|---|---|---:|
| `exp1_fit.csv` | fit | 0.001958447 |
| `exp2_fit.csv` | fit | 0.002028846 |
| `exp3_fit.csv` | fit | 0.001926702 |
| pooled fitting data | fit | 0.001971794 |
| `exp4_validation.csv` | validation only | 0.002499235 |

The pooled fitting error is at the stated approximately 0.002-m sensor-noise
standard deviation. The validation file was not passed to the optimizer.

## Structure comparison

A frictionless linear mass–spring–damper model was also fit as a baseline. Its
best fitting RMSEs were 0.111589 m, 0.095672 m and 0.042545 m for experiments
1–3. In particular, it predicts a substantial displacement for the 0.5-N
step, whereas the measured sled remains at rest. The nonzero post-pulse
stopping position in experiment 1 and the force-dependent static response in
experiments 2–3 therefore discriminate in favor of dry friction.

A series-compliance model, a second moving mass, or a more detailed hysteretic
friction model could also be made plausible from position-only data, but each
adds states or parameters that are not identifiable without velocity or an
additional measured force. They were rejected for parsimony: the one-mass
physical model explains all three fitting experiments at the noise floor and
also gives a 0.002499-m error on the held-out sinusoidal experiment.

## Verification

OpenModelica 1.27.0 with Modelica Standard Library 4.1.0 successfully ran
`checkModel(Sled)` and all four simulations. Introspection confirmed the
classes used (`Mass`, `SpringDamper`, `SupportFriction`, `Force`, `Fixed`, and
`PositionSensor`) and the final instantiated bindings were:

```text
m       = 1.50029
c       = 5.00020
d       = 0.300335
f_slide = 0.599754
peak    = 1.2
```
