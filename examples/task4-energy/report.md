# Task 4 — Drive-train rig: Modelica model and calibration

Deliverables in `work/`:

| file | role |
|---|---|
| `model.mo` | executable model: `DriveTrainRig` (with `RealInput u`, `RealOutput y_i, y_w`) + reusable sub-models `BatteryPack`, `DCMachine` |
| `sim_wrappers.mo` | one runnable model per experiment (`RunExp1`…`RunExp4`) that reproduces each commanded `u(t)` |
| `fit.py` | reproducible parameter fit (Python ODE + weighted least squares, 3 fitting experiments only) |
| `sim_validate.py` | runs the Modelica model for all 4 experiments via OMPython and reports RMSE vs the CSVs |
| `params_final.npy` | the fitted parameter values |

Everything was built with OpenModelica 1.27.0 / Modelica Standard Library 4.1.0.

---

## 1. Physical structure

The rig is modelled as distinct assemblies matching the description
(battery → machine → fixed reduction → commanded-torque brake), not as one flat
network:

```
 BatteryPack --(i=y_i)-- DCMachine --flange-- IdealGear(5.2) --flange-- Brake(u)
      |                        |  ^                     |                    |
     Gnd                 friction  |back-emf           wSensor(=y_w)         Gnd
                                (Coulomb)             SpeedSensor
```

* `BatteryPack` — Thevenin pack: OCV source (voltage that declines with the
  delivered charge) in series with the internal resistance `R_int`.
* `DCMachine` — lumped armature circuit (resistance `R`, inductance `L`,
  back-emf `ke·w`), electromagnetic torque `kt·i`, rotor inertia `J`.
* `IdealGear` — the fixed 5.2 : 1 reduction (motor : output), ideal and
  implicitly grounded (MSL default).
* `brake` (`Sources.Torque`) — the commanded load at the output shaft; `u` is
  negated with a gain so the brake opposes rotation.
* `friction` (`Sources.SignTorque`) — Coulomb friction at the motor shaft.
* Sensors: `battCurrent` → `y_i`, `wSensor` → `y_w`.

**Governing equations** (all quantities referred to the motor shaft, `w` motor
speed, `i` armature/battery current, `Q` delivered charge, `r = 5.2`):

```
L·di/dt = (V0 - α·Q) - i·(R_int + R) - ke·w     (armature loop)
J·dw/dt = kt·i - F0·sgn(w) - u/r                 (rotor dynamics)
dQ/dt   = i                                      (pack charge balance)
y_i = i ,   y_w = w / r
```

Only admissible library blocks are used: `Modelica.Electrical.Analog` (pins,
resistor, inductor, ground, signal voltage, current sensor),
`Modelica.Mechanics.Rotational` (inertia, ideal gear, torque/Coulomb sources,
speed sensor), and `Modelica.Blocks` (gain, step, sine, add) for signal routing.
No transfer-function / state-space / user-equation-system blocks, and no tables.

---

## 2. Free parameters — bounds and initial values

Bounds are the `min`/`fixed` attributes in the model; “fit start” is the value
used to seed the optimiser in `fit.py` (parameters are fitted in log-space).

| symbol | meaning | bound | fit start |
|---|---|---|---|
| `V0` | pack OCV at start of run [V] | ≥ 0 | 134 |
| `α` (= `dVdQ`) | OCV drop per delivered charge [V/C] | ≥ 0 | 1e-4 |
| `R_int` | pack internal resistance [Ω] | ≥ 0 | 0.10 (assumed) |
| `R` | armature resistance [Ω] | ≥ 0 | 0.17 |
| `L` | armature inductance [H] | > 0 | 0.02 |
| `ke` | back-emf constant [V·s/rad] | – | 0.6 |
| `kt` | torque constant [N·m/A] | – | 1.0 |
| `J` | inertia referred to motor shaft [kg·m²] | ≥ 0 | 0.19 |
| `F0` | Coulomb friction torque at motor shaft [N·m] | ≥ 0 | 3.5 |
| `r` | reduction ratio (motor:output) | fixed | 5.2 (given, not free) |

The fit optimises the **total** electrical resistance `R_tot = R_int + R` and
the **total** referred inertia `J`; see §6 for why the individual splits are not
identifiable. Initial conditions (every run starts from standstill, circuit
closed): `i(0) = 0`, `w(0) = 0`, `Q(0) = 0`.

---

## 3. Fitted parameter values

Obtained by weighted least squares (weights = sensor σ) on the three fitting
experiments only. 95 % confidence intervals from the local
`(JᵀWJ)⁻¹` covariance (reproducible with `fit.py`).

| symbol | value | 95 % CI |
|---|---|---|
| `R_tot = R_int + R` | **0.26846 Ω** | ± 0.002 |
| `ke` | **0.61416 V·s/rad** | ± 0.004 |
| `kt` | **1.15782 N·m/A** | ± 0.0007 |
| `F0` | **3.3268 N·m** | ± 0.04 |
| `L` | **0.022433 H** | ± 0.0002 |
| `J` | **0.191812 kg·m²** | ± 0.0007 |
| `V0` | **133.73 V** | ± 0.95 |
| `α = dVdQ` | **1.0794e-4 V/C** | ± 0.0008e-4 |

Split used in the model (assumption, not identifiable): `R_int = 0.10 Ω`,
`R = 0.16846 Ω` (sum 0.26846 Ω).

Goodness of fit: χ²/dof = 1.034 over 13 998 dof (N = 14 006 samples), i.e. the
residuals sit at the noise level.

---

## 4. Fit metrics (RMSE per output and experiment)

Modelica model (`sim_validate.py`, `cvode`, tol 1e-6) vs the measurements.
Noise σ: 0.5 A on `y_i`, 0.2 rad/s on `y_w`; “% n” = RMSE / σ.

Fitting experiments:

| exp | RMSE `y_i` [A] | (% n) | RMSE `y_w` [rad/s] | (% n) |
|---|---|---|---|---|
| exp1 (20 s) | 0.508 | 101.6 | 0.203 | 101.7 |
| exp2 (120 s) | 0.512 | 102.5 | 0.197 | 98.3 |
| exp3 (1800 s) | 0.514 | 102.9 | 0.204 | 102.1 |

Validation experiment (not used for fitting):

| exp | RMSE `y_i` [A] | (% n) | RMSE `y_w` [rad/s] | (% n) |
|---|---|---|---|---|
| exp4 full (900 s) | 0.511 | 102.1 | 0.197 | 98.3 |
| exp4, transients excluded (±5 s) | 0.509 | 101.8 | 0.197 | 98.5 |

Every metric is at the sensor-noise level, on both the fitting and the unseen
validation data. `fit.py` (independent Python ODE) reproduces the same RMSEs to
the quoted digits.

---

## 5. Physical assumptions (added beyond the description)

The description names the battery, the DC machine, the 5.2 : 1 reduction and the
commanded-torque brake. The following were added as the standard, minimal
physical content of such a rig:

1. **Battery = Thevenin model**: an OCV source in series with an internal
   resistance `R_int`. The OCV declines with the *delivered charge* (state of
   charge), OCV = `V0 − α·Q`, `Q(0)=0` (fresh/serviced pack). This single linear
   term reproduces the documented “speed slowly falls off during long runs and
   the effect disappears after the pack is serviced”: `Q` accumulates during a
   run (lowering the OCV and hence the speed) and is reset when the pack is
   serviced.
2. **Armature inductance `L`** — included in series with `R`; it shapes the
   current run-up transient.
3. **Coulomb friction `F0`** at the motor shaft (`Sources.SignTorque`); a dry
   (velocity-independent) friction, the physically sensible choice for a
   mechanical drive at these speeds.
4. **Rotor inertia `J`** (all of it referred to and placed on the motor shaft).
5. **Back-emf and torque constants `ke`, `kt`** treated as independent
   constants (see §6: the data require `kt/ke ≈ 1.89`).
6. **Ideal, lossless, massless reduction** (MSL `IdealGear`, grounded housing).
7. **Initial state**: standstill, `i=w=Q=0`, circuit closed at `t=0`.
8. **Coulomb sign** regularised smoothly (MSL `Exp`, `w0 = 0.1`) only to make
   the `sgn` numerically well behaved near `w=0`.

---

## 6. Plausible structures and how the data discriminate them

* **Direct battery→machine vs. battery→DC-DC-converter→machine.** A fixed-gain
  converter would only *rescale* the constants seen from the battery terminals
  (voltage gain `g`: effective `R,L` by `g²`, `ke,kt` by `g`) while leaving the
  battery-side model form — and the ratio `ke/kt` — unchanged. The two
  structures are therefore **observationally equivalent**; the data cannot
  separate them. The simpler **direct** model is chosen (the fitted `R, L, ke,
  kt` are then the battery-side effective values).

* **`ke` vs `kt`.** A permanent-magnet machine in SI units would have
  `ke ≈ kt`. The data force **`kt/ke = 1.1578/0.6142 = 1.885`**, and this ratio
  is a genuine machine/effective constant (a converter gain scales both by the
  same `g` and cannot change it). It is consistent with, e.g., a wound-field or
  re-wound machine, or the net effect of the (unobserved) drive stage; it is
  retained as two independently identified constants.

* **Battery-sag structure.** Three candidates were fitted (same 8-parameter
  budget, weighted LS on the 3 fitting experiments; reproducible in `fit.py`):

  | sag model | χ²/dof | exp3 `y_w` RMSE (% n) |
  |---|---|---|
  | none (ideal source) | 23.1 | 1.56 (780 %) |
  | vs time (`V0 − βt`) | 1.070 | 0.214 (107 %) |
  | vs delivered charge (`V0 − αQ`) — chosen | **1.034** | 0.204 (102 %) |

  The no-sag model is decisively rejected (it cannot capture the run-long speed
  drift). Time-based and charge-based both fit near the noise floor, but the
  charge-based model has the lower χ² (Δχ² ≈ 500, same dof) and matches the
  documented “serviced pack” behaviour physically: a recharge resets the
  delivered charge `Q`, i.e. the drift, whereas an elapsed-time sag would not.

* **Friction model.** Coulomb (`F0·sgn(w)`) vs viscous (`c·w`). Adding a viscous
  term pins `c ≈ 0`; Coulomb-only is the supported model.

* **Where to put the inertia.** Rotor-only vs rotor + output drum. Only the
  total referred inertia is identifiable; placing it all on the rotor is the
  minimal representation (equivalent dynamics).

---

## 7. Identifiability — what the data do (not) determine

* **`R_int` + `R` (series resistances).** Only the sum is visible to the current.
  The split is **not identifiable**; `R_int = 0.10 Ω` is fixed as a physically
  reasonable assumption and `R = R_tot − R_int`. The identifiable quantity is
  `R_tot = 0.26846 Ω`.
* **`J` split (rotor vs drum).** Only the referred total `J = 0.19181 kg·m²`
  is identifiable. Modelled as a single rotor inertia.
* **`V0` and `ke`.** Strongly correlated (r ≈ 0.999) because the speed fixes the
  *combination* `(V0 − i·R)/ke`. They are separated only by the OCV sag
  `α·Q`, which depends on the absolute voltage scale. Individually both have
  tight CIs, but the robust observable is the ratio `(V0 − i·R)/ke` (the
  no-load speed constant); interpret `V0`/`ke` with that in mind.
* **`α` (OCV slope) and absolute pack capacity.** Only the effective slope
  `α = dOCV/dQ [V/C]` is identifiable. The runs discharge the pack too little to
  resolve the full OCV curve, so the **absolute capacity is not identifiable**
  (it only enters through the product that is `α`).
* **Viscous friction `c`.** Not identifiable / negligible — pinned to 0.
* **`L` and `J`.** Both identifiable from the run-up transient; moderate
  negative correlation (r ≈ −0.36).

---

## 8. Reproducibility / how to run

```bash
PY=../.venv/bin/python          # venv with numpy, scipy, OMPython
$PY fit.py                       # refit parameters -> params_final.npy (+ CIs)
cd build && $PY ../sim_validate.py   # build+simulate all 4 experiments -> RMSE
```

Solver note: the armature inductance makes the electrical loop stiff at the
run-up. The default `dassl` solver with the default 1e-8 tolerance fails on the
long/high-load profiles; the validation uses `cvode` with tolerance `1e-6`
(passed in `sim_validate.py`), which is more than adequate for a noise floor of
0.5 A / 0.2 rad/s.
