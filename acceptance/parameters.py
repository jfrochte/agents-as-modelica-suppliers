"""Parameter layer V2: the delivered model carries the device's values.

Each task lists the quantities that a model of the device has to carry, each
with an independent value (``[parameters]`` in its task file). Where the
experiments cannot separate single parameters, the listed quantity is the
combination they do determine, for instance an inertia referred to the motor
shaft. A quantity is graded in one of three ways:

* a relative tolerance around a reference value::

      error = |value - reference| / |reference|  <=  tolerance

* a band, where the measurements of a real device give a range rather than a
  point, with a tolerance beyond its edges::

      error = distance from the band / nearer edge  <=  tolerance

* a factor, for a quantity that the data determine only weakly by design::

      max(value / reference, reference / value)  <=  factor

The layer passes when every listed quantity passes. A value exactly on the
edge passes; the comparison allows for floating-point rounding and nothing
more.

Which value in the delivered file is which quantity cannot be read off the
names, so the assignment is a reading, recorded in the reading file next to
the delivery. parameters.md is the checklist, including how to read a
component that the model leaves out and a quantity without counterpart::

    [parameters]
    m = { value = 2.0, read = "mass.m in the model class" }
    L = { value = 0.0, read = "no inductor in the armature circuit" }

An entry without a value, or a quantity not read, leaves the layer
undecided, even when another quantity fails, and each quantity still shows
its own verdict. A quantity without counterpart means that the model is
parametrised differently from the device, and its other values are then
not comparable with the reference as a set: a model that splits one
constant into two, for instance, fixes voltage, resistance and inductance
only up to a common factor. Without a reading the layer is pending.
"""
from __future__ import annotations

import math

from .bench import Task

SLACK = 1e-9
"""Relative allowance for floating-point rounding at the edge of a tolerance."""


def _error(spec: dict, value: float) -> tuple[float, float, str]:
    """Error of one value, its limit, and the kind of comparison."""
    if "band" in spec:
        low, high = spec["band"]
        if value < low:
            error = (low - value) / low
        elif value > high:
            error = (value - high) / high
        else:
            error = 0.0
        return error, spec["tolerance"], "band"
    reference = spec["reference"]
    if "factor" in spec:
        error = max(value / reference, reference / value) if value > 0 else math.inf
        return error, spec["factor"], "factor"
    return abs(value - reference) / abs(reference), spec["tolerance"], "tolerance"


def grade_quantity(spec: dict, entry: dict | None) -> dict:
    """Verdict on one listed quantity: True, False, or None if it has no value."""
    if entry is None:
        return {"passed": None, "reason": "not read"}
    if "value" not in entry:
        return {"passed": None, "reason": "no counterpart in the model",
                "read": entry.get("read", "")}
    value = float(entry["value"])
    error, limit, kind = _error(spec, value)
    return {"passed": error <= limit * (1.0 + SLACK), "value": value, "kind": kind,
            "error": error, "limit": limit, "read": entry.get("read", "")}


def parameters(task: Task, reading: dict | None) -> dict:
    """The parameter layer: one verdict per listed quantity, and the layer's."""
    if reading is None:
        return {"passed": None, "reason": "reading pending", "quantities": {}}
    unknown = sorted(set(reading) - set(task.parameters))
    if unknown:
        raise ValueError(f"parameters not listed for {task.name}: {unknown}")
    quantities = {name: grade_quantity(spec, reading.get(name))
                  for name, spec in task.parameters.items()}
    verdicts = [q["passed"] for q in quantities.values()]
    if None in verdicts:
        passed, reason = None, "a listed quantity has no value"
    else:
        passed, reason = all(verdicts), ""
    return {"passed": passed, "reason": reason, "quantities": quantities}
