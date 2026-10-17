"""Report check: does the delivered file carry what the report states?

The acceptance grades the delivered file, not the report that comes with it.
The two can disagree. A model file can keep the start values of a
calibration while its report states the fitted ones, and such a delivery
fails on behaviour although the supplier reports a good fit. Whether a report
describes its file is not a property of the model's behaviour, so the check
runs beside the layers.

The check has two parts, like conformance. An automatic part looks for every
value of the parameter reading (the values the file carries, see
parameters.md) among the numbers in the report: a value counts as named when
a number in the report agrees with it to 0.5 per cent or equals it rounded to
three significant figures. A quantity that the task file refers to the motor
shaft through a gear (``ratio`` in its entry) is also looked for as referred
to the output shaft. Values of zero (a component left out) and quantities
graded by a factor are not looked for.

The automatic part cannot decide. A round start value such as 1.0 appears in
almost every report, as a bound or a start value, even when the report states
a different fitted value. Two kinds of delivery therefore need a reading: one
with a value that the report does not name, and one whose values all have at
most two significant figures. The reader records the verdict in the reading
file::

    [report]
    verdict = "consistent"        # or "not consistent"
    reason = "report.md states m = 1.9999, c = 7.9977, d = 0.8008; the file carries them"
"""
from __future__ import annotations

import re
from pathlib import Path

from .bench import Task

NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?(?![\w.]*[A-Za-z_])")
DECIMAL_COMMA = re.compile(r"(?<=\d),(?=\d)")
RELATIVE = 0.005
"""Relative agreement at which a number in the report names a value."""

VERDICTS = {"consistent": True, "not consistent": False}


def numbers(text: str) -> list[float]:
    """Every number in a text; decimal commas are read as points."""
    found = []
    for token in NUMBER.findall(DECIMAL_COMMA.sub(".", text)):
        try:
            found.append(float(token))
        except ValueError:
            pass
    return found


def _three_figures(x: float) -> float:
    return float("%.3g" % x)


def _figures(x: float) -> int:
    return len(("%.6g" % abs(x)).replace(".", "").lstrip("0").rstrip("0"))


def named(value: float, candidates: list[float], ratio: float | None = None) -> bool:
    """Whether a number among the candidates names the value."""
    for v in [value] + ([value * ratio ** 2] if ratio else []):
        for z in candidates:
            if abs(z - v) <= RELATIVE * abs(v) or (z != 0 and _three_figures(z) == _three_figures(v)):
                return True
    return False


def automatic_part(task: Task, parameter_reading: dict | None,
                   report_files: list[str | Path]) -> dict:
    """Which values the file carries are named in the report."""
    values = {name: float(entry["value"]) for name, entry in (parameter_reading or {}).items()
              if "value" in entry}
    values = {n: v for n, v in values.items()
              if v != 0 and "factor" not in task.parameters.get(n, {})}
    if not values:
        return {"status": "no values read", "missing": {}}
    if not report_files:
        return {"status": "no report", "missing": {}}
    texts = [Path(f).read_text(encoding="utf-8", errors="replace") for f in report_files]
    candidates = [z for t in texts for z in numbers(t)]
    missing = {n: v for n, v in values.items()
               if not named(v, candidates, task.parameters.get(n, {}).get("ratio"))}
    if missing:
        status = "a value is not named in the report"
    elif all(_figures(v) <= 2 for v in values.values()):
        status = "only round values"
    else:
        status = "every value is named"
    return {"status": status, "missing": missing, "values": values,
            "report_files": [str(f) for f in report_files]}


def report_check(task: Task, record: dict, report_files: list[str | Path]) -> dict:
    """Automatic part and recorded reading of the report check."""
    automatic = automatic_part(task, record.get("parameters"), report_files)
    reading = record.get("report")
    if reading:
        verdict = reading.get("verdict", "").strip().lower()
        if verdict not in VERDICTS:
            raise ValueError(f"report verdict must be one of {sorted(VERDICTS)}")
        passed, reason = VERDICTS[verdict], reading.get("reason", "")
    else:
        passed = True if automatic["status"] == "every value is named" else None
        reason = "" if passed else "reading pending"
    return {"passed": passed, "reason": reason, "automatic": automatic}
