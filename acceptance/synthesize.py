"""Synthesize the measurements of a task from a reference model.

Where no device is at hand, a reference model stands in for it. This tool is
the bench used the other way round: it simulates the reference model on every
experiment of the task file, with the signal sources and settings with which
the bench later grades a delivery, and adds the sensor noise that the task
file states.

    python -m acceptance.synthesize experiments/mytask experiments/mytask/reference.mo --seed 1

For every experiment of the task, and every experiment of every variant, the
tool writes ``data/<experiment>.csv`` (for a variant
``data/variant_<name>_<experiment>.csv``) with the header ``time,u,y_...``:
the output grid of the experiment, the input sampled on it, and every output
with Gaussian noise of the standard deviation ``noise`` from ``[outputs]``.
The noise comes from one generator seeded with ``--seed``, drawn experiment
by experiment in the order of the task file and output by output, so the
seed fixes every file. A variant raises its quantity in the reference model
as the variant test raises it in a delivery (variants.py). Files that exist
are left alone, and their noise is still drawn, so that the other files do
not change; ``--overwrite`` replaces them.
"""
from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from pathlib import Path

import numpy as np

from .bench import Bench, Experiment, Variant, load_task
from .variants import raise_quantity, unreached


def noise_levels(task_dir: Path) -> dict[str, float]:
    """The standard deviation of the sensor noise of every output."""
    with open(task_dir / "task.toml", "rb") as fh:
        outputs = tomllib.load(fh)["outputs"]
    missing = [name for name, o in outputs.items() if "noise" not in o]
    if missing:
        raise ValueError(f"synthesis needs the noise of every output; none for {', '.join(missing)}")
    return {name: float(o["noise"]) for name, o in outputs.items()}


def synthesize(task_dir: str | Path, reference: str | Path, seed: int,
               overwrite: bool = False) -> tuple[list[Path], list[Path]]:
    """Write the data files of a task; returns the files written and the files kept."""
    task_dir = Path(task_dir)
    task = load_task(task_dir)
    levels = noise_levels(task_dir)
    rng = np.random.default_rng(seed)
    jobs: list[tuple[Experiment, Variant | None]] = [(e, None) for e in task.experiments]
    jobs += [(e, v) for v in task.variants for e in v.experiments]
    written, kept = [], []
    with Bench(reference, task) as bench:
        plans: dict[str, dict] = {}
        for experiment, variant in jobs:
            grid = np.linspace(0.0, experiment.stop_time, experiment.intervals + 1)
            noise = {o: rng.normal(0.0, sigma, grid.size) for o, sigma in levels.items()}
            if experiment.data.exists() and not overwrite:
                kept.append(experiment.data)
                continue
            raised: dict[str, float] = {}
            expected: dict[str, float] = {}
            if variant is not None:
                if variant.name not in plans:
                    plans[variant.name] = raise_quantity(task, bench, variant, {})
                plan = plans[variant.name]
                if "reason" in plan:
                    raise RuntimeError(f"variant {variant.name}: {plan['reason']}")
                raised, expected = plan["raised"], plan["expected"]
            traces = bench.simulate(experiment, (task.input, *expected), modifiers=raised)
            if unreached(traces, expected):
                raise RuntimeError(f"variant {variant.name}: the raised value does not reach "
                                   + ", ".join(unreached(traces, expected)))
            columns = {"time": grid, "u": np.interp(grid, traces["time"], traces[task.input])}
            for output in task.outputs:
                columns[output] = np.interp(grid, traces["time"], traces[output]) + noise[output]
            experiment.data.parent.mkdir(parents=True, exist_ok=True)
            with open(experiment.data, "w", encoding="utf-8") as fh:
                fh.write(",".join(columns) + "\n")
                for row in zip(*columns.values()):
                    fh.write(",".join(f"{x:.9g}" for x in row) + "\n")
            written.append(experiment.data)
    return written, kept


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Synthesize the data of a task from a reference model.")
    parser.add_argument("task_dir")
    parser.add_argument("reference", help="Modelica file of the reference model")
    parser.add_argument("--seed", type=int, required=True, help="seed of the noise")
    parser.add_argument("--overwrite", action="store_true", help="replace existing data files")
    parser.add_argument("--verbose", action="store_true",
                        help="show the compiler's warnings on the reference model")
    args = parser.parse_args(argv)
    if not args.verbose:
        logging.getLogger("OMPython").setLevel(logging.ERROR)
    written, kept = synthesize(args.task_dir, args.reference, args.seed, args.overwrite)
    for path in written:
        print(f"wrote {path}")
    if kept:
        print(f"kept {len(kept)} existing files; --overwrite replaces them")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
