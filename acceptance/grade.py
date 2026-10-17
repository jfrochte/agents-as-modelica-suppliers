"""Grade one delivery against one task, layer by layer.

    python -m acceptance.grade experiments/task1 path/to/model.mo \\
        [--reading path/to/reading.toml] [--report path/to/report.md] [--json result.json]

Each layer is recorded separately. Conformance (V1) is the precondition:
without it no further layer is awarded, because the layers above presume the
artefact the task asked for; a layer measured but not awarded keeps its
numbers and reports ``"awarded": false``. A task is solved when V1 and V3
pass, where V3 on the magnet is its feature list (features.py). V2, V4, the
test experiments, the variant test and the report check are recorded beside
them.

The client's reading of the file is one TOML file next to it, with a section
per layer that rests on a reading. Without ``[conformance]`` or
``[parameters]`` the layer stays pending; without ``[report]`` the automatic
part of the report check decides where it can::

    [conformance]                 # V1, see conformance.md
    verdict = "conformant"
    reason = "..."

    [parameters]                  # V2, see parameters.md
    m = { value = 2.0, read = "mass.m" }

    [[invariant.converter]]       # V4, only for a converter rebuilt from sources
    voltage = "backEMF.v"
    ...

    [report]                      # report check, see report.py
    verdict = "consistent"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import tomllib
from pathlib import Path

from .bench import Bench, BenchError, load_task
from .behaviour import ISSUED_ROLES, TEST_ROLE, behaviour, test_experiments
from .conformance import compiler_part, conformance, reading_part
from .features import feature_list
from .invariant import invariant
from .parameters import parameters
from .report import report_check
from .variants import variant_test


def load_reading(reading_file: str | Path | None) -> dict:
    """The client's reading of a delivery, or an empty one."""
    if reading_file is None:
        return {}
    with open(reading_file, "rb") as fh:
        return tomllib.load(fh)


def grade(task_dir: str | Path, model_file: str | Path,
          reading_file: str | Path | None = None,
          report_files: list[str | Path] = ()) -> dict:
    task = load_task(task_dir)
    result = {"task": task.name, "model_file": str(model_file)}
    record = load_reading(reading_file)
    reading = reading_part(record.get("conformance"))

    if not Path(model_file).exists():
        compiler = {"passed": False, "stage": "missing", "message": "no model file delivered"}
        result["V1"] = conformance(compiler, reading)
        result["solved"] = False
        return result

    v2 = parameters(task, record.get("parameters"))
    if report_files or "report" in record:
        result["report"] = report_check(task, record, list(report_files))
    v4 = variants = None
    try:
        with Bench(model_file, task) as bench:
            result["model_class"] = bench.model_class
            traces = {e.name: bench.simulate(e) for e in task.experiments
                      if e.role in ISSUED_ROLES}
            if task.invariant:
                v4 = invariant(task, bench, record.get("invariant"))
            # A test experiment that fails to simulate fails the test, not V1:
            # conformance only asks that the issued experiments run.
            failures = {}
            for e in task.experiments:
                if e.role == TEST_ROLE:
                    try:
                        traces[e.name] = bench.simulate(e)
                    except BenchError as error:
                        failures[e.name] = error.message
            if task.variants:
                variants = variant_test(task, bench, record.get("parameters"))
    except BenchError as error:
        result["V1"] = conformance(compiler_part(error), reading)
        result["V2"] = {**v2, "awarded": False}
        result["solved"] = False
        return result

    v1 = conformance(compiler_part(), reading)
    v2["awarded"] = v1["passed"] is True
    if task.behaviour == "features":
        v3 = feature_list(task, traces)
        v3["residuals_for_comparison"] = behaviour(task, traces)
    else:
        v3 = behaviour(task, traces)
    v3["awarded"] = v1["passed"] is True
    result["V1"] = v1
    result["V2"] = v2
    result["V3"] = v3
    if v4 is not None:
        v4["awarded"] = v1["passed"] is True
        result["V4"] = v4
    if any(e.role == TEST_ROLE for e in task.experiments):
        tests = test_experiments(task, traces, failures)
        tests["awarded"] = v1["passed"] is True
        result["test"] = tests
    if variants is not None:
        variants["awarded"] = v1["passed"] is True
        result["variants"] = variants
    # Solved needs both layers: a failed one decides, a pending reading leaves it open.
    if v1["passed"] is False or v3["passed"] is False:
        result["solved"] = False
    else:
        result["solved"] = None if v1["passed"] is None else True
    return result


def _summary(result: dict) -> str:
    v1 = result["V1"]
    lines = [f"task {result['task']}, class {result.get('model_class', '-')}"]
    compiler = v1["compiler"]
    lines.append("V1 compiler: " + ("passed" if compiler["passed"]
                                    else f"failed at {compiler['stage']}: {compiler['message']}"))
    lines.append("V1 reading:  " + {True: "conformant", False: "not conformant",
                                    None: "pending"}[v1["reading"]["passed"]])
    if "V2" in result:
        lines.extend(_parameter_lines(result["V2"]))
    if "V3" in result:
        v3 = result["V3"]
        awarded = "" if v3["awarded"] else " (not awarded without V1)"
        if v3.get("instrument") == "features":
            lines.append(f"V3 features: {v3['graded']} graded, {v3['missed']} missed, "
                         f"{v3['undetermined']} undetermined: "
                         f"{'passes' if v3['passed'] else 'fails'}" + awarded)
            for f in v3["features"]:
                deviation = ("-" if f["deviation_percent"] is None
                             else f"{f['deviation_percent']:+.1f} %")
                lines.append(f"    {f['experiment']:<16} {f['feature']:<19} {deviation:>9}"
                             f"  tolerance {f['tolerance_percent']:2.0f} %  {f['verdict']}")
            r = v3["residuals_for_comparison"]
            at = r["worst_at"]
            lines.append(f"    for comparison, not part of the verdict: worst residual ratio "
                         f"{r['worst_ratio']:.3f} on {at['output']} in {at['experiment']}")
        else:
            at = v3["worst_at"]
            lines.append(f"V3 worst ratio {v3['worst_ratio']:.3f} on {at['output']} in "
                         f"{at['experiment']}: {'passes' if v3['passed'] else 'fails'} the gate "
                         f"{v3['gate']:.3f}" + awarded)
    if "V4" in result:
        lines.extend(_invariant_lines(result["V4"]))
    if "test" in result:
        t = result["test"]
        awarded = "" if t["awarded"] else " (not awarded without V1)"
        verdict = "pass" if t["passed"] else "fail"
        worst = ("" if t["worst_ratio"] is None else
                 f", worst ratio {t['worst_ratio']:.3f} on {t['worst_at']['output']} "
                 f"in {t['worst_at']['experiment']}")
        lines.append(f"test experiments: {verdict}{worst}" + awarded)
        for name, message in t["failures"].items():
            lines.append(f"    {name} does not simulate: {message}")
    if "variants" in result:
        lines.extend(_variant_lines(result["variants"]))
    if "report" in result:
        r = result["report"]
        verdict = {True: "consistent", False: "not consistent", None: "reading pending"}[r["passed"]]
        lines.append(f"report check: {r['automatic']['status']}; {verdict}")
        for name, value in r["automatic"]["missing"].items():
            lines.append(f"    {name} = {value:.6g} is not named in the report")
    lines.append(f"solved: {result['solved']}")
    return "\n".join(lines)


def _invariant_lines(v4: dict) -> list[str]:
    verdict = {True: "passes", False: "fails", None: "undecided"}[v4["passed"]]
    awarded = "" if v4["awarded"] else " (not awarded without V1)"
    lines = [f"V4 invariant on {v4['experiment']}: {verdict}" + awarded]
    if not v4["converters"]:
        lines.append(f"    {v4['reason']}")
    for c in v4["converters"]:
        if "median_ratio" in c:
            lines.append(f"    {c['instance']:<24} P_mech/P_el = {c['median_ratio']:.4f}, "
                         f"{c['electrical_J'] / 1e3:.3g} kJ in, {c['mechanical_J'] / 1e3:.3g} kJ out: "
                         f"{'passes' if c['passed'] else 'fails'}")
        else:
            lines.append(f"    {c['instance']:<24} {c['reason']}")
    return lines


def _variant_lines(test: dict) -> list[str]:
    verdict = {True: "pass", False: "fail", None: "undecided"}[test["passed"]]
    awarded = "" if test["awarded"] else " (not awarded without V1)"
    lines = [f"variant test: {verdict}" + awarded]
    for name, v in test["variants"].items():
        head = f"    {name:<11} {v['quantity']} x {v['factor']:g}"
        if "experiments" not in v:
            lines.append(f"{head}: {v['reason']}")
            continue
        at = ", ".join(v["raised"])
        if v["carriers"] and v["carriers"] != list(v["raised"]):
            at += f" ({', '.join(v['carriers'])})"
        if v["worst_ratio"] is None:
            lines.append(f"{head} at {at}: no experiment simulates")
        else:
            lines.append(f"{head} at {at}: worst ratio {v['worst_ratio']:.3f} on "
                         f"{v['worst_at']['output']} in {v['worst_at']['experiment']}: "
                         f"{'passes' if v['passed'] else 'fails'}")
        for experiment, message in v["failures"].items():
            lines.append(f"        {experiment} does not simulate: {message}")
    return lines


def _parameter_lines(v2: dict) -> list[str]:
    if not v2["quantities"]:
        return [f"V2 parameters: {v2['reason']}"]
    verdict = {True: "passes", False: "fails", None: "undecided"}[v2["passed"]]
    awarded = "" if v2["awarded"] else " (not awarded without V1)"
    lines = [f"V2 parameters: {verdict}" + awarded]
    for name, q in v2["quantities"].items():
        if "value" not in q:
            lines.append(f"    {name:<6} {q['reason']}")
            continue
        if q["kind"] == "factor":
            measure = f"factor {q['error']:.3g} of at most {q['limit']:g}"
        else:
            within = "beyond the band" if q["kind"] == "band" else "from the reference"
            measure = f"{100 * q['error']:.3g} % {within}, at most {100 * q['limit']:g} %"
        lines.append(f"    {name:<6} {q['value']:<12.6g} {measure}: "
                     f"{'passes' if q['passed'] else 'fails'}")
    return lines


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Grade one delivery against one task.")
    parser.add_argument("task_dir")
    parser.add_argument("model_file")
    parser.add_argument("--reading", help="TOML file with the client's reading of the delivery")
    parser.add_argument("--report", action="append", default=[],
                        help="a report file of the delivery (repeat for several)")
    parser.add_argument("--json", help="write the full result to this file")
    parser.add_argument("--verbose", action="store_true",
                        help="show the compiler's warnings on the delivered model")
    args = parser.parse_args(argv)
    if not args.verbose:
        logging.getLogger("OMPython").setLevel(logging.ERROR)
    result = grade(args.task_dir, args.model_file, args.reading, args.report)
    print(_summary(result))
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
