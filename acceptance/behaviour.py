"""Behaviour layer V3: residual against noise on the issued experiments.

For every experiment ``e`` the agent was given and every measured output
``j``, the delivered model is simulated with the true input (bench.py),
interpolated onto the measurement times and compared with the measured trace:

    r[e, j] = RMSE[e, j] / sigma[j]

where ``sigma[j]`` is the noise level stated in the task. The layer passes
when the worst ratio over all fitting and validation experiments and all
outputs is at most sqrt(2). For zero-mean noise of variance sigma^2 and a
model error b uncorrelated with it, the expected squared residual is
sigma^2 + b^2, so the gate admits a systematic error up to the size of the
noise and no more.

The magnet is judged on features instead (features.py); its ratios against
the residual scale of its task file are reported for comparison. The test
experiments, which the agent never receives, are graded the same way and
reported beside the layer; one that does not run to its end fails.
"""
from __future__ import annotations

import math

import numpy as np

from .bench import Experiment, Task, read_measurement

GATE = math.sqrt(2.0)
"""Largest admitted ratio of residual RMSE to the stated noise level."""

ISSUED_ROLES = ("fit", "validation")
"""Experiments the agent received; the gate is taken over these."""

TEST_ROLE = "test"
"""Experiments the agent never received."""


def residual_ratios(task: Task, traces: dict[str, dict[str, np.ndarray]],
                    roles: tuple[str, ...] = ISSUED_ROLES) -> dict:
    """RMSE and RMSE/sigma for every experiment of the given roles and every output.

    ``traces`` maps experiment names to the output of ``Bench.simulate``.
    """
    return {experiment.name: {"role": experiment.role,
                              "outputs": output_ratios(task, experiment, traces[experiment.name])}
            for experiment in task.experiments
            if experiment.role in roles and experiment.name in traces}


def output_ratios(task: Task, experiment: Experiment,
                  simulated: dict[str, np.ndarray]) -> dict:
    """RMSE and RMSE/sigma of every output of one simulated experiment."""
    measured = read_measurement(experiment.data)
    per_output = {}
    for output, sigma in task.scale.items():
        y = np.interp(measured["time"], simulated["time"], simulated[output])
        rmse = float(np.sqrt(np.mean((y - measured[output]) ** 2)))
        per_output[output] = {"rmse": rmse, "ratio": rmse / sigma}
    return per_output


def behaviour(task: Task, traces: dict[str, dict[str, np.ndarray]]) -> dict:
    """The behaviour layer: all ratios, the worst one and whether it passes the gate."""
    ratios = residual_ratios(task, traces)
    worst, where = max(
        (values["ratio"], (name, output))
        for name, experiment in ratios.items()
        for output, values in experiment["outputs"].items()
    )
    return {
        "gate": GATE,
        "worst_ratio": worst,
        "worst_at": {"experiment": where[0], "output": where[1]},
        "passed": worst <= GATE,
        "experiments": ratios,
    }


def test_experiments(task: Task, traces: dict[str, dict[str, np.ndarray]],
                     failures: dict[str, str]) -> dict:
    """The test experiments: ratios, the worst one, and whether all pass the gate.

    ``failures`` maps the test experiments that did not simulate to the reason.
    """
    ratios = residual_ratios(task, traces, roles=(TEST_ROLE,))
    worst = max(((values["ratio"], (name, output))
                 for name, experiment in ratios.items()
                 for output, values in experiment["outputs"].items()), default=None)
    return {
        "gate": GATE,
        "worst_ratio": worst[0] if worst else None,
        "worst_at": {"experiment": worst[1][0], "output": worst[1][1]} if worst else None,
        "passed": not failures and worst is not None and worst[0] <= GATE,
        "experiments": ratios,
        "failures": failures,
    }
