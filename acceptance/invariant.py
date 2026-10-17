"""Invariant layer V4: the converter neither creates nor destroys energy.

In general the invariant is a power balance over the whole model. On the tasks
with an electromechanical converter, the acceptance checks its simplest form.
An ideal converter neither stores nor dissipates energy, so at every instant
the mechanical power it delivers equals the electrical power it takes::

    |P_mech / P_el| = |tau * w| / |v * i| = 1

A model that couples the two domains through a converter of the library
satisfies this by construction. A model that rebuilds the coupling from
signal-driven sources, a voltage source driven by the speed and a torque
source driven by the current, satisfies it only if the two constants agree.
Otherwise it creates or destroys energy, and its outputs can still match the
data, since current and speed do not reveal the ratio of the constants.

The layer simulates the experiment that the task file names under
``[invariant]`` and takes the median of |P_mech / P_el| over the output
instants at which electrical power flows (|P_el| above 1e-6 of its largest
value, or of 1 W). A converter passes when the median differs from one by at
most one per cent; every converter in the model has to pass. When no power
flows, the layer is undecided. The energies that flow on each side,
integrals of |P|, are reported beside the ratio.

Converters of the library are found through the compiler: every instance of
a type in CONVERTERS, in the delivered classes and inside the machine models
of the library. A converter rebuilt from sources has no type to look for, so
the reader names its four variables in the reading file::

    [[invariant.converter]]
    voltage = "backEMF.v"      # relative to the model class
    current = "backEMF.i"
    torque = "torqueSource.tau"
    speed = "speedSensor.w"
    read = "back EMF as a voltage source driven by the speed, torque source driven by the current"

Without a converter of either kind the layer is undecided.
"""
from __future__ import annotations

import numpy as np

from .bench import Bench, Task

TOLERANCE = 0.01
"""Largest admitted deviation of the median power ratio from one."""

CONVERTERS = {
    # type: names of voltage, current, torque and speed inside the instance
    "Modelica.Electrical.Analog.Basic.RotationalEMF": ("v", "i", "tau", "w"),
    "Modelica.Electrical.Machines.BasicMachines.Components.AirGapDC":
        ("vai", "ia", "tauElectrical", "w"),
}

HOSTS = ("Modelica.Electrical.Machines.",)
"""Library packages whose models contain a converter and are searched."""


def find_converters(bench: Bench) -> list[dict]:
    """Every converter of the library in the delivered model class."""
    found: dict[str, dict] = {}
    for component in bench.components(descend=_searched):
        if component.type in CONVERTERS:
            voltage, current, torque, speed = (f"{component.path}.{v}"
                                               for v in CONVERTERS[component.type])
            found[component.path] = {"instance": component.path, "type": component.type,
                                     "voltage": voltage, "current": current,
                                     "torque": torque, "speed": speed}
    return list(found.values())


def _searched(typ: str) -> bool:
    """Delivered classes and the machine models of the library, without the converters."""
    return (not typ.startswith("Modelica") or typ.startswith(HOSTS)) and typ not in CONVERTERS


def power_ratio(traces: dict, converter: dict) -> dict:
    """Median power ratio and energies of one converter on one simulation."""
    names = [converter[k] for k in ("voltage", "current", "torque", "speed")]
    missing = [n for n in names if n not in traces]
    if missing:
        return {"passed": None, "reason": f"not in the result: {', '.join(missing)}"}
    t = traces["time"]
    v, i, tau, w = (np.asarray(traces[n], dtype=float) for n in names)
    p_el, p_mech = v * i, tau * w
    flowing = np.abs(p_el) > 1e-6 * max(1.0, float(np.abs(p_el).max()))
    energies = {"electrical_J": float(np.trapezoid(np.abs(p_el), t)),
                "mechanical_J": float(np.trapezoid(np.abs(p_mech), t))}
    if not flowing.any():
        return {"passed": None, "reason": "no electrical power flows", **energies}
    ratio = np.abs(p_mech[flowing] / p_el[flowing])
    median = float(np.median(ratio))
    return {"passed": abs(median - 1.0) <= TOLERANCE, "median_ratio": median,
            "min_ratio": float(ratio.min()), "max_ratio": float(ratio.max()), **energies}


def invariant(task: Task, bench: Bench, reading: dict | None) -> dict:
    """The invariant layer on the experiment named in the task file."""
    name = task.invariant["experiment"]
    experiment = next(e for e in task.experiments if e.name == name)
    converters = find_converters(bench)
    for entry in (reading or {}).get("converter", ()):
        missing = [k for k in ("voltage", "current", "torque", "speed") if k not in entry]
        if missing:
            raise ValueError(f"[[invariant.converter]] in the reading lacks {', '.join(missing)}")
        converters.append({"instance": "rebuilt", "type": "read", "read": entry.get("read", ""),
                           **{k: entry[k] for k in ("voltage", "current", "torque", "speed")}})
    if not converters:
        return {"passed": None, "experiment": name, "converters": [],
                "reason": "no converter found; a converter rebuilt from sources needs a reading"}
    variables = tuple(converter[k] for converter in converters
                      for k in ("voltage", "current", "torque", "speed"))
    traces = bench.simulate(experiment, variables)
    for converter in converters:
        converter.update(power_ratio(traces, converter))
    verdicts = [c["passed"] for c in converters]
    passed = False if False in verdicts else (None if None in verdicts else True)
    return {"passed": passed, "experiment": name, "tolerance": TOLERANCE,
            "converters": converters}
