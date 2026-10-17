"""Conformance layer V1: the delivery is the artefact the task asked for.

Conformance has three conditions. The model has to translate, its physics has
to be built from components of the library admitted by the task, and it has
to respect the rule on what may represent the physics. The compiler decides
the first: the bench has to load the file, find the class with the required
interface and simulate every issued experiment to its end. A reading of the
file against the rule decides the other two (conformance.md). The reader
records the verdict and its reason in the reading file (see grade.py)::

    [conformance]
    verdict = "conformant"          # or "not conformant"
    reason = "Mass, spring and damper from Translational.Components; ..."

Without that section the reading is pending, and V1 is not awarded.
"""
from __future__ import annotations

VERDICTS = {"conformant": True, "not conformant": False}


def compiler_part(error=None) -> dict:
    """Result of the compiler part, from the bench error or its absence."""
    if error is None:
        return {"passed": True}
    return {"passed": False, "stage": error.stage, "message": error.message}


def reading_part(record: dict | None) -> dict:
    """The recorded reading, or a pending result if there is none."""
    if not record:
        return {"passed": None, "reason": "reading pending"}
    verdict = record.get("verdict", "").strip().lower()
    if verdict not in VERDICTS:
        raise ValueError(f"conformance verdict must be one of {sorted(VERDICTS)}")
    return {"passed": VERDICTS[verdict], "reason": record.get("reason", "")}


def conformance(compiler: dict, reading: dict) -> dict:
    """V1 passes only when both parts pass; a pending reading leaves it open."""
    if not compiler["passed"]:
        passed = False
    else:
        passed = reading["passed"]
    return {"passed": passed, "compiler": compiler, "reading": reading}
