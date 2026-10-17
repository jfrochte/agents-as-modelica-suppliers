# Task 1 — Carriage on an elastic element: model, calibration, validation

## 1. Deliverables

| File | Content |
|---|---|
| `model.mo` | **the deliverable model** `Carriage` (`RealInput u`, `RealOutput y_s`, `RealOutput y_v`) |
| `harness.mo` | calibration harness: feeds the three recorded force signals into `Carriage` (`Harness.Exp1_Pulse`, `Harness.Exp2_Step`, `Harness.Exp3_Sine`) |
| `alternatives.mo` | the structures that were considered and rejected (`Alternatives.*`) |
| `calibrate.py` | parameter estimation (every objective evaluation is one OpenModelica simulation) |
| `structure_study.py` | verification against a closed-form solution, solver study, structure comparison |
| `diagnostics.py` | uncertainty propagation, residual analysis, input-reconstruction sensitivity |
| `make_figure.py`, `fit_overview.png` | measured vs. simulated plot |
| `build/` | `omc` artefacts, simulation executables, `fit_result.json`, `structure_study.json`, `diagnostics.json` |

Environment: OpenModelica 1.27.0, Modelica Standard Library 4.1.0 (`~/.openmodelica/libraries`), Python 3.12 (numpy/scipy/OMPython/matplotlib) in `.venv`.

## 2. The model

`Carriage` is a one-dimensional translational oscillator: a rigid mass connected
to the (rigid) test-rig frame by a Kelvin–Voigt element, i.e. a linear spring and
a linear damper **in parallel**:

```
m*der(v) = u - c*s - d*v ,   der(s) = v ,   s(0) = 0 , v(0) = 0
```

Components used (all from the admissible subset, verified by `getClassNames` /
`list` against MSL 4.1.0 before use):

| Component | Class |
|---|---|
| carriage | `Modelica.Mechanics.Translational.Components.Mass` (`m`, `s(fixed=true,start=0)`, `v(fixed=true,start=0)`) |
| elastic element | `...Components.Spring` (`c`, `s_rel0 = 0`) |
| damping | `...Components.Damper` (`d`) |
| frame | `...Components.Fixed` (`s0 = 0`) |
| force input | `...Sources.Force` (`useSupport = false`), driven by `u` |
| sensors | `...Sensors.PositionSensor`, `...Sensors.SpeedSensor` |
| interface | `Modelica.Blocks.Interfaces.RealInput` / `RealOutput` |

No transfer function, state-space block, lookup table or user-defined equation
block is used. The model is balanced (37 equations / 37 variables), `checkModel`
passes and `omc` issues no warning about missing parameter values.

The model is **executable** in two ways:

* driven by an external signal source (used here for calibration, `harness.mo`),
* driven directly from the recorded data files by the simulation runtime:
  `./build/Carriage -csvInput=data/exp1_fit.csv -override=m=...,c=...,d=... -maxStepSize=0.05`
  (see §8 for why `-maxStepSize` is required and why this path was not used for
  the fit).

## 3. Free parameters, bounds, initial values, result

| Parameter | Meaning | Bounds | Initial value | Fitted value ± 1 s.e. |
|---|---|---|---|---|
| `m` | carriage mass | [0.1, 20] kg | 2.0056 | **1.999869 ± 0.001090** kg |
| `c` | stiffness | [0.1, 200] N/m | 8.0197 | **7.997732 ± 0.003974** N/m |
| `d` | damping coefficient | [0, 50] N·s/m | 0.8038 | **0.800783 ± 0.000900** N·s/m |

Initial values are *not* guesses: they are read off simple features of the
fitting data —

* `c0 = 2 N / x_ss` from the settled value of the step experiment
  (`x_ss = 0.2494 m` → `c0 = 8.02 N/m`),
* `ω_n = 1.9997 rad/s`, `ζ = 0.1002` from a damped-sinusoid fit to the free decay
  of the pulse experiment (`t ≥ 1.6 s`) → `m0 = c0/ω_n²`, `d0 = 2ζω_n m0`.

Derived quantities (1 s.e. by propagation of the covariance):

| Quantity | Value |
|---|---|
| natural frequency `ω_n = sqrt(c/m)` | 1.999782 ± 0.000225 rad/s (`f_n = 0.318275 ± 0.000036 Hz`) |
| damping ratio `ζ = d/(2√(cm))` | 0.100115 ± 0.000124 |
| static compliance `1/c` | 0.125035 ± 0.000062 m/N |
| damped period `T_d` | 3.1578 ± 0.0004 s |
| decay time constant `2m/d` | 4.9948 ± 0.0063 s |

`m` and `c` are strongly correlated (ρ = 0.911); the well-determined
combinations are `c/m = ω_n²` and `d/√(cm) = 2ζ`. The estimate of ζ is
essentially uncorrelated with both (|ρ| < 0.01).

## 4. Fit metrics

Weighted least squares (maximum likelihood for the stated noise) on **both
fitting experiments simultaneously**, `J = Σ[(y_s−ŷ_s)/σ_s]² + [(y_v−ŷ_v)/σ_v]²`
with `σ_s = 3e-3 m`, `σ_v = 1e-2 m/s`; 2004 residuals, 3 parameters:

`J = 2012.34` → weighted rms residual **1.0028** (i.e. the model reproduces the
fitting data at exactly the stated noise level).

RMSE per output and experiment (501 samples each, computed from OpenModelica
simulations of `model.mo`):

| Experiment | Role | RMSE `y_s` [m] | RMSE `y_v` [m/s] | RMSE `y_s`/σ_s | RMSE `y_v`/σ_v |
|---|---|---|---|---|---|
| `exp1_fit` (pulse) | fitting | 0.002874 | 0.010163 | 0.96 | 1.02 |
| `exp2_fit` (step) | fitting | 0.003063 | 0.010119 | 1.02 | 1.01 |
| `exp3_validation` (sine) | **validation only** | 0.003363 | 0.010533 | 1.12 | 1.05 |

The validation experiment was not used for fitting. Its error is fully explained
by measurement noise plus the propagated parameter uncertainty:
expected `sqrt(σ_s² + band²) = 0.00325 m` (observed 0.00336, 104 %) and
`0.01028 m/s` (observed 0.01053, 102 %). For reference, the validation signal
amplitude is ±1.73 m, i.e. a relative error of 0.2 %.

## 5. Calibration procedure

1. `omc` compiles `Harness.Exp1_Pulse`, `Harness.Exp2_Step`, `Harness.Exp3_Sine`
   once (C code, `stopTime=25`, `numberOfIntervals=500` → output exactly on the
   0.05 s measurement grid, tolerance 1e-10).
2. Each objective evaluation **runs the compiled Modelica models** with
   `-override=m=..,c=..,d=..`; the CSV result is read and compared with the data.
   No surrogate model is used for the reported numbers.
3. Optimisation: Nelder–Mead from the data-driven initial values (129
   evaluations), followed by a bounded Levenberg–Marquardt/trust-region
   refinement of the residual vector. Total runtime ≈ 4 s.
4. Standard errors from the linearised covariance `s²(JᵀJ)⁻¹`,
   `s² = J/(n−k) = 1.0057`.

Binding checks (the "silently filled parameter" trap):

* `m`, `c`, `d` are present as variables in `Harness.Exp*_init.xml` and are
  propagated through `carriage.m` → `carriage.carriage.m` at simulation time:
  `J(2,8,0.8) = 2014.4` vs `J(2.1,8,0.8) = 49289` — a 5 % change in `m` changes
  the cost by a factor 24, so the override is live. The script asserts this.
* `Carriage` itself declares `m`, `c`, `d` with explicit defaults, so it is
  executable without the harness, and `checkModel` reports no missing bindings.

## 6. Verification

* **Closed-form reference.** The OpenModelica simulation was compared with the
  analytic solution of `m x'' + d x' + c x = u` (matrix exponential for the
  piecewise-constant inputs, complex frequency response + transient for the
  sine): maximum deviation **4…7 · 10⁻⁹ m** (`y_s`) and **8…14 · 10⁻⁹ m/s**
  (`y_v`) in all three experiments — the simulation is numerically exact at the
  scale of interest.
* **Solver independence.** The metrics are identical for `dassl`, `cvode`,
  `rungekutta` (step 1e-4) and `euler` (step 1e-5).
* **Residual whiteness.** The residual rms equals the stated noise level on all
  three experiments; the systematic (1 s moving-average) part of the residual is
  0.00055 / 0.00068 / 0.00136 m — well below σ_s = 0.003 m, and for the
  validation experiment it matches the predicted parameter-uncertainty band
  (0.00124 m).

## 7. Physical assumptions

Given by the description and implemented as stated:

1. one translational degree of freedom, rigid carriage of mass `m`;
2. elastic element between carriage and frame, massless;
3. carriage at rest at `s = 0` at the start of each experiment → `s(0)=0`,
   `v(0)=0` set as **fixed** initial conditions (not merely start values).

Added by me (the description does not state them; each one is either forced by
the data or tested):

4. **Parallel (Kelvin–Voigt) arrangement** of spring and damper, not series —
   see §8, the step experiment decides this unambiguously.
5. **Linear spring and linear viscous damper**, no preload (`s_rel0 = 0`, which
   the "at rest at zero" statement also forces) and no progressive/nonlinear
   stiffness. Justified by the fit: one linear parameter set reproduces the step
   (0.25 m), the pulse (0.52 m) and the resonant sine (±1.73 m) at the noise
   level (§4), so there is no amplitude dependence left to model.
6. **No dry (Coulomb) friction, no stiction.** Tested: an exponentially decaying
   envelope fits the free decay with rms 0.0029 m (= noise), a linearly decaying
   envelope (`A − b·t`, the signature of Coulomb friction) gives 0.0239 m, 8×
   worse. Also, the carriage returns to |y_s| < 0.005 m (noise) rather than
   sticking at an offset.
7. **Ideal sensors**: no dynamics, bias or quantisation; `y_v = der(y_s)`. Both
   channels are reproduced simultaneously at their respective noise levels by one
   parameter set, which is the consistency check for this.
8. **Noise model**: independent Gaussian with the stated σ, used as weights
   (i.e. maximum-likelihood estimation). The residual rms per channel comes out
   at 0.96…1.12 σ, confirming the stated values.
9. **Input reconstruction** (see §8): the recorded `u` samples are the values
   *before* an input edge; the underlying signals start at `t = 1.0 s`
   (pulse 5 N over [1.0, 1.5) s, step 2 N from 1.0 s, sine 3 N at 0.3 Hz from
   1.0 s). This is inferred, not given, and it is supported by the data:
   estimating the start time as a free parameter gives `t₀ = 0.999 ± 0.001 s`
   and a pulse width of `0.500 ± 0.001 s`, and the sine samples are reproduced
   to 5·10⁻⁷ N by `3·sin(0.6π(t−1))`.
10. **No further dynamics**: no actuator/compliance dynamics between the input
    signal and the force on the carriage, no end stops, no gravity component
    along the axis (the carriage rests at `s = 0` with `u = 0`).

## 8. Structures that were considered, and why S1 was chosen

All structures are implemented in `alternatives.mo` and were fitted to the same
two experiments with the same objective:

| Structure | Parameters | `J_fit` | Verdict |
|---|---|---|---|
| **S1** mass ∥ spring ∥ damper (chosen) | 3 | **2012.34** | weighted rms residual 1.003 → at the noise floor |
| S1b mass ∥ spring (no damper) | 2 | 2 601 001 | rejected: the measured oscillation decays, an undamped model does not |
| S2 S1 + quadratic damping `−dq·v·|v|` | 4 | 2012.336 | rejected: `ΔJ = 0.005` for one extra parameter, `dq = 0.0004 ± 0.0056` → not identifiable, S1 is already at the noise floor |
| S3 Maxwell element (spring **in series** with damper) | 3 | 8 400 192 | rejected: a series damper creeps under constant force. At the fitted parameters it drifts at `u/d = 2.5 m/s` → `y_s(25 s) = 54 m` where 0.256 m was measured; the measured step settles at 0.25 m |
| Coulomb friction in addition to S1 | — | — | rejected by the envelope test of §7.6 (exponential vs. linear decay) |

S1 and S2 cannot be distinguished by the data, so S1 is chosen by parsimony
(AIC/BIC: one parameter less, same cost). Note that "damper to the frame" and
"damper between carriage and frame" are the same element here, and a
`SpringDamper` component would be algebraically identical to `Spring` + `Damper`
in parallel — separate components were used so that each free parameter maps to
one physical quantity.

## 9. Two pitfalls worth recording

1. **Input reconstruction dominates the fit quality.** The data give `u` on the
   0.05 s grid and the first non-zero sample of exp1/exp2 is at `t = 1.05 s`.
   Interpreting the samples naively (zero-order hold from the sample instant,
   i.e. edges at 1.05 s, and holding the sine between samples) leaves residuals
   2–3× above the noise **even after refitting** (`m = 1.9593`, `c = 7.9956`,
   `d = 0.8032`; exp1 0.0094 / 0.0262, exp2 0.0051 / 0.0130, exp3 0.0377 /
   0.0715; weighted rms residual 2.31). With the reconstruction of §7.9 the
   residuals fall to 1.00 σ. The effect is largest for the validation
   experiment, because 0.3 Hz is close to the resonance (0.318 Hz), where a
   0.05 s timing error is a large phase error.
2. **`omc -csvInput` silently skips short input pulses.** Driving the model
   directly from `data/exp1_fit.csv` with the default DASSL settings produces
   `y_s ≡ 0`: the state is flat before the pulse, the solver takes one huge step
   across the whole 0.5 s pulse, and the edge of a file-based input does not
   create a time event. With `-maxStepSize=0.05` (or a fixed-step solver) the
   input is picked up and the run reproduces the expected response. For this
   reason the calibration uses signal sources (`Modelica.Blocks.Sources.Pulse`,
   `Step`, `Sine`), which do generate time events — verified against the
   closed-form solution to 10⁻⁹ m.

## 10. Reproduction

```bash
cd work
python calibrate.py         # compile (if needed) + fit  -> build/fit_result.json
python structure_study.py   # closed-form check, solvers, structure comparison
python diagnostics.py       # uncertainty propagation, residuals, input timing
python make_figure.py       # fit_overview.png
```

`calibrate.py` builds the three `Harness` models with OMPython into `build/`
(omc writes its artefacts into the current directory); `structure_study.py`
additionally builds the `Alternatives` models if they are missing. All scripts
run synchronously and take a few seconds each (the calibration ≈ 4 s, the
structure study ≈ 25 s).
