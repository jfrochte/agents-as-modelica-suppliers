"""Behaviour layer V3 of the magnet (task 5): a list of nine features.

The magnet is a real device, and its data are laboratory measurements, not a
model plus noise. No lumped network reproduces such a device in every detail:
a bounce after an off-centre impact, for instance, can shift an edge in time
without making the model any less valid. A residual over a trace with sharp
edges is, moreover, dominated by where the edges lie. The behaviour layer on
the magnet therefore asks what a switching magnet is for: whether each
switching event happens at the right time and with the right shape. It reads
nine features from the measured traces and, by the same rules, from the
simulated ones, and compares each pair within a stated tolerance.

The nine graded features
------------------------

=======================  ===========================  =========  =========
Feature                  Experiment                   Measured   Tolerance
=======================  ===========================  =========  =========
closing time             exp1_fit, 6 V                3.90 ms    +-20 %
closing time             exp2_fit, 4 A                2.64 ms    +-20 %
closing time             exp3_validation, 8 A         1.06 ms    +-20 %
release time             exp2_fit, 4 A                1.68 ms    +-25 %
release time             exp3_validation, 8 A         1.76 ms    +-25 %
plateau current          exp1_fit, 6 V                6.82 A     +-5 %
peak closing speed       exp1_fit, 6 V                -1.01 m/s  +-30 %
peak closing speed       exp2_fit, 4 A                -1.08 m/s  +-30 %
peak closing speed       exp3_validation, 8 A         -1.68 m/s  +-30 %
=======================  ===========================  =========  =========

exp1_fit is voltage-controlled, exp2_fit and exp3_validation are
current-controlled. The measured values are not stored: they are read from
the data files by the same rules as the model's values, every time the layer
runs.

How a feature is read from a trace
----------------------------------

All four quantities are read from the coil current ``y_i``, the working air
gap ``y_x`` and the armature speed ``y_v`` at the sampling instants of the
measurement. The simulated traces are first interpolated linearly onto those
instants, so that both sides are read on the same grid.

plateau current
    The mean current inside the experiment's plateau window (exclusive of
    the window's ends): 7 to 10.5 ms in the voltage-controlled experiment,
    15 to 22 ms in the current-controlled ones. The plateau also sets the
    thresholds of switch-on and switch-off.
switch-on
    The first instant at which the current exceeds 10 % of the plateau.
switch-off
    The first instant after the plateau window at which the current falls
    below 50 % of the plateau.
closing time
    From switch-on to the first later instant at which the gap is below
    30 micrometres: the armature counts as closed there.
release time
    From switch-off to the first later instant at which the gap exceeds
    0.5 mm: the armature counts as open there. The stroke is about 0.53 mm.
peak closing speed
    The most negative speed between switch-on and the first contact, both
    included, that is the speed at which the armature strikes. Reading it
    over the flight only, not over the whole trace, keeps a later bounce of
    a poor model from being taken for the impact.

The release time of the voltage-controlled experiment is not graded: there
the armature is held at a low current whose force barely exceeds the preload
of the return spring, and the instant of release depends too strongly on
that balance to serve as a number.

The verdict
-----------

For each feature the layer computes the relative deviation of the model's
value from the measured one, 100 (model - measured) / |measured| per cent.
A feature is ``met`` when the deviation lies within the tolerance and
``missed`` when it does not. When the simulated trace never reaches the
state that a feature needs, for instance an armature that never opens again,
the feature has no value and is ``undetermined``. The layer passes only when
all nine are met.

The list, its tolerances and the reading rules are frozen; changing any of
them changes the acceptance. Static forces are not graded, since the
required interface has no flange at which the bench could hold the armature
at a given gap, and neither are qualitative signatures such as the bounce
after the first impact.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .bench import Task, read_measurement

SWITCH_ON_FRACTION = 0.1
"""Switch-on: the current exceeds this fraction of its plateau."""

SWITCH_OFF_FRACTION = 0.5
"""Switch-off: after the plateau window, the current falls below this fraction."""

CLOSED_GAP = 30e-6
"""Gap in m below which the armature counts as closed."""

OPEN_GAP = 0.5e-3
"""Gap in m above which the armature counts as open."""

PLATEAU_WINDOW = {
    "exp1_fit": (7e-3, 10.5e-3),
    "exp2_fit": (15e-3, 22e-3),
    "exp3_validation": (15e-3, 22e-3),
}
"""Window in s over which the plateau current of each experiment is averaged."""

UNITS = {"closing_time": "s", "release_time": "s",
         "plateau_current": "A", "peak_closing_speed": "m/s"}


@dataclass(frozen=True)
class Feature:
    """One graded feature: a quantity read from one experiment."""

    experiment: str
    quantity: str        # a key of UNITS
    tolerance: float     # admitted relative deviation from the measurement, in per cent


FEATURES = (
    Feature("exp1_fit", "closing_time", 20.0),
    Feature("exp2_fit", "closing_time", 20.0),
    Feature("exp3_validation", "closing_time", 20.0),
    Feature("exp2_fit", "release_time", 25.0),
    Feature("exp3_validation", "release_time", 25.0),
    Feature("exp1_fit", "plateau_current", 5.0),
    Feature("exp1_fit", "peak_closing_speed", 30.0),
    Feature("exp2_fit", "peak_closing_speed", 30.0),
    Feature("exp3_validation", "peak_closing_speed", 30.0),
)
"""The frozen list of the nine graded features with their tolerances."""


def _first(time: np.ndarray, condition: np.ndarray) -> float:
    """The first instant at which the condition holds; NaN if it never does."""
    hits = np.flatnonzero(condition)
    return time[hits[0]] if hits.size else math.nan


def read_trace(time: np.ndarray, current: np.ndarray, gap: np.ndarray,
               speed: np.ndarray, window: tuple[float, float]) -> dict[str, float]:
    """The four quantities of one experiment's traces; NaN where a state is never reached."""
    plateau = current[(time > window[0]) & (time < window[1])].mean()
    switch_on = _first(time, current > SWITCH_ON_FRACTION * plateau)
    switch_off = _first(time, (time > window[1]) & (current < SWITCH_OFF_FRACTION * plateau))
    closed = _first(time, (time > switch_on) & (gap < CLOSED_GAP))
    opened = _first(time, (time > switch_off) & (gap > OPEN_GAP))
    flight = (time >= switch_on) & (time <= closed)
    return {
        "plateau_current": float(plateau),
        "closing_time": float(closed - switch_on),
        "release_time": float(opened - switch_off),
        "peak_closing_speed": float(speed[flight].min()) if flight.any() else math.nan,
    }


def feature_list(task: Task, traces: dict[str, dict[str, np.ndarray]]) -> dict:
    """The behaviour layer of the magnet: every feature, its verdict, and the layer's.

    ``traces`` maps experiment names to the output of ``Bench.simulate``.
    """
    measured, simulated = {}, {}
    for experiment in task.experiments:
        if experiment.name not in PLATEAU_WINDOW:
            continue
        data = read_measurement(experiment.data)
        sim = traces[experiment.name]
        time = data["time"]
        window = PLATEAU_WINDOW[experiment.name]
        measured[experiment.name] = read_trace(
            time, data["y_i"], data["y_x"], data["y_v"], window)
        simulated[experiment.name] = read_trace(
            time, *(np.interp(time, sim["time"], sim[o]) for o in ("y_i", "y_x", "y_v")),
            window)

    rows = []
    for feature in FEATURES:
        value = measured[feature.experiment][feature.quantity]
        model = simulated[feature.experiment][feature.quantity]
        deviation = 100.0 * (model - value) / abs(value) if value else math.nan
        if math.isnan(deviation):
            verdict = "undetermined"
        else:
            verdict = "met" if abs(deviation) <= feature.tolerance else "missed"
        rows.append({
            "experiment": feature.experiment,
            "feature": feature.quantity,
            "unit": UNITS[feature.quantity],
            "measured": value,
            "model": None if math.isnan(model) else model,
            "deviation_percent": None if math.isnan(deviation) else deviation,
            "tolerance_percent": feature.tolerance,
            "verdict": verdict,
        })
    missed = sum(r["verdict"] == "missed" for r in rows)
    undetermined = sum(r["verdict"] == "undetermined" for r in rows)
    return {
        "instrument": "features",
        "graded": len(rows),
        "missed": missed,
        "undetermined": undetermined,
        "passed": missed == 0 and undetermined == 0,
        "features": rows,
    }
