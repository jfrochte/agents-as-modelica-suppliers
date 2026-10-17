"""Test bench of the acceptance: drive a delivered model with the true input.

Every layer that simulates a delivery uses this bench. It loads the file with
the Modelica Standard Library, finds the class that declares the task's input
as ``Modelica.Blocks.Interfaces.RealInput`` and every measured output as
``RealOutput`` (a delivery may be a package with helper classes), connects it
to the signal source that produced the data of each experiment, and simulates
it under one fixed setting for every delivery.

The bench uses the true input, not the sampled column ``u`` of the data
files. The agent sees only the samples and has to reconstruct the input, and
a reconstruction by linear interpolation can delay the edges of a pulse
enough to leave a correct model far above the noise. The acceptance judges
the model, not that reconstruction. Where the input is itself a recording,
as on the magnet, the source is a table of the recorded samples.

To check from the command line that a delivery can be driven::

    python -m acceptance.bench experiments/task1 path/to/model.mo
"""
from __future__ import annotations

import dataclasses
import re
import sys
import tempfile
import tomllib
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from OMPython import OMCSessionException, OMCSessionZMQ

MSL_VERSION = "4.1.0"
"""Version of the Modelica Standard Library the deliveries are built against."""

TOLERANCE = 1e-8
"""Relative tolerance of the integrator, fixed for every delivery."""

SEARCH_DEPTH = 3
"""How deep the bench descends into packages when it looks for the interface."""

COMPONENT_DEPTH = 12
"""How deep the bench descends into components when it lists them."""

DATA_PLACEHOLDER = "{data}"
"""Stands for the task's data directory in a source declaration (see load_task)."""

BEHAVIOUR_LAYERS = ("residual", "features")
"""Behaviour layers a task can name: the residual gate or a list of features."""


class BenchError(Exception):
    """A delivery that the bench cannot drive.

    ``stage`` says where it failed: ``"load"`` (the file does not load),
    ``"interface"`` (no class carries the required interface) or
    ``"simulate"`` (an experiment does not simulate to the end).
    """

    def __init__(self, stage: str, message: str):
        super().__init__(f"{stage}: {message}")
        self.stage = stage
        self.message = message


@dataclass(frozen=True)
class Experiment:
    """One experiment of a task, as described in its task file."""

    name: str
    role: str                  # "fit", "validation", "test" or "variant"
    stop_time: float           # simulated time span in s, starting at 0
    intervals: int             # number of output intervals of the simulation
    source: tuple[str, ...]    # Modelica declarations of the signal source
    wiring: tuple[str, ...]    # connections inside a composite source
    signal: str                # source output that drives the model input
    data: Path                 # measured traces, CSV with header time,u,y_...


@dataclass(frozen=True)
class Variant:
    """A variant of the device with one listed quantity changed (variants.py)."""

    name: str
    quantity: str              # a quantity listed under [parameters]
    factor: float              # the variant multiplies the quantity by this factor
    carriers: dict[str, str]   # library type -> its parameter that carries the quantity
    experiments: tuple[Experiment, ...]  # experiments of the task, on the variant's data


@dataclass(frozen=True)
class Task:
    """What the acceptance needs to know about a task."""

    name: str
    input: str                 # name of the RealInput, "u" in every task
    scale: dict[str, float]    # measured output -> scale of its residual (see load_task)
    behaviour: str             # behaviour layer that grades the task, one of BEHAVIOUR_LAYERS
    experiments: tuple[Experiment, ...]
    parameters: dict[str, dict]  # listed quantity -> reference or band (parameters.py)
    invariant: dict[str, str]    # experiment on which the converter is checked (invariant.py)
    variants: tuple[Variant, ...] = ()  # variants of the device (variants.py)

    @property
    def outputs(self) -> tuple[str, ...]:
        return tuple(self.scale)


def load_task(task_dir: str | Path) -> Task:
    """Read ``task.toml`` from a task directory (see experiments/README.md).

    Every measured output states the scale against which its residual is
    expressed: ``noise``, the standard deviation of the sensor noise, on the
    synthetic tasks, or ``residual_scale`` on a task with laboratory data,
    where the sensor noise is no target a model of the device could reach.

    A source declaration may read a file from the task's data directory, such
    as the table of a recorded input. It names that directory ``{data}``, and
    the placeholder is replaced here by the absolute path, because the bench
    simulates in an empty working directory.
    """
    task_dir = Path(task_dir)
    with open(task_dir / "task.toml", "rb") as fh:
        spec = tomllib.load(fh)
    data_dir = (task_dir / "data").resolve().as_posix()
    experiments = tuple(
        Experiment(
            name=name,
            role=e["role"],
            stop_time=float(e["stop_time"]),
            intervals=int(e["intervals"]),
            source=tuple(d.replace(DATA_PLACEHOLDER, data_dir) for d in e["source"]),
            wiring=tuple(e.get("wiring", ())),
            signal=e["signal"],
            data=task_dir / "data" / f"{name}.csv",
        )
        for name, e in spec["experiments"].items()
    )
    scale = {name: float(o["noise"] if "noise" in o else o["residual_scale"])
             for name, o in spec["outputs"].items()}
    behaviour = spec.get("behaviour", "residual")
    if behaviour not in BEHAVIOUR_LAYERS:
        raise ValueError(f"{task_dir}: behaviour must be one of {BEHAVIOUR_LAYERS}")
    by_name = {e.name: e for e in experiments}
    variants = tuple(
        Variant(
            name=name,
            quantity=v["quantity"],
            factor=float(v["factor"]),
            carriers=dict(c.rsplit(".", 1) for c in v["carriers"]),
            experiments=tuple(
                dataclasses.replace(by_name[e], role="variant",
                                    data=task_dir / "data" / f"variant_{name}_{e}.csv")
                for e in v["experiments"]),
        )
        for name, v in spec.get("variants", {}).items()
    )
    return Task(name=spec["name"], input=spec["input"], scale=scale,
                behaviour=behaviour, experiments=experiments,
                parameters=spec.get("parameters", {}),
                invariant=spec.get("invariant", {}), variants=variants)


def read_measurement(path: Path) -> dict[str, np.ndarray]:
    """Measured traces of one experiment, one array per CSV column."""
    table = np.genfromtxt(path, delimiter=",", names=True)
    return {name: np.asarray(table[name]) for name in table.dtype.names}


@dataclass(frozen=True)
class Component:
    """A component of the delivered model, found by Bench.components."""

    path: str                  # relative to the model class, "drive.emf"
    type: str                  # fully qualified type
    dimensions: tuple          # array dimensions, empty for a scalar
    owner: str                 # the class whose declarations contain it


def delivered(typ: str) -> bool:
    """Whether a type is one of the delivered classes, not of the library."""
    return not typ.startswith("Modelica")


def _modification(values: dict[str, float]) -> str:
    """A Modelica modification that sets parameters given by their paths.

    ``{"carriage.m": 3.0, "c": 12.0}`` becomes ``(carriage(m = 3.0), c = 12.0)``.
    """
    tree: dict = {}
    for path, value in values.items():
        *outer, last = path.split(".")
        node = tree
        for name in outer:
            node = node.setdefault(name, {})
        node[last] = float(value)

    def render(node: dict) -> str:
        return ", ".join(f"{name}({render(sub)})" if isinstance(sub, dict) else f"{name} = {sub!r}"
                         for name, sub in node.items())

    return f"({render(tree)})" if tree else ""


def _strip_strings(source: str) -> str:
    """Empty every string literal, so that documentation text is not read as code."""
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', source, flags=re.S)


def _interface_class_from_source(model_file: Path, names: list[str]) -> str | None:
    """Find the interface class by reading the declarations in the file.

    Used when the compiler's introspection fails, which happens for some
    component lists that the Python interface cannot parse. The class must
    declare the input and every output as fully qualified
    ``Modelica.Blocks.Interfaces.RealInput`` / ``RealOutput`` in its own body;
    nested classes are not counted for the class that contains them.
    """
    source = _strip_strings(model_file.read_text(encoding="utf-8"))
    header = re.compile(r"^([ \t]*)(?:(model|block|package)\s+(\w+)|end\s+(\w+)\s*;)", re.M)
    nested = re.compile(r"\n[ \t]*(?:model|block|package)\s+(\w+)\b.*?\n[ \t]*end\s+\1\s*;", re.S)
    port = re.compile(r"Modelica\.Blocks\.Interfaces\.Real(?:Input|Output)\s+(\w+)")
    stack: list[tuple[str, int]] = []
    for m in header.finditer(source):
        if m.group(3):
            stack.append((m.group(3), m.start()))
        elif m.group(4) and stack and stack[-1][0] == m.group(4):
            name, start = stack.pop()
            own_body = nested.sub("", source[start:m.end()])
            if set(names) <= set(port.findall(own_body)):
                return ".".join([n for n, _ in stack] + [name])
    return None


class Bench:
    """An OpenModelica session with one delivered model loaded.

    Use it as a context manager; leaving the block ends the session::

        with Bench("model.mo", task) as bench:
            traces = bench.simulate(task.experiments[0])
    """

    def __init__(self, model_file: str | Path, task: Task):
        self.task = task
        self.model_file = Path(model_file).resolve()
        self._workdir = tempfile.TemporaryDirectory(prefix="bench_")
        self.omc = OMCSessionZMQ()
        try:
            # A missing library is a fault of the installation, not of the
            # delivery, so it raises an ordinary error and never a BenchError.
            try:
                loaded = self.omc.sendExpression(f'loadModel(Modelica, {{"{MSL_VERSION}"}})')
            except OMCSessionException:
                loaded = False
            if not loaded:
                raise RuntimeError(f"Modelica Standard Library {MSL_VERSION} is not installed")
            if not self._send(f'loadFile("{self.model_file}")', "load"):
                raise BenchError("load", self._compiler_messages())
            # Simulate in an empty directory: a delivery must not depend on
            # files that happen to lie next to it.
            self.omc.sendExpression(f'cd("{self._workdir.name}")')
            self.model_class = self._find_interface_class()
        except BaseException:
            self.close()
            raise

    def __enter__(self) -> Bench:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """End the OpenModelica session and remove the working directory."""
        self.omc = None   # dropping the session sends quit() to the compiler
        self._workdir.cleanup()

    def query(self, expression: str):
        """Ask the compiler about the loaded classes; a failed query gives None."""
        try:
            return self.omc.sendExpression(expression)
        except OMCSessionException:
            return None

    def bases(self, cls: str) -> list[str]:
        """The classes that a class extends directly."""
        count = self.query(f"getInheritanceCount({cls})") or 0
        return [b for b in (self.query(f"getNthInheritedClass({cls}, {k})")
                            for k in range(1, count + 1)) if b]

    def ancestors(self, cls: str) -> list[str]:
        """Every class that a class extends, directly or through other classes."""
        found: list[str] = []
        pending = [cls]
        while pending:
            for base in self.bases(pending.pop()):
                if base not in found:
                    found.append(base)
                    pending.append(base)
        return found

    def components(self, descend: Callable[[str], bool] = delivered) -> Iterator[Component]:
        """Every component of the model class, found through the compiler.

        The walk follows the inheritance of every class it enters and enters
        the type of a component when ``descend`` admits it. By default it
        enters the delivered classes and leaves the library closed, so that
        a mass of the library is listed but not the components inside it.
        """
        def walk(cls: str, path: str, depth: int) -> Iterator[Component]:
            if depth > COMPONENT_DEPTH:
                return
            for base in self.bases(cls):
                if descend(base):
                    yield from walk(base, path, depth + 1)
            for entry in self.query(f"getComponents({cls})") or ():
                typ, name = entry[0], entry[1]
                instance = f"{path}.{name}" if path else name
                yield Component(instance, typ, tuple(entry[11]) if len(entry) > 11 else (), cls)
                if descend(typ) and self.query(f"getClassRestriction({typ})") in ("model", "block", "class"):
                    yield from walk(typ, instance, depth + 1)

        yield from walk(self.model_class, "", 0)

    def _compiler_messages(self) -> str:
        return (self.omc.sendExpression("getErrorString()") or "").strip()

    def _send(self, expression: str, stage: str, context: str = ""):
        """Send an expression; a compiler error becomes a BenchError of this stage.

        The Python interface raises an exception when the compiler reports an
        error, for instance a parse error on loading or a translation error
        on simulating; the bench reports it as a delivery it cannot drive.
        """
        try:
            return self.omc.sendExpression(expression)
        except OMCSessionException as error:
            message = re.sub(r"^\[OMC log for '.*?'\]:\s*", "", str(error), flags=re.S)
            raise BenchError(stage, context + message.strip()) from None

    def _find_interface_class(self) -> str:
        """The class with the task's input and all its outputs as components."""
        names = [self.task.input, *self.task.outputs]
        try:
            found = self._interface_class_by_introspection(set(names))
        except Exception:
            found = None
        if found is None:
            found = _interface_class_from_source(self.model_file, names)
        if found is None:
            raise BenchError("interface", "no model class declares RealInput %s and RealOutput %s"
                             % (self.task.input, ", ".join(self.task.outputs)))
        return found

    def _interface_class_by_introspection(self, names: set[str]) -> str | None:
        def classes(scope: str = "", depth: int = 0):
            listed = self.omc.sendExpression(f"getClassNames({scope})")
            for name in listed or ():
                full = f"{scope}.{name}" if scope else name
                if full.startswith("Modelica") or full in ("Complex", "ModelicaServices"):
                    continue
                yield full
                if depth < SEARCH_DEPTH:
                    yield from classes(full, depth + 1)

        for cls in classes():
            if self.omc.sendExpression(f"getClassRestriction({cls})") != "model":
                continue
            components = self.omc.sendExpression(f"getComponents({cls})") or ()
            if names <= {c[1] for c in components if len(c) > 1}:
                return cls
        return None

    def simulate(self, experiment: Experiment, variables: tuple[str, ...] = (),
                 modifiers: dict[str, float] | None = None) -> dict[str, np.ndarray]:
        """Simulate one experiment; returns ``time`` and every task output.

        The delivered model is instantiated as ``sol`` next to the signal
        source of the experiment, and the source output is connected to its
        input. The traces come on the simulator's output grid, which includes
        event instants; callers interpolate them onto the measurement times.

        ``variables`` names further variables of the model, relative to it
        (``"emf.v"``), that are returned as well. Protected variables are
        included; a variable that the result does not contain is left out.

        ``modifiers`` sets parameters of the model, again by their paths
        (``{"carriage.m": 3.0}``), as a modification of the instance. The
        modification replaces the value the delivered file gives them and
        leaves the file unchanged.
        """
        name = f"Bench_{experiment.name}"
        equations = [*experiment.wiring,
                     f"connect({experiment.signal}, sol.{self.task.input});"]
        wrapper = (f"model {name}\n"
                   f"  {self.model_class} sol{_modification(modifiers or {})};\n"
                   + "".join(f"  {d}\n" for d in experiment.source)
                   + "equation\n"
                   + "".join(f"  {e}\n" for e in equations)
                   + f"end {name};\n")
        context = f"{experiment.name}: "
        if not self._send('loadString("%s")' % wrapper.replace('"', '\\"'), "simulate", context):
            raise BenchError("simulate", context + "wrapper does not load: "
                             + self._compiler_messages())
        flags = ', simflags="-emit_protected"' if variables else ""
        result = self._send(
            f"simulate({name}, stopTime={experiment.stop_time}, "
            f"numberOfIntervals={experiment.intervals}, tolerance={TOLERANCE}{flags})",
            "simulate", context)
        # The result file is the reliable sign of success: the simulator's
        # messages can report a successful initialization and then abort.
        if not result.get("resultFile"):
            raise BenchError("simulate", f"{experiment.name}: "
                             + (result.get("messages") or "no result file").strip())
        names = list(self.task.outputs)
        if variables:
            available = set(self.omc.sendExpression(
                f'readSimulationResultVars("{result["resultFile"]}")') or ())
            names += [v for v in variables if f"sol.{v}" in available]
        columns = self._send(
            f'readSimulationResult("{result["resultFile"]}", {{time, '
            + ", ".join(f"sol.{n}" for n in names) + "})",
            "simulate", context)
        self.omc.sendExpression("closeSimulationResultFile()")
        traces = {"time": np.asarray(columns[0])}
        for variable, values in zip(names, columns[1:]):
            traces[variable] = np.asarray(values)
        return traces


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    task = load_task(argv[0])
    try:
        with Bench(argv[1], task) as bench:
            print(f"interface class: {bench.model_class}")
            for experiment in task.experiments:
                try:
                    traces = bench.simulate(experiment)
                except BenchError as e:
                    if experiment.role != "test":
                        raise
                    print(f"{experiment.name:<18} {experiment.role:<10} does not simulate ({e})")
                    continue
                print(f"{experiment.name:<18} {experiment.role:<10} simulated, "
                      f"{traces['time'].size} output points")
    except BenchError as e:
        print(f"cannot drive the delivery ({e})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
