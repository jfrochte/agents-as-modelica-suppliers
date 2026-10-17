"""Variant test: does the delivered model carry over to a changed device?

A model whose parameters are properties of the device can be adapted to a
variant by changing them; a model that only reproduces the data cannot,
although within the issued range the two can look the same. Each task file
describes variants of the device in which one listed quantity is raised by
half, with data simulated from the reference model with that change. The
test raises the same quantity in the delivered model and grades it on these
data with the gate of the behaviour layer.

The quantity is found through the compiler. A carrier is an instance of a
library type that the task file names, with the parameter that holds the
quantity, such as ``Modelica.Mechanics.Translational.Components.Mass`` with
``m``. When the carrier takes its value from a parameter of the model, as in
``carriage(m = m)``, the test raises that parameter, the one a user would
change; otherwise it raises the carrier's own. Every carrier in the model is
raised, and each simulation checks that every carrier holds its delivered
value times the factor.

The search sees only the carriers the task file names. A model that carries
the quantity, or a part of it, elsewhere needs a reading: its entry under
``[parameters]`` names the parameters to raise with ``at``, relative to the
model class, and takes precedence over the search. They are raised as
named, without a check against the carriers::

    [parameters]
    m = { value = 2.0002, read = "sled.m", at = ["sled.m"] }

The bench raises the parameters through a modification of the instance; the
delivered file stays unchanged. A variant passes when the worst ratio over
its experiments and outputs is at most sqrt(2); an experiment that does not
run to its end fails it. The test passes when every variant passes. A
variant whose carriers are neither found nor read, or whose raised value
does not reach a carrier, is undecided.
"""
from __future__ import annotations

import math
import re

from .behaviour import GATE, output_ratios
from .bench import Bench, BenchError, Task, Variant, delivered

IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


def find_carriers(bench: Bench, variant: Variant) -> tuple[dict[str, str | None], list[str]]:
    """The carriers of the variant's quantity, and carriers that are arrays.

    Returns, for every carrier, the parameter of the model that its value is
    bound to, or None when the binding is not a plain parameter name. A
    component counts as a carrier when its type, or for a delivered class one
    of the classes it extends, is named in the task file.
    """
    carriers: dict[str, str | None] = {}
    arrays: list[str] = []
    for component in bench.components():
        types = [component.type]
        if delivered(component.type):
            types += bench.ancestors(component.type)
        carrier = next((t for t in types if t in variant.carriers), None)
        if carrier is None:
            continue
        parameter = variant.carriers[carrier]
        path = f"{component.path}.{parameter}"
        if component.dimensions:
            arrays.append(path)
            continue
        parent, _, name = component.path.rpartition(".")
        binding = (bench.query(f"getElementModifierValue({component.owner}, {name}.{parameter})")
                   or "").strip()
        carriers[path] = ((f"{parent}.{binding}" if parent else binding)
                          if IDENTIFIER.fullmatch(binding) else None)
    return carriers, arrays


def variant_test(task: Task, bench: Bench, parameter_reading: dict | None) -> dict:
    """Every variant of the task on the delivered model."""
    reading = parameter_reading or {}
    variants = {v.name: _variant(task, bench, v, reading.get(v.quantity, {}))
                for v in task.variants}
    verdicts = [v["passed"] for v in variants.values()]
    passed = False if False in verdicts else (None if None in verdicts else True)
    return {"gate": GATE, "passed": passed, "variants": variants}


def raise_quantity(task: Task, bench: Bench, variant: Variant, entry: dict) -> dict:
    """The parameters that raise the variant's quantity in a model, and their values.

    ``entry`` is the reading of the quantity under ``[parameters]``; without
    ``at`` the carriers are searched. The result holds ``raised`` (parameter
    path -> raised value, for ``Bench.simulate``), ``expected`` (carrier ->
    the value it must then hold) and ``found_by``, or only a ``reason`` why
    the quantity cannot be raised.
    """
    if "at" in entry:
        targets = [entry["at"]] if isinstance(entry["at"], str) else list(entry["at"])
        carriers: dict[str, str | None] = {}
        found_by = "reading"
    else:
        carriers, arrays = find_carriers(bench, variant)
        found_by = "search"
        if arrays:
            return {"reason": f"carriers in an array ({', '.join(arrays)}); "
                              f"a reading names the parameters to raise with `at`"}
        targets = []
    if not targets and not carriers:
        return {"reason": f"no carrier of {variant.quantity} found; "
                          f"a reading names the parameters to raise with `at`"}

    # The values in the model, as the simulation evaluates them.
    bound = [b for b in carriers.values() if b]
    try:
        values = bench.simulate(task.experiments[0],
                                tuple(dict.fromkeys([*targets, *carriers, *bound])))
    except BenchError as error:
        return {"reason": error.message}
    for carrier, binding in carriers.items():
        target = binding if binding in values else carrier
        if target not in targets:
            targets.append(target)
    missing = [p for p in [*targets, *carriers] if p not in values]
    if missing:
        return {"reason": f"not in the result: {', '.join(missing)}"}
    return {"found_by": found_by,
            "delivered": {p: float(values[p][0]) for p in targets},
            "raised": {p: variant.factor * float(values[p][0]) for p in targets},
            "expected": {c: variant.factor * float(values[c][0]) for c in carriers}}


def unreached(simulated: dict, expected: dict[str, float]) -> list[str]:
    """Carriers that do not hold the raised value in a simulation."""
    return [c for c, value in expected.items() if c not in simulated
            or not math.isclose(float(simulated[c][0]), value, rel_tol=1e-9)]


def _variant(task: Task, bench: Bench, variant: Variant, entry: dict) -> dict:
    result = {"quantity": variant.quantity, "factor": variant.factor}
    plan = raise_quantity(task, bench, variant, entry)
    if "reason" in plan:
        return {**result, "passed": None, "reason": plan["reason"]}
    raised, expected = plan["raised"], plan["expected"]
    result["found_by"] = plan["found_by"]
    result["raised"] = {p: {"delivered": plan["delivered"][p], "raised": raised[p]} for p in raised}
    result["carriers"] = list(expected)

    ratios, failures = {}, {}
    for experiment in variant.experiments:
        try:
            simulated = bench.simulate(experiment, tuple(expected), modifiers=raised)
        except BenchError as error:
            failures[experiment.name] = error.message
            continue
        missed = unreached(simulated, expected)
        if missed:
            return {**result, "passed": None,
                    "reason": f"raising {', '.join(raised)} does not reach {', '.join(missed)}"}
        ratios[experiment.name] = {"role": experiment.role,
                                   "outputs": output_ratios(task, experiment, simulated)}
    worst = max(((r["ratio"], (name, output))
                 for name, experiment in ratios.items()
                 for output, r in experiment["outputs"].items()), default=None)
    return {
        **result,
        "worst_ratio": worst[0] if worst else None,
        "worst_at": {"experiment": worst[1][0], "output": worst[1][1]} if worst else None,
        "passed": not failures and worst is not None and worst[0] <= GATE,
        "experiments": ratios,
        "failures": failures,
    }
