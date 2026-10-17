# Task 5 — Flat-armature switching electromagnet: model and calibration

**Deliverables in `work/`**

| file | content |
|---|---|
| `model.mo` | package `SwitchingMagnet` with the model `FlatArmatureMagnet` (`RealInput u`, `RealOutput y_i, y_x, y_v`), the material record `Material.YokeSteel` and the harness `TestRig` |
| `model_variant_partitionedYoke.mo` | rejected structural variant (see §7) |
| `magcircuit.py` | Python replica of the algebraic magnetic circuit of `model.mo` (used for the fast static fit) |
| `fit_static.py` | stage 1: magnetic circuit from the component characteristics |
| `fit_dynamic.py` | stage 2: mechanics + eddy currents from the fitting experiments |
| `simdrv.py` | runs the compiled `TestRig` with overridden parameters, resamples, computes residuals |
| `fit_joint.py` | stage 3: single joint objective (static characteristics + both fitting experiments) — the numbers below come from this |
| `report_metrics.py` | produces the metrics and the figures |
| `check_diagram.py` | automated check of the diagram layout |
| `make_input_tables.py` | writes `build/u_exp*.txt` (time and `u` only) for the harness |
| `parameters.json` | fitted parameter values in machine-readable form |
| `fit_exp1_fit.png`, `fit_exp2_fit.png`, `fit_exp3_validation.png`, `fit_static.png` | measurement vs. model |

Reproduce with
```
cd work
../../.venv/bin/python make_input_tables.py         # build/u_exp*.txt from data/exp*.csv
cd build && omc build.mos                           # compiles SwitchingMagnet.TestRig
./TestRig -override=fileName=u_exp2_fit.txt -stopTime=0.050035 -stepSize=2e-5 -r=out_exp2.csv
cd .. && ../../.venv/bin/python report_metrics.py --plot --sens
../../.venv/bin/python check_diagram.py
```
Re-running the calibration: `fit_static.py` (≈ 3 min), then
`fit_dynamic.py 500` and `fit_joint.py 500 --reset` repeatedly (≈ 8 min per
call, checkpointed in `/tmp`).

---

## 1. What the data say before any model is written

Six facts were extracted from the measurements first, because they fix the structure.

1. **Coil resistance.** During the flat constant-current hold phases `di/dt ≈ 0` and
   `dx/dt = 0`, hence `u = R·i`. Least squares over the three hold segments
   (exp1 at 6.99 A, exp2 at 3.95 A, exp3 at 7.90 A) gives **R = 0.7943 Ω**
   (individual segments 0.792 / 0.784 / 0.797 Ω).
2. **Flux linkage is directly measurable.** `Ψ(t) = ∫(u − R·i) dt` is exact
   (Faraday's law). Integrated over the whole of each record it returns to
   −0.71 / −0.59 / +0.28 mWb against peak values of 15–17 mWb, i.e. the
   integration closes to 2–4 %, which confirms `R` to about 1 %.
   This gives absolute DC operating points: `Ψ = 15.48 mWb` at (x = 0, 3.95 A),
   `16.42 mWb` at (x ≈ 3 µm, 6.99 A), `10.43 mWb` at (x = 527 µm, 4.28 A),
   `7.96 mWb` at (x ≈ 4 µm, 0.39 A). Six of these were used as fit data.
3. **The return spring is heavily pre-loaded.** After switch-off the armature
   opens with an almost *constant* acceleration of ≈ 950 m/s² over the whole
   0.53 mm stroke. With the 18.6 g moving mass that is ≈ 18–19 N, whereas a
   0.7854 N/mm spring changes by only 0.42 N over the stroke. So the spring must
   be pre-compressed by ≈ 25 mm; the stroke sits on a nearly flat part of its
   characteristic. (Task description gives only the *rate*, not the pre-load.)
4. **The force cannot come from an ideal 1/x² air gap.** The apparent gap area
   `2·F·x²/(µ₀(N·I)²)` rises from 10 mm² at x = 60 µm to 53 mm² at x = 740 µm
   for I = 1 A. Plotting `1/√A_apparent` against `1/x` is a straight line, the
   signature of a **constant reluctance in series with the working gap**. Its
   size, ≈ 1.1·10⁶ A/Wb, is 10–15 times more than the yoke iron can produce with
   the supplied B(H) curve at 1 A (where the iron is at 0.4–0.8 T and far from
   saturation). A residual non-magnetic gap at the pole faces is therefore
   unavoidable — see §6/§7.
5. **The iron saturates at Φ ≈ 1.4·10⁻⁴ Wb.** Eliminating the gap from the static
   map collapses all 280 (x, I) points onto one V(Φ) curve which turns over at
   0.14 mWb, in agreement with the measured `Ψ` at the closed stop
   (16.4 mWb / 131 = 1.25·10⁻⁴ Wb). Divided by a 1.9 T saturation flux density
   this implies a bottleneck cross-section of ≈ 70 mm², much *smaller* than the
   pole faces demanded by item 4 — so the saturating section must be a thin
   radial-flux section (armature disc, yoke bottom), not the pole face.
6. **The flux lags the current.** In exp3 at t = 10.22 ms the flux is
   `Ψ = 9.25 mWb` at `i = 5.74 A`; 0.5 ms later, at the *lower* current
   `4.05 A` (exp2, same gap), it is `10.33 mWb`. Same position, lower current,
   12 % *more* flux — i.e. during a 25 kA/s ramp about a third of the flux is
   missing, and it appears afterwards with a time constant of ≈ 0.2 ms. During
   the ramp itself `dΨ/di` is 1.65 mH, against 2.5 mH in quasi-static
   conditions. The yoke is solid, non-laminated steel, so this is expected:
   treated as one shorted turn around the flux, a path of length
   `π(r_pole+r_wallIn) ≈ 55 mm` through a meridional cross-section of ≈ 82 mm²
   at ρ ≈ 0.2 µΩ·m has a resistance of 0.13 mΩ, i.e. a magnetic loss
   conductance of ≈ 7500 S; divided by the total circuit reluctance
   (5 … 7·10⁶ A/Wb) that is a flux time constant of 1 … 1.5 ms. An
   eddy-current element is mandatory, and its fitted conductance (3500 S, §3)
   is about half of this geometric estimate — the expected order of magnitude
   for a one-turn lump of a distributed diffusion problem.

---

## 2. Model structure

`SwitchingMagnet.FlatArmatureMagnet`, built only from
`Modelica.Magnetic.FluxTubes`, `Modelica.Mechanics.Translational`,
`Modelica.Electrical.Analog` and `Modelica.Blocks`.

```
 u ──► SignalVoltage ── Resistor R_coil ── CurrentSensor ──┐
                                                           │
                       ElectroMagneticConverter (N = 131) ─┘  ──► y_i
                                   │
   central pole  g_mFeCore  (HollowCylinderAxialFlux, non-linear)
                                   │
   working gap   g_mGapCore  (Force.HollowCylinderAxialFlux,  l = x_res + x)
                  ∥  g_mLeakCore (Force.LeakageAroundPoles,   l = x_res + x)
                                   │
   armature disc g_mFeArm   (HollowCylinderRadialFlux, non-linear)
                                   │
   working gap   g_mGapRing  (Force.HollowCylinderAxialFlux,  l = x_res + x)
                  ∥  g_mLeakRing (Force.LeakageAroundPoles,   l = x_res + x)
                                   │
   yoke wall     g_mFeWall  (HollowCylinderAxialFlux, non-linear)
                                   │
   yoke bottom   g_mFeBot   (HollowCylinderRadialFlux, non-linear)
                                   │
   eddy currents eddy       (Basic.EddyCurrent)  ── back to the converter

   g_mLeakWindow (Basic.ConstantPermeance) shunts pole → wall across the coil
   window, in parallel with gap–armature–gap; it carries no force.

   mechanics:  Mass(armature)  ── Spring(c = 785.4 N/m, pre-loaded)
                              ── Damper
                              ── ElastoGap stopClosed  (x = 0)
                              ── ElastoGap stopOpen    (x = x_max)
               PositionSensor ──► y_x     SpeedSensor ──► y_v
```

Distinct components, not one flat network: the coil, the magnetic circuit
(9 flux tubes, an eddy element and a converter), and the armature assembly
(mass, spring, damper, two end stops) are separate, and the armature position
**is** the working air gap, so `y_x` is read directly with a `PositionSensor`.

The four flange-carrying flux tubes (two working gaps, two fringing paths) are
all attached to the armature mass, so the total reluctance force is the sum
of the four `0.5·V_m²·dG_m/dx` contributions computed by the library.

**Tabulated characteristic.** The only table is the material record
`Material.YokeSteel`, a `Modelica.Magnetic.FluxTubes.Material.SoftMagnetic.BaseData`
whose five coefficients were fitted to `data/material_BH.csv`. The quantity it
represents is the **initial magnetisation curve of the yoke/armature steel**,
i.e. flux density B versus field strength H, stored in the form the library
uses, µ_r(B). No table maps time, input, current, position or velocity onto an
output or a force; no transfer function, state-space block or user-written
equation appears. `TestRig` (a separate harness model, not part of the magnet
model) uses a `Blocks.Sources.CombiTimeTable` only to replay the *measured
excitation* `u(t)` from file.

---

## 3. Free parameters, bounds and initial values

Calibration ran in three stages. Stage 1 and 2 only produced the starting point
for stage 3; **all reported values come from the single joint objective of
stage 3** (`fit_joint.py`):

```
J = Σ_{e ∈ {exp1_fit, exp2_fit}} Σ_{c ∈ {y_i, y_x, y_v}}  w_c · mean((sim−meas)²)/std(meas)²
  + mean( ((F_model−F_meas)/(0.05·F_meas+0.3 N))² )            (280 static-force points)
  + (1/6)·mean( ((Ψ_model−Ψ_meas)/σ_Ψ)² )                       (6 DC flux linkages)
```
with `w = 1` for `y_i` and `y_x` and `w = 0.5` for the very spiky `y_v`.
Optimiser: repeated adaptive Nelder–Mead with shrinking initial simplex (the two
unilateral end stops make `J` non-smooth, which defeats finite-difference
Jacobians — a Levenberg–Marquardt attempt stalled after one Jacobian).
`exp3_validation` was never evaluated during any fit.

| # | parameter | meaning | bounds | initial value | fitted |
|---|---|---|---|---|---|
| 1 | `r_pole` | radius of the central pole | 4.0 … 8.0 mm | 6.58 mm | **5.7704 mm** |
| 2 | `r_wallIn` | inner radius of the annular pole / yoke wall | 9.0 … 12.2 mm | 10.63 mm | **11.7224 mm** |
| 3 | `t_yokeBot` | effective radial-flux thickness of the yoke bottom | 0.5 … 6.0 mm | 2.0 mm | **1.0523 mm** |
| 4 | `t_arm` | effective radial-flux thickness of the armature disc | 0.5 … 6.0 mm | 1.3 mm | **1.2236 mm** |
| 5 | `x_res` | residual non-magnetic gap at each pole face | 5 … 120 µm | 94 µm | **32.49 µm** |
| 6 | `r_leak` | radius of the fringing field around the pole faces | 0.2 … 8.0 mm | 1.5 mm | **1.3800 mm** |
| 7 | `G_mLeakWnd` | permeance of the coil-window leakage path | 1·10⁻⁹ … 3·10⁻⁷ H | 5·10⁻⁸ H | **2.2159·10⁻⁸ H** |
| 8 | `A_eddy` | cross-section of the one-turn eddy path | 1 … 120 mm² | 8 mm² | **38.430 mm²** |
| 9 | `R_coil` | coil resistance | 0.780 … 0.810 Ω | 0.79428 Ω | **0.79312 Ω** |
| 10 | `m_arm` | moving mass | 18.6 … 21.2 g | 19.47 g | **19.598 g** |
| 11 | `s_spring0` | spring free length in gap coordinates (sets the pre-load) | 5 … 45 mm | 23.6 mm | **24.821 mm** |
| 12 | `d_arm` | viscous damping of the moving assembly | 0.001 … 40 N·s/m | 0.5 N·s/m | **0.203 N·s/m** |
| 13 | `x_max` | working gap at the open end stop | 500 … 552 µm | 527 µm | **530.09 µm** |
| 14 | `c_stopClosed` | contact stiffness, closed stop | 10⁶ … 10¹⁰ N/m | 10⁸ N/m | **2.784·10⁸ N/m** |
| 15 | `d_stopClosed` | contact damping, closed stop | 5 … 5000 N·s/m | 400 N·s/m | **2520 N·s/m** |
| 16 | `c_stopOpen` | contact stiffness, open stop | 10⁶ … 10¹⁰ N/m | 10⁸ N/m | **8.330·10⁷ N/m** |
| 17 | `d_stopOpen` | contact damping, open stop | 5 … 5000 N·s/m | 400 N·s/m | **1138 N·s/m** |

Bound rationale: geometry bounded by the given 25 mm × 12.5 mm envelope;
`m_arm` bounded below by the stated 18.6 g moving assembly and above by
18.6 g + 2.6 g (whole spring co-moving); `x_max` bounded by the stated
"about 0.53 mm"; `R_coil` bounded by ±2 % of the value measured on the hold
segments; the rest by orders of magnitude.

The five coefficients of `Material.YokeSteel` (`mu_i = 251.681`,
`B_myMax = 0.859115 T`, `c_a = 10543.72`, `c_b = 2.125021`, `n = 7.109318`)
were fitted to `material_BH.csv` **alone** (weighted least squares on H(B),
r.m.s. 2.8 %, max 9.1 %) and then held fixed. Releasing them inside the device
fit changed the static-force r.m.s. from 4.65 % to 4.59 % only, so they were
kept tied to the measured curve.

Fixed, not fitted: `N = 131`, `r_yokeOut = 12.5 mm`, `l_yoke = 12.5 mm`,
`c_spring = 785.4 N/m` (all given), `rho_fe = 0.20 µΩ·m` (literature value for
mild steel; only the product `A_eddy/(rho_fe·l_eddy)` is identified, see §8).

### Derived quantities of the calibrated model

| quantity | value |
|---|---|
| central pole face `A_core = π r_pole²` | 104.61 mm² |
| annular pole face `A_ring = π(r_yokeOut² − r_wallIn²)` | 59.18 mm² |
| series-equivalent gap area `1/A_eff = 1/A_core + 1/A_ring` | **37.79 mm²** |
| armature radial cross-section at mean radius | 68.74 mm² |
| yoke-bottom radial cross-section | 57.83 mm² |
| coil window: width × height | 5.95 mm × 11.97 mm |
| spring pre-load at the closed stop `F_pre = c·s_spring0` | **19.494 N** |
| spring force at the open stop | 19.078 N |
| eddy conductance `G_eddy = A_eddy/(ρ_fe·l_eddy)` | 3497 S (0.286 mΩ one-turn; 4.91 Ω referred to the coil) |
| flux-diffusion time constant `G_eddy/R_m,total` | 0.43 … 0.51 ms (open), 0.77 ms (closed, 4 A) |
| `Ψ/i` at x = 528 µm, 4 A | 2.50 mH (measured 2.55 mH) |
| `Ψ/i` at x = 0, 4 A | 3.76 mH (measured 3.92 mH) |
| flux density when closed at 8 A: core / wall / bottom / armature | 1.23 / 2.17 / 2.22 / 1.81 T |

---

## 4. Fit metrics

All numbers below are produced by simulating `model.mo` **with its default
parameters**, driven by the measured coil voltage of the respective record
(`report_metrics.py`). `y_x` is in µm to keep the table readable.

| record | role | RMSE `y_i` [A] | RMSE `y_x` [µm] | RMSE `y_v` [m/s] |
|---|---|---|---|---|
| `exp1_fit` | fitting | 0.1160 | 9.55 | 0.0378 |
| `exp2_fit` | fitting | 0.5919 | 7.43 | 0.0334 |
| **`exp3_validation`** | **validation only** | **0.6471** | **12.84** | **0.1001** |

Normalised by the standard deviation of the respective measured channel:

| record | `y_i` | `y_x` | `y_v` |
|---|---|---|---|
| `exp1_fit` | 0.081 | 0.043 | 0.505 |
| `exp2_fit` | 0.337 | 0.034 | 0.291 |
| `exp3_validation` | 0.185 | 0.055 | 0.762 |

`exp1_fit`'s velocity channel carries the stated constant offset; it was
estimated from the two at-rest segments of that record as **−3.71 mm/s** and
removed from the measurement before comparison. Against the raw channel the
RMSE is 0.0380 m/s instead of 0.0378 m/s, i.e. the choice is immaterial.

The current RMSE of the two current-controlled records is dominated by 3 % of
the samples, namely ±0.4 ms around the two ±45 V steps of the amplifier
(see §6):

| record | RMSE `y_i` outside the voltage edges | share of samples kept |
|---|---|---|
| `exp1_fit` | 0.1052 A | 99 % |
| `exp2_fit` | 0.1431 A | 97 % |
| `exp3_validation` | 0.1961 A | 97 % |

Switching instants (`y_x` crossing 90 % and 10 % of the stroke), simulation vs.
measurement, in ms:

| record | closing starts | closed | release starts | open |
|---|---|---|---|---|
| `exp1_fit` | 5.400 / 5.400 | 6.200 / 6.200 | 81.80 / 81.10 | 83.00 / 83.10 |
| `exp2_fit` | 11.640 / 11.660 | 12.620 / 12.640 | 24.220 / 24.320 | 25.020 / 25.040 |
| `exp3_validation` | 10.620 / 10.600 | 11.120 / 11.060 | 24.440 / 24.360 | 25.240 / 25.100 |

Component characteristics (`fit_static.png`):

* static force map, 280 points, gaps 60 … 740 µm, 1 … 8 A:
  **r.m.s. relative deviation 4.56 %**, maximum 19.6 %, r.m.s. absolute 1.38 N.
  Per current: 1 A → 11.3 %, 2 A → 3.6 %, 3 A → 2.3 %, 4 A → 2.2 %,
  5 A → 1.8 %, 6 A → 1.1 %, 7 A → 1.7 %, 8 A → 2.8 %.
* DC flux linkages: deviations +5.6 %, +3.7 %, +0.9 %, −2.2 %, −3.1 %, 0.0 %.
* material record vs. `material_BH.csv`: r.m.s. 2.8 %, max 9.1 %.

Data windows used from the static files: only gaps above 60 µm entered the fit,
because near contact the load cell is unloaded and the reading is invalid
(visible as a 40 … 110 N scatter below ≈ 7 µm). Both branches of each file
(towards contact and back) were averaged; they differ by up to ≈ 4 %, which is
the magnetic hysteresis of the steel plus friction in the testing machine and
is the accuracy floor of that data set. In the excluded region 10 … 40 µm the
finished model still agrees to within 11 % (5.8 % r.m.s.).

---

## 5. Sensitivity / identifiability

One-at-a-time scans around the optimum (`report_metrics.py --sens`), reported as
the interval over which `J` rises by less than 5 %:

| parameter | well determined? | interval in which ΔJ < 5 % |
|---|---|---|
| `x_res` | yes, very | ±0.2 µm |
| `r_wallIn` | yes, very | ±5 µm |
| `x_max` | yes, very | −10 / +5 µm |
| `s_spring0` (i.e. `F_pre`) | yes, very | ±0.1 mm, i.e. `F_pre` to ±0.08 N (±0.4 %) |
| `G_mLeakWnd` | yes | ±1·10⁻⁹ H (±4.5 %) |
| `t_yokeBot` | yes | −10 / +20 µm |
| `A_eddy` | yes | ±2 mm² (±5 %), i.e. `G_eddy` to ±180 S |
| `r_pole` | yes | −40 / +80 µm |
| `R_coil` | yes | −5 / +2 mΩ |
| `t_arm` | yes | −20 / +80 µm |
| `r_leak` | yes | ±100 µm |
| `m_arm` | moderately | −1.0 / +0.5 g |
| `c_stopClosed` | only a range | 1·10⁸ … 3·10⁸ N/m. Below ≈ 2·10⁷ N/m the contact penetration reaches 29 µm, comparable to the residual gap, and below 1.5·10⁷ N/m the simulation no longer completes |
| `d_stopClosed` | lower bound only | ≥ 2.5·10³ N·s/m |
| `c_stopOpen` | upper bound only | ≤ 1·10⁸ N/m (1·10⁷ … 8·10⁷ N/m equivalent) |
| `d_stopOpen` | lower bound only | ≥ 1.1·10³ N·s/m |
| `d_arm` | **not identifiable** | any value in 0 … 1 N·s/m fits equally well (ΔJ < 1 %); only the upper bound `d_arm < 1 N·s/m` is supported. Kept at 0.203 N·s/m |

These are **one-at-a-time** intervals: every other parameter is held at its
optimum. They measure the curvature of `J` along one coordinate, not a joint
confidence region. Where parameters are correlated (§8.7) the joint uncertainty
is larger — the very narrow interval of `x_res` in particular reflects the
leverage that this parameter has on the objective, not a claim that the residual
gap of the physical magnet is known to 0.2 µm.

---

## 6. Physical assumptions, and what the model does not reproduce

### Assumptions added beyond the task description

1. **Axisymmetric pot-magnet layout.** The description says "cylinder … with an
   embedded coil" and "flat armature disc above it" but does not give the
   internal geometry. I assumed the standard flat-armature pot magnet: a
   central pole, an annular coil window and an outer wall, both pole faces
   working against the same armature disc, flux returning through the yoke
   bottom. Two working gaps of equal length in series follow from this.
2. **Spring pre-load ≈ 19.5 N.** Only the *rate* is given. The pre-load is a
   fitted parameter; it is the single most sensitive parameter of the model
   (§5) and is fixed to ±0.3 % by the release dynamics.
3. **Orientation / gravity.** Not modelled separately. With the armature above
   the yoke, gravity (0.192 N, 1.0 % of the pre-load) assists closing, i.e. only
   the *combination* `F_pre − m·g` is observable — see §8.
4. **Effective moving mass.** 19.598 g = 18.6 g + 38 % of the 2.6 g spring;
   the classical Rayleigh share for a spring fixed at one end is 33 %, so the
   fitted value is physically consistent. Bounds were set from that argument.
5. **Residual non-magnetic gap of 32.5 µm at each pole face** when the armature
   sits on the closed stop. This is *not* in the description. It is demanded by
   the data (§1.4, §7) and is the model's largest single reluctance at small
   gaps. Any of these produce the same effect and the data cannot separate them:
   a deliberately recessed pole face, an anti-stick shim/coating, pole-face
   flatness and parallelism error, joint reluctances of an assembled yoke, and
   the error of describing a three-dimensional field with a one-dimensional flux
   path. It should be read as an *effective* residual gap of the whole circuit.
6. **Fringing flux** around both pole faces (`LeakageAroundPoles`, one leakage
   radius `r_leak` shared by both poles) and a **coil-window leakage**
   (`ConstantPermeance`) between the central pole and the wall.
7. **Eddy currents lumped into one element** carrying the whole loop flux, with
   its conductance fitted. Resistivity fixed at 0.20 µΩ·m.
8. **Effective, not measured, iron thicknesses.** `t_arm` and `t_yokeBot` are
   the thicknesses of *flux-carrying* radial sections in a one-dimensional
   representation, and they came out around 1.1 … 1.2 mm. They should not be
   read as the physical thickness of the armature disc.
9. **The mechanical end stops** are described only as "two mechanical end
   positions"; I used two unilateral spring-damper contacts (`ElastoGap`) with
   fitted stiffness and damping. Their existence is confirmed by the bounces in
   all three records.
10. **No friction, no hysteresis, no temperature dependence** (a single coil
    resistance describes all three records to 1 %, so self-heating is not
    resolvable in 100 ms).
11. Both current-controlled records are simulated **voltage-driven** with the
    measured coil voltage, as the task prescribes; the amplifier and its
    controller are outside the model.

### Effects present in the data that the model does not reproduce

1. **Current spikes at the amplifier's voltage edges.** At the ±45 V steps of
   exp2/exp3 the model overshoots the current by up to 7 A for ≈ 0.1 ms
   (e.g. exp3 at t = 10.02 ms: 8.2 A simulated vs. 0.8 A measured). The single
   lumped `EddyCurrent` element is, referred to the coil terminals, a resistance
   `N²/G_eddy = 4.9 Ω` in parallel with the magnetising branch, so an applied
   45 V immediately drives ≈ 9 A through it. The measurement contains no such
   shunt on that time scale: 20 µs after the 45 V step the current is 0.82 A, of
   which 0.58 A is accounted for by the measured high-frequency inductance
   (1.65 mH, §1.6), leaving ≈ 0.24 A at ≈ 35 V, i.e. an effective parallel
   resistance of the order of 10² Ω rather than 5 Ω. Yet the *motion* requires
   the slow flux lag that only a strong element produces (§7, variant G). One
   element cannot do both; the real process is flux diffusion with a whole
   spectrum of time constants. This is
   the model's main defect and the reason for the current RMSE of the two
   current-controlled records. Outside these windows the error drops to
   0.14 A / 0.20 A. §7 documents the two-branch alternative that was tried.
2. **Slow release creep.** In exp1 the measured gap drifts from 7 µm to 22 µm
   over 4 ms (t = 77 … 81 ms) before the armature accelerates; the model holds
   until 81 ms and then releases in 1.2 ms. Candidates: magnetic remanence of
   the steel (the model has no hysteresis) and stiction in the armature guide
   (no friction element). The completion of the release is then matched to
   0.1 ms.
3. **Post-impact ringing of the gap signal.** After closing, the measured `y_x`
   oscillates by ±2 … 6 µm at some tens of kHz for the whole hold phase, well
   above the stated 0.6 µm sensor noise. This is very probably an elastic mode of
   the thin armature disc with its needle and reflector; a single rigid mass
   cannot show it. It contributes ≈ 3 µm to the `y_x` RMSE of the hold phases.
4. **Zero offset of the gap channel.** In exp1 the closed position reads
   +4 µm, in exp2/exp3 it reads 0 … −2 µm, and the open rest position differs by
   up to 4 µm between records. The model has one `x_max` for all three; part of
   the residual 9 … 13 µm RMSE in `y_x` is this record-to-record offset.
5. **Static force at 1 A** is over-predicted by up to 20 % at small gaps
   (11.3 % r.m.s. for that current, versus 1 … 3 % for 2 … 8 A). At 1 A the flux
   is small and the result depends on the initial permeability and on the
   residual gap, i.e. on exactly the two quantities the lumped one-dimensional
   description represents least well. The magnet operates at 4 … 8 A in all
   three experiments, so this does not affect the dynamic fit.
6. **Bounce details.** Number, height and decay of the bounces at both end
   stops are reproduced qualitatively but not sample-by-sample; this is the main
   contribution to the `y_v` RMSE (the velocity signal is zero except during
   ≈ 2 ms of each record, so its standard deviation is small and the normalised
   error is correspondingly large).

---

## 7. Alternative structures and how the data discriminate

Each variant was **refitted** (not merely evaluated at the chosen optimum) so
that the comparison is fair. `J_dyn` is the dynamic part of the objective of §3;
the static column is the r.m.s. relative deviation of the 280-point force map
after refitting the seven magnetic parameters.

| variant | static force r.m.s. / max | `J_dyn` | verdict |
|---|---|---|---|
| **(A) chosen structure** | **4.65 % / 20.5 %** | **0.208** | kept |
| (B) residual pole gap forced to 5 µm | 8.52 % / 50.3 % | — | rejected |
| (C) no residual pole gap | 9.43 % / 55.7 % | — | rejected |
| (D) no fringing (`LeakageAroundPoles` removed) | 5.26 % / 22.1 % | — | kept in (A), see below |
| (E) no coil-window leakage | 4.52 % / 19.9 % | — | kept in (A), see below |
| (F) thick armature and yoke bottom (no radial bottleneck) | 4.38 % / 19.3 % | — | see below |
| (G) eddy element weak (`A_eddy` = 2 mm², the value the current edges imply), everything else refitted incl. `d_arm` | 4.55 % / 20.0 % | 0.756 | rejected |
| (H) yoke wall/bottom partitioned into surface layer + eddy-shielded interior (`model_variant_partitionedYoke.mo`) | identical by construction | 0.543 | rejected |

* **Residual pole gap (B, C).** Removing it roughly doubles the static-force
  error and triples the worst-case error. The alternative explanation — that the
  extra series reluctance is iron with a much longer effective path — was tested
  in stage 1 and requires an equivalent iron length of ≈ 165 mm at 72 mm²
  cross-section for a magnet 12.5 mm high, and it also predicts the *wrong shape*:
  a flux-dependent reluctance would make the small-signal inductance at the
  closed stop far larger than the 20 mH that the measurement shows. The data
  need a reluctance that is *constant* at low flux (the residual gap) **and** one
  that saturates (the iron). Both are in the model.
* **Fringing and window leakage (D, E).** Neither is required by the static map
  alone (D costs 0.6 percentage points, E is even marginally better without).
  They are kept because the *dynamic* data determine them: `G_mLeakWnd` is
  identified to ±4 % and `r_leak` to ±90 µm by the joint objective, since they
  control the inductance and hence the current waveform. This is the clearest
  case in this task of a parameter that one data set cannot see and another can.
* **Location of the saturating cross-section (F).** A geometry with a thick
  armature and yoke bottom fits the static map just as well by moving the
  bottleneck into the annular wall instead. The static map therefore fixes the
  *amount* of saturating reluctance but not *where* it sits; the individual
  values of `t_arm`, `t_yokeBot` and `r_wallIn` in the table of §3 are effective
  values of the chosen topology, and the meaningful, structure-independent
  numbers are the series-equivalent gap area `A_eff = 37.8 mm²` and the
  saturation flux `Φ_sat ≈ 1.3 · 10⁻⁴ Wb`.
* **Eddy currents (G, H).** This is where the data are most informative and the
  answer is least comfortable. The motion needs a strong flux lag: forcing
  `A_eddy` down to the value that the current edges imply (2 mm²) and letting the
  optimiser compensate with the viscous damper and everything else raises
  `J_dyn` from 0.208 to 0.756 — the `y_x` RMSE of exp2 then rises from 7.4 µm to
  59.9 µm and that of exp1 from 9.5 µm to 27.4 µm. A linear damper cannot substitute, because the
  eddy element reduces the force in proportion to `G_eddy·dΦ/dx·v` and therefore
  scales with the flux as well as with the velocity. The physically more correct
  refinement — partitioning the solid yoke into a surface layer that the flux
  reaches immediately and an interior in series with the eddy element, as the
  FluxTubes documentation recommends — was implemented
  (`model_variant_partitionedYoke.mo`) and is *worse* (`J_dyn` = 0.543): its
  optimum drives the surface fraction to the lower bound, which reduces it to
  the single-element case again. The reason is that a fixed area split multiplies
  the yoke reluctance by the same factor at every flux level, whereas the real
  skin depth grows as the yoke saturates, so the partition over-blocks the flux
  exactly in the closed, saturated state where the force matters most.
  A ladder of three or more nested sections would be needed; that adds four to
  six parameters that the available records cannot separate, so the single
  element was kept and its consequence documented in §6.

---

## 8. Parameters that are not separately determined

1. **Spring pre-load and weight.** Only the constant net force
   `F_pre − m·g·cos(orientation)` is observable, because both are constant over
   the 0.53 mm stroke. The identified value is
   **`F_pre_net` = 19.494 N at the closed stop, 19.078 N at the open stop**.
   If the magnet was mounted with the armature above the yoke as the description
   suggests, the spring pre-load is 19.494 N + 0.192 N = 19.69 N and the weight
   accounts for 1.0 % of it. Reported as the combination; the model contains the
   spring only.
2. **Eddy-current path.** Only the conductance
   `G_eddy = A_eddy/(ρ_fe·l_eddy) = 3497 S` is identified (equivalently the
   one-turn resistance 0.286 mΩ, or 4.91 Ω referred to the coil).
   `ρ_fe`, `l_eddy` and `A_eddy` are not separately determined; `ρ_fe` was fixed
   at a literature value and `l_eddy` is derived from geometry so that the
   remaining `A_eddy = 38.4 mm²` is interpretable (47 % of the meridional
   cross-section of the yoke, 81.8 mm²). Reported as `G_eddy`.
3. **The two pole-face areas.** The reluctance force depends on
   `1/A_core + 1/A_ring` only, so the static force map fixes the harmonic
   combination `A_eff = 37.79 mm²` but not the split. The split is fixed here
   only indirectly, through the different saturation of the two poles;
   `A_eff` is the trustworthy number.
4. **Viscous damping `d_arm` is not identifiable** (see §5): the data support
   only `d_arm < 1 N·s/m`. It is kept at 0.203 N·s/m. Setting it to zero changes
   no reported metric in the third decimal.
5. **Contact stiffnesses and dampings** are determined only as ranges
   (§5); the bounces constrain the *restitution*, i.e. roughly `d/√(c·m)`, more
   tightly than `c` and `d` individually. Reported as intervals/bounds.
6. **Material behaviour above B = 1.19 T** is an extrapolation of the fitted
   Roters record; `material_BH.csv` ends there, while the model reaches
   2.2 T in the yoke bottom when closed at 8 A. The record gives B = 1.5 T at
   3.65 kA/m and 2.0 T at 26 kA/m. Releasing the record's coefficients inside the
   device fit improved nothing (§3), so no attempt was made to "measure" the
   high-field branch from the force data; the model's behaviour deep in
   saturation rests on this extrapolation and is a stated limitation.
7. **`x_res`, `A_eff` and the coil-window leakage are mildly correlated**: all
   three raise the reluctance at small gaps. The joint objective (static map at
   eight currents plus two dynamic records) separates them to the intervals in
   §5, but a data set with only one excitation level would not.

---

## 9. Diagram usability

All 29 components carry `Placement` annotations and all 38 `connect()`
statements carry `Line` annotations. `check_diagram.py` verifies automatically
that

* every `connect()` has a `Line`;
* 36 of 38 lines start and end exactly on the placement-derived connector
  positions, and the remaining 2 (the electrical and the magnetic ground) end on
  a vertex of another wire of the same connection set;
* all wire segments are axis-parallel;
* no two component icons overlap;
* every icon lies inside the declared diagram extent `{{-240,-170},{360,320}}`.

Layout: the electrical part is on the left, the magnetic loop runs along the
middle of the sheet from the coil (left) through the central pole, the two
working gaps with their fringing paths in parallel above them, the armature, the
yoke wall (right) and the yoke bottom back to the coil, with the eddy-current
element in the return path. The mechanical parts sit on a horizontal bus above
the magnetic circuit; the two output sensors are on the right, the coil-current
sensor feeds `y_i` along the bottom edge.

Output of `check_diagram.py`:

```
components placed        : 29
connect() statements     : 38   (with Line annotation: 38)
end points exact / vertex: 36 / 2      mismatched: 0
non-orthogonal segments  : none
overlapping icons        : none
icons outside the extent : none
DIAGRAM CHECK: OK
```
