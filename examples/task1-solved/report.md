# Task 1 — Carriage on an elastic element: model, calibration and validation

## 0. Result in one line

A single translational degree of freedom — point mass, linear spring, parallel
linear viscous damper, all referred to the fixed rig frame — reproduces both
fitting experiments *and* the untouched validation experiment down to the stated
sensor noise floor:

| | m [kg] | c [N/m] | d [N·s/m] |
|---|---|---|---|
| fitted value | **1.999869** | **7.997732** | **0.800783** |
| 1σ (from the fit) | ± 0.001087 | ± 0.003963 | ± 0.000898 |

ω_n = 1.99978 rad/s (0.31828 Hz), ζ = 0.100115, damped period T_d = 3.1578 s,
static compliance 1/c = 0.125035 m/N.

Weighted χ²/(N−k) = **1.0057** (N = 2004 residuals, k = 3 parameters). A value of
1.0 means the residuals are *exactly* as large as the declared sensor noise, i.e.
there is no unexplained signal left to model.

---

## 1. Deliverable files

| File | Content |
|---|---|
| `model.mo` | **The deliverable model**, `model Carriage`: `RealInput u`, `RealOutput y_s`, `RealOutput y_v`. Only `Modelica.Mechanics.Translational.{Components,Sources,Sensors}` + `Modelica.Blocks.Interfaces`. Fitted parameters are its default values. |
| `Experiments.mo` | Test benches `Experiments.Exp1/Exp2/Exp3`: the same `Carriage` driven by the three measured excitations. Not part of the model — this is the experiment definition. |
| `calibrate.py` | The calibration of record. Compiles the benches with `omc`, then fits m, c, d by simulating **the actual Modelica model** for every function evaluation. `--multistart` adds the uniqueness check. |
| `verify.py` | Independent verification: runs the benches with **no `-override` at all** (i.e. with the values written in `model.mo`) and recomputes every number in this report; also cross-checks against a separately coded ODE. |
| `plot_fit.py`, `fit_overview.png` | Measurement vs. model vs. residual for all three experiments. |
| `fitted_parameters.txt` | Machine-readable fitted values. |
| `analysis/explore.py` | Exploratory structure identification (Python reference ODE). |
| `analysis/structures.py` | The rejected alternative structures, quantified. |
| `analysis/timing_check.py` | Identifiability test for the excitation timing I had to infer. |
| `analysis/validation_check.py` | Decomposition of the validation residual. |
| `build/` | All `omc` build artefacts. |

Reproduce with, from the project root:

```
.venv/bin/python tasks/task1/work/calibrate.py --multistart
.venv/bin/python tasks/task1/work/verify.py
```

---

## 2. Model structure

```
frame (Fixed, s0=0) ── SpringDamper(c, d, s_rel0=0) ── Mass(m, L=0) ── Force(u)
                                                          │
                                                    PositionSensor → y_s
                                                    SpeedSensor    → y_v
```

which is `m·ÿ = u − c·y − d·ẏ`, with `y(0) = 0`, `ẏ(0) = 0`.

The description gives three facts, and each pins down one element:

* *"connected to the test-rig frame through an elastic element"* → one spring
  between a `Fixed` frame and the carriage, i.e. a restoring force proportional
  to absolute position, not to a relative coordinate of a second body.
* *"the measured position oscillates"* → the carriage has inertia; a mass is
  needed for the spring to oscillate against.
* *"and slowly returns to rest"* → energy dissipation, and the decay is slow, so
  the damping is small compared to critical.

The data then confirms all three quantitatively before any optimiser is started:
the free decay of `exp1` has a half-period of ≈ 1.575 s (→ ω_d ≈ 1.99 rad/s) and
a peak-to-peak amplitude ratio of ≈ 1.39 (→ ζ ≈ 0.104), and the settled position
of the 2 N step in `exp2` is 0.251 m (→ c ≈ 7.97 N/m). Those three coarse numbers
already give (m, c, d) ≈ (1.98, 7.97, 0.83), so the structure is not in doubt;
the fit only sharpens the values.

---

## 3. Physical assumptions

### 3.1 Stated in the task, encoded in the model

1. **One translational DOF.** Position and velocity of the carriage are the only
   kinematic quantities.
2. **The force acts on the carriage** and is the only excitation.
3. **Initial condition**: at rest at position zero. Encoded as
   `carriage.s(start=0, fixed=true)`, `carriage.v(start=0, fixed=true)`.

### 3.2 Added by me — the description does *not* state these

4. **The elastic element is linear** in deflection over the traversed range
   (|y_s| up to 1.73 m in the validation run). Tested: adding a cubic term
   `c·(y + ε·y³)` drives ε → −6·10⁻⁴ and does not reduce χ² at all (§5).
5. **Damping is linear viscous**, and it is **lumped into the elastic element**
   as a parallel damper. The description does not say where the dissipation
   sits. A damper inside the elastic element and a separate damper from carriage
   to frame are *observationally identical here*, because the frame is
   inertially fixed — in both cases the force is `d·ẏ`. I chose the parallel
   `SpringDamper` because it is one component instead of two and because the
   description attributes the connection to a single "elastic element". Nothing
   in the data can distinguish the two, so this is a modelling-style choice, not
   a physical claim.
6. **No dry friction.** A Coulomb term is not needed (§5) and its estimate
   collapses to 2·10⁻⁴ N, four orders below the excitation. Consistent with the
   pulse experiment settling at 0.0035 m ≈ 0, i.e. no measurable stick band.
7. **The position datum coincides with the force-free equilibrium**:
   `frame.s0 = 0` and `elasticElement.s_rel0 = 0`, so `y_s = 0` is simultaneously
   the measurement zero and the unstretched configuration. Justified by `exp1`
   returning to zero and by `exp2`'s settled offset being exactly u/c with no
   additive constant (a fitted constant offset comes out at −1.4·10⁻⁵ m).
8. **No gravity / no static preload.** The motion axis is treated as horizontal.
   `Modelica.Mechanics.Translational` has no gravity field, so this required no
   action — but it *is* an assumption: a vertical axis with a preloaded spring
   would be numerically indistinguishable, with the preload absorbed into the
   datum of assumption 7.
9. **Ideal actuation and sensing.** No actuator dynamics or force-sensor lag; the
   sensors return true position and velocity with no gain error, bias or delay.
   `y_v` is treated as an *independent* measurement of the same trajectory, not
   as a numerical derivative of `y_s`.
10. **Carriage length L = 0** (point mass). `Modelica.Mechanics.Translational.Components.Mass.L`
    has **no default value** in MSL 4.1.0 — it is declared `parameter SI.Length L(start = 0)`.
    Left unbound it would be silently filled from its start value with a warning.
    I bind it explicitly. It has no dynamic effect (both flanges coincide).
11. **No end stops or backlash** within the traversed range.
12. **Excitation reconstruction.** The task states the *kind* of each input but
    not its parameters, so I recovered them from the `u` column:

    | experiment | reconstructed input |
    |---|---|
    | `exp1_fit` | rectangular pulse, 5 N, from t = 1.0 s, width 0.5 s |
    | `exp2_fit` | step, 2 N, at t = 1.0 s |
    | `exp3_validation` | 3·sin(2π·0.3·(t−1.0)) N for t > 1.0 s |

    The sine is exact to 5·10⁻⁷ N over all 501 samples, which fixes the common
    reference time at t = 1.0 s to seven digits. The reconstructed inputs of the
    benches match the recorded `u` column **sample-for-sample, difference 0**
    (`exp1`, `exp2`) and 5·10⁻⁷ (`exp3`, floating point).
13. **Equal weighting of the two fitting experiments**, with residuals scaled by
    the stated noise σ per channel (3·10⁻³ m, 10⁻² m/s). This makes the objective
    the negative log-likelihood under the stated noise model, and makes
    χ²/(N−k) ≈ 1 the correct target.

### 3.3 The one assumption in 3.2 that could have hurt, tested

Assumption 12 fixes the edge times to the grid values 1.0 / 1.5 / 1.0, but the
`u` samples alone only locate each edge within one 0.05 s sample interval, and a
0.05 s timing error on a 3.16 s period is a 5.7° phase error — about 0.05 m on
`exp1`, seventeen times the noise. So I released the three edge times as free
parameters (`analysis/timing_check.py`, fitting experiments only):

| | t_on (exp1) | t_off (exp1) | t_step (exp2) |
|---|---|---|---|
| estimated | 0.998880 ± 0.000660 | 1.499215 ± 0.000657 | 0.999069 ± 0.001101 |
| assumed | 1.0 | 1.5 | 1.0 |

They are identifiable to ±0.7 ms from the *response* and land on the assumed
values within 1.1 ms, i.e. within 2 % of one sample interval. Releasing them
moves m by +0.001 kg, c by +0.0009 N/m and d by +0.0004 N·s/m — every one below
1σ. The assumption costs nothing.

---

## 4. Free parameters: bounds and initial values

Three free parameters. Bounds are deliberately wide — several decades either
side of anything a lab carriage could plausibly be — so that they carry no
information about the answer; initial values are round numbers, *not* the
graphical estimates of §2, again so the fit is not handed its own result.

| parameter | meaning | initial value | lower bound | upper bound |
|---|---|---|---|---|
| `m` | carriage mass [kg] | 1.0 | 0.05 | 50 |
| `c` | stiffness of the elastic element [N/m] | 10.0 | 0.1 | 1000 |
| `d` | viscous damping [N·s/m] | 1.0 | 1·10⁻⁴ | 100 |

Optimisation is done on log(m), log(c), log(d) — the parameters span decades and
must stay positive — with `scipy.optimize.least_squares` (trust-region
reflective), forward differences with a relative step of 10⁻⁶. No bound is
active at the solution; the lower bound on `d` exists only to keep the
logarithm finite.

**Uniqueness.** From six widely separated starts spanning the whole box, all six
converge to the same point with identical χ² = 2012.34:

| start (m, c, d) | → (m, c, d) | χ² |
|---|---|---|
| 0.2, 1, 0.05 | 1.99987, 7.99773, 0.80078 | 2012.34 |
| 1, 10, 1 | 1.99987, 7.99773, 0.80078 | 2012.34 |
| 10, 100, 5 | 1.99987, 7.99773, 0.80078 | 2012.34 |
| 30, 500, 30 | 1.99987, 7.99773, 0.80078 | 2012.34 |
| 0.5, 200, 0.01 | 1.99987, 7.99773, 0.80078 | 2012.34 |
| 20, 2, 10 | 1.99987, 7.99773, 0.80078 | 2012.34 |

All three parameters are individually identifiable because the input is known in
absolute newtons: `c` from the static gain, `c/m` from the frequency, `d` from
the decay rate. The only appreciable correlation is corr(m, c) = +0.911 — the
frequency constrains the ratio c/m much more tightly than either alone — while
`d` is essentially uncorrelated with both (|corr| ≤ 0.006).

---

## 5. Fitted values, and the alternatives I rejected

### 5.1 Fitted values

```
m = 1.999869 ± 0.001087 kg        (0.05 % relative)
c = 7.997732 ± 0.003963 N/m       (0.05 % relative)
d = 0.800783 ± 0.000898 N·s/m     (0.11 % relative)
```

1σ values from the Gauss-Newton covariance (J^T J)⁻¹ of the σ-weighted residual;
this is the correct covariance precisely because χ²/(N−k) comes out at 1.0057.

The values land strikingly close to 2, 8 and 0.8. I have no way to confirm from
inside the task whether those are the generating values, so I report what the
fit gives.

### 5.2 Rejected alternatives

Four richer structures were fitted on the same two fitting experiments
(`analysis/structures.py`). None of them reduces χ², and all of them pay for the
extra freedom:

| structure | k | χ²/N | AIC | what the extra parameters do |
|---|---|---|---|---|
| **(a) mass + spring + parallel damper (chosen)** | **3** | **1.0042** | **2018.3** | — |
| (b) (a) + Coulomb friction F | 4 | 1.0039 | 2019.7 | F → 2·10⁻⁴ N, i.e. zero |
| (c) (a) + cubic spring c·(y+εy³) | 4 | 1.0042 | 2020.3 | ε → −6·10⁻⁴, i.e. zero |
| (d) two-mass chain m₁–(c₁,d₁)–m₂–(c₂,d₂)–frame | 6 | 1.0040 | 2023.9 | m₂ → 0.033 kg; collapses back to (a), the two stiffnesses 24.18 and 11.95 N/m combining in series to 8.00 N/m |
| (e) standard linear solid (spring ∥ Maxwell branch) | 5 | 1.0042 | 2022.4 | Maxwell branch stiffness → 0.013 N/m against the main 8.0 N/m, i.e. zero |

Two things are worth naming explicitly:

* **The choice is not close.** χ²/N = 1.0042 for the 3-parameter model already
  means the residual equals the declared noise; there is no signal left for a
  fourth parameter to explain, so every extension is pure penalty. AIC prefers
  (a) by 1.4 to 5.6 nats.
* **Structure (d) is the one plausible competitor and it self-destructs.** "The
  carriage is connected to the frame through an elastic element" leaves room for
  the *rig itself* to be compliant, which is a genuine 2-DOF possibility and a
  real effect on real test rigs. The optimiser drives the rig mass to 0.033 kg —
  a rigid-body limit — and reassembles the two stiffnesses into exactly the
  8.0 N/m series equivalent. The data contains no second mode, so the second DOF
  is not identifiable and must not be carried.

Structure (e) deserves a note because "slowly returns to rest" can also describe
*viscoelastic relaxation* rather than an oscillatory decay — a physically
different reading of the same sentence. It is ruled out by the step response:
`exp2` settles at 0.251 m and stays there, with no creep, and the Maxwell branch
duly collapses.

### 5.3 What was *not* tried, and why

Backlash, end stops and load-dependent friction were not fitted. All three are
switching nonlinearities that would show up as an amplitude-dependent period or
decay rate. The free decay of `exp1` alone sweeps a 100:1 amplitude range, from
0.52 m down to the noise floor, and `exp3` extends the range upward to 1.73 m —
and one constant (m, c, d) leaves a white residual across all of it (§6). An
amplitude-dependent effect cannot hide under a residual that is already at the
noise floor over a 300:1 amplitude span.

---

## 6. Fit metrics

RMSE over all 501 samples of each 25 s record, model against measurement.

| experiment | role | RMSE `y_s` [m] | RMSE `y_v` [m/s] | RMSE/σ (s, v) | RMSE/range (s, v) |
|---|---|---|---|---|---|
| `exp1_fit` | fitting | **0.002874** | **0.010163** | 0.96, 1.02 | 0.32 %, 0.55 % |
| `exp2_fit` | fitting | **0.003063** | **0.010119** | 1.02, 1.01 | 0.69 %, 1.31 % |
| `exp3_validation` | **validation** | **0.003363** | **0.010533** | 1.12, 1.05 | 0.10 %, 0.16 % |
| *stated sensor noise σ* | | *0.003000* | *0.010000* | | |

Pooled: fitting y_s = 0.002970 m, y_v = 0.010141 m/s; validation y_s = 0.003363 m,
y_v = 0.010533 m/s.

Worst single-sample error, validation: 0.0110 m on `y_s` (3.7 σ) and 0.0338 m/s
on `y_v` (3.4 σ) — the expected extreme of 501 Gaussian draws.

Lag-1 residual autocorrelation, the test for leftover dynamics:

| experiment | `y_s` | `y_v` |
|---|---|---|
| `exp1_fit` | +0.091 | +0.078 |
| `exp2_fit` | +0.042 | −0.085 |
| `exp3_validation` | +0.234 | +0.036 |

Five of the six are at the level expected from white noise. See `fit_overview.png`:
the residual traces are visually indistinguishable from noise in all three runs.

### 6.1 The one non-white residual, taken seriously

`exp3`'s `y_s` residual has lag-1 autocorrelation +0.234 and an RMSE of 1.12 σ
rather than 1.00 σ. Subtracting the noise in quadrature leaves a systematic
component of 1.5·10⁻³ m. It is small — 0.04 % of the 3.45 m peak-to-peak signal —
but it is real, and it should not be waved away, so I decomposed it
(`analysis/validation_check.py`, using the frozen parameters; `exp3` is never
refitted):

* Propagating the fit's own parameter covariance through the `exp3` prediction
  gives a predicted 1σ spread of **1.24·10⁻³ m RMS** (peak 1.69·10⁻³ m) — the same
  size as the 1.5·10⁻³ m observed. So the parameter uncertainty alone accounts
  for it.
* Projecting the residual onto a gain error and a phase error yields a relative
  gain error of −1.15·10⁻⁴ (0.01 %) and an apparent time shift of −0.69 ms
  (1.4 % of one sample interval). Removing those two degrees of freedom brings
  the RMSE to 0.003075 m, i.e. exactly σ.

The mechanism is simply that `exp3` excites at 0.3 Hz against a natural frequency
of 0.3183 Hz with ζ = 0.1 — frequency ratio 0.94, amplification 4.56. Near
resonance a lightly damped system amplifies parameter error, so a 0.05 % error in
m and c, which is invisible in the fitting experiments, becomes the dominant
residual in the validation experiment. This is amplified parameter uncertainty,
not a missing physical effect: a structural deficiency would not be removable by
a pure gain-and-phase correction of that size, and none of the four richer
structures in §5.2 found anything to explain.

**The validation experiment is the strongest evidence in the package.** It is a
different excitation class (sustained, near-resonant, ±3 N) than either fitting
experiment (transient pulse; constant step), it drives the carriage 3.3× further
than anything in the fitting set, and the model extrapolates into it with
RMSE = 1.12 σ.

---

## 7. Verification of the delivered artefact

The numbers above are not read off the optimiser. `verify.py` runs the three
benches with **no parameter override whatsoever**, so the simulator uses the
values written into `model.mo`, and recomputes every metric. Additionally:

* **`checkModel`** on `Carriage` and all three benches: clean, no errors, no
  warnings, 33 equations / 33 variables (balanced).
* **Every parameter is bound.** The generated `Experiments.Exp1_init.xml` was
  inspected programmatically: `m`, `c`, `d` carry values and are overridable;
  `dut.m`, `dut.c`, `dut.d`, `dut.carriage.m`, `dut.elasticElement.c/d` are
  non-changeable aliases of them, i.e. bound by equation rather than filled from
  a start value; `carriage.L`, `frame.s0` and `elasticElement.s_rel0` are bound
  to 0. `calibrate.py` fails loudly if any parameter is unbound.
* **Initialisation is what the description demands**: `y_s(0) = 0`, `y_v(0) = 0`,
  reported by the simulator, with no homotopy needed.
* **The model agrees with an independently coded ODE** `m·ÿ = u − c·y − d·ẏ`,
  integrated by `scipy.solve_ivp` with a different method and tighter tolerance,
  to **3.8·10⁻⁸ / 3.2·10⁻⁸ / 8.2·10⁻⁸** (exp1/exp2/exp3, max over both channels).
  That is five orders of magnitude below the noise floor, so nothing in the
  reported metrics is numerical.
* **The parameter values are read back out of the simulator.** The benches echo
  `m`, `c`, `d` into the result file as `p_m`, `p_c`, `p_d`; `calibrate.py`
  asserts they equal what was requested before touching the trajectory. This was
  not paranoia in the abstract — see §8.

---

## 8. Two traps that were hit and closed

Recorded because both fail *silently* and both would have produced a
plausible-looking but wrong calibration.

1. **`omc -override` accepts garbage without complaint.** My first driver built
   the override string with Python's `repr()`. Under NumPy 2, `repr(np.float64(1.0))`
   is `"np.float64(1.0)"`, so the simulator received
   `-override=m=np.float64(1.0),...`, parsed it to **0.0**, and exited with
   status 0 and no warning. Here it happened to blow up as a division by zero in
   `m`; had it hit only `c` or `d` the simulation would have completed happily
   with a parameter silently set to zero. Fixed by formatting with `%.17g` from
   plain floats, and closed permanently by the `p_m`/`p_c`/`p_d` read-back, which
   I confirmed fires on exactly this defect.
2. **`Mass.L` has no default in MSL 4.1.0.** `parameter SI.Length L(start = 0)`
   would have been filled from its start value with only a warning. Bound
   explicitly to 0. This is why the class definitions were read out of the
   installed library by introspection rather than from memory — which is also
   how `Sine.f` was confirmed (it was `freqHz` in MSL 3.x).

---

## 9. Scope notes

* `model.mo` deliberately contains **only** the physical model with its signal
  interface, as specified: `RealInput u`, `RealOutput y_s`, `RealOutput y_v`,
  built solely from `Modelica.Mechanics.Translational.{Components,Sources,Sensors}`
  and `Modelica.Blocks.Interfaces`. Consequently it is a *block to be driven* and
  is not simulable on its own — with `u` unconnected, OpenModelica would take
  u = 0. The excitation signals live in `Experiments.mo`, which is the experiment
  definition and not part of the model.
* `Experiments.mo` uses `Modelica.Blocks.Sources.{Pulse,Step,Sine}` to generate
  the three measured excitations. These are signal *generators* for the
  experiment, not signal-processing blocks standing in for physics; no transfer
  function, state-space block, lookup table or user-written equation block
  appears anywhere in either file. In particular the measured CSVs are never read
  into a Modelica model — the inputs are reproduced analytically, and §3.3 shows
  the reproduction is exact.
* `Bench` adds three trivial states `p_m`, `p_c`, `p_d` (`der = 0`, `start = m/c/d`)
  purely so the simulator reports back which parameter values it used (§7). They
  are in the bench, not in `Carriage`, and have no effect on the mechanics.
* The exploratory scripts under `analysis/` use a Python reference ODE for speed.
  It is not the deliverable and no reported result rests on it alone: the
  parameter values, all RMSE figures and the validation numbers all come from
  simulating `model.mo`, and §7 pins the two implementations together to 10⁻⁸.
* `exp3_validation` was used for exactly two things: reporting validation error,
  and the residual decomposition in §6.1 that uses the already-frozen parameters.
  It never entered any objective function.
